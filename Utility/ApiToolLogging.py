#!/usr/bin/env python

import tempfile
import platform
import sys
import os

from datetime import datetime
from traceback import print_exc, extract_tb, format_list


class ApiToolLog:
    def __init__(self):
        self.logPath = ""
        if platform.system() == "Windows":
            self.logPath = (
                "%s\\EsperApiTool\\ApiTool.log"
                % tempfile.gettempdir().replace("Local", "Roaming").replace("Temp", "")
            )
        else:
            self.logPath = "%s/EsperApiTool/ApiTool.log" % os.path.expanduser(
                "~/Desktop/"
            )
        if not os.path.exists(self.logPath):
            if not os.path.exists(self.logPath):
                parentPath = os.path.abspath(os.path.join(self.logPath, os.pardir))
                if not os.path.exists(parentPath):
                    os.makedirs(parentPath)
                with open(self.logPath, "w"):
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

    def LogResponse(self, response):
        with open(self.logPath, "a") as myfile:
            myfile.write(response)
