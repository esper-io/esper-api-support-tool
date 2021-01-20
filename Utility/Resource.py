#!/usr/bin/env python

import os
import platform
import requests
import shlex
import sys
import subprocess
import wx
import Utility.wxThread as wxThread
import Common.Globals as Globals

from Common.decorator import api_tool_decorator


def resourcePath(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def createNewFile(filePath):
    """ Create a new File to write in """
    if not os.path.exists(filePath):
        parentPath = os.path.abspath(os.path.join(filePath, os.pardir))
        if not os.path.exists(parentPath):
            os.makedirs(parentPath)
        with open(filePath, "w"):
            pass


def scale_bitmap(bitmap, width, height):
    image = wx.Image(bitmap)
    image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
    result = wx.Bitmap(image)
    return result


@api_tool_decorator
def postEventToFrame(eventType, eventValue=None):
    """ Post an Event to the Main Thread """
    evt = wxThread.CustomEvent(eventType, -1, eventValue)
    if Globals.frame:
        wx.PostEvent(Globals.frame, evt)


def download(url, file_name, overwrite=True):
    try:
        if os.path.exists(file_name) and overwrite:
            os.remove(file_name)
    except Exception as e:
        print(e)
    # open in binary mode
    with open(file_name, "wb") as file:
        # get request
        response = requests.get(url)
        # write to file
        file.write(response.content)


def checkEsperInternetConnection():
    try:
        requests.get(Globals.ESPER_LINK)
        return True
    except Exception as e:
        print(e)
    return False


def deleteFile(file):
    try:
        if os.path.exists(file):
            os.remove(file)
            return True
    except Exception as e:
        print(e)
    return False


def isModuleInstalled(module):
    cmd = "pip list"
    runAsShell = False if platform.system() == "Windows" else True
    output, _ = runSubprocessPOpen(cmd, shell=runAsShell)

    if output:
        output = output.decode("utf-8")
        if module in output:
            return True

    return False


def installRequiredModules():
    cmd = "pip install -r requirements.txt"
    runAsShell = False if platform.system() == "Windows" else True
    _, error = runSubprocessPOpen(cmd, shell=runAsShell)

    if error:
        error = error.decode("utf-8")
        print(error)


def runSubprocessPOpen(cmd, shell=False):
    test = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, shell=shell)
    output, error = test.communicate()
    return output, error
