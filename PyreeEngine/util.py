from typing import Union, List, Tuple
from pathlib import Path
from OpenGL import GL

import numpy as np

from typing import NamedTuple

def ObjLoader(objFilePath: Path):
    # TODO: Check if file is valid obj file, return None otherwise (general error handling would be nice :-)
    vertices = []
    uv = []
    normals = []
    faces = []

    normsavailable = False

    with objFilePath.open("r") as f:
        for line in f:
            lineSplit = line.split(" ")
            if line.startswith("vt"):
                uv.append([float(lineSplit[1]), float(lineSplit[2])])
            elif line.startswith("vn"):
                normals.append([float(lineSplit[1]), float(lineSplit[2]), float(lineSplit[3])])
                normsavailable = True
            elif line.startswith("v"):
                vertices.append([float(lineSplit[1]), float(lineSplit[2]), float(lineSplit[3])])
            elif line.startswith("f"):
                # subtract 1 because OBJ starts indexing from 1, while python is indexing from 0
                faces.append([[int(x)-1 for x in lineSplit[1].split("/")],
                              [int(x)-1 for x in lineSplit[2].split("/")],
                              [int(x)-1 for x in lineSplit[3].split("/")]])


    outdata = np.array([], np.float32)

    for face in faces:
        if not normsavailable:
            # calculate face normal manually
            edge1 = np.array(vertices[face[1][0]], np.float32) - np.array(vertices[face[0][0]], np.float32)
            edge2 = np.array(vertices[face[2][0]], np.float32) - np.array(vertices[face[1][0]], np.float32)
            calcnorm = np.cross(edge1, edge2)
            calcnorm /= np.linalg.norm(calcnorm)

        for vert in face:
            v = vertices[vert[0]]   # Vertex
            uvval = uv[vert[1]]        # UV coord
            if normsavailable:
                n = normals[vert[2]]   # Normal
                outdata = np.append(outdata, np.array(v + uvval + n, np.float32))
            else:
                outdata = np.append(outdata, np.array(v + uvval, np.float32))
                outdata = np.append(outdata, calcnorm)

    texturedata = None

    return (outdata, texturedata)


# TODO: Maybe convert these to actual classes, but then again what's the point? It would just be reimplementing features np arrays already have... 🤔
def Vec2(v0: Union[int, float]=0, v1: Union[int, float]=0):
    return np.array([v0, v1], np.float32)

def Vec3(v0: Union[int, float]=0, v1: Union[int, float]=0, v2: Union[int, float]=0):
    return np.array([v0, v1, v2], np.float32)

def Vec4(v0: Union[int, float]=0, v1: Union[int, float]=0, v2: Union[int, float]=0, v3: Union[int, float]=0):
    return np.array([v0, v1, v2, v3], np.float32)

class Resolution(NamedTuple):
    width: int = 800
    height: int = 600
