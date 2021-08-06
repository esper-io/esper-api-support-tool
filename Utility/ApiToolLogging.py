#!/usr/bin/env python

import tempfile
import platform
import sys
import os
import traceback
import Common.Globals as Globals
import Common.ApiTracker as ApiTracker
import threading

from datetime import datetime
from traceback import print_exc, extract_tb, format_list


class ApiToolLog:
    def __init__(self):
        self.logPath = ""
        self.placePath = ""
        if platform.system() == "Windows":
            self.logPath = (
                "%s\\EsperApiTool\\ApiTool.log"
                % tempfile.gettempdir().replace("Local", "Roaming").replace("Temp", "")
            )
            self.placePath = (
                "%s\\EsperApiTool\\ApiToolPlace.log"
                % tempfile.gettempdir().replace("Local", "Roaming").replace("Temp", "")
            )
        else:
            self.logPath = "%s/EsperApiTool/ApiTool.log" % os.path.expanduser(
                "~/Desktop/"
            )
            self.placePath = "%s/EsperApiTool/ApiToolPlace.log" % os.path.expanduser(
                "~/Desktop/"
            )
        if not os.path.exists(self.logPath):
            parentPath = os.path.abspath(os.path.join(self.logPath, os.pardir))
            if not os.path.exists(parentPath):
                os.makedirs(parentPath)
            with open(self.logPath, "w"):
                pass
        if not os.path.exists(self.placePath) and Globals.RECORD_PLACE:
            parentPath = os.path.abspath(os.path.join(self.placePath, os.pardir))
            if not os.path.exists(parentPath):
                os.makedirs(parentPath)
            with open(self.placePath, "w"):
                pass

    def LogError(self, e, exc_type=None, exc_value=None, exc_traceback=None):
        if exc_type == None or exc_value == None or exc_traceback == None:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            exc_traceback = format_list(extract_tb(exc_traceback))

        with open(self.logPath, "a") as myfile:
            myfile.write("\n%s\t: An Error has occured: %s\n" % (datetime.now(), e))
            myfile.write(str(exc_type))
            myfile.write(str(exc_value))
            for line in exc_traceback:
                myfile.write(str(line))
            myfile.write("\n")

    def LogPlace(self, str):
        with open(self.placePath, "a") as myfile:
            myfile.write("%s\t: %s\n" % (datetime.now(), str))

    def LogResponse(self, response):
        with open(self.logPath, "a") as myfile:
            myfile.write(response)

    def excepthook(self, type, value, tb):
        message = "\n%s\tUncaught exception:\n" % datetime.now()
        print_exc()
        exc_type, exc_value, exc_traceback = sys.exc_info()
        exc_traceback = format_list(extract_tb(exc_traceback))
        message += "".join(traceback.format_exception(type, value, tb))
        message += "Exc Type: %s\n" % str(exc_type) if str(exc_type) else type
        message += "Exc Value: %s\n" % str(exc_value) if str(exc_value) else value
        message += (
            "Exc Traceback:\n%s\n" % str(exc_traceback) if str(exc_traceback) else tb
        )
        for line in exc_traceback:
            message += str(line)
        message += "\n"
        print(message)
        with open(self.logPath, "a") as myfile:
            myfile.write(message)

    def LogApiRequestOccurrence(self, src, api_func, writeToFile=False):
        if "main" in threading.current_thread().name.lower():
            thread = threading.Thread(
                target=self.LogApiRequest, args=(src, api_func, writeToFile)
            )
            thread.start()
            return thread
        else:
            self.LogApiRequest(src, api_func, writeToFile)

    def LogApiRequest(self, src, api_func, writeToFile=False):
        strToWrite = ""
        if api_func and type(api_func) == dict:
            strToWrite = "%s Session API Summary:\t%s\nTotal Requests: %s\n\n" % (
                datetime.now(),
                str(api_func),
                ApiTracker.API_REQUEST_SESSION_TRACKER,
            )
        else:
            ApiTracker.API_REQUEST_SESSION_TRACKER += 1
            incremented = False
            for key in ApiTracker.API_REQUEST_TRACKER.keys():
                if (
                    api_func
                    and hasattr(api_func, "__name__")
                    and key.replace("/", "") in api_func.__name__
                ):
                    ApiTracker.API_REQUEST_TRACKER[key] += 1
                    incremented = True
                elif (
                    api_func
                    and type(api_func) == str
                    and (key in api_func or api_func.endswith(key))
                ):
                    ApiTracker.API_REQUEST_TRACKER[key] += 1
                    incremented = True
                if incremented:
                    break
            if not incremented:
                if (
                    api_func
                    and hasattr(api_func, "__name__")
                    and api_func.__name__ in ApiTracker.API_FUNCTIONS.keys()
                ):
                    ApiTracker.API_REQUEST_TRACKER[
                        ApiTracker.API_FUNCTIONS[api_func.__name__]
                    ] += 1
                else:
                    ApiTracker.API_REQUEST_TRACKER["OtherAPI"] += 1
                    writeToFile = True
            strToWrite = (
                "%s API Request orginated from %s, triggerring %s. Total Requests: %s\n"
                % (
                    datetime.now(),
                    str(src),
                    str(api_func)
                    if not hasattr(api_func, "__name__")
                    else api_func.__name__,
                    ApiTracker.API_REQUEST_SESSION_TRACKER,
                )
            )
        if strToWrite and writeToFile:
            Globals.api_log_lock.acquire()
            try:
                with open(self.logPath, "a") as myfile:
                    myfile.write(strToWrite)
            except:
                pass
            finally:
                if Globals.api_log_lock.locked():
                    Globals.api_log_lock.release()
