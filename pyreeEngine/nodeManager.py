from typing import Dict, Tuple

from pathlib import Path
from pyreeEngine.project import Project

import importlib
import sys
import traceback

from inotify_simple import INotify, flags, masks
import inotify_simple

import types

import time

from pyreeEngine.node import BaseNode
from pyreeEngine.engine import NodeGlobalData

from pyreeEngine import log


class NodeDefinition():
    def __init__(self, data):
        self.name = data["name"]
        self.guid = data["guid"]
        self.modulePath = data["module"]
        self.className = data["class"]

    def __eq__(self, other):
        return self.name == other.name and self.guid == other.guid and self.modulePath == other.modulePath and self.className == other.className

    def __hash__(self):
        return hash(self.name + self.guid + self.modulePath + self.className)

    def __repr__(self):
        return ("NodeDefinition (name=%s guid=%s modpath=%s class=%s" % (self.name, self.guid, self.modulePath, self.className))


class SignalDefinition():
    def __init__(self, data):
        self.source = data["source"]
        self.target = data["target"]
        self.sourceSigName = data["sourceSigName"]
        self.targetSigName = data["targetSigName"]
        self.sigtype = data["__PYREE__sigtype"]

    def __eq__(self, other):
        return self.source == other.source and self.target == other.target and self.sourceSigName == other.sourceSigName and self.targetSigName == other.targetSigName

    def __hash__(self):
        return hash(self.source + self.target + self.sourceSigName + self.targetSigName)


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
            try:
                importlib.reload(self.module)
            except Exception as exc:
                print(traceback.format_exc(), file=sys.stderr)
                print(exc, file=sys.stderr)
                log.error("NodeMan", "Failed to reload module %s, old module persists!" % self.modulePath)
                return None
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

    def checkFileWatch(self) -> bool:
        retVal = False
        if not self.valid:
            return False
        events = self.iNotify.read(timeout=0)
        for event in events:
            if self.checkEvent(event):
                retVal = True
        return retVal

    def checkEvent(self, event: inotify_simple.Event) -> bool:
        retVal = False
        if event.name == self.moduleFilePath.name:
            if event.mask & (flags.CREATE | flags.MODIFY | flags.MOVED_TO):
                self.loadNodeModule()
                retVal = True
            elif event.mask & (flags.DELETE | flags.DELETE_SELF):
                pass    # TODO: Implement
        return retVal


class NodeHandler():
    """Manages node instance"""
    def __init__(self, nodedef: NodeDefinition, modulewatch: ModuleWatcher, globdata:NodeGlobalData):
        self.nodeDef = nodedef
        self.moduleWatch = modulewatch
        self.globalData = globdata
        self.nodeClass = None
        self.nodeInstance = None    # type: BaseNode
        self.valid = False
        self.inited = False

        self.reloadInstance()

    def reloadInstance(self) -> bool:
        # TODO: More error-handling
        self.valid = False
        if self.nodeInstance is not None:
            oldData = self.nodeInstance.getData()
        else:
            oldData = None

        newClass = self.moduleWatch.getClass(self.nodeDef.className)

        if not issubclass(newClass, BaseNode):
            log.error("NodeMan", "Nodeclass '%s' from module '%s' is not subclass of BaseNode" % (self.nodeDef.className, self.moduleWatch.modulePath))
            return False

        del self.nodeInstance

        try:
            self.nodeInstance = newClass(self.globalData)
            self.inited = False
            self.nodeClass = newClass
        except Exception as exc:
            print(traceback.format_exc(), file=sys.stderr)
            print(exc, file=sys.stderr)
            log.error("NodeMan", "Node instantiation failed. Module: %s Node: %s" % (self.nodeDef.modulePath, self.nodeDef.className))
            return

        if oldData is not None:
            self.nodeInstance.setData(oldData)
        self.valid = True
        log.success("NodeMan", "Succesful node reinstantiation %s" % self.nodeDef)


