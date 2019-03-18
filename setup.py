import sys, os
from cx_Freeze import setup, Executable

__version__ = "1.0"

include_files = []
excludes = []
packages = ["sys", "PIL", "random"]

setup(
    name="steganography",
    description='Simple steganography app',
    version=__version__,
    executables=[Executable("steg.py")]
)
