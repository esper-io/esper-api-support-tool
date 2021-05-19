#!/usr/bin/env python

import Common.Globals as Globals
import json
import sys
import time
import wx
import threading

from datetime import datetime
from esperclient.rest import ApiException
from Utility.ApiToolLogging import ApiToolLog
from traceback import print_exc, extract_tb, format_list


def api_tool_decorator(func):
    def inner(*args, **kwargs):
        start = None
        try:
            start = time.perf_counter()
        except:
            pass
        result = None
        excpt = None
        logPlace(func)
        try:
            result = func(*args, **kwargs)
            logPlaceDone(func)
        except ApiException as e:
            excpt = determineErrorDisplay(e)
            logError(e)
        except Exception as e:
            excpt = determineErrorDisplay(e)
            logError(e)
        finally:
            if Globals.frame and excpt:
                Globals.frame.Logging(str(excpt), isError=True)
                otherThreadsRunning = False
                for thread in threading.enumerate():
                    if (
                        thread.name != "InternetCheck"
                        and thread.name != "updateErrorTracker"
                        and "main" in thread.name.lower()
                        and thread.name != "SavePrefs"
                    ):
                        otherThreadsRunning = True
                        break
                if not otherThreadsRunning:
                    Globals.frame.onComplete(None, True)
                    Globals.frame.setCursorDefault()
                    Globals.frame.setGaugeValue(100)
                if Globals.msg_lock.locked():
                    Globals.msg_lock.release()
        end = time.perf_counter()
        if start and end:
            duration = end - start
            if Globals.PRINT_FUNC_DURATION:
                print("%s executed in %s seconds." % (func.__name__, duration))
        return result

    return inner


def determineErrorDisplay(e):
    Globals.error_lock.acquire()
    if str(e) in Globals.error_tracker:
        occurred = Globals.error_tracker[str(e)]
        timeDiff = datetime.now() - occurred
        minutes = timeDiff.total_seconds() / 60
        if minutes > Globals.MAX_ERROR_TIME_DIFF:
            Globals.error_tracker[str(e)] = datetime.now()
            if isinstance(e, ApiException):
                displayApiExcpetionMsg(e)
            else:
                displayGenericErrorMsg(e)
        else:
            print_exc()
    else:
        Globals.error_tracker[str(e)] = datetime.now()
        if isinstance(e, ApiException):
            displayApiExcpetionMsg(e)
        else:
            displayGenericErrorMsg(e)
    Globals.error_lock.release()
    return e


def displayApiExcpetionMsg(e):
    Globals.msg_lock.acquire()
    bodyMsg = json.loads(e.body)["message"]
    wx.MessageBox(
        "%s %s: %s" % (e.reason, e.status, bodyMsg),
        style=wx.OK | wx.ICON_ERROR,
    )
    return e


def displayGenericErrorMsg(e):
    Globals.msg_lock.acquire()
    wx.MessageBox("An Error has occured: \n\n%s" % e, style=wx.OK | wx.ICON_ERROR)
    return e


def logError(e):
    print_exc()
    exc_type, exc_value, exc_traceback = sys.exc_info()
    exc_traceback = format_list(extract_tb(exc_traceback))
    ApiToolLog().LogError(e, exc_type, exc_value, exc_traceback)


def logPlace(func):
    try:
        if Globals.RECORD_PLACE:
            place = ""
            currThread = threading.current_thread()
            if func.__name__ and func.__doc__:
                place = str(
                    func.__name__ + "\t:\t" + func.__doc__ + "\t:\t" + currThread.name
                )
            elif func.__name__:
                place = str(func.__name__ + "\t:\t" + currThread.name)
            ApiToolLog().LogPlace(place)
    except Exception as e:
        ApiToolLog().LogError(e)


def logPlaceDone(func):
    try:
        if Globals.RECORD_PLACE:
            place = "Finshed "
            currThread = threading.current_thread()
            if func.__name__ and func.__doc__:
                place += str(
                    func.__name__ + "\t:\t" + func.__doc__ + "\t:\t" + currThread.name
                )
            elif func.__name__:
                place += str(func.__name__ + "\t:\t" + currThread.name)
            ApiToolLog().LogPlace(place)
    except Exception as e:
        ApiToolLog().LogError(e)
