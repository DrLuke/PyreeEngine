from pathlib import Path
from pyreeEngine.project import Project

import importlib
import sys


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

        self.loadProject()

    def loadProject(self):
        self.project = Project(self.projectPath)

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
        return False

    def delNode(self, nodeDef):
        pass



    def loadNodeClasses(self, modulepath):
        """Imports module and fetches all nodes from it

        :param modulepath: Path to module (e.g. foo.bar.mymodule)
        :type modulepath: string
        :return: All node-classes from module or None on failure
        :rtype: List[Class]
        """
        importlib.invalidate_caches()
        try:
            newmod = importlib.import_module(modulepath)
        except ModuleNotFoundError:
            print("ERRO: Module %s not found" % modulepath, file=sys.stderr)
        try:
            classes = newmod.__nodeclasses__
        except AttributeError:
            print("ERROR: Module %s is missing '__nodeclasses__' attribute" % modulepath, file=sys.stderr)
            return None





