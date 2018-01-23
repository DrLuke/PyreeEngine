from pyreeEngine.engine import PyreeObject
from OpenGL.GL import *
from OpenGL.GL import shaders


from pyreeEngine.util import ObjLoader
from pathlib import Path

import numpy as np

class ModelObject(PyreeObject):
    def __init__(self):
        super(ModelObject, self).__init__()


class ObjModelObject(ModelObject):
    def __init__(self, pathToObj: Path):
        super(ObjModelObject, self).__init__()

        self.vbo = None
        self.vao = None

        self.tricount = None

        self.vertexCode = """#version 450 core
        #extension GL_ARB_separate_shader_objects : enable
        
        layout (location = 0) in vec3 vert_Position;
        layout (location = 1) in vec2 vert_UV;
        layout (location = 2) in vec3 vert_Normal;
        
        layout (location = 0) out vec3 vert_Position_out;
        layout (location = 1) out vec2 vert_UV_out;
        layout (location = 2) out vec3 vert_Normal_out;
        
        uniform mat4 MVP;
        
        void main()
        {
            gl_Position = MVP * vec4(vert_Position * 0.001, 1);
            vert_Position_out = (MVP * vec4(vert_Position * 0.001, 1)).xyz;
            vert_UV_out = vert_UV;
            vert_Normal_out = vert_Normal;
        }
        """
        self.vertShader = shaders.compileShader(self.vertexCode, GL_VERTEX_SHADER)

        self.fragCode = """#version 450 core
        #extension GL_ARB_separate_shader_objects : enable
        
        layout (location = 0) in vec3 vert_Position;
        layout (location = 1) in vec2 vert_UV;
        layout (location = 2) in vec3 vert_Normal;
        
        out vec4 outCol;

        void main()
        {
            outCol = vec4(vert_Normal, 1.);
        }
        """
        self.fragShader = shaders.compileShader(self.fragCode, GL_FRAGMENT_SHADER)
        self.shaderProgram = shaders.compileProgram(self.fragShader, self.vertShader)

        if pathToObj is not None:
            self.loadFromObj(pathToObj)


    def loadFromObj(self, pathToObj: Path):
        verts, texdata = ObjLoader(pathToObj)
        self.tricount = int(len(verts) / 8)

        self.vbo = glGenBuffers(1)

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, verts.nbytes, verts, GL_STATIC_DRAW)

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 8 * verts.itemsize, ctypes.c_void_p(0))    # XYZ
        glEnableVertexAttribArray(0)

        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 8 * verts.itemsize, ctypes.c_void_p(3 * verts.itemsize))   # UV
        glEnableVertexAttribArray(1)

        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 8 * verts.itemsize, ctypes.c_void_p(5 * verts.itemsize))   # Normal
        glEnableVertexAttribArray(2)

    def render(self, viewProjMatrix):
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBindVertexArray(self.vao)

        glUseProgram(self.shaderProgram)

        uniformLoc = glGetUniformLocation(self.shaderProgram, "MVP")
        if not uniformLoc == -1:
            glUniformMatrix4fv(uniformLoc, 1, GL_TRUE, viewProjMatrix*self.getModelMatrix())

        glDrawArrays(GL_TRIANGLES, 0, self.tricount)
