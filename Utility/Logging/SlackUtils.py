import json
import os
import platform
from datetime import datetime

import pytz
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import Common.Globals as Globals
from Utility.Resource import resourcePath


class SlackUtils:
    def __init__(self):
        self.token = ""
        self.channel_id = ""
        self.debug = Globals.IS_DEBUG
        if not self.token or not self.channel_id:
            self.get_slack_details()
        self.client = WebClient(token=self.token) if self.token else None

    def send_message(self, message):
        if self.client is None:
            return
        return self.post_block_message(message, None)

    def get_slack_details(self):
        expected_file_path = resourcePath("Utility/Logging/slack_details.json")
        if os.path.exists(expected_file_path):
            with open(expected_file_path, "r") as f:
                data = json.load(f)
                if "token" not in data or "channel_id" not in data:
                    return
                self.token = data["token"]
                self.channel_id = data["channel_id"]
        else:
            print("Current CWD: %s" % os.getcwd())
            print(os.listdir(os.getcwd()))

    def post_block_message(self, msg, blocks, thread_id=None):
        if self.client is None:
            return
        resp = None
        try:
            resp = self.client.chat_postMessage(
                channel=self.channel_id,
                thread_ts=thread_id,
                text=msg,
                blocks=blocks,
            )
        except SlackApiError as e:
            print(f"Error posting message: {e}")
        except Exception as e:
            print(f"Error posting message: {e}")

        return resp

    def get_operation_blocks(self, operation, data, resp):
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "EAST Usage",
                    "emoji": True
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Tenant:* %s\t\t\t*User:* %s (*ID:* %s)" % (
                            Globals.configuration.host.replace("https://", "").replace(
                            "-api.esper.cloud/api", "",
                            Globals.TOKEN_USER["username"]
                            if Globals.TOKEN_USER and "username" in Globals.TOKEN_USER
                            else "Unknown",
                            Globals.TOKEN_USER["id"]
                            if Globals.TOKEN_USER and "id" in Globals.TOKEN_USER
                            else "Unknown"
                        )
                    )
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Operation:* %s\t\t\t*Platform:* %s" % (operation, platform.system())
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Date:* %s" % datetime.now(tz=pytz.utc).strftime("%Y-%m-%d_%H:%M:%S")
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Data:* %s" % data
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Other:* %s" % resp
                }
            }
        ]
        return blocks