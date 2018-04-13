from typing import Union, Type, List, Callable

from pyreeEngine.engine import Framebuffer


def signalInput(name: str, type: Union[Type, List[Type]], desc: str=""):
    def decorator(func:Callable):
        obj = func.__self__
        obj.__signalInputs__[name] = (func, type, desc)
        return func
    return decorator

def signalOutput(name: str, type: Union[Type, List[Type]], desc: str=""):
    def decorator(func:Callable):
        obj = func.__self__
        obj.__signalOutputs__[name] = (func, type, desc)
        return func
    return decorator

class Node:
    def __init__(self):
        self.__signalInputs__ = {}
        self.__signalOutputs__ = {}

    def init(self):
        pass

    def getData(self):
        """Get data to restore new instance of class

        :return: Data for object restoration
        """
        return None

    def setData(self, data):
        """Set data on object replacement

        This method takes data and restored object state from a previous instance. 

        :param data: Data to be incorported into new instance
        :return:
        """
        pass