"""
Manages reloading nodes

1: Detect all scenes within a project folder
2: Load all scenes
3: Install inotify to detect changes
4: Run instances of classes in set order
"""
class NodeManager():
    def __init__(self, projectpath:Path, globdata:NodeGlobalData):
        """Initialize ModuleManager

        :param projectpath: Path to project file
        :type projectpath: Path
        """
        self.projectPath = projectpath
        self.project = None

        self.globalData = globdata

        self.nodeDefinitions = set()    # type: set
        self.signalDefinitions = set()  # type: set
        self.moduleWatchers = {}        # type: dict
        self.nodeHandlers = {}          # type: dict
        self.signalNodeMap = {}         # type: Dict[SignalDefinition, Tuple(NodeDefinition, NodeDefinition)]

        self.projecti = None
        self.installProjectWatch()

        self.entryNode = None
        self.entryMethod = None

        self.loadProject()

    def installProjectWatch(self):
        fl = flags.MODIFY | flags.MOVED_TO
        self.projecti = INotify()
        self.projectwatch = self.projecti.add_watch(self.projectPath.parent, fl)

    def checkProjectWatch(self, event: inotify_simple.Event):
        if event.name == self.projectPath.name:
            self.loadProject()

    def loadProject(self):
        log.info("NodeMan", "Reloading project")
        self.project = Project(self.projectPath)    # TODO: Check if project is valid, keep using old one if error occurs

        self.parseNodeDefinitions()
        self.parseSignalDefinitions()
        self.initNodes()
        self.prepareEntry()

    def parseNodeDefinitions(self):
        """Parses node definitions from project

        Each node definition in the project json is read by a NodeDefinition object. New Objects need to have iNotify
        watchers installed on the module file, while modules that aren't in use anymore need their watchers removed.
        """
        allNodes = set()    # Current state as defined in project
        newNodes = set()    # Nodes that have been added
        for nodeDef in self.project.nodes:
            newDef = NodeDefinition(nodeDef)
            allNodes.add(newDef)
            if newDef not in self.nodeDefinitions:
                newNodes.add(newDef)

        # Initialize all nodes that are new
        for nodeDef in newNodes:
            self.initModuleWatch(nodeDef)

            if self.moduleWatchers[nodeDef.modulePath].valid:
                self.nodeDefinitions.add(nodeDef)
                self.initNodeHandler(nodeDef, self.moduleWatchers[nodeDef.modulePath])
            else:
                print("WARNING: Module %s isn't valid" % nodeDef.modulePath)

        # Uninitialize all nodes that aren't existant anymore
        for nodeDef in self.nodeDefinitions.difference(allNodes):
            self.delNode(nodeDef)
            self.nodeDefinitions.remove(nodeDef)

    def parseSignalDefinitions(self):
        allSignals = set()
        newSignals = set()
        for signalDef in self.project.signals:
            newDef = SignalDefinition(signalDef)
            allSignals.add(newDef)
            if newDef not in self.signalDefinitions:
                newSignals.add(newDef)

        for signalDef in newSignals:
            nodeDefs = self.getNodeDefsFromSignalDef(signalDef)
            if nodeDefs[0] is not None and nodeDefs[1] is not None:
                self.signalDefinitions.add(signalDef)
                self.signalNodeMap[signalDef] = nodeDefs
            else:
                print("ERROR: Couldn't find nodes for signal")    # TODO: Better error message
            self.patchSignal(signalDef)

        for signalDef in self.signalDefinitions.difference(allSignals):
            pass    # TODO: What to do if signal doesn't exist anymore?

    def getNodeDefsFromSignalDef(self, signaldef: SignalDefinition) -> Tuple[NodeDefinition, NodeDefinition]:
        for nodeDef in self.nodeDefinitions:
            if signaldef.source == nodeDef.guid:
                sourceNodeDef = nodeDef
            if signaldef.target == nodeDef.guid:
                targetNodeDef = nodeDef
        return (sourceNodeDef, targetNodeDef)

    def initNodes(self):
        for nodehandler in self.nodeHandlers.values():
            if not nodehandler.inited:
                try:
                    nodehandler.nodeInstance.init()
                    nodehandler.inited = True
                except Exception as exc:
                    nodehandler.valid = False
                    self.patchNodeSignals(nodehandler.nodeDef)
                    log.warning("NodeMan", "Node disabled: %s" % nodehandler.nodeDef)
                    log.error("NodeMan", "Node exception on init(): %s" % nodehandler.nodeDef)
                    print(traceback.format_exc(), file=sys.stderr)
                    print(exc, file=sys.stderr)

    def initModuleWatch(self, nodeDef) -> bool:
        # Check if module already is being watched
        if nodeDef.modulePath not in self.moduleWatchers:
            newwatcher = ModuleWatcher(nodeDef.modulePath)
            if newwatcher.valid:
                self.moduleWatchers[nodeDef.modulePath] = newwatcher
                return True

        return False

    def initNodeHandler(self, nodedef, modulewatch) -> bool:
        if nodedef not in self.nodeHandlers:
            self.nodeHandlers[nodedef] = NodeHandler(nodedef, modulewatch, self.globalData)
        else:
            print("WARNING: NodeHandler for nodeDef already exists! %s %s %s %s" % (nodedef.name, nodedef.modulePath, nodedef.className, nodedef.guid))

        return False

    def delNode(self, nodeDef):
        pass    # TODO: Check if any more nodes reference modulewatch equal to this node. If yes, remove moduleWatch.

    def tick(self):
        events = self.projecti.read(timeout=0)
        for event in events:
            self.checkProjectWatch(event)

        for modulewatcher in self.moduleWatchers.values():
            if modulewatcher.checkFileWatch():  # Module has been reloaded -> reload all nodes from this module
                for nodehandler in self.nodeHandlers.values():
                    if nodehandler.moduleWatch is modulewatcher:
                        nodehandler.reloadInstance()
                        if nodehandler.valid:
                            self.patchNodeSignals(nodehandler.nodeDef)
                            if not nodehandler.inited:
                                try:
                                    nodehandler.nodeInstance.init()
                                    nodehandler.inited = True
                                except Exception as exc:
                                    nodehandler.valid = False
                                    self.patchNodeSignals(nodehandler.nodeDef)
                                    log.warning("NodeMan", "Node disabled: %s" % nodehandler.nodeDef)
                                    log.error("NodeMan", "Node exception on init(): %s" % nodehandler.nodeDef)
                                    print(traceback.format_exc(), file=sys.stderr)
                                    print(exc, file=sys.stderr)
                        if nodehandler.nodeDef.guid == self.project.entry["guid"]:
                            self.prepareEntry()

        if self.entryMethod is not None:
            if self.entryNode.valid:
                try:
                    self.entryMethod()  # TODO: try except crash-resistance
                except Exception as exc:
                    print(traceback.format_exc(), file=sys.stderr)
                    print(exc, file=sys.stderr)
                    log.error("NodeMan", "Exception in node: ")

                    nodedeftorepatch = None
                    for nodehandler in self.nodeHandlers.values():
                        if nodehandler.nodeInstance is self.globalData.__PYREE__lasttarget__:
                            nodehandler.valid = False
                            nodedeftorepatch = nodehandler.nodeDef
                            break

                    if nodedeftorepatch is not None:
                        self.patchNodeSignals(nodedeftorepatch)

            else:
                log.error("NodeMan", "Entry node invalid %s" % self.entryNode.nodeDef)
                self.entryMethod = None

    def patchNodeSignals(self, nodedef: NodeDefinition):
        for signalDef in self.signalDefinitions:
            if signalDef.source == nodedef.guid or signalDef.target == nodedef.guid:
                self.patchSignal(signalDef)

    def patchSignal(self, signaldef: SignalDefinition):
        nodeDefSource = self.signalNodeMap[signaldef][0]
        nodeDefTarget = self.signalNodeMap[signaldef][1]

        nodeHandlerSource = self.nodeHandlers[nodeDefSource]    # type: NodeHandler
        nodeHandlerTarget = self.nodeHandlers[nodeDefTarget]    # type: NodeHandler

        if not nodeHandlerSource.valid and not nodeHandlerTarget.valid:
            print("ERROR: Nodehandlers not valid!")
            return False

        if signaldef.sourceSigName in nodeHandlerSource.nodeClass.__signalOutputs__ and signaldef.targetSigName in nodeHandlerTarget.nodeClass.__signalInputs__:
            outputMethod = nodeHandlerSource.nodeClass.__signalOutputs__[signaldef.sourceSigName][0]
            inputMethod = nodeHandlerTarget.nodeClass.__signalInputs__[signaldef.targetSigName][0]
        else:
            print("ERROR: Inputs/Outputs not found")    # TODO: More elaborate error message
            return False

        if signaldef.sigtype == "signal":
            if hasattr(nodeHandlerTarget.nodeClass, inputMethod.__name__):
                setattr(nodeHandlerTarget.nodeClass, inputMethod.__name__, outputMethod)
                #inputMethod.__PYREE__target__ = nodeHandlerTarget.nodeInstance
                #inputMethod.__PYREE__globdata__ = self.globalData
            else:
                print("ERROR: Function is not an attribute")
            return True
        elif signaldef.sigtype == "exec":
            if hasattr(nodeHandlerSource.nodeClass, outputMethod.__name__):
                setattr(nodeHandlerSource.nodeClass, outputMethod.__name__, inputMethod)
                #outputMethod.__PYREE__target__ = nodeHandlerTarget.nodeInstance
                #outputMethod.__PYREE__globdata__ = self.globalData
            else:
                print("ERROR: Function is not an attribute")
            return True
        return False

    def prepareEntry(self):
        for nodedef in self.nodeHandlers:
            if nodedef.guid == self.project.entry["guid"]:
                if self.project.entry["sigName"] in self.nodeHandlers[nodedef].nodeClass.__signalInputs__:
                    entryFunc = self.nodeHandlers[nodedef].nodeClass.__signalInputs__[self.project.entry["sigName"]][0]
                    self.entryNode = self.nodeHandlers[nodedef]
                    self.entryMethod = getattr(self.nodeHandlers[nodedef].nodeInstance, entryFunc.__name__)
                    return
        self.entryNode = None
        self.entryMethod = None
        print("ERROR: Entrypoint not found! guid:%s signame:%s" % (self.project.entry["guid"], self.project.entry["sigName"]))
        log.warning("NodeMan", "Program execution halted due to missing entry function")
