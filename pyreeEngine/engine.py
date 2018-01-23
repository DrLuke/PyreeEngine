from typing import Union, List, Tuple, Callable
import numpy as np
import quaternion
import math
from pyreeEngine.util import Vec3

import glfw
import time

from OpenGL.GL import *

class PyreeObject():
    def __init__(self):
        self.children = []
        self.pos = Vec3()
        self.rot = np.quaternion(1, 0, 0, 0)

    def render(self, mat):
        pass

    def getModelMatrix(self) -> np.matrix:
        translationMat = np.matrix([[1, 0, 0, self.pos[0]],
                                    [0, 1, 0, self.pos[1]],
                                    [0, 0, 1, self.pos[2]],
                                    [0, 0, 0, 1]])

        orientMat = np.identity(4)
        orientMat[:3, :3] = quaternion.as_rotation_matrix(self.rot)

        return orientMat * translationMat

class LaunchOptions:
    def __init__(self):
        self.resolution = None
        self.fullscreen = False
        self.monitor = None

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

class Engine():
    def __init__(self, config: LaunchOptions):
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

    def render(self, objects: List[PyreeObject], camera: Camera) -> None:
        projectionMatrix = camera.projectionMatrix
        viewMatrix = camera.viewMatrix

        for object in objects:
            object.render(projectionMatrix * viewMatrix)

