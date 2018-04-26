from typing import Union, Type, List, Callable
import inspect

from pyreeEngine.engine import Framebuffer


class execType():
    pass


def signalInput(name: str, type: Union[Type, List[Type]], meta: dict= None) -> Callable:
    def decorator(func: Callable):
        func.__PYREESIGNAL__data__ = ("input", name, type, meta)
        return func
    return decorator


def signalOutput(name: str, type: Union[Type, List[Type]], meta: dict= None) -> Callable:
    def decorator(func: Callable):
        func.__PYREESIGNAL__data__ = ("output", name, type, meta)
        return func
    return decorator


def execIn(name: str, meta: dict= None) -> Callable:
    def decorator(func: Callable):
        func.__PYREESIGNAL__data__ = ("input", name, execType, meta)
        return func
    return decorator


def execOut(name: str, meta: dict= None) -> Callable:
    def decorator(func: Callable):
        func.__PYREESIGNAL__data__ = ("output", name, execType, meta)
        return func
    return decorator


class BaseNodeMetaclass(type):
    def __new__(cls, *args, **kwargs):
        newClass = type.__new__(cls, *args, **kwargs)
        newClass.__signalInputs__ = {}
        newClass.__signalOutputs__ = {}

        functions = inspect.getmembers(newClass, predicate=inspect.isfunction)
        for func in functions:
            if hasattr(func[1], "__PYREESIGNAL__data__"):
                data = func[1].__PYREESIGNAL__data__
                if data[0] == "output":
                    newClass.__signalOutputs__[data[1]] = (func[1], data[2], data[3])
                elif data[0] == "input":
                    newClass.__signalInputs__[data[1]] = (func[1], data[2], data[3])

        return newClass


class BaseNode(metaclass=BaseNodeMetaclass):
    def __init__(self):
        pass
        #self.init()

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


