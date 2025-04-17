#!/usr/bin/env python

import json
import os
import platform
import re
import shlex
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

import esperclient
import requests
import wx
import wx.grid
from ratelimit import limits, sleep_and_retry
from thefuzz import fuzz, process

import Common.Globals as Globals
from Common import enum
from Common.decorator import api_tool_decorator
from Utility import EventUtility
from Utility.EventUtility import CustomEvent
from Utility.FileUtility import write_content_to_file
from Utility.Logging.ApiToolLogging import ApiToolLog


def resourcePath(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


@api_tool_decorator()
def createNewFile(filePath, fileData=None):
    """Create a new File to write in"""
    if not os.path.exists(filePath):
        parentPath = os.path.abspath(os.path.join(filePath, os.pardir))
        if not os.path.exists(parentPath):
            os.makedirs(parentPath)
        write_content_to_file(filePath, fileData)


def scale_bitmap(bitmap, width, height):
    try:
        image = wx.Image(bitmap)
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        result = wx.Bitmap(image)
        return result
    except:
        data = bytearray((0, 0, 0))
        alpha = bytearray((0,))
        image = wx.Image(1, 1, data, alpha)
        return image.ConvertToBitmap()


def postEventToFrame(eventType, eventValue=None):
    """Post an Event to the Main Thread"""
    if eventType:
        try:
            evt = CustomEvent(eventType, -1, eventValue)
            if Globals.frame and not Globals.frame.kill:
                wx.PostEvent(Globals.frame, evt)
        except Exception as e:
            ApiToolLog().LogError(e)
            raise e


def download(url, file_name, overwrite=True, raiseError=True):
    try:
        if os.path.exists(file_name) and overwrite:
            os.remove(file_name)
    except Exception as e:
        print(e)
        ApiToolLog().LogError(e, postIssue=False)
    # open in binary mode
    try:
        with open(file_name, "wb") as file:
            # get request
            response = requests.get(url)
            # write to file
            file.write(response.content)
    except Exception as e:
        ApiToolLog().LogError(e, postIssue=False)
        if raiseError:
            raise e
        else:
            print(e)


def checkInternetConnection(url):
    try:
        requests.get(url)
        return True
    except Exception as e:
        print(e)
    return False


def checkEsperInternetConnection():
    return checkInternetConnection(Globals.ESPER_LINK)


def checkForInternetAccess(frame):
    while not frame.kill:
        if frame.IsShownOnScreen() and frame.IsActive():
            if (
                not checkEsperInternetConnection()
                and not checkInternetConnection(Globals.LATEST_UPDATE_LINK)
            ):
                displayMessageBox(
                    (
                        "ERROR: An internet connection is required when using the tool!",
                        wx.OK | wx.ICON_ERROR | wx.CENTRE,
                    )
                )
                Globals.HAS_INTERNET = False
            else:
                if Globals.HAS_INTERNET is None and Globals.frame:
                    Globals.frame.loadPref()
                Globals.HAS_INTERNET = True
        time.sleep(15 if Globals.HAS_INTERNET else 30)


def checkForUpdate():
    try:
        response = None
        if Globals.CHECK_PRERELEASES:
            response = requests.get(Globals.UPDATE_LINK)
        else:
            response = requests.get(Globals.LATEST_UPDATE_LINK)
        if response:
            json_resp = response.json()
            if Globals.CHECK_PRERELEASES:
                json_resp = json_resp[0]
            return json_resp
    except Exception as e:
        print(e)

    return None


def downloadFileFromUrl(
    url, fileName, filepath="", redirects=True, chunk_size=1024
):
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
        total_length = r.headers.get("content-length")
        if total_length:
            total_length = int(total_length)

        dl = 0
        with open(fullPath, "wb") as file:
            for chunk in r.iter_content(chunk_size=chunk_size):
                dl += len(chunk)
                if chunk:
                    file.write(chunk)
                postEventToFrame(
                    EventUtility.myEVT_UPDATE_GAUGE,
                    int(dl / total_length * 100),
                )
        return fullPath
    except Exception as e:
        print(e)
        ApiToolLog().LogError(e, postIssue=False)
    return None


def deleteFile(file):
    try:
        if os.path.exists(file):
            os.remove(file)
            return True
    except Exception as e:
        print(e)
        ApiToolLog().LogError(e, postIssue=False)
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


@api_tool_decorator(locks=[Globals.join_lock])
def joinThreadList(threads):
    if threads:
        Globals.join_lock.acquire()
        for thread in threads:
            if thread and thread.is_alive():
                thread.join()
    if Globals.join_lock.locked():
        Globals.join_lock.release()


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


@api_tool_decorator(locks=[Globals.msg_lock])
def displayMessageBox(event):
    if (
            platform.system() == "Darwin"
            and "main" not in threading.current_thread().name.lower()
        ):
            determineDoHereorMainThread(displayMessageBox, event)
            return
    value = None
    if hasattr(event, "GetValue"):
        value = event.GetValue()
    elif type(event) == tuple:
        value = event
    elif type(event) == str:
        value = event

    msg = ""
    sty = wx.ICON_INFORMATION
    if type(value) == tuple:
        msg = value[0]
        if len(value) > 1:
            sty = value[1]
    elif isinstance(value, str):
        msg = value
    if (sty & wx.CENTRE) != wx.CENTRE:
        sty |= wx.CENTRE

    res = None
    Globals.msg_lock.acquire()
    if msg:
        res = wx.MessageBox(msg, style=sty, parent=Globals.frame)
    if Globals.msg_lock.locked():
        Globals.msg_lock.release()
    return res


def splitListIntoChunks(
    mainList, maxThread=Globals.MAX_THREAD_COUNT, maxChunkSize=None
):
    if maxThread <= 0:
        return mainList
    if not mainList:
        return []
    n = int(len(mainList) / maxThread)
    if maxChunkSize:
        n = maxChunkSize
    if n == 0:
        n = len(mainList)
    if n > 0:
        splitResults = [
            mainList[i * n : (i + 1) * n]
            for i in range((len(mainList) + n - 1) // n)
        ]
    else:
        splitResults = mainList
    return splitResults


def logBadResponse(url, resp, json_resp=None, displayMsgBox=False):
    if Globals.PRINT_RESPONSES or (
        resp and hasattr(resp, "status_code") and resp.status_code >= 300
    ):
        print(url)
        prettyReponse = ""
        if not json_resp:
            try:
                json_resp = resp.json()
            except:
                pass
        if json_resp:
            prettyReponse = url + "\nResponse {result}".format(
                result=json.dumps(json_resp, indent=4, sort_keys=True)
            )
        else:
            prettyReponse = str(resp)
        print(prettyReponse)
        ApiToolLog().LogResponse(
            "\n%s\t" % datetime.now() + prettyReponse + "\n"
        )
        if displayMsgBox:
            displayMessageBox((prettyReponse, wx.ICON_ERROR))


def openWebLinkInBrowser(link, isfile=False):
    if hasattr(link, "GetLinkInfo"):
        link = link.GetLinkInfo().GetHref()
    if platform.system() == "Darwin" and isfile:
        link = "file://" + os.path.realpath(link)
    webbrowser.open(link)


@api_tool_decorator(locks=[Globals.error_lock])
def updateErrorTracker():
    while Globals.frame and not Globals.frame.kill:
        try:
            Globals.error_lock.acquire()
            if Globals.error_tracker:
                new_tracker = {}
                for key, value in Globals.error_tracker.items():
                    timeDiff = datetime.now() - value
                    minutes = timeDiff.total_seconds() / 60
                    if minutes <= Globals.MAX_ERROR_TIME_DIFF:
                        new_tracker[key] = value
                Globals.error_tracker = new_tracker
            if Globals.error_lock.locked():
                Globals.error_lock.release()
        except Exception as e:
            ApiToolLog().LogError(e)
        finally:
            if Globals.error_lock.locked():
                Globals.error_lock.release()
            time.sleep(60)
            if checkIfCurrentThreadStopped():
                break


def getStrRatioSimilarity(s, t, usePartial=False):
    try:
        if s and t:
            if s.lower().strip() == t.lower().strip():
                return 100

            if hasattr(fuzz, "ratio") and not usePartial:
                return fuzz.ratio(s.lower(), t.lower())
            elif hasattr(fuzz, "partial_ratio"):
                return fuzz.partial_ratio(s.lower(), t.lower())
    except Exception as e:
        ApiToolLog().LogError(e, postIssue=False, postStatus=False)
    return 0


def isApiKey(key):
    if type(key) != str:
        return False
    return len(key) == 36 and "-" in key


def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)


def acquireLocks(locks, timeout=5):
    if type(locks) == list:
        for lock in locks:
            if type(locks) == threading.Lock:
                locks.acquire(timeout=5)
    elif type(locks) == threading.Lock:
        locks.acquire(timeout=5)


def releaseLocks(locks):
    if type(locks) == list:
        for lock in locks:
            if type(locks) == threading.Lock and lock.locked():
                lock.release()
    elif type(locks) == threading.Lock and locks.locked():
        locks.release()


@api_tool_decorator()
def getHeader():
    if (
        Globals.configuration
        and Globals.configuration.api_key
        and "Authorization" in Globals.configuration.api_key
    ):
        return {
            "Authorization": f"Bearer {Globals.configuration.api_key['Authorization']}",
            "Content-Type": "application/json",
            "User-Agent": "Esper Api Support Tool %s " % Globals.VERSION,
        }
    else:
        return {}


@sleep_and_retry
@limits(calls=4000, period=(5 * 60))
def enforceRateLimit():
    pass


def getEsperConfig(host, apiKey, auth="Bearer"):
    configuration = esperclient.Configuration()
    configuration.host = host.replace("/v0/enterprise/", "")
    configuration.api_key["Authorization"] = apiKey
    configuration.api_key_prefix["Authorization"] = auth
    return configuration


def processFunc(event):
    """Primarily used to execute functions on the main thread (e.g. execute GUI actions on Mac)"""
    fun = event.GetValue()
    if callable(fun):
        fun()
    elif type(fun) == tuple and callable(fun[0]):
        if type(fun[1]) == tuple:
            # This breaks if intended tuple is given as a single argument
            fun[0](*fun[1])
        else:
            fun[0](fun[1])


@api_tool_decorator()
def determineDoHereorMainThread(func, *args, **kwargs):
    if not callable(func):
        return

    if (
        platform.system() == "Windows"
        and "main" in threading.current_thread().name.lower()
    ):
        # do here
        if args and kwargs:
            func(*args, **kwargs)
        elif not args and kwargs:
            func(**kwargs)
        elif args and not kwargs:
            func(*args)
        else:
            func()
    else:
        # do on main thread
        postEventToFrame(
            EventUtility.myEVT_PROCESS_FUNCTION,
            (func, args),
        )


def checkIfCurrentThreadStopped():
    isAbortSet = False
    if hasattr(threading.current_thread(), "abort"):
        isAbortSet = threading.current_thread().abort.is_set()
    elif hasattr(threading.current_thread(), "isStopped"):
        isAbortSet = threading.current_thread().isStopped()
    return isAbortSet


def correctSaveFileName(inFile):
    return re.sub("[#%&{}\\<>*?/$!'\":@+`|=]*", "", inFile)


def displayFileDialog(
    msg, wildcard, defaultFile="", styles=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
):
    Globals.frame.isSaving = True
    inFile = ""
    result = wx.ID_CANCEL
    with wx.FileDialog(
        Globals.frame,
        message=msg,
        defaultFile=defaultFile,
        wildcard=wildcard,
        defaultDir=str(Globals.frame.defaultDir),
        style=styles,
    ) as dlg:
        Globals.OPEN_DIALOGS.append(dlg)
        result = dlg.ShowModal()
        Globals.OPEN_DIALOGS.remove(dlg)
        inFile = dlg.GetPath()
        correctSaveFileName(inFile)

    if result == wx.ID_OK:  # Save button was pressed
        return inFile
    return None


def isDarkMode():
    return wx.SystemSettings.GetAppearance().IsDark()


def setElmTheme(elm):
    isDarkModeVar = isDarkMode()
    bgColor = enum.Color.darkdarkGrey.value
    fgColor = enum.Color.white.value

    if Globals.THEME == "Dark":
        isDarkModeVar = True
    elif Globals.THEME == "Light":
        isDarkModeVar = False

    if not isDarkModeVar:
        bgColor = enum.Color.lightGrey.value
        fgColor = enum.Color.black.value

    if (
        isDarkModeVar 
        and (
            isinstance(elm, wx.SearchCtrl)
            or (
                isinstance(elm, wx.TextCtrl)
                and isinstance(elm.GetParent(), wx.SearchCtrl)
                )
            )
        ):
        bgColor = enum.Color.grey.value
    elif (isDarkModeVar and isinstance(elm, wx.RadioBox)):
        bgColor = enum.Color.darkGrey.value
        fgColor = enum.Color.black.value
    elif (not isDarkModeVar 
        and (
            isinstance(elm, wx.SearchCtrl) 
            or isinstance(elm, wx.TextCtrl)
            or isinstance(elm, wx.grid.Grid)
            or isinstance(elm, wx.ListCtrl)
            or isinstance(elm, wx.ListBox)
            or isinstance(elm, wx.SpinCtrl)
        )
    ):
        bgColor = enum.Color.white.value

    if platform.system() == "Windows" and sys.getwindowsversion().build < 22000:
        # Windows 10
        if (isinstance(elm, wx.Panel) or isinstance(elm, wx.Button)) and hasattr(
            elm, "SetBackgroundColour"
        ):
            if isDarkModeVar:
                elm.SetBackgroundColour(enum.Color.darkdarkGrey.value)
                elm.SetForegroundColour(enum.Color.white.value)
            else:
                elm.SetBackgroundColour(enum.Color.lightGrey.value)
                elm.SetForegroundColour(enum.Color.black.value)
        if hasattr(elm, "GetChildren") and elm.GetChildren():
            for child in elm.GetChildren():
                setElmTheme(child)
    else:
        # Windows 11 & Mac
        if ((isinstance(elm, wx.Panel) 
            or isinstance(elm, wx.Button)
            or isinstance(elm, wx.Window))
            and not isInThemeBlacklist(elm)):
            setElementTheme(elm, bgColor, fgColor)
        if isinstance(elm, wx.grid.Grid):
            elm.SetDefaultCellBackgroundColour(bgColor)
            elm.SetDefaultCellTextColour(fgColor)
        if hasattr(elm, "GetChildren") and elm.GetChildren() and not isInThemeBlacklist(elm):
            for child in elm.GetChildren():
                setElmTheme(child)


def isInThemeBlacklist(elm):
    return (isinstance(elm, wx.grid.Grid)
            or isinstance(elm, wx.ToolBar)
            or isinstance(elm, wx.Button))


def setElementTheme(elm, bgColor, fgColor):
    if platform.system() == "Darwin" and "main" not in threading.current_thread().name.lower():
        determineDoHereorMainThread(setElementTheme, elm, bgColor, fgColor)
        return
    if hasattr(elm, "SetThemeEnabled"):
        elm.SetThemeEnabled(False)
    if hasattr(elm, "SetBackgroundColour"):
        elm.SetBackgroundColour(bgColor)
    if hasattr(elm, "SetForegroundColour"):
        elm.SetForegroundColour(fgColor)
    if hasattr(elm, "SetOwnBackgroundColour"):
        elm.SetOwnBackgroundColour(bgColor)
    if hasattr(elm, "SetOwnForegroundColour"):
        elm.SetOwnForegroundColour(fgColor)
    if hasattr(elm, "SetItemBackgroundColour"):
        for n in range(0, len(elm.GetItems())):
            elm.SetItemBackgroundColour(n, bgColor)
    if hasattr(elm, "SetItemForegroundColour"):
        for n in range(0, len(elm.GetItems())):
            elm.SetItemForegroundColour(n, fgColor)


def determineKeyEventClose(event) -> bool:
    keycode = event.GetKeyCode()
    isCmdOrCtrlDown = event.CmdDown() or event.ControlDown()
    if keycode == wx.WXK_ESCAPE or (isCmdOrCtrlDown and keycode == wx.WXK_CONTROL_W):
        return True
    return False

def onDialogEscape(elm, event):
    if hasattr(elm, "onClose") and determineKeyEventClose(event):
        elm.onClose(event)
    event.Skip()