#!/usr/bin/env python

import json
import sys
import threading
import time
from datetime import datetime
from functools import wraps
from traceback import extract_tb, format_list, print_exc

import wx
from esperclient.rest import ApiException

import Common.Globals as Globals
from Utility.Logging.ApiToolLogging import ApiToolLog


def api_tool_decorator(locks=None, displayPrompt=True):
    def inner(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = None
            try:
                start = time.perf_counter()
            except:
                pass
            result = None
            excpt = None
            logPlace(func, *args, **kwargs)
            if not Globals.API_LOGGER:
                Globals.API_LOGGER = ApiToolLog()
            try:
                result = func(*args, **kwargs)
                logPlaceDone(func, *args, **kwargs)
            except ApiException as e:
                logError(e)
                if displayPrompt:
                    excpt = determineErrorDisplay(e)
            except Exception as e:
                logError(e)
                if displayPrompt:
                    excpt = determineErrorDisplay(e)
            finally:
                if Globals.frame and excpt:
                    Globals.frame.Logging(str(excpt), isError=True)
                    currThread = threading.current_thread()
                    invalidThreadNames = [
                        "InternetCheck",
                        "updateErrorTracker",
                        "SavePrefs",
                        currThread.name,
                    ]
                    for thread in threading.enumerate():
                        if (
                            thread.name not in invalidThreadNames
                            and "main" not in thread.name.lower()
                            and hasattr(thread, "stop")
                        ):
                            thread.stop()
                    Globals.frame.onComplete(None, True)
                    Globals.frame.setCursorDefault()
                    Globals.frame.statusBar.setGaugeValue(100)
                    if Globals.msg_lock.locked():
                        Globals.msg_lock.release()
                    if "locks" in kwargs:
                        for lock in kwargs["locks"]:
                            if lock.locked():
                                lock.release()
                    if locks:
                        for lock in locks:
                            if lock.locked():
                                lock.release()
            end = time.perf_counter()
            if start and end:
                duration = end - start
                if Globals.PRINT_FUNC_DURATION:
                    print(
                        "%s executed in %s seconds." % (func.__name__, duration)
                    )
            return result

        return wrapper

    return inner


def determineErrorDisplay(e):
    Globals.error_lock.acquire(timeout=10)
    if str(e) in Globals.error_tracker and str(e) not in Globals.EXCEPTION_MSGS:
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
    if Globals.error_lock.locked():
        Globals.error_lock.release()
    return e


def displayApiExcpetionMsg(e):
    Globals.msg_lock.acquire(timeout=10)
    bodyMsg = json.loads(e.body)["message"]
    wx.MessageBox(
        "%s %s: %s" % (e.reason, e.status, bodyMsg),
        style=wx.OK | wx.ICON_ERROR,
        parent=Globals.frame,
    )
    if Globals.msg_lock.locked():
        Globals.msg_lock.release()
    return e


def displayGenericErrorMsg(e):
    Globals.msg_lock.acquire(timeout=10)
    wx.MessageBox(
        "An Error has occured: \n\n%s" % e,
        style=wx.OK | wx.ICON_ERROR,
        parent=Globals.frame,
    )
    if Globals.msg_lock.locked():
        Globals.msg_lock.release()
    return e


def logError(e):
    print_exc()
    exc_type, exc_value, exc_traceback = sys.exc_info()
    exc_traceback = format_list(extract_tb(exc_traceback))
    ApiToolLog().LogError(e, exc_type, exc_value, exc_traceback)


def logPlace(func, *args, **kwargs):
    try:
        if Globals.RECORD_PLACE:
            place = construct_log_place_str("Starting", func, *args, **kwargs)
            ApiToolLog().LogPlace(place)
    except Exception as e:
        ApiToolLog().LogError(e)


def logPlaceDone(func, *args, **kwargs):
    try:
        if Globals.RECORD_PLACE:
            place = "Finshed"
            place = construct_log_place_str(place, func, *args, **kwargs)
            ApiToolLog().LogPlace(place)
    except Exception as e:
        ApiToolLog().LogError(e)


def construct_log_place_str(prefix, func, *args, **kwargs):
    currThread = threading.current_thread()
    place = "%s\t:\t%s" % (
        currThread.name,
        prefix + " " if not prefix.endswith(" ") else prefix,
    )
    if func.__name__ and func.__doc__:
        place += str(func.__name__ + "\t:\t" + func.__doc__)
    elif func.__name__:
        place += str(func.__name__)
    else:
        place += str(func)

    # argStrList = "\tArguements: "
    # if args:
    #     for x in args:
    #         if isinstance(x) is dict:
    #             argStrList += type(x) + ", "
    #         else:
    #             argStrList += str(x) + ", "

    # kwargStrList = "\tKeyword Arguements: "
    # if kwargs:
    #     for key, val in kwargs.items():
    #         if isinstance(val) is dict:
    #             kwargStrList += "%s:%s, " % (str(key), str(type(dict)))
    #         else:
    #             kwargStrList += "%s:%s, " % (str(key), str(val))

    return place  # + argStrList + kwargStrList
