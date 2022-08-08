#!/usr/bin/env python

import datetime
import subprocess
import pathlib
import platform
import os
import re
import shutil
import Common.Globals as Globals

from Utility.Resource import isModuleInstalled, installRequiredModules


def updateFileVersionInfo(path="file_version_info.txt"):
    content = []
    newContent = []
    with open(path, "r") as file:
        content = file.readlines()

    if content:
        for line in content:
            match = re.search(
                r"StringStruct\(u'(?:FileVersion|LegalCopyright|ProductVersion)', u'.+",
                line,
            )
            newLine = ""
            if match:
                match = match.group(0)
                parts = match.split(", u'")
                field = parts[1]
                if field.endswith("'),") and "FileVersion" in parts[0]:
                    field = Globals.VERSION[1:] + "'),"
                elif field.endswith("'),") and "LegalCopyright" in parts[0]:
                    field = str(datetime.datetime.now().year) + "'),"
                elif field.endswith("')])"):
                    field = Globals.VERSION[1:] + "')])"
                parts[1] = field
                tmp = ", u'".join(parts)
                newLine = line.replace(match, tmp)
            if newLine:
                newContent.append(newLine)
            else:
                newContent.append(line)
    with open(path, "w") as file:
        for line in newContent:
            file.write(line)


if __name__ == "__main__":
    curDirPath = str(pathlib.Path().absolute()).replace("\\", "/")
    dispath = curDirPath + "/output"
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

    app_name = "%s_%s_%s_EsperApiSupportTool.%s" % (
        system[0:3].lower() if system == "Windows" else "mac",
        bit,
        Globals.VERSION.replace(".", "-"),
        "exe" if system == "Windows" else "app",
    )
    old_app_name = "EsperApiSupportTool.%s" % ("exe" if system == "Windows" else "app",)

    if not isModuleInstalled("pyinstaller"):
        installRequiredModules()
        raise Exception("Required Modules Installed. Please rerun the script.")

    if not os.path.exists(dispath):
        os.makedirs(dispath)

    cmd = []
    if platform.system() == "Windows":
        updateFileVersionInfo()
        cmd = [
            "pyinstaller",
            "--noconfirm",
            "--onefile",
            "--windowed",
            "--ascii",
            "--clean",
            "--name",
            app_name,
            "--distpath",
            dispath,
            "--version-file",
            curDirPath + "/file_version_info.txt",
            "--icon",
            curDirPath + "/Images/icon.ico",
            "--add-data",
            curDirPath
            + "/Images%sImages/" % (";" if platform.system() == "Windows" else ":"),
            "--add-data",
            curDirPath
            + "/Utility/Logging/token.json%s."
            % (";" if platform.system() == "Windows" else ":"),
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
            "--ascii",
            "--clean",
            "--name",
            app_name.replace(".app", ""),
            "--osx-bundle-identifier",
            "com.esper.esperapisupporttool",
            "--distpath",
            dispath,
            "--add-data",
            curDirPath
            + "/Images%sImages/" % (";" if platform.system() == "Windows" else ":"),
            "--add-data",
            curDirPath
            + "/Utility/Logging/token.json%s."
            % (";" if platform.system() == "Windows" else ":"),
            curDirPath + "/Main.py",
        ]
    test = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output, error = test.communicate()

    try:
        if os.path.exists(dispath + "/Main.exe"):
            if os.path.exists(dispath + "/" + old_app_name):
                os.remove(dispath + "/" + old_app_name)
            if os.path.exists(dispath + "/" + app_name):
                os.remove(dispath + "/" + app_name)
            os.rename(
                dispath + "/Main.exe",
                dispath + "/" + app_name,
            )
        elif os.path.exists(dispath + "/Main.app"):
            if os.path.exists(dispath + "/" + old_app_name):
                if os.path.isfile(dispath + "/" + old_app_name):
                    os.remove(dispath + "/" + old_app_name)
                else:
                    shutil.rmtree(dispath + "/" + old_app_name)
                if os.path.isfile(
                    dispath + "/" + app_name,
                ):
                    os.remove(
                        dispath + "/" + app_name,
                    )
                else:
                    shutil.rmtree(
                        dispath + "/" + app_name,
                    )
            os.rename(
                dispath + "/Main.app",
                dispath + "/" + app_name,
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

    for item in os.listdir():
        if item.endswith(".spec"):
            os.remove(item)

    if os.path.exists("build"):
        try:
            shutil.rmtree("build")
        except OSError as e:
            print("Error: %s - %s." % (e.filename, e.strerror))
