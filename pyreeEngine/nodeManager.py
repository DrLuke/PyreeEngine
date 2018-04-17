from pathlib import Path
from pyreeEngine.project import Project

import importlib
import sys

from inotify_simple import INotify, flags, masks
import inotify_simple

import types

import time


class NodeDefition():
    def __init__(self, data):
        self.name = data["name"]
        self.guid = data["guid"]
        self.modulePath = data["module"]
        self.className = data["module"]

    def __eq__(self, other):
        return self.name == other.name and self.guid == other.guid and self.modulePath == other.modulePath and self.className == other.className

    def __hash__(self):
        return hash(self.name + self.guid + self.modulePath + self.className)

class ModuleWatcher():
    def __init__(self, modulepath: str):
        self.modulePath = modulepath
        self.moduleFilePath = None
        self.module = None
        self.classes = None
        self.valid = False  # type: bool

        self.loadNodeModule()

        if type(self.module) is types.ModuleType:
            self.valid = True
            self.installFileWatch()

    def loadNodeModule(self):
        """Imports module and fetches all nodes from it

        :param modulepath: Path to module (e.g. foo.bar.mymodule)
        :type modulepath: string
        :return: All node-classes from module or None on failure
        :rtype: List[Class]
        """
        importlib.invalidate_caches()
        if self.module is None:
            try:
                self.module = importlib.import_module(self.modulePath)
            except ModuleNotFoundError:
                print("ERROR: Module %s not found" % self.modulePath, file=sys.stderr)
                return None
        elif type(self.module) is types.ModuleType:
            importlib.reload(self.module)
        else:
            self.module = None  # Failback
        try:
            self.classes = self.module.__nodeclasses__
        except AttributeError:
            print("ERROR: Module %s is missing '__nodeclasses__' attribute" % self.modulePath, file=sys.stderr)
            return None
        self.moduleFilePath = Path(self.module.__file__)

    def getClass(self, classname: str):
        for nodeclass in self.classes:
            if nodeclass.__name__ == classname:
                return nodeclass
        return None

    def installFileWatch(self):
        fl = flags.CREATE | flags.MODIFY | flags.MOVED_TO
        self.iNotify = INotify()
        self.watch = self.iNotify.add_watch(self.moduleFilePath.parent, fl)

    def checkFileWatch(self):
        if not self.valid:
            return
        events = self.iNotify.read(timeout=0)
        for event in events:
            self.checkEvent(event)

    def checkEvent(self, event: inotify_simple.Event):
        if event.name == self.moduleFilePath.name:
            if event.mask & (flags.CREATE | flags.MODIFY | flags.MOVED_TO):
                self.loadNodeModule()
            elif event.mask & (flags.DELETE | flags.DELETE_SELF):
                pass    # TODO: Implement


"""
Manages reloading nodes

1: Detect all scenes within a project folder
2: Load all scenes
3: Install inotify to detect changes
4: Run instances of classes in set order
"""
class NodeManager():
    def __init__(self, projectpath:Path):
        """Initialize ModuleManager

        :param projectpath: Path to project file
        :type projectpath: Path
        """
        self.projectPath = projectpath
        self.project = None

        self.nodeDefinitions = set()    # type: set
        self.moduleWatchers = {}        # type: dict

        self.projecti = None
        self.installProjectWatch()

        self.loadProject()

    def installProjectWatch(self):
        fl = flags.MODIFY | flags.MOVED_TO
        self.projecti = INotify()
        self.projectwatch = self.projecti.add_watch(self.projectPath.parent, fl)

    def checkProjectWatch(self, event: inotify_simple.Event):
        if event.name == self.projectPath.name:
            self.loadProject()

    def loadProject(self):
        print("NODEMAN: Reloading Project")
        self.project = Project(self.projectPath)    # TODO: Check if project is valid, keep using old one if error occurs

        self.parseNodeDefinitions()

    def parseNodeDefinitions(self):
        """Parses node definitions from project

        Each node definition in the project json is read by a NodeDefinition object. New Objects need to have iNotify
        watchers installed on the module file, while modules that aren't in use anymore need their watchers removed.
        """
        allNodes = set()    # Current state as defined in project
        newNodes = set()    # Nodes that have been added
        for nodeDef in self.project.nodes:
            newDef = NodeDefition(nodeDef)
            allNodes.add(newDef)
            if newDef not in self.nodeDefinitions:
                newNodes.add(newDef)

        # Initialize all nodes that are new
        for nodeDef in newNodes:
            if self.initNode(nodeDef):
                self.nodeDefinitions.add(nodeDef)

        # Uninitialize all nodes that aren't existant anymore
        for nodeDef in self.nodeDefinitions.difference(allNodes):
            self.delNode(nodeDef)
            self.nodeDefinitions.remove(nodeDef)

    def initNode(self, nodeDef) -> bool:
        # Check if module already is being watched
        if nodeDef.modulePath not in self.moduleWatchers:
            newwatcher = ModuleWatcher(nodeDef.modulePath)
            if newwatcher.valid:
                self.moduleWatchers[nodeDef.modulePath] = newwatcher
                return True

        return False

    def delNode(self, nodeDef):
        pass

    def tick(self):
        events = self.projecti.read(timeout=0)
        for event in events:
            self.checkProjectWatch(event)

        for modulewatcher in self.moduleWatchers.values():
            modulewatcher.checkFileWatch()






