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


    def readJSON(self, path: Path):
        with path.open("r") as f:
            self.data = json.load(f)

        self.projectName = self.getFromData("projectName")
        self.author = self.getFromData("author")
        self.nodes = self.getFromData("nodes")

    def getFromData(self, key):
        if key in self.data:
            return self.data[key]
        else:
            return None
