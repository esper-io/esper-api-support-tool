import csv
import json
import os
import platform
import re
import ssl
import sys
from datetime import datetime

import pytz
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import Common.Globals as Globals
from Utility.FileUtility import getToolDataPath
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Resource import enforceRateLimit, resourcePath


class SlackUtils:
    def __init__(self):
        self.token = ""
        self.channel_id = ""
        self.debug = Globals.IS_DEBUG
        if not self.token or not self.channel_id:
            self.get_slack_details()
        self.client = WebClient(token=self.token) if self.token else None

        ssl._create_default_https_context = ssl._create_unverified_context

        basePath = getToolDataPath()
        self.filename = "east_operations.csv"
        self.operations_path = os.path.join(basePath, self.filename)
        self.messages_and_blocks = []

    def send_message(self, message):
        if self.client is None:
            return
        enforceRateLimit()
        return self.post_block_message(message, None)

    def get_slack_details(self):
        expected_file_path = "slack_details.json"
        base_path = ""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
            base_path = os.path.join(base_path, "Utility", "Logging")
        expected_file_path = os.path.join(base_path, expected_file_path)
        if os.path.exists(expected_file_path):
            with open(expected_file_path, "r") as f:
                data = json.load(f)
                if "token" not in data or "channel_id" not in data:
                    return
                self.token = data["token"]
                self.channel_id = data["channel_id"]
        else:
            ApiToolLog().Log("Current CWD: %s" % resourcePath(""))
            ApiToolLog().Log(os.listdir(resourcePath("")))

    def post_block_message(self, msg, blocks, thread_id=None):
        if self.client is None:
            return
        resp = None
        enforceRateLimit()
        try:
            resp = self.client.chat_postMessage(
                channel=self.channel_id,
                thread_ts=thread_id,
                text=msg,
                blocks=blocks,
            )
        except SlackApiError as e:
            print(f"Error posting message: {e}")
            ApiToolLog().LogError(e)
        except Exception as e:
            print(f"Error posting message: {e}")
            ApiToolLog().LogError(e)

        return resp

    def get_operation_blocks(self, operation, data, resp):
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "%sEAST Usage" % (":bug: " if self.debug else ""),
                    "emoji": True,
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Tenant:* %s\t\t\t*User:* %s (*ID:* %s)"
                    % (
                        Globals.configuration.host.replace(
                            "https://", ""
                        ).replace("-api.esper.cloud/api", ""),
                        (
                            Globals.TOKEN_USER["username"]
                            if Globals.TOKEN_USER
                            and "username" in Globals.TOKEN_USER
                            else "Unknown"
                        ),
                        (
                            Globals.TOKEN_USER["id"]
                            if Globals.TOKEN_USER and "id" in Globals.TOKEN_USER
                            else "Unknown"
                        ),
                    ),
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Operation:* %s\t\t\t*Platform:* %s %s"
                    % (operation, platform.system(), platform.release()),
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Date:* %s\t\t\tEAST Version:%s"
                    % (
                        datetime.now(tz=pytz.utc).strftime("%Y-%m-%d_%H:%M:%S"),
                        Globals.VERSION,
                    ),
                },
            },
            self.add_rich_text_section("Data", data),
            self.add_rich_text_section("Other", resp),
        ]
        return blocks

    def add_rich_text_section(self, section_name, data):
        dataStr = str(data) if data else "None"
        if len(dataStr) > 4000:
            dataStr = dataStr[0:1000]
        rich_text = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": [
                        {
                            "type": "text",
                            "text": "%s: " % section_name,
                            "style": {"bold": True},
                        },
                        {"type": "text", "text": dataStr},
                    ],
                }
            ],
        }
        return rich_text

    def reset_operations_file(self):
        if os.path.exists(self.operations_path):
            try:
                os.remove(self.operations_path)
            except Exception as e:
                ApiToolLog().LogError(e)
                return False
        return True

    def append_message_and_blocks(self, operation, data, resp):
        username = (
            Globals.TOKEN_USER["username"]
            if Globals.TOKEN_USER
            and "username" in Globals.TOKEN_USER
            else "Unknown"
        )
        userid =(
            Globals.TOKEN_USER["id"]
            if Globals.TOKEN_USER and "id" in Globals.TOKEN_USER
            else "Unknown"
        )
        if "error" in operation.lower():
            # Send error message immediately
            self.post_block_message(
                "EAST Error",
                self.get_operation_blocks(operation, data, resp),
            )
        else:
            # Save operation details to file so we can send latter
            self.messages_and_blocks.append({
                    "t": datetime.now(tz=pytz.utc).strftime("%Y-%m-%d_%H:%M:%S"),
                    "u": "%s (*ID:* %s)" % (username, userid),
                    "o": operation,
                    "d": data,
                    "r": resp
                }
            )
            try:
                with open(self.operations_path, "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    for entry in self.messages_and_blocks:
                        writer.writerow([entry["t"], entry["o"], entry["d"], entry["r"]])

                self.messages_and_blocks = []
            except Exception as e:
                return

    def get_summary_operations_block(self, data):
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "%sEAST Usage" % (":bug: " if self.debug else ""),
                    "emoji": True,
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Tenant:* %s\t\t\t*User:* %s (*ID:* %s)"
                    % (
                        Globals.configuration.host.replace(
                            "https://", ""
                        ).replace("-api.esper.cloud/api", ""),
                        (
                            Globals.TOKEN_USER["username"]
                            if Globals.TOKEN_USER
                            and "username" in Globals.TOKEN_USER
                            else "Unknown"
                        ),
                        (
                            Globals.TOKEN_USER["id"]
                            if Globals.TOKEN_USER and "id" in Globals.TOKEN_USER
                            else "Unknown"
                        ),
                    ),
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Platform:* %s %s\t\t\tEAST Version:%s"
                    % (platform.system(), platform.release(), Globals.VERSION,),
                },
            },
        ]
        if type(data) is list:
            operation_dict = {}
            for entry in data:
                api_summary_str = ""
                if type(entry) is list:
                    operation = entry[1]
                    if operation == "API Usage Summary" and len(entry) > 2:
                        data = entry[2]
                        summary_parts = data.split(":\t")
                        if len(summary_parts) > 1:
                            api_summary_str = summary_parts[1]
                    elif operation in operation_dict:
                        operation_dict[operation] += 1
                    else:
                        operation_dict[operation] = 1
            blocks.append(
                    self.add_rich_text_section(
                        "Operation Summary",
                        operation_dict
                    )
                )
            blocks.append(
                self.add_rich_text_section(
                    "API Summary",
                    re.sub("\\s", "", api_summary_str)
                )
            )
        return blocks

    def postMessageWithFile(self, message):
        resp = None
        if self.client is None:
            return resp
        try:
            if os.path.exists(self.operations_path):
                data = []
                with open(self.operations_path, "r") as f:
                    reader = csv.reader(f)
                    data = list(reader)

                if data:
                    blocks = self.get_summary_operations_block(data)

                    upload = self.client.files_upload(file=self.operations_path, filename=self.filename)
                    message = message+"<"+upload['file']['permalink']+"| >"
                    resp = self.client.chat_postMessage(
                        channel=self.channel_id,
                        text=message,
                        blocks=blocks,
                    )
        except Exception as e:
            ApiToolLog().LogError(e)
        return resp

    def send_stored_operations(self):
        if not Globals.IS_DEBUG:
            self.postMessageWithFile("East Usage")
            self.reset_operations_file()

