"""Framebuffer classes"""

from OpenGL.GL import *
from PyreeEngine.util import Resolution
from PyreeEngine.basicObjects import FSQuad
from PyreeEngine.shaders import FullscreenTexture
from PyreeEngine.camera import Camera

class Framebuffer():
    def __init__(self):
        self.fbo = None

    def bindFramebuffer(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)


class DefaultFramebuffer():
    """Default OpenGL framebuffer object required for rendering to screen"""

    def __init__(self):
        self.fbo = 0  # OpenGL default framebuffer

    def bindFramebuffer(self):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)


class RegularFramebuffer(Framebuffer):
    """Framebuffer with 2d Texture and depth attachment"""

    fsquad: FSQuad = None
    fstextureshader: FullscreenTexture = None
    fscamera: Camera = None

    def __init__(self, resolution: Resolution):
        super(RegularFramebuffer, self).__init__()
        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, resolution.width, resolution.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.texture, 0)

        self.depthBuf = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, self.depthBuf)

        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT, resolution.width, resolution.height)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.depthBuf)

        self.initrendertoscreen()

    def __del__(self):
        glDeleteFramebuffers([self.fbo])
        glDeleteTextures([self.texture])

    def initrendertoscreen(self):
        """Sets up the objects required to render framebuffer contents to default framebuffer"""
        if RegularFramebuffer.fsquad is None:
            RegularFramebuffer.fsquad = FSQuad()
        if RegularFramebuffer.fstextureshader is None:
            RegularFramebuffer.fstextureshader = FullscreenTexture()
            RegularFramebuffer.fsquad.shader = RegularFramebuffer.fstextureshader
        if RegularFramebuffer.fscamera is None:
            RegularFramebuffer.fscamera = Camera()

    def rendertoscreen(self):
        """Renders the framebuffer to default framebuffer (Aka the screen)"""
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        RegularFramebuffer.fsquad.textures = [self.texture]
        RegularFramebuffer.fsquad.render(RegularFramebuffer.fscamera.viewMatrix)
