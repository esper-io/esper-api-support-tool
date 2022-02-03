#!/usr/bin/env python

from Common.decorator import api_tool_decorator
from Utility.EsperAPICalls import getAllApplications
from Utility.CommandUtility import executeCommandOnDevice, executeCommandOnGroup
import wx
from Utility.Resource import displayMessageBox, getHeader, performGetRequestWithRetry
import Common.Globals as Globals


def uninstallAppOnDevice(packageName, device=None):
    return executeCommandOnDevice(
        Globals.frame,
        {"package_name": packageName},
        command_type="UNINSTALL",
        deviceIds=device,
    )


def uninstallAppOnGroup(packageName, groups=None):
    return executeCommandOnGroup(
        Globals.frame,
        {"package_name": packageName},
        command_type="UNINSTALL",
        groupIds=groups,
    )


def installAppOnDevices(packageName, version=None, devices=None):
    appVersion = version
    appVersionId = version
    if not appVersion:
        appList = getAllApplications()
        if appList:
            if hasattr(appList, "results"):
                for app in appList.results:
                    if app.package_name == packageName:
                        app.versions.sort(key=lambda s: s.version_code.split("."))
                        appVersion = app.versions[-1]
                        appVersionId = appVersion.id
                        break
            elif type(appList) == dict and "results" in appList:
                for app in appList["results"]:
                    if app["package_name"] == packageName:
                        app["versions"].sort(key=lambda s: s["version_code"].split("."))
                        appVersion = app["versions"][-1]
                        appVersionId = appVersion["id"]
                        break
    if appVersion:
        return executeCommandOnDevice(
            Globals.frame,
            {
                "app_version": appVersionId,
                "package_name": packageName,
            },
            command_type="INSTALL",
            deviceIds=devices,
        )
    else:
        displayMessageBox(
            (
                "Failed to find application! Please upload application (%s) to the endpoint."
                % packageName,
                wx.ICON_ERROR,
            )
        )
        return {
            "Error": "Failed to find app version for %s. Please ensure app package name is correct!"
            % packageName,
        }


def installAppOnGroups(packageName, version=None, groups=None):
    appVersion = version
    appVersionId = version
    if not appVersion:
        appList = getAllApplications()
        if hasattr(appList, "results"):
            for app in appList.results:
                if app.package_name == packageName:
                    app.versions.sort(key=lambda s: s.version_code.split("."))
                    appVersion = app.versions[-1]
                    appVersionId = appVersion.id
                    break
        elif type(appList) == dict and "results" in appList:
            for app in appList["results"]:
                if app["package_name"] == packageName:
                    app["versions"].sort(key=lambda s: s["version_code"].split("."))
                    appVersion = app["versions"][-1]
                    appVersionId = appVersion["id"]
                    break
    if appVersion:
        return executeCommandOnGroup(
            Globals.frame,
            {
                "app_version": appVersionId,
                "package_name": packageName,
            },
            command_type="INSTALL",
            groupIds=groups,
        )
    else:
        displayMessageBox(
            (
                "Failed to find application! Please upload application (%s) to the endpoint."
                % packageName,
                wx.ICON_ERROR,
            )
        )

@api_tool_decorator()
def getAllInstallableApps():
    tenant = Globals.configuration.host.replace("https://", "").replace(
        "-api.esper.cloud/api", ""
    )
    url = "https://%s-api.esper.cloud/api/v1/enterprise/%s/application/?limit=%s&without_download_url=true&format=json&is_hidden=false" % (
        tenant,
        Globals.enterprise_id,
        Globals.limit
    )
    appsResp = performGetRequestWithRetry(url, headers=getHeader())
    appsRespJson = None
    if appsResp:
        appsRespJson = appsResp.json()

        if appsRespJson and "next" in appsRespJson:
            appsRespJson = getAllInstallableAppsOffsets(appsRespJson, appsRespJson["next"])

    return appsRespJson

def getAllInstallableAppsOffsets(respJson, url):
    appsResp = performGetRequestWithRetry(url, headers=getHeader())
    appsRespJson = None
    if appsResp:
        appsRespJson = appsResp.json()

        if appsRespJson and "results" in appsRespJson:
            respJson["results"] = respJson["results"] + appsRespJson["results"]

        if appsRespJson and "next" in appsRespJson:
            respJson = getAllInstallableAppsOffsets(respJson, appsRespJson["next"])

    return respJson
