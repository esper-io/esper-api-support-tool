import os
import sys

import sentry_sdk

from Utility.FileUtility import read_json_file


class SentryUtils():

    def __init__(self):
        self.dsn = ""

        self.readTokenInfo()

        if self.dsn:
            sentry_sdk.init(self.dsn, traces_sample_rate=1.0)

    def readTokenInfo(self):
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
            self.dsn = tokenJson.get("sentry_dsn", "")