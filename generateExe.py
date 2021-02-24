#!/usr/bin/env python

import subprocess
import pathlib
import platform
import os
import shutil
import Common.Globals as Globals

from Utility.Resource import isModuleInstalled, installRequiredModules


if __name__ == "__main__":
    curDirPath = str(pathlib.Path().absolute()).replace("\\", "/")
    dispath = curDirPath + "/output"

    if not isModuleInstalled("pyinstaller"):
        installRequiredModules()
        raise Exception("Required Modules Installed. Please rerun the script.")

    if not os.path.exists(dispath):
        os.makedirs(dispath)

    cmd = []
    if platform.system() == "Windows":
        cmd = [
            "pyinstaller",
            "--noconfirm",
            "--onefile",
            "--windowed",
            "--clean",
            "--distpath",
            dispath,
            "--add-data",
            curDirPath
            + "/Images%sImages/" % (";" if platform.system() == "Windows" else ":"),
            curDirPath + "/Main.py",
        ]
    else:
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
            curDirPath
            + "/Images%sImages/" % (";" if platform.system() == "Windows" else ":"),
            curDirPath + "/Main.py",
        ]
    test = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output, error = test.communicate()

    try:
        if os.path.exists(dispath + "/Main.exe"):
            if os.path.exists(dispath + "/EsperApiSupportTool.exe"):
                os.remove(dispath + "/EsperApiSupportTool.exe")
            if os.path.exists(
                dispath
                + "/%s_EsperApiSupportTool.exe" % Globals.VERSION.replace(".", "-")
            ):
                os.remove(
                    dispath
                    + "/%s_EsperApiSupportTool.exe" % Globals.VERSION.replace(".", "-")
                )
            os.rename(
                dispath + "/Main.exe",
                dispath
                + "/%s_EsperApiSupportTool.exe" % Globals.VERSION.replace(".", "-"),
            )
        elif os.path.exists(dispath + "/Main.app"):
            if os.path.exists(dispath + "/EsperApiSupportTool.app"):
                if os.path.isfile(dispath + "/EsperApiSupportTool.app"):
                    os.remove(dispath + "/EsperApiSupportTool.app")
                else:
                    shutil.rmtree(dispath + "/EsperApiSupportTool.app")
                if os.path.isfile(
                    dispath
                    + "/%s_EsperApiSupportTool.app" % Globals.VERSION.replace(".", "-")
                ):
                    os.remove(
                        dispath
                        + "/%s_EsperApiSupportTool.app"
                        % Globals.VERSION.replace(".", "-")
                    )
                else:
                    shutil.rmtree(
                        dispath
                        + "/%s_EsperApiSupportTool.app"
                        % Globals.VERSION.replace(".", "-")
                    )
            os.rename(
                dispath + "/Main.app",
                dispath
                + "/%s_EsperApiSupportTool.app" % Globals.VERSION.replace(".", "-"),
            )
    except Exception as e:
        print(
            "FAILED to remove old executeable or rename the newly generated executable"
        )
        print(e)
        pass

    if output:
        output = output.decode("utf-8")
        print(output)

    if error:
        error = error.decode("utf-8")
        print(error)
