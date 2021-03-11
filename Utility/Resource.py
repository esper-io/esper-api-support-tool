#!/usr/bin/env python

import os
import platform
import requests
import shlex
import sys
import time
import subprocess
import wx
import Utility.wxThread as wxThread
import Common.Globals as Globals

from Utility.ApiToolLogging import ApiToolLog
from pathlib import Path


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


def postEventToFrame(eventType, eventValue=None):
    """ Post an Event to the Main Thread """
    if eventType:
        try:
            evt = wxThread.CustomEvent(eventType, -1, eventValue)
            if Globals.frame:
                wx.PostEvent(Globals.frame, evt)
        except Exception as e:
            ApiToolLog().LogError(e)


def download(url, file_name, overwrite=True):
    try:
        if os.path.exists(file_name) and overwrite:
            os.remove(file_name)
    except Exception as e:
        print(e)
        ApiToolLog().LogError(e)
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


def checkForInternetAccess(frame):
    while not frame.kill:
        if (
            not checkEsperInternetConnection()
            and frame.IsShownOnScreen()
            and frame.IsActive()
        ):
            displayMessageBox(
                (
                    "ERROR: An internet connection is required when using the tool!",
                    wx.OK | wx.ICON_ERROR | wx.CENTRE | wx.STAY_ON_TOP,
                )
            )
        time.sleep(15)


def checkForUpdate():
    try:
        response = requests.get(Globals.UPDATE_LINK)
        json_resp = response.json()
        return json_resp
    except Exception as e:
        print(e)

    return None


def downloadFileFromUrl(url, fileName, filepath="", redirects=True, chunk_size=1024):
    if not filepath:
        filepath = str(os.path.join(Path.home(), "Downloads"))
    fullPath = os.path.join(filepath, fileName)
    num = 1
    while os.path.exists(fullPath):
        parts = fileName.split(".")
        parts.insert(1, (" (%s)" % num))
        parts[len(parts) - 1] = ".%s" % parts[len(parts) - 1]
        tmpFileName = "".join(parts)
        fullPath = os.path.join(filepath, tmpFileName)
        num += 1
    parentPath = os.path.abspath(os.path.join(fullPath, os.pardir))
    if not os.path.exists(parentPath):
        os.makedirs(parentPath)
    try:
        r = requests.get(url, stream=True, allow_redirects=redirects)
        with open(fullPath, "wb") as file:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    file.write(chunk)
        return fullPath
    except Exception as e:
        print(e)
        ApiToolLog().LogError(e)
    return None


def deleteFile(file):
    try:
        if os.path.exists(file):
            os.remove(file)
            return True
    except Exception as e:
        print(e)
        ApiToolLog().LogError(e)
    return False


def isModuleInstalled(module):
    cmd = "%s list" % ("pip" if platform.system() == "Windows" else "pip3")
    output = None
    if platform.system() == "Windows":
        output, _ = runSubprocessPOpen(cmd)
    else:
        output, _ = runOsPOpen(cmd)

    if output:
        if hasattr(output, "decode"):
            output = output.decode("utf-8")
        if module in output:
            return True

    return False


def installRequiredModules():
    cmd = "%s install -r requirements.txt" % (
        "pip" if platform.system() == "Windows" else "pip3"
    )
    error = None
    if platform.system() == "Windows":
        _, error = runSubprocessPOpen(cmd)
    else:
        _, error = runOsPOpen(cmd)

    if error:
        if hasattr(error, "decode"):
            error = error.decode("utf-8")
        print(error)


def runSubprocessPOpen(cmd, shell=False):
    output = error = None
    if platform.system() == "Windows":
        if isinstance(cmd, str):
            cmd = shlex.split(cmd)
        test = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=shell)
        output, error = test.communicate()
    return output, error


def runOsPOpen(cmd):
    output = error = None
    if not isinstance(cmd, str):
        cmd = " ".join(cmd)
    out = os.popen(cmd)
    output = out.read()
    return output, error


def joinThreadList(threads):
    if threads:
        for thread in threads:
            if thread and thread.is_alive():
                thread.join()


def limitActiveThreads(threads, max_alive=Globals.MAX_THREAD_COUNT, sleep=1):
    Globals.lock.acquire()
    numAlive = 0
    for thread in threads:
        if thread.is_alive():
            numAlive += 1
    if numAlive >= max_alive:
        for thread in threads:
            thread.join()
        time.sleep(1)
    Globals.lock.release()


def ipv6Tomac(ipv6):
    # remove subnet info if given
    subnetIndex = ipv6.find("/")
    if subnetIndex != -1:
        ipv6 = ipv6[:subnetIndex]

    ipv6Parts = ipv6.split(":")
    macParts = []
    for ipv6Part in ipv6Parts[-4:]:
        while len(ipv6Part) < 4:
            ipv6Part = "0" + ipv6Part
        macParts.append(ipv6Part[:2])
        macParts.append(ipv6Part[-2:])

    # modify parts to match MAC value
    macParts[0] = "%02x" % (int(macParts[0], 16) ^ 2)
    del macParts[4]
    del macParts[3]

    return ":".join(macParts)


def displayMessageBox(event):
    value = None
    if hasattr(event, "GetValue"):
        value = event.GetValue()
    elif type(event) == tuple:
        value = event
    msg = ""
    sty = wx.ICON_INFORMATION
    if type(value) == tuple:
        msg = value[0]
        if len(value) > 1:
            sty = value[1]
    elif isinstance(value, str):
        msg = value

    if msg:
        wx.MessageBox(msg, style=sty)


def splitListIntoChunks(mainList, maxThread=Globals.MAX_THREAD_COUNT):
    n = int(len(mainList) / maxThread)
    if n == 0:
        n = len(mainList)
    splitResults = [
        mainList[i * n : (i + 1) * n] for i in range((len(mainList) + n - 1) // n)
    ]
    return splitResults
