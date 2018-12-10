"""Layer system for Engine. Each layer represents a single python file that is run on every tick."""

import types
import typing
from typing import List, Tuple

from pathlib import Path

import importlib
import sys
import traceback

from inotify_simple import INotify, flags, masks
import inotify_simple

import time

from PyreeEngine import log

from inotify_simple import INotify, flags, masks
import inotify_simple

from pathlib import Path

import json

import pythonosc.dispatcher
import pythonosc.udp_client

from PyreeEngine.util import Resolution

class LayerConfig(typing.NamedTuple):
    """Configuration for layers"""
    name: str = None  # Name of the Layer
    module: str = None  # Importer friendly module name
    filepath: Path = None  # Path to module
    entryclass: str = "LayerEntry"  # Class that is instantiated from layer as the main layer class

    onloadoscpath: str = "/load"  # OSC path to send message to on load
    onloadoscmessage: str = "LOAD"  # Message to send on load to onloadoscpath


class ProgramConfig(typing.NamedTuple):
    layerdefs: List[LayerConfig] = []  # Layers read from configpath

    oscserveraddress: str = "127.0.0.1"  # IP address of OSC server
    oscserverport: int = 1337  # Port of OSC server
    oscclientaddress: str = "127.0.0.1"  # IP address of OSC client
    oscclientport: int = 1337  # Port of OSC client


class LayerContext():
    """Stores important runtime information, like the current resolution and the OSC dispatcher"""

    def __init__(self):
        self.time: float = 0.
        self.dt: float = 1.
        self.frame: int = 0

        self.resolution: Resolution = Resolution(width=800, height=600)
        self.aspect = self.resolution.width / self.resolution.height
        self.resolutionChangeCallbacks: List[types.FunctionType] = []

        self.oscdispatcher: pythonosc.dispatcher.Dispatcher = None  # Server for receiving messages
        self.oscclient: pythonosc.udp_client.UDPClient = None  # Client for sending out messages

    def addresolutioncallback(self, newfunc: types.FunctionType):
        self.resolutionChangeCallbacks.append(newfunc)

    def removeresolutionscallback(self, removefunc: types.FunctionType):
        if removefunc in self.resolutionChangeCallbacks:
            self.resolutionChangeCallbacks.remove(removefunc)

    def setresolution(self, width, height):
        self.resolution = Resolution(width=width, height=height)
        self.aspect = self.resolution.width / self.resolution.height
        for callback in self.resolutionChangeCallbacks:
            callback(self.resolution)


class BaseEntry():
    def __init__(self, context: LayerContext):
        self.context: LayerContext = context

    def __serialize__(self) -> dict:
        return {}

    def __deserialize__(self, data: dict) -> None:
        pass

    def init(self):
        pass

    def tick(self):
        pass


class Layer():
    """Layer of Pyree.

    A layer represents a piece of code that is running within Pyree. Multiple layers can run sequentially to provide
    more complex behaviour."""

    def __init__(self, config: LayerConfig, context: LayerContext):
        self.enabled: bool = False  # Layer is currently being run
        self.valid: bool = False  # A layer is valid if it was imported successfully, and is invalidated on exceptions
        self.old: bool = False  # If a layer failed to reload, indicate that current module reflects old version
        self.tickfunction: types.FunctionType = None  # Function to call on tick
        self.config: LayerConfig = config
        self.context: LayerContext = context

        self.inotify: INotify = None
        self.watch: int = None

        self.module = None
        self.entryclass = None
        self.entryinstance: BaseEntry = None
        self.entrytick = None

        if self.loadmodule():
            self.valid = True
        else:
            self.valid = False

        self.installfilewatch()

    def tick(self):
        """Check iwatch and replace module if necessary"""
        if self.checkfilewatch():
            self.loadmodule()

        self.entryinstance.tick()

    def loadmodule(self) -> bool:
        """Loads the module and extracts entry point class"""
        importlib.invalidate_caches()  # Without this, python won't take file changes into account
        try:
            if self.module is None:
                log.info("LAYER", "Importing module %s" % self.config.module)
                self.module = importlib.import_module(self.config.module)  # Initial import

            elif type(self.module) is types.ModuleType:
                log.info("LAYER", "Reloading module %s" % self.config.module)
                importlib.reload(self.module)  # Reload module from same source

            else:  # Emergency fallback if self.module is something else for whatever reason!
                log.warning("LAYER",
                            "Layer module property of layer %s is of type %s" % (self.config.name, type(self.module)))
                self.module = None
        except ModuleNotFoundError:
            log.error("LAYER", "Module %s not found" % self.config.module)
            return False
        except Exception as exc:
            print(traceback.format_exc(), file=sys.stderr)
            print(exc, file=sys.stderr)
            log.error("LAYER", "Module %s load exception, old instance persists on Layer %s" % (
                self.config.module, self.config.name))
            return False

        # Import was successful, try to get class
        if hasattr(self.module, self.config.entryclass):
            self.entryclass = getattr(self.module, self.config.entryclass)
        else:
            log.error("LAYER", "Module %s has no class %s" % (self.config.module, self.config.entryclass))
            return False

        # Replace old instance with new instance
        try:
            newinstance: BaseEntry = self.entryclass(self.context)  # TODO: add context here
            if self.entryinstance is not None:
                newinstance.__deserialize__(self.entryinstance.__serialize__())
            del self.entryinstance
            self.entryinstance = newinstance
            self.entryinstance.init()
        except Exception as exc:
            print(traceback.format_exc(), file=sys.stderr)
            print(exc, file=sys.stderr)
            log.error("LAYER", "Failed to replace old instance with new instance on Layer %s" % self.config.name)
            return False

        return True

    def installfilewatch(self) -> None:
        fl = flags.CREATE | flags.MODIFY | flags.MOVED_TO
        self.iNotify = INotify()
        self.watch = self.iNotify.add_watch(self.config.filepath.parent, fl)

    def checkfilewatch(self) -> bool:
        retVal = False
        if not self.valid:
            return False
        events = self.iNotify.read(timeout=0)
        for event in events:
            if self.checkevent(event):
                retVal = True
        return retVal

    def checkevent(self, event: inotify_simple.Event) -> bool:
        retVal = False
        if event.name == self.config.filepath.name:
            if event.mask & (flags.CREATE | flags.MODIFY | flags.MOVED_TO):
                log.info("LAYER", "Layer %s updated" % self.config.name)
                retVal = True
            elif event.mask & (flags.DELETE | flags.DELETE_SELF):
                self.valid = False
                log.info("LAYER", "Layer %s deleted" % self.config.name)
        return retVal


class LayerManager():
    def __init__(self, config: ProgramConfig, context: LayerContext):
        self.config: ProgramConfig = config
        self.context: LayerContext = context
        self.layers: List[Layer] = []

        self.loadlayers()

    def loadlayers(self) -> None:
        for layerdef in self.config.layerdefs:
            layerdef["filepath"] = Path(layerdef["module"].replace(".", "/") + ".py")
            layerconf = LayerConfig(**layerdef)
            newlayer = Layer(layerconf, self.context)
            self.layers.append(newlayer)

    def tick(self):
        for layer in self.layers:
            layer.tick()
