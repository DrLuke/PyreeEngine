"""Simple fullscreen shader

Allows to easily apply a fullscreen shader to the screen without big hassle.
Enables multi-staged rendering by exposing Framebuffer content as textures."""

from OpenGL.GL import *

from PyreeEngine.layers import LayerContext
from PyreeEngine.framebuffers import RegularFramebuffer, DefaultFramebuffer
from PyreeEngine.util import Resolution
from PyreeEngine.shaders import HotloadingShader, DebugShader
from PyreeEngine.basicObjects import FSQuad
from PyreeEngine.camera import Camera

from typing import List, Union


class SimpleShader():
    def __init__(self, context: LayerContext, quadz: float = 0):
        self.context: LayerContext = context
        self.context.addresolutioncallback(self.resolutionchangecallback)

        self.quadz: float = quadz

        self.framebuffer: RegularFramebuffer = RegularFramebuffer(self.context.resolution)
        self.shader: HotloadingShader = None
        self.fsquad: FSQuad = FSQuad(z=quadz)
        self.camera: Camera = Camera()

        self.updateshader(self.shader)

    def updateshader(self, newshader: HotloadingShader):
        self.shader = newshader

        if self.shader is not None:
            self.fsquad.shader = self.shader
        else:
            self.fsquad.shader = DebugShader()

    def resolutionchangecallback(self, newres: Resolution):
        self.framebuffer = RegularFramebuffer(self.context.resolution)  # Regenerate Framebuffer

    def __del__(self):
        self.context.removeresolutionscallback(self.resolutionchangecallback)

    def tick(self):
        self.shader.tick()

        self.framebuffer.bindFramebuffer()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.setuniform("time", self.context.time)
        self.setuniform("dt", self.context.dt)
        self.setuniform("frame", self.context.frame)

        self.fsquad.render(self.camera.viewMatrix)

        self.framebuffer.rendertoscreen()

    def setuniform(self, name: str, value: Union[any, List[any]]):
        self.fsquad.uniforms[name] = value

    def clearuniforms(self):
        self.fsquad.uniforms = {}
