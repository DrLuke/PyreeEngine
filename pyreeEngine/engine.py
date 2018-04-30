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


class DebugShader():
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

    layout (location = 0) out vec4 colorOut;
    void main()
    {
        colorOut = vec4(uvIn, 0, 1);
    }
    """

    vertShader = None
    fragShader = None
    program = None

    @staticmethod
    def getShaderProgram():
        if DebugShader.program is None:
            DebugShader.vertShader = shaders.compileShader(DebugShader.vertexCode, GL_VERTEX_SHADER)
            DebugShader.fragShader = shaders.compileShader(DebugShader.fragCode, GL_FRAGMENT_SHADER)
            DebugShader.program = shaders.compileProgram(DebugShader.vertShader, DebugShader.fragShader)

        return DebugShader.program

from pathlib import Path
import inotify_simple

class HotloadingShader():
    def __init__(self, vertexpath: Path, fragmentpath: Path, geometrypath: Path=None):
        self.program = DebugShader.getShaderProgram()   # Have default shader program
        self.vertShader = None
        self.fragShader = None
        self.geomShader = None

        fl = inotify_simple.flags.CREATE | inotify_simple.flags.MODIFY | inotify_simple.flags.MOVED_TO
        self.inotify = inotify_simple.INotify()

        self.vertexPath = vertexpath
        self.vertWatch = self.inotify.add_watch(self.vertexPath.parent, fl)

        self.fragmentPath = fragmentpath
        self.fragWatch = self.inotify.add_watch(self.fragmentPath.parent, fl)

        self.geometryPath = geometrypath
        if geometrypath is not None:
            self.geomWatch = self.inotify.add_watch(self.geometryPath.parent, fl)

        self.regenShader()

    def regenShader(self):
        if self.vertexPath.exists():
            with self.vertexPath.open() as f:
                self.vertShader = shaders.compileShader(f.read(), GL_VERTEX_SHADER)
        else:
            print("HOTLOADSHADER ERROR: vertex file doesn't exist")
            return
        if self.fragmentPath.exists():
            with self.fragmentPath.open() as f:
                self.fragShader = shaders.compileShader(f.read(), GL_FRAGMENT_SHADER)
        else:
            print("HOTLOADSHADER ERROR: fragment file doesn't exist")
            return

        if self.geometryPath is not None:
            if self.geometryPath.exists():
                with self.geometryPath.open() as f:
                    self.vertShader = shaders.compileShader(f.read(), GL_FRAGMENT_SHADER)
            else:
                print("HOTLOADSHADER ERROR: geometry file doesn't exist")
                return

        if self.program is not None:
            pass#glDeleteProgram(self.program)
        if self.geometryPath is None:
            self.program = shaders.compileProgram(self.vertShader, self.fragShader)
        else:
            self.program = shaders.compileProgram(self.vertShader, self.fragShader, self.geomShader)

    def tick(self):
        events = self.inotify.read(0)
        for event in events:
            if event.name == self.vertexPath.name or event.name == self.fragmentPath.name or (self.geometryPath is not None and self.geometryPath.name == self.geometryPath.name):
                self.regenShader()

    def getShaderProgram(self):
        return self.program

    #def __del__(self):
    #    shaders.glDeleteShader(self.program)

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
        self.projectionMatrix = np.identity(4)
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


class OrthoCamera(Camera):
    def __init__(self):
        super(OrthoCamera, self).__init__()

        self.setOrtho(1, 640/480, 0.01, 100.)

    def setOrtho(self, sizeY, aspect, nearZ, farZ):
        t,b = sizeY / 2, -sizeY / 2
        r,l = t*aspect, b*aspect
        self.projectionMatrix = np.matrix([[2/(r-l), 0,       0,               -(r+l)/(r-l)],
                                           [0,       2/(t-b), 0,               -(t+b)/(t-b)],
                                           [0,       0,       -2/(farZ-nearZ), -(farZ + nearZ)/(farZ - nearZ)],
                                           [0,       0,       0,               1]])


class NodeGlobalData():
    def __init__(self):
        self.resolution = [1, 1]
        self.time = 0
        self.dt = 0.01
        self.resChanged = True
        self.aspect = 1

        self.otherData = {}


from pyreeEngine.nodeManager import NodeManager
class Engine():
    def __init__(self, config: LaunchOptions):

        ####################
        # TODO: Init glfw and opengl
        glfw.init()     # TODO: Check if init successful, exit otherwise

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 5)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.SAMPLES, 4)

        self.window = glfw.create_window(640, 480, "PyreeEngine", None, None)

        glfw.set_framebuffer_size_callback(self.window, self.framebufferResizeCallback)


        glfw.make_context_current(self.window)

        glEnable(GL_MULTISAMPLE)
        glEnable(GL_DEPTH_TEST)

        self.init()

        ### Project management
        self.globalData = NodeGlobalData()
        self.globalData.resolution = [640, 480]
        self.globalData.time = glfw.get_time()
        self.nodeMan = NodeManager(config.projectPath, self.globalData)

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

        newtime = glfw.get_time()
        self.globalData.dt = newtime - self.globalData.time
        self.globalData.time = newtime

        glClearColor(0.2, 0.2, 0.3, 1.)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glViewport(0, 0, self.globalData.resolution[0], self.globalData.resolution[1])

        self.loop()

        glfw.swap_buffers(self.window)

        self.globalData.resChanged = False

        glfw.swap_interval(1)

    def framebufferResizeCallback(self, window, width, height):
        self.globalData.resChanged = True
        self.globalData.resolution = [width, height]
        self.globalData.aspect = width/height

    def loop(self):
        self.nodeMan.tick()

    def render(self, objects: List[PyreeObject], camera: Camera, framebuffer) -> None:
        projectionMatrix = camera.projectionMatrix
        viewMatrix = camera.viewMatrix

        for object in objects:
            object.render(projectionMatrix * viewMatrix)
