#!/usr/bin/env python

import json
import os
import sys
import threading
import traceback
from datetime import datetime
from traceback import extract_tb, format_list, print_exc

from esperclient.rest import ApiException
from fuzzywuzzy import fuzz

import Common.ApiTracker as ApiTracker
import Common.Globals as Globals
from Utility.FileUtility import getToolDataPath, write_content_to_file
from Utility.Logging.IssueTracker import IssueTracker


class ApiToolLog:
    def __init__(self):
        self.tracker_lock = threading.Lock()

        basePath = getToolDataPath()
        self.logPath = "%s/ApiTool.log" % basePath
        self.placePath = "%s/ApiToolPlace.log" % basePath
        if not os.path.exists(self.logPath):
            parentPath = os.path.abspath(os.path.join(self.logPath, os.pardir))
            if not os.path.exists(parentPath):
                os.makedirs(parentPath)
            write_content_to_file(self.logPath, "")
        if not os.path.exists(self.placePath) and Globals.RECORD_PLACE:
            parentPath = os.path.abspath(
                os.path.join(self.placePath, os.pardir)
            )
            if not os.path.exists(parentPath):
                os.makedirs(parentPath)
            write_content_to_file(self.placePath, "")

        self.contain_blacklist = [
            "Invalid token",
            "ConnectionError",
            "HTTP Response",
            "Bad Gateway",
            "Permission denied",
            "HTTP",
            "Failed to load configuration",
            "Read-only file system",
            "ApiException",
        ]

    def limitLogFileSizes(self):
        self.limitFileSize(self.logPath)
        self.limitFileSize(self.placePath)

    def limitFileSize(self, file, maxFileSizeInMb=5):
        if (
            os.path.exists(file)
            and (os.path.getsize(file) / (1024 * 1024)) > maxFileSizeInMb
        ):
            write_content_to_file(file, "")

    def LogError(
        self,
        e,
        exc_type=None,
        exc_value=None,
        exc_traceback=None,
        postIssue=True,
        postStatus=True,
    ):
        if exc_type is None or exc_value is None or exc_traceback is None:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            exc_traceback = format_list(extract_tb(exc_traceback))

            if not exc_traceback:
                exc_traceback = traceback.format_exc()

        self.limitLogFileSizes()
        content = [
            "\n%s\t: An Error has occured: %s\n" % (datetime.now(), e),
            "\t%s\t%s\n" % (str(exc_type), str(exc_value)),
            "\tEsper Tool Version: %s\n" % Globals.VERSION,
        ]
        for line in exc_traceback:
            content.append(line.split('",')[1])

        self.Log(content)

        if postIssue:
            self.postIssueToTrack(e, content)

        if Globals.frame and postStatus:
            if Globals.frame.audit and not self.should_skip(content):
                Globals.frame.audit.postOperation(
                    {
                        "operation": "ERROR",
                        "data": content,
                    }
                )
            Globals.frame.Logging(str(e), True)

    def Log(self, msg):
        with open(self.logPath, "a") as myfile:
            if type(msg) == list:
                for entry in msg:
                    myfile.write("%s\n" % entry)
                myfile.write("\n")
            else:
                myfile.write("%s\n" % msg)

    def LogPlace(self, str_place):
        write_content_to_file(
            self.placePath, "%s\t: %s\n" % (datetime.now(), str_place), "a"
        )

    def LogResponse(self, response):
        write_content_to_file(
            self.placePath, "%s\t: %s\n" % (datetime.now(), response), "a"
        )

    def excepthook(self, type, value, tb):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        exc_traceback = format_list(extract_tb(exc_traceback))
        content = [
            "\n%s\tUncaught exception:\n" % datetime.now(),
            "".join(traceback.format_exception(type, value, tb)),
            "\tExc Type: %s\n" % str(exc_type) if str(exc_type) else type,
            "\tExc Value: %s\n" % str(exc_value) if str(exc_value) else value,
            (
                "\tExc Traceback:\n%s\n" % str(exc_traceback)
                if str(exc_traceback)
                else tb
            ),
            "\tEsper Tool Version: " + Globals.VERSION,
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

        if Globals.frame and hasattr(Globals.frame, "Logging"):
            Globals.frame.Logging(str(content), True)

    def LogApiRequestOccurrence(self, src, api_func, writeToFile=False):
        if "main" in threading.current_thread().name.lower():
            Globals.THREAD_POOL.enqueue(
                self.LogApiRequest, src, api_func, writeToFile
            )
        else:
            self.LogApiRequest(src, api_func, writeToFile)

    def LogApiRequest(self, src, api_func, writeToFile=False):
        strToWrite = ""
        if api_func and type(api_func) == dict:
            strToWrite = (
                "%s\tTenant: %s\n\tUser: %s (id: %s)\n\n\tSession API Summary:\t%s\n\n\tTotal Requests: %s\n\n"
                % (
                    datetime.now(),
                    str(Globals.configuration.host),
                    (
                        str(Globals.TOKEN_USER["username"])
                        if Globals.TOKEN_USER
                        and "username" in Globals.TOKEN_USER
                        else "Unknown"
                    ),
                    (
                        str(Globals.TOKEN_USER["id"])
                        if Globals.TOKEN_USER and "id" in Globals.TOKEN_USER
                        else "Unknown"
                    ),
                    (
                        str(api_func)
                        if api_func != ApiTracker.API_REQUEST_TRACKER
                        else json.dumps(
                            ApiTracker.API_REQUEST_TRACKER, indent=4
                        )
                    ),
                    ApiTracker.API_REQUEST_SESSION_TRACKER,
                )
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
            if not strToWrite:
                strToWrite = (
                    "%s API Request orginated from Tenant: %s User: %s (id: %s)\n\n\tFunction: %s, triggerring %s.\n\n\tTotal Requests: %s\n"
                    % (
                        datetime.now(),
                        str(Globals.configuration.host),
                        (
                            str(Globals.TOKEN_USER["username"])
                            if Globals.TOKEN_USER
                            and "username" in Globals.TOKEN_USER
                            else "Unknown"
                        ),
                        (
                            str(Globals.TOKEN_USER["id"])
                            if Globals.TOKEN_USER and "id" in Globals.TOKEN_USER
                            else "Unknown"
                        ),
                        str(src),
                        (
                            str(api_func)
                            if not hasattr(api_func, "__name__")
                            else api_func.__name__
                        ),
                        ApiTracker.API_REQUEST_SESSION_TRACKER,
                    )
                )
            Globals.api_log_lock.acquire()
            self.limitLogFileSizes()
            try:
                write_content_to_file(self.logPath, strToWrite, "a")
                if "Summary" in strToWrite and Globals.frame.audit:
                    Globals.frame.audit.postOperation(
                        {"operation": "API Usage Summary", "data": strToWrite}
                    )
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

        if self.should_skip(excpt):
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

        try:
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
        except Exception as e:
            print("Failed to post issue to tracker: %s" % e)

        if self.tracker_lock.locked():
            self.tracker_lock.release()

    def should_skip(self, error_excpt):
        if (
            Globals.IS_DEBUG
            or type(error_excpt) is ApiException
        ):
            return True
        
        for s in self.contain_blacklist:
            if s.lower() in str(error_excpt).lower():
                return True

        return False