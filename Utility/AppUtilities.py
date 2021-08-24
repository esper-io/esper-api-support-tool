#!/usr/bin/env python

from Utility.EsperAPICalls import getAllApplications
from Utility.CommandUtility import executeCommandOnDevice, executeCommandOnGroup
import wx
from Utility.Resource import displayMessageBox
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
            for app in appList.results:
                if app.package_name == packageName:
                    app.versions.sort(key=lambda s: s.version_code.split("."))
                    appVersion = app.versions[-1]
                    appVersionId = appVersion.id
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
        for app in appList.results:
            if app.package_name == packageName:
                app.versions.sort(key=lambda s: s.version_code.split("."))
                appVersion = app.versions[-1]
                appVersionId = appVersion.id
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
