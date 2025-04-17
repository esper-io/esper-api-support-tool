import json
import os
import platform
import sys
from datetime import datetime

import pytz

import Common.Globals as Globals
import Utility.Email.EmailUtils as email
from Utility.FileUtility import read_json_file
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Logging.SlackUtils import SlackUtils


class AuditPosting:
    def __init__(self):
        self.login = ""
        self.pw = ""
        self.to_addr = []

        if Globals.THREAD_POOL:
            Globals.THREAD_POOL.enqueue(self.initAudit)
        else:
            self.getEmailInfo()

            self.util = email.EmailUtils(self.login, self.pw, self.to_addr)
            self.slack_utils = SlackUtils()

    def initAudit(self):
        self.getEmailInfo()

        self.util = email.EmailUtils(self.login, self.pw, self.to_addr)
        self.slack_utils = SlackUtils()

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
            tokenJson = read_json_file(filePath)
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

        # Avoid sending messages when debugging
        if Globals.IS_DEBUG and not Globals.DO_EXTRA_LOGGING:
            return

        if type(values) is dict and "operation" in values and "data" in values:
            try:
                self.slack_utils.append_message_and_blocks(
                    values["operation"],
                    values["data"],
                    values["resp"] if "resp" in values else "",
                )
            except Exception as e:
                ApiToolLog().LogError(e)
                if "resp" in values:
                    self.emailOperation(values["operation"], values["data"], values["resp"])
                else:
                    self.emailOperation(values["operation"], values["data"])

    def emailOperation(self, operation, data, resp=""):
        now = datetime.now(tz=pytz.utc).strftime("%Y-%m-%d_%H:%M:%S")
        host = Globals.configuration.host.replace("https://", "").replace("-api.esper.cloud/api", "")
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
            userStr = "User (id: %s) [OS: %s]: %s\n\n" % (
                (Globals.TOKEN_USER["id"] if Globals.TOKEN_USER and "id" in Globals.TOKEN_USER else "Unknown"),
                platform.system(),
                (Globals.TOKEN_USER["username"] if Globals.TOKEN_USER and "username" in Globals.TOKEN_USER else "Unknown"),
            )
            contentStr = "\nResponse Content: " + content if content else ""
            if hasattr(data, "to_dict"):
                data = data.to_dict()
            if type(data) is dict:
                data = json.dumps(data, indent=4)
            self.util.sendEmail(
                "%s UTC %s : %s" % (now, host, str(operation)),
                userStr + "Data:\n%s" % str(data) + contentStr,
            )

    def postStoredOperations(self):
        self.slack_utils.send_stored_operations()
