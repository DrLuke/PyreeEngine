from typing import List

from PyreeEngine.engine import PyreeObject
from OpenGL.GL import *
from OpenGL.GL import shaders

# from pyreeEngine.util import ObjLoader
from PyreeEngine.objloader import ObjLoader
from PyreeEngine.shaders import Shader, DebugShader
from PyreeEngine.engine import GeometryObject
from PyreeEngine.shaders import DebugShader
from pathlib import Path

import numpy as np


class ModelObject(GeometryObject):
    def __init__(self, pathToObj: Path = None):
        super(ModelObject, self).__init__()

        self.vbo = None
        self.vao = None

        self.tricount = None

        self.textures = []

        self.shader: Shader = DebugShader()

        if pathToObj is not None:
            self.loadFromObj(pathToObj)

        self.uniforms = {}

    def loadFromObj(self, pathToObj: Path):
        vertlist = ObjLoader(pathToObj).verts
        verts = []
        for l in vertlist:
            verts += l
        self.loadFromVerts(verts)

    def loadFromVerts(self, verts: List[float]):
        if verts is not np.array:
            verts = np.array(verts, np.float32)
        self.tricount = int(len(verts) / 8)

        if self.vbo is None:
            self.vbo = glGenBuffers(1)

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, verts.nbytes, verts, GL_STATIC_DRAW)

        if self.vao is None:
            self.vao = glGenVertexArrays(1)
            glBindVertexArray(self.vao)

            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 8 * verts.itemsize, ctypes.c_void_p(0))  # XYZ
            glEnableVertexAttribArray(0)

            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 8 * verts.itemsize,
                                  ctypes.c_void_p(3 * verts.itemsize))  # UV
            glEnableVertexAttribArray(1)

            glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 8 * verts.itemsize,
                                  ctypes.c_void_p(5 * verts.itemsize))  # Normal
            glEnableVertexAttribArray(2)

    def render(self, viewProjMatrix):
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBindVertexArray(self.vao)

        glUseProgram(self.shader.getshaderprogram())

        uniformLoc = glGetUniformLocation(self.shader.getshaderprogram(), "MVP")
        if not uniformLoc == -1:
            glUniformMatrix4fv(uniformLoc, 1, GL_TRUE, viewProjMatrix * self.getModelMatrix())

        for uniformName in self.uniforms:
            uniform = self.uniforms[uniformName]
            uniformLoc = glGetUniformLocation(self.shader.getshaderprogram(), uniformName)
            if not uniformLoc == -1:
                if type(uniform) == float or type(uniform) == int:
                    glUniform1f(uniformLoc, float(uniform))
                elif len(uniform) == 2:
                    glUniform2f(uniformLoc, uniform[0], uniform[1])
                elif len(uniform) == 3:
                    glUniform3f(uniformLoc, uniform[0], uniform[1], uniform[2])
                elif len(uniform) == 4:
                    glUniform4f(uniformLoc, uniform[0], uniform[1], uniform[2], uniform[3])

        texUnit = GL_TEXTURE0
        for tex in self.textures:
            glActiveTexture(texUnit)
            glBindTexture(GL_TEXTURE_2D, tex)
            texUnit += 1

        glDrawArrays(GL_TRIANGLES, 0, self.tricount)

    def __del__(self):
        if self.vbo is not None:
            glDeleteBuffers(1, [self.vbo])
        if self.vao is not None:
            glDeleteVertexArrays(1, [self.vao])


class FSQuad(ModelObject):
    def __init__(self, z: float = 0):
        super(FSQuad, self).__init__()

        verts = np.array([1, -1, z, 1, 0, 0, 0, 1,
                          -1, 1, z, 0, 1, 0, 0, 1,
                          -1, -1, z, 0, 0, 0, 0, 1,
                          1, -1, z, 1, 0, 0, 0, 1,
                          1, 1, z, 1, 1, 0, 0, 1,
                          -1, 1, z, 0, 1, 0, 0, 1], np.float32)

        self.loadFromVerts(verts)
