from pathlib import Path
import json

class Project:
    """Reads project file data
    """
    def __init__(self, path: Path):
        self.path = path    # Path to config file

        self.data = None

        self.projectName = None
        self.authorName = None
        self.nodes = None
        self.signals = None
        self.entry = None

        self.readJSON(self.path)

    def readJSON(self, path: Path):
        with path.open("r") as f:
            self.data = json.load(f)

        # TODO: Check file to be correct
        self.projectName = self.getFromData("projectName")
        self.author = self.getFromData("author")
        self.nodes = self.getFromData("nodes")
        self.signals = self.getSignals()
        self.signals += self.getExecs()
        self.entry = self.getFromData("entry")

    def getFromData(self, key):
        if key in self.data:
            return self.data[key]
        else:
            return None

    def getSignals(self):
        sigs = self.getFromData("signals")
        for sig in sigs:
            sig["__PYREE__sigtype"] = "signal"
        return sigs

    def getExecs(self):
        execs = self.getFromData("execSignals")
        for exec in execs:
            exec["__PYREE__sigtype"] = "exec"
        return execs