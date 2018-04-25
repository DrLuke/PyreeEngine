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

        self.readJSON(self.path)

    def readJSON(self, path: Path):
        with path.open("r") as f:
            self.data = json.load(f)

        # TODO: Check file to be correct
        self.projectName = self.getFromData("projectName")
        self.author = self.getFromData("author")
        self.nodes = self.getFromData("nodes")
        self.signals = self.getFromData("signals")

    def getFromData(self, key):
        if key in self.data:
            return self.data[key]
        else:
            return None
