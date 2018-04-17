from typing import Union, List, Tuple, Callable
import numpy as np
import quaternion
import math
from pyreeEngine.util import Vec3

import glfw
import time

from OpenGL.GL import *
from OpenGL.GL import shaders

class DeferredShader():
    """Singleton class containing the default shader for deferred rendering. This way the shader program only has
    to exist once on the GPU."""
    vertexCode = """#version 450 core
    layout (location = 0) in vec3 posIn;
    layout (location = 1) in vec2 uvIn;
    layout (location = 2) in vec3 normIn;

    layout (location = 0) out vec3 posOut;
    layout (location = 1) out vec2 uvOut;
    layout (location = 2) out vec3 normOut;

    uniform mat4 MVP;

    void main()
    {
        gl_Position = MVP * vec4(posIn, 1);
        posOut = (MVP * vec4(posIn, 1)).xyz;
        uvOut = uvIn;
        normOut = normIn;
    }
    """

    fragCode = """#version 450 core
    layout (location = 0) in vec3 posIn;
    layout (location = 1) in vec2 uvIn;
    layout (location = 2) in vec3 normIn;
    
    layout (location = 0) out vec3 albedoOut;
    layout (location = 1) out vec3 normalOut;
    void main()
    {
        albedoOut = normIn; // TODO: Texturemapping!
        normalOut = normIn;
    }
    """

    vertShader = None
    fragShader = None
    program = None

    @staticmethod
    def getShaderProgram():
        if DeferredShader.program is None:
            DeferredShader.vertShader = shaders.compileShader(DeferredShader.vertexCode, GL_VERTEX_SHADER)
            DeferredShader.fragShader = shaders.compileShader(DeferredShader.fragCode, GL_FRAGMENT_SHADER)
            DeferredShader.program = shaders.compileProgram(DeferredShader.vertShader, DeferredShader.fragShader)

        return DeferredShader.program

class PyreeObject():
    def __init__(self):
        self.children = []
        self.pos = Vec3()
        self.rot = np.quaternion(1, 0, 0, 0)
        self.scale = Vec3(1, 1, 1)

    def render(self, mat):
        pass

    def getModelMatrix(self) -> np.matrix:
        translationMat = np.matrix([[1, 0, 0, self.pos[0]],
                                    [0, 1, 0, self.pos[1]],
                                    [0, 0, 1, self.pos[2]],
                                    [0, 0, 0, 1]])

        orientMat = np.identity(4)
        orientMat[:3, :3] = quaternion.as_rotation_matrix(self.rot)

        scaleMat = np.matrix([[self.scale[0], 0, 0, 0],
                              [0, self.scale[1], 0, 0],
                              [0, 0, self.scale[2], 0],
                              [0, 0, 0, 1]])

        return translationMat * orientMat * scaleMat

class ModelObject(PyreeObject):
    def __init__(self):
        super(ModelObject, self).__init__()

class LightObject(PyreeObject):
    def __init__(self):
        super(LightObject, self).__init__()

class Framebuffer():
    def __init__(self):
        self.fbo = None

    def bindFramebuffer(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

class DefaultFramebuffer():
    def __init__(self):
        self.fbo = 0    # OpenGL default framebuffer

class DeferredFramebuffer():
    def __init__(self):
        pass

class LaunchOptions:
    def __init__(self):
        self.resolution = None
        self.fullscreen = False
        self.monitor = None

        self.projectPath = None     # type: Path

class Camera():
    def __init__(self) -> None:
        self.projectionMatrix = None
        self.viewMatrix = None
        self.pos = Vec3()

        self.lookAt(np.array([0, 0, 0], np.float32), np.array([0, 0, -1], np.float32))

    def lookAt(self, eye: np.array, target: np.array, up: np.array = np.array([0, 1, 0], np.float32)) -> None:
        forward = target - eye
        forward /= np.linalg.norm(forward)
        up /= np.linalg.norm(up)
        side = np.cross(forward, up)
        up = np.cross(side, forward)

        orientMat = np.transpose(np.matrix([[side[0], up[0], -forward[0], 0],
                                            [side[1], up[1], -forward[1], 0],
                                            [side[2], up[2], -forward[2], 0],
                                            [0,       0,     0,          1]], np.float32))

        translMat = np.matrix([[1, 0, 0, -eye[0]],
                               [0, 1, 0, -eye[1]],
                               [0, 0, 1, -eye[2]],
                               [0, 0, 0, 1]], np.float32)

        self.viewMatrix = orientMat * translMat

class PerspectiveCamera(Camera):
    def __init__(self) -> None:
        super(PerspectiveCamera, self).__init__()

        self.setPerspective(60, 640/480, 0.01, 100.)

    def setPerspective(self, fovY, aspect, nearZ, farZ) -> None:
        s = 1.0 / math.tan(math.radians(fovY) / 2.0)
        sx, sy = s / aspect, s
        zz = (farZ + nearZ) / (nearZ - farZ)
        zw = 2 * farZ * nearZ / (nearZ - farZ)
        self.projectionMatrix = np.matrix([[sx, 0, 0, 0],
                                           [0, sy, 0, 0],
                                           [0, 0, zz, zw],
                                           [0, 0, -1, 0]])

from pyreeEngine.nodeManager import NodeManager
class Engine():
    def __init__(self, config: LaunchOptions):
        ### Project management
        self.nodeMan = NodeManager(config.projectPath)

        while(True):

            self.nodeMan.tick()

            time.sleep(0.01)


        ####################
        # TODO: Init glfw and opengl
        glfw.init()     # TODO: Check if init successful, exit otherwise

        self.window = glfw.create_window(640, 480, "PyreeEngine", None, None)


        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        glfw.make_context_current(self.window)

        glEnable(GL_DEPTH_TEST)

        self.init()

        while(not glfw.window_should_close(self.window)):
            self.mainLoop()

    def init(self):
        pass

    def mainLoop(self) -> None:
        # TODO: Query communications (midi, sockets)
        # TODO: Check for changes in code
        # TODO: Handle resize events from glfw or communications
        glfw.make_context_current(self.window)

        glfw.poll_events()

        glClearColor(0.2, 0.2, 0.3, 1.)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glViewport(0, 0, 640, 480)

        self.loop()

        glfw.swap_buffers(self.window)

        time.sleep(0.01)    # TODO: Proper frame limiting

    def loop(self):
        self.render([], PerspectiveCamera())

    def render(self, objects: List[PyreeObject], camera: Camera, framebuffer) -> None:
        projectionMatrix = camera.projectionMatrix
        viewMatrix = camera.viewMatrix

        for object in objects:
            object.render(projectionMatrix * viewMatrix)
