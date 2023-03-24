import Utility.Email.EmailUtils as email
import sys
import os
import json
import pytz

import Common.Globals as Globals

from datetime import datetime

class AuditPosting():
    def __init__(self):
        self.login = ""
        self.pw = ""
        self.to_addr = []

        self.getEmailInfo()

        self.util = email.EmailUtils(self.login, self.pw, self.to_addr)

    def getEmailInfo(self):
        filePath = "token.json"
        base_path = ""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
            base_path = os.path.join(base_path, "Utility", "Logging")

        filePath = os.path.join(base_path, filePath)
        if os.path.exists(filePath):
            tokenJson = {}
            with open(filePath, "r") as file:
                tokenJson = json.load(file)
            if "email_to" in tokenJson:
                self.to_addr = tokenJson["email_to"]
            if "email_login" in tokenJson:
                self.login = tokenJson["email_login"]
            if "email_to" in tokenJson:
                self.pw = tokenJson["email_pw"]

    def postOperation(self, event):
        values = None
        if hasattr(event, "GetValue"):
            values = event.GetValue()
        else:
            values = event

        if (type(values) is dict 
            and "operation" in values 
            and "data" in values):
            if "resp" in values:
                self.emailOperation(values["operation"], values["data"], values["resp"])
            else:
                self.emailOperation(values["operation"], values["data"])

    def emailOperation(self, operation, data, resp=""):
        now = datetime.now(tz=pytz.utc).strftime("%Y-%m-%d_%H:%M:%S")
        host = Globals.configuration.host.replace("https://", "").replace(
            "-api.esper.cloud/api", ""
        )
        if not Globals.TOKEN_USER and Globals.frame:
            Globals.frame.validateToken()

        content = None
        if hasattr(resp, "content"):
            content = str(resp.content.decode("utf-8"))
        elif hasattr(resp, "results"):
            content = resp.results
        else:
            content = str(resp)

        if type(data) is list:
            compoundStr = ""
            for line in data:
                compoundStr += line
            data = compoundStr

        if self.util.isReadyToSend():
            userStr = "User (id: %s): %s\n\n" % (Globals.TOKEN_USER["id"] if Globals.TOKEN_USER and "id" in Globals.TOKEN_USER else "Unknown",
                Globals.TOKEN_USER["username"] if Globals.TOKEN_USER and "username" in Globals.TOKEN_USER else "Unknown")
            contentStr = "Response Content: " + content if content else ""
            if type(data) is dict:
                data = json.dumps(data, indent=4)
            self.util.sendEmail(
                "%s UTC %s: %s" % (now, host, str(operation)),
                userStr
                + "Data:\n%s" % str(data)
                + contentStr
            )

