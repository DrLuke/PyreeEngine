from typing import Union, List, Tuple, Callable, Optional

from pyreeEngine.engine import PyreeObject
from OpenGL.GL import *
from OpenGL.GL import shaders

import numpy as np
from pathlib import Path
from PIL import Image

from scipy.ndimage import imread

from enum import Enum

class Texture():
    """Abstract Texture Container
    A texture container abstracts the handling of textures to be more pythonic.
    """
    class Wrapping(Enum):
        repeat = GL_REPEAT
        mirror = GL_MIRRORED_REPEAT
        clampEdge = GL_CLAMP_TO_EDGE
        clampBorder = GL_CLAMP_TO_BORDER

    class Filter(Enum):
        nearest = GL_NEAREST
        linear = GL_LINEAR
        nearestMipmapNearest = GL_NEAREST_MIPMAP_NEAREST
        nearestMipmapLinear = GL_NEAREST_MIPMAP_LINEAR
        linearMipmapNearest = GL_LINEAR_MIPMAP_NEAREST
        linearMipmapLinear = GL_LINEAR_MIPMAP_LINEAR

    class TexTarget(Enum):
        texture1D = GL_TEXTURE_1D
        texture2D = GL_TEXTURE_2D
        texture3D = GL_TEXTURE_3D
        # TODO: Add other texture types if required

    def __init__(self):
        self.height = None  # type: int
        self.width = None   # type: int
        self.depth = None   # type: int
        self.textures = None    # type: List
        self.targetType = Texture.TexTarget.texture2D   # Default texture is regular 2D texture

    def getTexture(self) -> Union[int, List[int]]:
        """Returns textures, and checks if they need updating"""
        pass

    def textureGen(self):
        """Generator for returning ALL textures related to this container"""
        for tex in self.textures:
            yield tex

    def setMagFilter(self, filterMode: int=GL_NEAREST):
        if filterMode in [x.value for x in Texture.Filter]:
            for tex in self.textureGen():
                glBindTexture(tex)
                glTexParameterf(self.targetType, GL_TEXTURE_MIN_FILTER, filterMode)
        else:
            raise ValueError("Invalid filterMode (filtermode=%s)" % filterMode)

    def setMinFilter(self, filterMode: int=GL_NEAREST):
        if filterMode in [x.value for x in Texture.Filter]:
            for tex in self.textureGen():
                glBindTexture(tex)
                glTexParameterf(self.targetType, GL_TEXTURE_MAG_FILTER, filterMode)
        else:
            raise ValueError("Invalid filterMode (filtermode=%s)" % filterMode)

    def setSWrap(self, wrapMode: int=GL_REPEAT):
        if wrapMode in [x.value for x in Texture.Wrapping]:
            for tex in self.textureGen():
                glBindTexture(tex)
                glTexParameterf(self.targetType, GL_TEXTURE_WRAP_S, wrapMode)
        else:
            raise ValueError("Invalid wrapMode (wrapMode=%s)" % wrapMode)

    def setTWrap(self, wrapMode: int=GL_REPEAT):
        if wrapMode in [x.value for x in Texture.Wrapping]:
            for tex in self.textureGen():
                glBindTexture(tex)
                glTexParameterf(self.targetType, GL_TEXTURE_WRAP_T, wrapMode)
        else:
            raise ValueError("Invalid wrapMode (wrapMode=%s)" % wrapMode)

    def setRWrap(self, wrapMode: int=GL_REPEAT):
        if wrapMode in [x.value for x in Texture.Wrapping]:
            for tex in self.textureGen():
                glBindTexture(tex)
                glTexParameterf(self.targetType, GL_TEXTURE_WRAP_R, wrapMode)
        else:
            raise ValueError("Invalid wrapMode (wrapMode=%s)" % wrapMode)

class TextureFromImage(Texture):
    def __init__(self, path: Path):
        super(TextureFromImage, self).__init__()

        self.path = path

        self.texFromImage(path)

    def texFromImage(self, path: Path, mode: str="RGBA"):
        imdata = np.flipud(imread(path, False, mode))

        if self.textures is not None:
            glDeleteTextures(self.textures)    # Clean up old texture
        self.textures = [glGenTextures(1)]

        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glBindTexture(GL_TEXTURE_2D, self.textures[0])
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, imdata.shape[0], imdata.shape[1], 0, GL_RGBA, GL_UNSIGNED_BYTE, np.array(imdata.flatten(), 'B'))
        glGenerateMipmap(GL_TEXTURE_2D)

    def getTexture(self):
        if type(self.textures) is list and len(self.textures) == 1:
            return self.textures[0]
        else:
            return 0

class HotloadingTextureFromImage(TextureFromImage):
    def __init__(self, path: Path):
        super(HotloadingTextureFromImage, self).__init__(path)
