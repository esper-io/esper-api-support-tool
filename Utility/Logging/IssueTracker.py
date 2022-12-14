#!/usr/bin/env python

import json
import os
import sys

import requests

import Common.Globals as Globals


class IssueTracker:
    def listOpenIssues(self):
        url = "https://api.github.com/repos/esper-io/esper-api-support-tool/issues?labels=bug&state=open"
        resp = self.performGetRequestWithRetry(url)
        if resp:
            return resp.json()
        else:
            return None

    def createIssue(self, title, body):
        url = "https://api.github.com/repos/esper-io/esper-api-support-tool/issues"
        token = self.getAccessToken()
        if token:
            header = {
                "Authorization": "Bearer %s" % token,
                "Content-Type": "application/json",
            }
            body = {"title": title, "body": body, "labels": ["bug"]}
            resp = self.performPostRequestWithRetry(url, headers=header, json=body)
            return resp

    def getAccessToken(self):
        filePath = "token.json"
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
            base_path = os.path.join(base_path, "Utility", "Logging")

        filePath = os.path.join(base_path, filePath)
        if os.path.exists(filePath):
            with open(filePath, "r") as file:
                tokenJson = json.load(file)
            if "pat" in tokenJson:
                return tokenJson["pat"]

    def postIssueComment(self, issueNum, body):
        url = (
            "https://api.github.com/repos/esper-io/esper-api-support-tool/issues/%s/comments"
            % issueNum
        )
        webBody = {"body": "\n".join(body)}
        token = self.getAccessToken()
        if token:
            header = {
                "Authorization": "Bearer %s" % token,
                "Content-Type": "application/json",
            }
            resp = self.performPostRequestWithRetry(url, headers=header, json=webBody)
            return resp

    def performGetRequestWithRetry(
        self, url, headers=None, json=None, data=None, maxRetry=Globals.MAX_RETRY
    ):
        resp = None
        for _ in range(maxRetry):
            try:
                resp = requests.get(url, headers=headers, json=json, data=data)
                if resp.status_code < 300:
                    break
            except:
                pass
        return resp

    def performPostRequestWithRetry(
        self, url, headers=None, json=None, data=None, maxRetry=Globals.MAX_RETRY
    ):
        resp = None
        for _ in range(maxRetry):
            try:
                resp = requests.post(url, headers=headers, json=json, data=data)
                if resp.status_code < 300:
                    break
            except:
                pass
        return resp
