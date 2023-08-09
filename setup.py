"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

import pathlib
import platform
import Common.Globals as Globals

from setuptools import setup

system = platform.system()
bit = platform.machine()
if bit.endswith("i686") or bit == "arm64":
    bit = "arm64"
elif bit.endswith("x86_64"):
    bit = "x86_64"
elif bit.endswith("x86"):
    bit = "x86"
elif bit.endswith("64"):
    bit = "x64"

app_name = "%s_%s_%s_EsperApiSupportTool" % (
    system[0:3].lower() if system == "Windows" else "mac",
    bit,
    Globals.VERSION.replace(".", "-"),
)
curDirPath = str(pathlib.Path().absolute()).replace("\\", "/")

if system == "Windows":
    raise Exception("Py2app is not compatible with Windows")

APP = ["Main.py"]
DATA_FILES = [curDirPath + "/Utility/Logging/token.json", curDirPath + "/Images"]
OPTIONS = {
    "argv_emulation": True,
    "extension": ".app",
    "iconfile": curDirPath + "/Images/icon.png",
    "includes": ["os", "platform"],
    "plist": {
        "CFBundleName": app_name,
        "CFBundleDisplayName": app_name,
        "CFBundleGetInfoString": "Esper API Support Tool",
        "CDBundleIdentifier": "com.esper.esperapisupporttool",
        "CFBundleVersion": Globals.VERSION,
        "CFBundleShortVersionString": Globals.VERSION,
        "NSHumanReadableCopyright": "No Copyright © 2022",
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
    version=Globals.VERSION,
    long_description=Globals.DESCRIPTION,
    name="Esper API Support Tool",
    url="https://github.com/esper-io/esper-api-support-tool/",
)
