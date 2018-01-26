from pyreeEngine import *
from pyreeEngine.engine import Engine, PerspectiveCamera
from pyreeEngine.basicObjects import ObjModelObject
from pyreeEngine.util import *

import glfw
from OpenGL.GL import *
from OpenGL.GL import shaders

import math

import time

import numpy as np
import quaternion

class exampleApp(Engine):
    def init(self):
        self.camera = PerspectiveCamera()

        self.model1 = ObjModelObject(Path("deer.obj"))
        self.model1.scale = Vec3(0.001, 0.001, 0.001)
        self.model2 = ObjModelObject(Path("deer.obj"))
        self.model2.scale = Vec3(0.001, 0.001, 0.001)

    def loop(self):
        t = glfw.get_time() * 1

        self.camera.lookAt(Vec3(math.sin(t) * 2, 2, math.cos(t) * 2), Vec3(0, 0.4, 0))

        self.model2.pos = Vec3(-0.15 - math.sin(t*3.14159*4.) * 0.05, math.sin(t*3.14159*4.) * 0.1 + 0.2, 0)
        self.model2.rot = quaternion.from_euler_angles(0, t*10., 0)

        self.render([self.model1, self.model2], self.camera, None)

if __name__ == "__main__":
    eng = exampleApp(None)
