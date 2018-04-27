from typing import List

from pyreeEngine.engine import PyreeObject
from OpenGL.GL import *
from OpenGL.GL import shaders


from pyreeEngine.util import ObjLoader
from pyreeEngine.engine import DeferredShader, ModelObject
from pathlib import Path

import numpy as np


class ModelObject(ModelObject):
    def __init__(self, pathToObj: Path=None):
        super(ModelObject, self).__init__()

        self.vbo = None
        self.vao = None

        self.tricount = None

        self.shaderProgram = DeferredShader.getShaderProgram()

        if pathToObj is not None:
            self.loadFromObj(pathToObj)


    def loadFromObj(self, pathToObj: Path):
        verts, texdata = ObjLoader(pathToObj)
        self.loadFromVerts(verts)


    def loadFromVerts(self, verts: List[float]):
        if verts is not np.array:
            verts = np.array(verts, np.float32)
        self.tricount = int(len(verts) / 8)

        self.vbo = glGenBuffers(1)

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, verts.nbytes, verts, GL_STATIC_DRAW)

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 8 * verts.itemsize, ctypes.c_void_p(0))  # XYZ
        glEnableVertexAttribArray(0)

        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 8 * verts.itemsize, ctypes.c_void_p(3 * verts.itemsize))  # UV
        glEnableVertexAttribArray(1)

        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 8 * verts.itemsize,
                              ctypes.c_void_p(5 * verts.itemsize))  # Normal
        glEnableVertexAttribArray(2)

    def render(self, viewProjMatrix):
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBindVertexArray(self.vao)

        glUseProgram(self.shaderProgram)

        uniformLoc = glGetUniformLocation(self.shaderProgram, "MVP")
        if not uniformLoc == -1:
            glUniformMatrix4fv(uniformLoc, 1, GL_TRUE, viewProjMatrix*self.getModelMatrix())

        glDrawArrays(GL_TRIANGLES, 0, self.tricount)
