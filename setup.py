#!/usr/bin/env python3

from setuptools import setup
from pathlib import Path

with Path("VERSION").open("r") as f:
    version = f.read()

with Path("LICENSE").open("r") as f:
    license = f.read()

setup(
    name='PyreeEngine',
    version=version,
    description='Pyree Engine',
    author='Lukas Jackowski',
    author_email='Lukas@Jackowski.de',
    url='https://github.com/DrLuke/PyreeEngine/',
    packages=['PyreeEngine'],
    license=license,
    install_requires=[
        "PyOpenGL",
        "scipy",
        "numpy",
        "numpy-quaternion",
        "glfw",
        "numba",
        "inotify_simple",
        "Pillow",
        "cffi",
        "mido",
        "python-rtmidi",
    ]
)
