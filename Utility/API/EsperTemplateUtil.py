#!/usr/bin/env python

from datetime import datetime

import wx
from esperclient import InlineResponse201

import Common.Globals as Globals
import Utility.EventUtility as eventUtil
import Utility.Threading.wxThread as wxThread
from Common.decorator import api_tool_decorator
from Utility.API.AppUtilities import (
    getAllApplicationsForHost,
    getAllAppVersionsForHost,
    uploadApplicationForHost,
)
from Utility.API.GroupUtility import createDeviceGroupForHost, getDeviceGroupsForHost
from Utility.API.WallpaperUtility import uploadWallpaper
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Resource import (
    deleteFile,
    download,
    getEsperConfig,
    joinThreadList,
    postEventToFrame,
)
from Utility.Web.WebRequests import (
    performGetRequestWithRetry,
    performPatchRequestWithRetry,
    performPostRequestWithRetry,
)


class EsperTemplateUtil:
    def __init__(self, toInfo=None, templateName=None, parent=None):
        self.apiLink = "https://{tenant}-api.esper.cloud/api/v0/enterprise/"
        self.template_extension = "/devicetemplate/"
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

    @api_tool_decorator()
    def prepareTemplate(self, dest=None, chosenTemplate=None):
        if self.parent and self.parent.gauge:
            self.parent.statusBar.gauge.Pulse()

        self.toApi = self.apiLink.format(tenant=self.toTenant)

        toTemplates = (
            dest if dest else self.getTemplates(self.toApi, self.toKey, self.toEntId)
        )
        toApps = getAllApplicationsForHost(
            getEsperConfig(self.toApi, self.toKey), self.toEntId
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
                getEsperConfig(self.toApi, self.toKey),
                self.toEntId,
            )

            if templateExist:
                templateFound["id"] = templateExist[0]["id"]
                postEventToFrame(
                    eventUtil.myEVT_CONFIRM_CLONE_UPDATE,
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
                    eventUtil.myEVT_CONFIRM_CLONE,
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
                eventUtil.myEVT_LOG, "Template was not found. Check arguements."
            )

    @api_tool_decorator()
    def processDeviceGroup(self, templateFound):
        toDeviceGroups = getDeviceGroupsForHost(
            getEsperConfig(self.toApi, self.toKey), 
            self.toEntId, 
            tolerance=Globals.THREAD_POOL.getNumberOfActiveThreads()
        )
        allDeviceGroupId = None
        found, templateFound, allDeviceGroupId = self.checkDeviceGroup(
            templateFound, toDeviceGroups, allDeviceGroupId
        )
        if not found:
            postEventToFrame(eventUtil.myEVT_LOG, "Creating new device group...")
            res = createDeviceGroupForHost(
                getEsperConfig(self.toApi, self.toKey),
                self.toEntId,
                templateFound["template"]["device_group"]["name"],
            )
            if res:
                toDeviceGroups = getDeviceGroupsForHost(
                    getEsperConfig(self.toApi, self.toKey), 
                    self.toEntId, 
                    tolerance=Globals.THREAD_POOL.getNumberOfActiveThreads()
                )
                _, templateFound, _ = self.checkDeviceGroup(
                    templateFound, toDeviceGroups, allDeviceGroupId
                )
            else:
                templateFound["template"]["device_group"] = allDeviceGroupId
                postEventToFrame(
                    eventUtil.myEVT_LOG,
                    "Failed to recreate Device Group, using All Device group!",
                )
                wx.MessageBox(
                    "Failed to recreate Device Group, using All Device group!",
                    style=wx.OK | wx.ICON_ERROR,
                )
        return templateFound

    @api_tool_decorator()
    def processWallpapers(self, templateFound):
        if self.toApi and self.toKey and self.toEntId:
            postEventToFrame(
                eventUtil.myEVT_LOG, "Processing wallpapers in template..."
            )
            if templateFound["template"]["brand"]:
                bgList = []
                for bg in templateFound["template"]["brand"]["wallpapers"]:
                    newBg = uploadWallpaper(self.toApi, self.toKey, self.toEntId, bg)
                    if newBg:
                        newBg["enterprise"] = self.toEntId
                        newBg["wallpaper"] = newBg["id"]
                        newBg["orientations"] = bg["orientations"]
                        newBg["screen_types"] = bg["screen_types"]
                        bgList.append(newBg)
                if bgList:
                    templateFound["template"]["brand"]["wallpapers"] = bgList
        return templateFound

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
                    getEsperConfig(self.toApi, self.toKey), self.toEntId
                ).results
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
                pass
            else:
                found = False
                for toApp in apps:
                    if toApp.package_name == app["packageName"]:
                        appVersions = getAllAppVersionsForHost(
                            getEsperConfig(self.toApi, self.toKey),
                            self.toEntId,
                            toApp.id,
                        )
                        if appVersions and hasattr(appVersions, "results"):
                            for version in appVersions.results:
                                if version.version_code == app[
                                    "versionName"
                                ] and version.build_number == str(app["versionCode"]):
                                    found = True
                                    newTemplate = self.addAppVersionToTemplate(
                                        app, newTemplate, toApp, version.id
                                    )
                                    break
                        elif appVersions and type(appVersions) == dict:
                            for version in appVersions["results"]:
                                if version["version_code"] == app[
                                    "versionName"
                                ] and version["build_number"] == str(
                                    app["versionCode"]
                                ):
                                    found = True
                                    newTemplate = self.addAppVersionToTemplate(
                                        app, newTemplate, toApp, version["id"]
                                    )
                                    break
                if not found:
                    upload = wxThread.GUIThread(
                        self.parent,
                        self.uploadMissingApk,
                        (app, template, newTemplate, config, entId),
                    )
                    missingAppThreads.append(upload)
                    upload.startWithRetry()

    def addAppVersionToTemplate(self, app, template, toApp, appVersion):
        if (
            ("isGPlay" not in app)
            or ("isGPlay" in app and not app["isGPlay"])
            or ("is_g_play" not in app)
            or ("is_g_play" in app and not app["is_g_play"])
        ):
            template["application"]["apps"].append(
                {
                    "is_g_play": False,
                    "id": toApp.id,
                    "app_version": appVersion,
                    "appVersionId": appVersion,
                    "package_name": app["packageName"],
                    "installationRule": app["installationRule"],
                }
            )
        return template

    def processApplications(self, template, newTemplate, apps):
        for app in template["template"]["application"]["apps"]:
            if ("isGPlay" in app and app["isGPlay"]) or (
                "is_g_play" in app and app["is_g_play"]
            ):
                matchingApps = getAllApplicationsForHost(
                    getEsperConfig(self.toApi, self.toKey),
                    self.toEntId,
                    package_name=app["packageName"],
                )
                if matchingApps and hasattr(matchingApps, "results"):
                    found = False
                    for match in matchingApps.results:
                        appId = None
                        matchPkgName = None
                        if type(match) is dict:
                            appId = match["id"]
                            matchPkgName = match["package_name"]
                        elif hasattr(match, "id"):
                            appId = match.id
                            matchPkgName = match.package_name
                        if matchPkgName != app["packageName"]:
                            continue
                        versions = getAllAppVersionsForHost(
                            getEsperConfig(self.toApi, self.toKey),
                            self.toEntId,
                            appId,
                        )
                        if versions and hasattr(versions, "results"):
                            for ver in versions.results:
                                if (
                                    type(ver) == dict
                                    and "isGPlay" in ver
                                    and ver["isGPlay"]
                                ) or (
                                    type(ver) == dict
                                    and "is_g_play" in ver
                                    and ver["is_g_play"]
                                ):
                                    newTemplate["application"]["apps"].append(ver)
                                    found = True
                                    break
                        elif versions and type(versions) == dict:
                            for ver in versions["results"]:
                                if (
                                    type(ver) == dict
                                    and "isGPlay" in ver
                                    and ver["isGPlay"]
                                ) or (
                                    type(ver) == dict
                                    and "is_g_play" in ver
                                    and ver["is_g_play"]
                                ):
                                    isPlay = False
                                    if (
                                        type(ver) == dict
                                        and "is_g_play" in ver
                                        and ver["is_g_play"]
                                    ):
                                        isPlay = ver["is_g_play"]
                                    else:
                                        isPlay = ver["isGPlay"]
                                    newTemplate["application"]["apps"].append(
                                        {
                                            "is_g_play": isPlay,
                                            "id": appId,
                                            "package_name": matchPkgName,
                                            "installationRule": app["installationRule"],
                                            "google_product": ver["id"],
                                            "google_product_id": ver["id"],
                                        }
                                    )
                                    found = True
                                    break
                        if found:
                            break
                if not found:
                    postEventToFrame(
                        eventUtil.myEVT_LOG,
                        "ERROR: Failed to find matching Play Store app, %s. Please make sure it is Approved and add to template"
                        % app["packageName"],
                    )
            else:
                for toApp in apps:
                    if toApp.package_name == app["packageName"]:
                        appMatch = list(
                            filter(
                                lambda x: x["package_name"] == app["packageName"]
                                if "package_name" in x
                                else False
                                if type(x) is dict
                                else x.package_name == app["packageName"],
                                newTemplate["application"]["apps"],
                            )
                        )
                        if appMatch:
                            continue

                        versionId = list(
                            filter(
                                lambda x: x.version_code == app["versionName"]
                                and x.build_number == app["versionCode"],
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
                            eventUtil.myEVT_LOG,
                            "Added the '%s' app to the template"
                            % app["applicationName"],
                        )
                        break

    def uploadMissingApk(self, app, template, newTemplate, config, entId):
        try:
            postEventToFrame(
                eventUtil.myEVT_LOG,
                "Attempting to download %s to upload to tenant" % app["packageName"],
            )
            file = "%s.apk" % app["applicationName"].replace("<", "").replace(">", "").replace("\n","")
            deleteFile(file)
            download(app["downloadUrl"], file)
            ApiToolLog().LogApiRequestOccurrence(
                "download", app["downloadUrl"], Globals.PRINT_API_LOGS
            )
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
                eventUtil.myEVT_LOG,
                "To Enterprise is missing app, %s, not adding to template"
                % app["applicationName"],
            )
            self.missingApps += str(app["applicationName"]) + ", "

    def processDictKeyValuePairs(self, newTemplate, template):
        newTempKeys = newTemplate.keys()
        tempKeys = template.keys()
        blacklist = ["id", "url", "customSettingsConfig"]
        for key in tempKeys:
            if key not in newTempKeys and (key != "id" and key != "url"):
                if type(template[key]) is dict and key not in blacklist:
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
            if type(dicton[key]) is dict and key != "customSettingsConfig":
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

    @api_tool_decorator()
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
            if resp:
                json_resp = resp.json()
                return json_resp
        except Exception as e:
            raise e

    @api_tool_decorator()
    def getTemplate(self, link, key, enterprise_id, template_id):
        try:
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            }
            if (
                not link.endswith("/v0/enterprise/")
                or not link.endswith("v0/enterprise/")
                or not link.endswith("v0/enterprise")
                or not link.endswith("/v0/enterprise")
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

    @api_tool_decorator()
    def createTemplate(self, link, key, enterprise_id, template, level=0):
        try:
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            }
            url = link + enterprise_id + self.template_extension
            resp = performPostRequestWithRetry(url, headers=headers, json=template)
            json_resp = resp.json()
            if hasattr(resp, "status_code"):
                if resp.status_code > 299 and level > 0:
                    postEventToFrame(
                        eventUtil.myEVT_MESSAGE_BOX,
                        (str(json_resp), wx.ICON_ERROR),
                    )
            return json_resp
        except Exception as e:
            raise e

    @api_tool_decorator()
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
