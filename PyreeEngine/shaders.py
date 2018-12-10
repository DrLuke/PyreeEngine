"""Handy shader classes"""

from OpenGL.GL import *
from OpenGL.GL import shaders

import traceback, sys

from pathlib import Path

import inotify_simple


class Shader():
    def __init__(self):
        self.shaderprogram: shaders.ShaderProgram = None

    def getshaderprogram(self) -> shaders.ShaderProgram:
        return self.shaderprogram


class DebugShader(Shader):
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

    def getshaderprogram(self):
        if DebugShader.program is None:
            DebugShader.vertShader = shaders.compileShader(DebugShader.vertexCode, GL_VERTEX_SHADER)
            DebugShader.fragShader = shaders.compileShader(DebugShader.fragCode, GL_FRAGMENT_SHADER)
            DebugShader.program = shaders.compileProgram(DebugShader.vertShader, DebugShader.fragShader)

        return DebugShader.program

class FullscreenTexture(Shader):
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
        
        layout(binding=0) uniform sampler2D tex1;
        
        layout (location = 0) out vec4 colorOut;
        void main()
        {
            colorOut = texture(tex1, vec2(uvIn.x, uvIn.y)).rgba;
            colorOut.a = 1.;
        }
        """

    vertShader = None
    fragShader = None
    program = None

    def getshaderprogram(self):
        if FullscreenTexture.program is None:
            FullscreenTexture.vertShader = shaders.compileShader(FullscreenTexture.vertexCode, GL_VERTEX_SHADER)
            FullscreenTexture.fragShader = shaders.compileShader(FullscreenTexture.fragCode, GL_FRAGMENT_SHADER)
            FullscreenTexture.program = shaders.compileProgram(FullscreenTexture.vertShader, FullscreenTexture.fragShader)

        return FullscreenTexture.program

class HotloadingShader(Shader):
    def __init__(self, vertexpath: Path, fragmentpath: Path, geometrypath: Path = None):
        super(HotloadingShader, self).__init__()
        self.shaderprogram = DebugShader().getshaderprogram()  # Have default shader program
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

            if self.shaderprogram is not None:
                pass  # glDeleteProgram(self.program)
            if self.geometryPath is None:
                self.shaderprogram = shaders.compileProgram(self.vertShader, self.fragShader)
            else:
                self.shaderprogram = shaders.compileProgram(self.vertShader, self.fragShader, self.geomShader)
        except Exception as exc:
            print(traceback.format_exc(), file=sys.stderr)
            print(exc, file=sys.stderr)

    def tick(self):
        events = self.inotify.read(0)
        for event in events:
            if event.name == self.vertexPath.name or event.name == self.fragmentPath.name or (
                    self.geometryPath is not None and self.geometryPath.name == self.geometryPath.name):
                self.regenShader()

    def __del__(self):
        if self.shaderprogram:
            pass  # shaders.glDeleteShader(self.program)
