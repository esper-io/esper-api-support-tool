#!/usr/bin/env python

import tempfile
import platform
import sys

from datetime import date
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
            self.logPath = "%s/EsperApiTool/ApiTool.log" % tempfile.gettempdir()

    def LogError(self, e, exc_type=None, exc_value=None, exc_traceback=None):
        if exc_type == None or exc_value == None or exc_traceback == None:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            exc_traceback = format_list(extract_tb(exc_traceback))

        with open(self.logPath, "a") as myfile:
            myfile.write("\n%s\t: An Error has occured: %s\n" % (date.today(), e))
            myfile.write(str(exc_type))
            myfile.write(str(exc_value))
            for line in exc_traceback:
                myfile.write(str(line))

    def LogResponse(self, response):
        with open(self.logPath, "a") as myfile:
            myfile.write(response)
