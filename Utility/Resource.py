import os
import sys
import subprocess


def resourcePath(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def isModuleInstalled(module):
    cmd = "pip list"
    test = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output, error = test.communicate()

    if output:
        output = output.decode("utf-8")
        if module in output:
            return True

    return False


def installRequiredModules():
    cmd = "pip install -r requirements.txt"
    test = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output, error = test.communicate()

    if error:
        error = error.decode("utf-8")
        print(error)
