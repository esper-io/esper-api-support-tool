#!/usr/bin/env python

import tempfile
import platform

from datetime import date


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

    def LogError(self, e, exc_type, exc_value, exc_traceback):
        with open(self.logPath, "a") as myfile:
            myfile.write("%s\t: An Error has occured: %s\n" % (date.today(), e))
            myfile.write(str(exc_type))
            myfile.write(str(exc_value))
            for line in exc_traceback:
                myfile.write(str(line))

    def LogResponse(self, response):
        with open(self.logPath, "a") as myfile:
            myfile.write(response)
