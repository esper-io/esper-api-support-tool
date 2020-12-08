import subprocess
import pathlib
import os

from Utility.Resource import isModuleInstalled, installRequiredModules


if __name__ == "__main__":
    curDirPath = str(pathlib.Path().absolute()).replace("\\", "/")
    dispath = curDirPath + "/output"

    if not isModuleInstalled("pyinstaller"):
        installRequiredModules()

    if not os.path.exists(dispath):
        os.makedirs(dispath)

    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--clean",
        "--distpath",
        dispath,
        "--add-data",
        curDirPath + "/Images;Images/",
        "--add-data",
        curDirPath + "/Images/icon.png;Images/",
        "--add-data",
        curDirPath + "/Images/logo.png;Images/",
        curDirPath + "/Main.py",
    ]
    test = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output, error = test.communicate()

    if os.path.exists(dispath + "/Main.exe"):
        if os.path.exists(dispath + "/EsperApiSupportTool.exe"):
            os.remove(dispath + "/EsperApiSupportTool.exe")
        os.rename(dispath + "/Main.exe", dispath + "/EsperApiSupportTool.exe")

    if output:
        output = output.decode("utf-8")
        print(output)

    if error:
        error = error.decode("utf-8")
        print(error)
