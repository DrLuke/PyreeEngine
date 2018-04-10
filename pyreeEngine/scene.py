from typing import Union, Type, List, Callable

from pyreeEngine.engine import Framebuffer


def signalInput(name:str, type:Union[Type, List[Type]], desc:str=""):
    def decorator(func:Callable):
        obj = func.__self__
        obj.__signalInputs__[name] = (func, type, desc)
        return func
    return decorator

def signalOutput(name:str, type:Union[Type, List[Type]], desc:str=""):
    def decorator(func:Callable):
        obj = func.__self__
        obj.__signalOutputs__[name] = (func, type, desc)
        return func
    return decorator

class Scene:
    def __init__(self):
        self.__signalInputs__ = {}
        self.__signalOutputs__ = {}

    def init(self):
        pass

    def render(self, fbo: Framebuffer):
        fbo.bindFramebuffer()


