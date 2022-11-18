#!/usr/bin/env python

import os
import platform
import sys
import tempfile
import threading
import traceback
from datetime import datetime
from traceback import extract_tb, format_list, print_exc

import Common.ApiTracker as ApiTracker
import Common.Globals as Globals
from esperclient.rest import ApiException
from fuzzywuzzy import fuzz
from Utility.Logging.IssueTracker import IssueTracker


class ApiToolLog:
    def __init__(self):
        self.logPath = ""
        self.placePath = ""
        self.tracker_lock = threading.Lock()

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

    def limitLogFileSizes(self):
        self.limitFileSize(self.logPath)
        self.limitFileSize(self.placePath)

    def limitFileSize(self, file, maxFileSizeInMb=5):
        if (
            os.path.exists(file)
            and (os.path.getsize(file) / (1024 * 1024)) > maxFileSizeInMb
        ):
            with open(file, "w"):
                pass

    def LogError(self, e, exc_type=None, exc_value=None, exc_traceback=None, postIssue=True):
        if exc_type is None or exc_value is None or exc_traceback is None:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            exc_traceback = format_list(extract_tb(exc_traceback))

        self.limitLogFileSizes()
        content = [
            "\n%s\t: An Error has occured: %s\n" % (datetime.now(), e),
            str(exc_type),
            str(exc_value),
            "Esper Version: " + Globals.VERSION,
        ]
        for line in exc_traceback:
            content.append(line)

        with open(self.logPath, "a") as myfile:
            for entry in content:
                myfile.write("%s\n" % entry)
            myfile.write("\n")

        if postIssue:
            self.postIssueToTrack(e, content)

        if Globals.frame:
            Globals.frame.Logging(str(e), True)

    def LogPlace(self, str):
        with open(self.placePath, "a") as myfile:
            myfile.write("%s\t: %s\n" % (datetime.now(), str))

    def LogResponse(self, response):
        with open(self.logPath, "a") as myfile:
            myfile.write(response + "\n")

    def excepthook(self, type, value, tb):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        exc_traceback = format_list(extract_tb(exc_traceback))
        content = [
            "\n%s\tUncaught exception:\n" % datetime.now(),
            "".join(traceback.format_exception(type, value, tb)),
            "Exc Type: %s\n" % str(exc_type) if str(exc_type) else type,
            "Exc Value: %s\n" % str(exc_value) if str(exc_value) else value,
            "Exc Traceback:\n%s\n" % str(exc_traceback) if str(exc_traceback) else tb,
            "Esper Version: " + Globals.VERSION,
        ]
        print_exc()
        for line in exc_traceback:
            content.append(str(line))
        self.limitLogFileSizes()
        with open(self.logPath, "a") as myfile:
            for entry in content:
                myfile.write("%s\n" % entry)
            myfile.write("\n")

        self.postIssueToTrack("%s %s" % (content[2], content[3]), content)

        Globals.frame.Logging(str(content), True)

    def LogApiRequestOccurrence(self, src, api_func, writeToFile=False):
        if "main" in threading.current_thread().name.lower():
            Globals.THREAD_POOL.enqueue(self.LogApiRequest, src, api_func, writeToFile)
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
        if writeToFile:
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
            Globals.api_log_lock.acquire()
            self.limitLogFileSizes()
            try:
                with open(self.logPath, "a") as myfile:
                    myfile.write(strToWrite)
            except:
                pass
            finally:
                if Globals.api_log_lock.locked():
                    Globals.api_log_lock.release()

    def postIssueToTrack(self, excpt, content):
        if not Globals.AUTO_REPORT_ISSUES:
            return

        def getStrRatioSimilarity(s, t, usePartial=False):
            if usePartial:
                return fuzz.partial_ratio(s.lower(), t.lower())
            return fuzz.ratio(s.lower(), t.lower())

        if (
            Globals.IS_DEBUG
            or "Invalid token" in str(excpt)
            or "ConnectionError" in str(excpt)
            or "HTTP Response" in str(excpt)
            or "Bad Gateway" in str(excpt)
            or "Permission denied" in str(excpt)
            or "HTTP" in str(excpt)
            or "Failed to load configuration" in str(excpt)
            or type(excpt) is ApiException
        ):
            return

        self.tracker_lock.acquire()

        tracker = IssueTracker()
        title = None
        if excpt is not None:
            content.insert(0, str(excpt))
        content.append("EAST Version:\t%s" % Globals.VERSION)
        dir_path = os.path.dirname(os.path.realpath(__file__))
        body = "\n".join(
            str(entry)
            .replace(os.getcwd(), "<user_path>")
            .replace(dir_path, "<user_path>")
            .replace(os.path.expanduser("~"), "<user_path>")
            for entry in content
        )

        if isinstance(excpt, Exception):
            title = repr(excpt)
        elif excpt is not None:
            title = str(excpt)

        issues = tracker.listOpenIssues()
        if issues:
            match = False
            for issue in issues:
                ratio = getStrRatioSimilarity(issue["title"], title, True)
                if ratio >= 90:
                    match = True
                    tracker.postIssueComment(issue["number"], content)
                    break
            if not match:
                tracker.createIssue(title, body)
        else:
            tracker.createIssue(title, body)

        if self.tracker_lock.locked():
            self.tracker_lock.release()
