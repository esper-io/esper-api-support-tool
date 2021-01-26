#!/usr/bin/env python

import subprocess
import pathlib
import platform
import os

from Utility.Resource import isModuleInstalled, installRequiredModules


if __name__ == "__main__":
    curDirPath = str(pathlib.Path().absolute()).replace("\\", "/")
    dispath = curDirPath + "/output"

    if not isModuleInstalled("pyinstaller"):
        installRequiredModules()
        raise Exception("Required Modules Installed. Please rerun the script.")

    if not os.path.exists(dispath):
        os.makedirs(dispath)

    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--icon",
        curDirPath + "/Images/icon.png",
        "--clean",
        "--distpath",
        dispath,
        "--add-data",
        curDirPath + "/Images%sImages/" % (";" if platform.system() == "Windows" else ":"),
        curDirPath + "/Main.py",
    ]
    test = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output, error = test.communicate()

    if os.path.exists(dispath + "/Main.exe"):
        if os.path.exists(dispath + "/EsperApiSupportTool.exe"):
            os.remove(dispath + "/EsperApiSupportTool.exe")
        os.rename(dispath + "/Main.exe", dispath + "/EsperApiSupportTool.exe")
    elif os.path.exists(dispath + "/Main.app"):
        if os.path.exists(dispath + "/EsperApiSupportTool.app"):
            os.remove(dispath + "/EsperApiSupportTool.app")
        os.rename(dispath + "/Main.app", dispath + "/EsperApiSupportTool.app")

    if output:
        output = output.decode("utf-8")
        print(output)

    if error:
        error = error.decode("utf-8")
        print(error)
