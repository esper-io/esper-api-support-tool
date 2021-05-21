#!/usr/bin/env python

import requests
import esperclient
import os
import wx
import time

import Utility.wxThread as wxThread
import Common.Globals as Globals

from Utility.ApiToolLogging import ApiToolLog
from Utility.Resource import (
    download,
    deleteFile,
    joinThreadList,
    performGetRequestWithRetry,
    performPatchRequestWithRetry,
    performPostRequestWithRetry,
)
from Utility.Resource import postEventToFrame

from Utility.EsperAPICalls import (
    getAllApplicationsForHost,
    createDeviceGroupForHost,
    getDeviceGroupsForHost,
    uploadApplicationForHost,
)

from datetime import datetime

from Common.decorator import api_tool_decorator

from esperclient import InlineResponse201


class EsperTemplateUtil:
    def __init__(self, toInfo=None, templateName=None, parent=None):
        self.apiLink = "https://{tenant}-api.esper.cloud/api/v0/enterprise/"
        self.template_extension = "/devicetemplate/"
        self.wallpaper_extension = "/wallpaper/"
        self.limit_extension = "?limit={num}"
        self.parent = parent
        self.toTenant = (
            toInfo["apiHost"]
            .strip()
            .replace("https://", "")
            .replace("http://", "")
            .replace("-api.esper.cloud/api", "")
            if toInfo
            else None
        )
        self.toKey = toInfo["apiKey"] if toInfo else None
        self.toEntId = toInfo["enterprise"] if toInfo else None
        self.templateName = templateName

        self.missingApps = ""

    @api_tool_decorator
    def prepareTemplate(self, dest=None, chosenTemplate=None):
        if self.parent and self.parent.gauge:
            self.parent.gauge.Pulse()

        self.toApi = self.apiLink.format(tenant=self.toTenant)

        toTemplates = (
            dest if dest else self.getTemplates(self.toApi, self.toKey, self.toEntId)
        )
        toApps = getAllApplicationsForHost(
            self.getEsperConfig(self.toApi, self.toKey), self.toEntId
        )

        templateFound = None
        maxId = len(toTemplates) + 1
        templateExist = list(
            filter(lambda x: x["name"] == self.templateName, toTemplates)
        )
        templateFound = chosenTemplate

        if templateFound:
            templateFound["enterprise"] = self.toEntId
            templateFound = self.checkTemplate(
                templateFound,
                toApps.results,
                self.getEsperConfig(self.toApi, self.toKey),
                self.toEntId,
            )

            if templateExist:
                templateFound["id"] = templateExist[0]["id"]
                postEventToFrame(
                    wxThread.myEVT_CONFIRM_CLONE_UPDATE,
                    (
                        self,
                        self.toApi,
                        self.toKey,
                        self.toEntId,
                        templateFound,
                        self.missingApps,
                    ),
                )
            else:
                templateFound["id"] = maxId + 1
                postEventToFrame(
                    wxThread.myEVT_CONFIRM_CLONE,
                    (
                        self,
                        self.toApi,
                        self.toKey,
                        self.toEntId,
                        templateFound,
                        self.missingApps,
                    ),
                )
        else:
            postEventToFrame(
                wxThread.myEVT_LOG, "Template was not found. Check arguements."
            )

    @api_tool_decorator
    def processDeviceGroup(self, templateFound):
        toDeviceGroups = getDeviceGroupsForHost(
            self.getEsperConfig(self.toApi, self.toKey), self.toEntId
        )
        allDeviceGroupId = None
        found, templateFound, allDeviceGroupId = self.checkDeviceGroup(
            templateFound, toDeviceGroups, allDeviceGroupId
        )
        if not found:
            postEventToFrame(wxThread.myEVT_LOG, "Creating new device group...")
            res = createDeviceGroupForHost(
                self.getEsperConfig(self.toApi, self.toKey),
                self.toEntId,
                templateFound["template"]["device_group"]["name"],
            )
            if res:
                toDeviceGroups = getDeviceGroupsForHost(
                    self.getEsperConfig(self.toApi, self.toKey), self.toEntId
                )
                _, templateFound, _ = self.checkDeviceGroup(
                    templateFound, toDeviceGroups, allDeviceGroupId
                )
            else:
                templateFound["template"]["device_group"] = allDeviceGroupId
                postEventToFrame(
                    wxThread.myEVT_LOG,
                    "Failed to recreate Device Group, using All Device group!",
                )
                wx.MessageBox(
                    "Failed to recreate Device Group, using All Device group!",
                    style=wx.OK | wx.ICON_ERROR,
                )
        return templateFound

    @api_tool_decorator
    def processWallpapers(self, templateFound):
        if self.toApi and self.toKey and self.toEntId:
            postEventToFrame(wxThread.myEVT_LOG, "Processing wallpapers in template...")
            if templateFound["template"]["brand"]:
                bgList = []
                for bg in templateFound["template"]["brand"]["wallpapers"]:
                    newBg = self.uploadWallpaper(
                        self.toApi, self.toKey, self.toEntId, bg
                    )
                    if newBg:
                        newBg["enterprise"] = self.toEntId
                        newBg["wallpaper"] = newBg["id"]
                        newBg["orientations"] = bg["orientations"]
                        newBg["screen_types"] = bg["screen_types"]
                        bgList.append(newBg)
                templateFound["template"]["brand"]["wallpapers"] = bgList
        return templateFound

    def getEsperConfig(self, host, apiKey, auth="Bearer"):
        configuration = esperclient.Configuration()
        configuration.host = host.replace("/v0/enterprise/", "")
        configuration.api_key["Authorization"] = apiKey
        configuration.api_key_prefix["Authorization"] = auth
        return configuration

    @api_tool_decorator
    def uploadWallpaper(self, link, key, enterprise_id, bg):
        json_resp = None
        files = None
        try:
            headers = {
                "Authorization": f"Bearer {key}",
            }
            download(bg["url"], "wallpaper.jpeg")
            if os.path.exists("wallpaper.jpeg"):
                payload = {
                    "orientation": bg["orientation"],
                    "enterprise": enterprise_id,
                }
                url = (
                    link
                    + enterprise_id
                    + self.wallpaper_extension
                    + self.limit_extension.format(num=Globals.limit)
                )
                files = {"image_file": open("wallpaper.jpeg", "rb")}
                postEventToFrame(
                    wxThread.myEVT_LOG, "Attempting to upload wallpaper..."
                )
                resp = performPostRequestWithRetry(
                    url, headers=headers, data=payload, files=files
                )
                if resp.ok:
                    postEventToFrame(wxThread.myEVT_LOG, "Wallpaper upload Succeeded!")
                    json_resp = resp.json()
                else:
                    postEventToFrame(wxThread.myEVT_LOG, "Wallpaper upload Failed!")
                    wx.MessageBox(
                        "Wallpaper upload Failed! Source: %s" % bg["url"],
                        style=wx.OK | wx.ICON_ERROR,
                    )
                    resp.raise_for_status()
            else:
                wx.MessageBox(
                    "Failed to download wallpaper for uploading",
                    style=wx.OK | wx.ICON_ERROR,
                )
        except Exception as e:
            raise e
        finally:
            if files:
                files["image_file"].close()
        deleteFile("wallpaper.jpeg")
        if json_resp:
            return json_resp

    def checkDeviceGroup(self, templateFound, toDeviceGroups, allDeviceGroupId):
        found = False
        for group in toDeviceGroups.results:
            if (
                "name" in templateFound["template"]["device_group"]
                and group.name == templateFound["template"]["device_group"]["name"]
            ):
                found = True
                templateFound["template"]["device_group"] = group.id
            if group.name == "All devices":
                allDeviceGroupId = group.id
        return found, templateFound, allDeviceGroupId

    def checkTemplate(self, template, apps, config, entId):
        newTemplate = {}
        startOn = list(
            filter(
                lambda x: x.package_name
                == template["template"]["application"]["startOnBoot"],
                apps,
            )
        )
        bootVal = (
            template["template"]["application"]["startOnBoot"] if startOn else None
        )
        appModeVal = (
            template["template"]["application"]["appMode"] if startOn else "MULTI_APP"
        )
        manageGPlay = True
        launchOnStartVal = None
        preloadVal = []
        whitelistVal = []
        if "managedGooglePlayDisabled" in template["template"]["application"]:
            manageGPlay = template["template"]["application"][
                "managedGooglePlayDisabled"
            ]
        if "launchOnStart" in template["template"]["application"]:
            launchOnStartVal = template["template"]["application"]["launchOnStart"]
        if "preloadApps" in template["template"]["application"]:
            preloadVal = template["template"]["application"]["preloadApps"]
        if "whitelistPreload" in template["template"]["application"]:
            whitelistVal = template["template"]["application"]["whitelistPreload"]
        newTemplate["application"] = {
            "appMode": appModeVal,
            "startOnBoot": bootVal,
            "apps": [],
            "whitelistPreload": whitelistVal,
            "preloadApps": preloadVal,
            "launchOnStart": launchOnStartVal,
            "managedGooglePlayDisabled": manageGPlay,
        }

        missingAppThreads = []
        if template["template"]["application"]["apps"]:
            self.processMissingApplications(
                template, newTemplate, apps, config, entId, missingAppThreads
            )

            joinThreadList(missingAppThreads)

            if missingAppThreads:
                apps = getAllApplicationsForHost(
                    self.getEsperConfig(self.toApi, self.toKey), self.toEntId
                ).results
            newTemplate["application"]["apps"] = []
            self.processApplications(template, newTemplate, apps)
        if (
            not newTemplate["application"]["startOnBoot"]
            and template["template"]["application"]["startOnBoot"]
        ):
            self.missingApps = (
                "Missing Start-Up App (Multi-App Mode enforced); " + self.missingApps
            )
        newTemplate["brand"] = template["template"]["brand"]

        newTemplate["devicePolicy"] = template["template"]["devicePolicy"]
        if "id" in newTemplate["devicePolicy"]:
            del newTemplate["devicePolicy"]["id"]

        tmp_pw_len = template["template"]["securityPolicy"]["devicePasswordPolicy"][
            "minimumPasswordLength"
        ]
        pw_len = tmp_pw_len if tmp_pw_len else 4
        newTemplate["securityPolicy"] = template["template"]["securityPolicy"]
        if not newTemplate["securityPolicy"]["devicePasswordPolicy"][
            "minimumPasswordLength"
        ]:
            newTemplate["securityPolicy"]["devicePasswordPolicy"][
                "minimumPasswordLength"
            ] = pw_len

        newTemplate["settings"] = template["template"]["settings"]
        if "id" in newTemplate["settings"]:
            del newTemplate["settings"]["id"]
        newTemplate["deviceGroup"] = template["template"]["deviceGroup"]
        newTemplate = self.processDictKeyValuePairs(newTemplate, template["template"])
        newTemplate = self.processDictKeyNames(newTemplate)
        template["template"] = newTemplate
        template["is_active"] = False
        template["created_on"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        template["updated_on"] = template["created_on"]
        return template

    def processMissingApplications(
        self, template, newTemplate, apps, config, entId, missingAppThreads
    ):
        for app in template["template"]["application"]["apps"]:
            if ("isGPlay" in app and app["isGPlay"]) or (
                "is_g_play" in app and app["is_g_play"]
            ):
                newTemplate["application"]["apps"].append(app)
            else:
                found = False
                for toApp in apps:
                    if (
                        toApp.application_name == app["applicationName"]
                        or toApp.package_name == app["packageName"]
                    ):
                        found = True
                if not found:
                    upload = wxThread.GUIThread(
                        self.parent,
                        self.uploadMissingApk,
                        (app, template, newTemplate, config, entId),
                    )
                    missingAppThreads.append(upload)
                    upload.start()

    def processApplications(self, template, newTemplate, apps):
        for app in template["template"]["application"]["apps"]:
            if ("isGPlay" in app and app["isGPlay"]) or (
                "is_g_play" in app and app["is_g_play"]
            ):
                newTemplate["application"]["apps"].append(app)
            else:
                for toApp in apps:
                    if (
                        toApp.application_name == app["applicationName"]
                        or toApp.package_name == app["packageName"]
                    ):
                        versionId = list(
                            filter(
                                lambda x: x.version_code == app["versionName"],
                                toApp.versions,
                            )
                        )
                        if not versionId:
                            versionId = toApp.versions[0].id
                        else:
                            versionId = versionId[0].id
                        newTemplate["application"]["apps"].append(
                            {
                                "is_g_play": False,
                                "id": toApp.id,
                                "app_version": versionId,
                                "appVersionId": versionId,
                                "installationRule": app["installationRule"],
                            }
                        )
                        postEventToFrame(
                            wxThread.myEVT_LOG,
                            "Added the '%s' app to the template"
                            % app["applicationName"],
                        )
                        break

    def uploadMissingApk(self, app, template, newTemplate, config, entId):
        try:
            postEventToFrame(
                wxThread.myEVT_LOG,
                "Attempting to download %s to upload to endpoint" % app["packageName"],
            )
            file = "%s.apk" % app["applicationName"]
            deleteFile(file)
            download(app["downloadUrl"], file)
            res = uploadApplicationForHost(config, entId, file)
            if type(res) != InlineResponse201:
                deleteFile(file)
                raise Exception("Upload failed!")
            deleteFile(file)

            if template["template"]["application"]["startOnBoot"] == app["packageName"]:
                newTemplate["application"]["appMode"] = template["template"][
                    "application"
                ]["appMode"]
                newTemplate["application"]["startOnBoot"] = template["template"][
                    "application"
                ]["startOnBoot"]
        except Exception as e:
            print(e)
            ApiToolLog().LogError(e)
            postEventToFrame(
                wxThread.myEVT_LOG,
                "To Enterprise is missing app, %s, not adding to template"
                % app["applicationName"],
            )
            self.missingApps += str(app["applicationName"]) + ", "

    def processDictKeyValuePairs(self, newTemplate, template):
        newTempKeys = newTemplate.keys()
        tempKeys = template.keys()
        for key in tempKeys:
            if key not in newTempKeys and (key != "id" and key != "url"):
                if type(template[key]) is dict:
                    newTemplate[key] = {}
                    newTemplate[key] = self.processDictKeyValuePairs(
                        newTemplate[key], template[key]
                    )
                else:
                    newTemplate[key] = template[key]
        return newTemplate

    def processDictKeyNames(self, dicton):
        if "id" in dicton and "wallpaper" not in dicton:
            del dicton["id"]

        newDict = dicton.copy()
        for key in dicton.keys():
            res = [char for char in key if char.isupper()]
            newKey = key
            for c in res:
                newKey = newKey.replace(c, "_%s" % c.lower())
            if type(dicton[key]) is dict:
                newDict[newKey] = self.processDictKeyNames(dicton[key])
            elif type(dicton[key]) is list:
                newList = []
                for data in dicton[key]:
                    if type(data) is dict:
                        newList.append(self.processDictKeyNames(data))
                    else:
                        newList.append(data)
                newDict[newKey] = newList
            else:
                newDict[newKey] = dicton[key]
            if newKey != key:
                del newDict[key]
        return newDict

    @api_tool_decorator
    def getTemplates(self, link, key, enterprise_id):
        try:
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            }
            if not link.endswith("/v0/enterprise/") or not link.endswith(
                "v0/enterprise/"
            ):
                if not link.endswith("/"):
                    link = link + "/"
                link = link + "v0/enterprise/"
            url = (
                link
                + enterprise_id
                + self.template_extension
                + self.limit_extension.format(num=Globals.limit)
            )
            resp = performGetRequestWithRetry(url, headers=headers)
            json_resp = resp.json()
            return json_resp
        except Exception as e:
            raise e

    @api_tool_decorator
    def getTemplate(self, link, key, enterprise_id, template_id):
        try:
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            }
            if not link.endswith("/v0/enterprise/") or not link.endswith(
                "v0/enterprise/"
            ):
                if not link.endswith("/"):
                    link = link + "/"
                link = link + "v0/enterprise/"
            url = link + enterprise_id + self.template_extension + str(template_id)
            resp = performGetRequestWithRetry(url, headers=headers)
            json_resp = resp.json()
            return json_resp
        except Exception as e:
            raise e

    @api_tool_decorator
    def createTemplate(self, link, key, enterprise_id, template):
        try:
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            }
            url = link + enterprise_id + self.template_extension
            resp = performPostRequestWithRetry(url, headers=headers, json=template)
            json_resp = resp.json()
            if hasattr(resp, "status_code"):
                if resp.status_code > 299:
                    postEventToFrame(
                        wxThread.myEVT_MESSAGE_BOX,
                        (str(json_resp), wx.ICON_ERROR),
                    )
            return json_resp
        except Exception as e:
            raise e

    @api_tool_decorator
    def updateTemplate(self, link, key, enterprise_id, template):
        try:
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            }
            url = link + enterprise_id + self.template_extension + str(template["id"])
            resp = performPatchRequestWithRetry(url, headers=headers, json=template)
            json_resp = resp.json()
            return json_resp
        except Exception as e:
            raise e
