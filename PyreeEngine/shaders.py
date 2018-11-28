"""Handy shader classes"""

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

from pathlib import Path

import inotify_simple

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
        print(self.fragmentPath);
        try:
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
        except Exception as exc:
            print(traceback.format_exc(), file=sys.stderr)
            print(exc, file=sys.stderr)


    def tick(self):
        events = self.inotify.read(0)
        for event in events:
            if event.name == self.vertexPath.name or event.name == self.fragmentPath.name or (self.geometryPath is not None and self.geometryPath.name == self.geometryPath.name):
                self.regenShader()

    def getShaderProgram(self):
        return self.program

    #def __del__(self):
    #    shaders.glDeleteShader(self.program)