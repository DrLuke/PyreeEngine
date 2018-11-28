from typing import Union, List, Tuple, Callable, Dict
import numpy as np
import quaternion
import math
from PyreeEngine.util import Vec3
from PyreeEngine.camera import *

import glfw
import ctypes
import time

from OpenGL.GL import *
from OpenGL.GL import shaders

import traceback, sys



class PyreeObject():
    def __init__(self):
        self.children = []
        self.parent = None
        self.pos = Vec3()
        self.rot = np.quaternion(1, 0, 0, 0)
        self.scale = Vec3(1, 1, 1)

    def render(self, mat):
        pass

    def getModelMatrix(self) -> np.matrix:
        pos = self.pos
        if self.parent is not None:
            pos += self.parent.pos
        translationMat = np.matrix([[1, 0, 0, pos[0]],
                                    [0, 1, 0, pos[1]],
                                    [0, 0, 1, pos[2]],
                                    [0, 0, 0, 1]])

        orientMat = np.identity(4)
        rot = self.rot
        if self.parent is not None:
            rot = rot * self.parent.rot
        orientMat[:3, :3] = quaternion.as_rotation_matrix(rot)

        scale = self.scale
        if self.parent is not None:
            scale *= self.parent.scale
        scaleMat = np.matrix([[scale[0], 0, 0, 0],
                              [0, scale[1], 0, 0],
                              [0, 0, scale[2], 0],
                              [0, 0, 0, 1]])

        return translationMat * orientMat * scaleMat

class GeometryObject(PyreeObject):
    def __init__(self):
        super(GeometryObject, self).__init__()

class LightObject(PyreeObject):
    def __init__(self):
        super(LightObject, self).__init__()


class LaunchOptions:
    def __init__(self):
        self.resolution = None
        self.fullscreen = False
        self.monitor = None

        self.projectPath = None     # type: Path



class NodeGlobalData():
    def __init__(self):
        self.__PYREE__lasttarget__ = None

        self.resolution = [1, 1]
        self.time = 0
        self.dt = 0.01
        self.resChanged = True
        self.aspect = 1

        self.otherData = {}

class Monitor():
    """Monitor abstraction

    Stores name and videomodes of monitor, and can be updated on changes
    """
    def __init__(self, monitorptr: ctypes.POINTER(ctypes.POINTER(glfw._GLFWmonitor))):
        if monitorptr is not None:
            self.parse(monitorptr)

    def parse(self, monitorptr: ctypes.POINTER(ctypes.POINTER(glfw._GLFWmonitor))):
        self.monitorptr: ctypes.POINTER(ctypes.POINTER(glfw._GLFWmonitor)) = monitorptr

        self.vidmodes = glfw.get_video_modes(self.monitorptr)
        self.name = glfw.get_monitor_name(self.monitorptr)


from PyreeEngine.layers import LayerContext, LayerManager, ProgramConfig
import json
import pythonosc.dispatcher
import pythonosc.osc_server
import pythonosc.udp_client
import asyncio

class Engine():
    def __init__(self):

        self.initglfw()

        self.monitors: Dict[str, Monitor] = {}
        self.monitors = self.getmonitors()

        resolution = (1280, 720)

        #self.window = glfw.create_window(1920, 1200, "PyreeEngine", self.monitors[1], None)
        self.window = glfw.create_window(resolution[0], resolution[1], "PyreeEngine", None, None)
        glfw.set_framebuffer_size_callback(self.window, self.framebufferResizeCallback)

        glfw.make_context_current(self.window)

        glEnable(GL_MULTISAMPLE)
        glEnable(GL_DEPTH_TEST)

        self.init()

        ## Program Config
        with open("programconfig.json", "r") as f:
            self.programconfig = ProgramConfig(**json.load(f))

        ## OSC setup
        self.oscdispatcher = pythonosc.dispatcher.Dispatcher()
        self.oscserverloop = asyncio.get_event_loop()
        self.oscserver = pythonosc.osc_server.AsyncIOOSCUDPServer((self.programconfig.oscserveraddress, self.programconfig.oscserverport), self.oscdispatcher, self.oscserverloop)

        self.oscclient = pythonosc.udp_client.UDPClient(self.programconfig.oscclientaddress, self.programconfig.oscclientport)

        ## Layer Context and Manager
        self.layercontext: LayerContext = LayerContext()
        self.layercontext.setresolution(resolution[0], resolution[1])
        self.layercontext.time = glfw.get_time()

        self.layercontext.oscdispatcher = self.oscdispatcher
        self.layercontext.oscclient = self.oscclient

        newtime = glfw.get_time()
        self.layercontext.dt = newtime - self.layercontext.time
        self.layercontext.time = newtime

        self.layermanager: LayerManager = LayerManager(self.programconfig, self.layercontext)


    def getmonitors(self) -> Dict[str, ctypes.POINTER(ctypes.POINTER(glfw._GLFWmonitor))]:
        monitors = {}
        for monitor in glfw.get_monitors():
            newmonitor = Monitor(monitor)
            monitors[newmonitor.name] = newmonitor
        return monitors

    def initglfw(self):
        glfw.init()  # TODO: Check if init successful, exit otherwise

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 5)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.SAMPLES, 4)
        glfw.window_hint(glfw.AUTO_ICONIFY, False)

    def init(self):
        pass

    def startmainloop(self) -> None:
        while (not glfw.window_should_close(self.window)):
            self.mainLoop()

    def mainLoop(self) -> None:
        glfw.make_context_current(self.window)

        glfw.poll_events()

        newtime = glfw.get_time()
        self.layercontext.dt = newtime - self.layercontext.time
        self.layercontext.time = newtime

        glClearColor(0.2, 0.2, 0.3, 1.)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glViewport(0, 0, self.layercontext.resolution[0], self.layercontext.resolution[1])

        self.loop()

        glfw.swap_buffers(self.window)

        glfw.swap_interval(1)

    def framebufferResizeCallback(self, window, width, height):
        self.layercontext.setresolution(width, height)

    def loop(self):
        self.layermanager.tick()

    def render(self, objects: List[PyreeObject], camera: Camera, framebuffer) -> None:
        projectionMatrix = camera.projectionMatrix
        viewMatrix = camera.viewMatrix

        for object in objects:
            object.render(projectionMatrix * viewMatrix)
