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

        self.classes = {}

    def loadProject(self):
        self.project = Project(self.projectPath)

    def reloadNodes(self, path:Path):
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





