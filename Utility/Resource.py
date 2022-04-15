#!/usr/bin/env python

import threading
import json
import os
import platform
import requests
import shlex
import sys
import time
import subprocess
import wx
import webbrowser
import Common.Globals as Globals
import esperclient

from Common.decorator import api_tool_decorator
from fuzzywuzzy import fuzz
from datetime import datetime, timezone
from Utility.EventUtility import CustomEvent
from Utility.Logging.ApiToolLogging import ApiToolLog
from pathlib import Path
from ratelimit import sleep_and_retry, limits


def resourcePath(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def createNewFile(filePath, fileData=None):
    """ Create a new File to write in """
    if not os.path.exists(filePath):
        parentPath = os.path.abspath(os.path.join(filePath, os.pardir))
        if not os.path.exists(parentPath):
            os.makedirs(parentPath)
        with open(filePath, "w") as outfile:
            if fileData:
                outfile.write(fileData)


def scale_bitmap(bitmap, width, height):
    image = wx.Image(bitmap)
    image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
    result = wx.Bitmap(image)
    return result


def postEventToFrame(eventType, eventValue=None):
    """ Post an Event to the Main Thread """
    if eventType:
        try:
            evt = CustomEvent(eventType, -1, eventValue)
            if Globals.frame:
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
        ApiToolLog().LogError(e)
    # open in binary mode
    try:
        with open(file_name, "wb") as file:
            # get request
            response = requests.get(url)
            # write to file
            file.write(response.content)
    except Exception as e:
        ApiToolLog().LogError(e)
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
            if not checkEsperInternetConnection() and not checkInternetConnection(
                Globals.UPDATE_LINK
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


@api_tool_decorator(locks=[])
def limitActiveThreads(
    threads,
    max_alive=(Globals.MAX_ACTIVE_THREAD_COUNT / 2),
    timeout=-1,
    breakEnabled=True,
):
    if threads:
        numAlive = 0
        for thread in threads:
            if thread.is_alive():
                numAlive += 1
        if numAlive >= max_alive:
            for thread in threads:
                if thread.is_alive():
                    thread.join()
                    if breakEnabled:
                        if timeout > -1:
                            time.sleep(timeout)
                        break


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

    res = None
    Globals.msg_lock.acquire()
    if msg:
        res = wx.MessageBox(msg, style=sty)
    if Globals.msg_lock.locked():
        Globals.msg_lock.release()
    return res


def splitListIntoChunks(mainList, maxThread=Globals.MAX_THREAD_COUNT):
    n = int(len(mainList) / maxThread)
    if n == 0:
        n = len(mainList)
    if n > 0:
        splitResults = [
            mainList[i * n : (i + 1) * n] for i in range((len(mainList) + n - 1) // n)
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
        ApiToolLog().LogResponse("\n%s\t" % datetime.now() + prettyReponse + "\n")
        if displayMsgBox:
            displayMessageBox((prettyReponse, wx.ICON_ERROR))


def openWebLinkInBrowser(link):
    if hasattr(link, "GetLinkInfo"):
        link = link.GetLinkInfo().GetHref()
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
            if hasattr(threading.current_thread(), "isStopped"):
                if threading.current_thread().isStopped():
                    break


def getStrRatioSimilarity(s, t, usePartial=False):
    if usePartial:
        return fuzz.partial_ratio(s.lower(), t.lower())
    return fuzz.ratio(s.lower(), t.lower())


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
        }
    else:
        return {}


def getAllFromOffsets(
    func, group, api_response, maxAttempt=Globals.MAX_RETRY, results=[]
):
    threads = []
    responses = []
    count = None
    if hasattr(api_response, "count"):
        count = api_response.count
    elif type(api_response) is dict and "count" in api_response:
        count = api_response["count"]
    apiNext = None
    if hasattr(api_response, "next"):
        apiNext = api_response.next
    elif type(api_response) is dict and "next" in api_response:
        apiNext = api_response["next"]
    if apiNext:
        respOffset = apiNext.split("offset=")[-1].split("&")[0]
        respOffsetInt = int(respOffset)
        respLimit = apiNext.split("limit=")[-1].split("&")[0]
        while int(respOffsetInt) < count and int(respLimit) < count:
            thread = threading.Thread(
                target=func,
                args=(group, respLimit, str(respOffsetInt), maxAttempt),
            )
            threads.append(thread)
            thread.start()
            respOffsetInt += int(respLimit)
            limitActiveThreads(threads, max_alive=(Globals.MAX_THREAD_COUNT))
        joinThreadList(threads)
        obtained = sum(len(v["results"]) for v in responses) + int(respOffset)
        remainder = count - obtained
        if remainder > 0:
            respOffsetInt -= int(respLimit)
            respOffsetInt += 1
            thread = threading.Thread(
                target=func,
                args=(group, respLimit, str(respOffsetInt), maxAttempt),
            )
            threads.append(thread)
            thread.start()
            limitActiveThreads(threads)
    joinThreadList(threads)
    for resp in responses:
        if resp and hasattr(resp, "results") and resp.results:
            results += resp.results
        elif type(resp) is dict and "results" in resp and resp["results"]:
            results += resp["results"]
    return results


@sleep_and_retry
@limits(calls=10, period=1)
def enforceRateLimit():
    pass


def getEsperConfig(host, apiKey, auth="Bearer"):
    configuration = esperclient.Configuration()
    configuration.host = host.replace("/v0/enterprise/", "")
    configuration.api_key["Authorization"] = apiKey
    configuration.api_key_prefix["Authorization"] = auth
    return configuration
