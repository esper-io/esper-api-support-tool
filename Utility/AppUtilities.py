#!/usr/bin/env python

import esperclient
import time
import wx

import Common.Globals as Globals
import Utility.EventUtility as eventUtil

from Common.decorator import api_tool_decorator

from esperclient.rest import ApiException
from Utility import EventUtility

from Utility.ApiToolLogging import ApiToolLog
from Utility.EsperAPICalls import getInfo
from Utility.CommandUtility import (
    executeCommandOnDevice,
    executeCommandOnGroup,
    postEsperCommand,
)
from Utility.Resource import (
    displayMessageBox,
    getHeader,
    logBadResponse,
    performGetRequestWithRetry,
    postEventToFrame,
)


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
    url = (
        "https://%s-api.esper.cloud/api/v1/enterprise/%s/application/?limit=%s&without_download_url=true&format=json&is_hidden=false"
        % (tenant, Globals.enterprise_id, Globals.limit)
    )
    appsResp = performGetRequestWithRetry(url, headers=getHeader())
    appsRespJson = None
    if appsResp:
        appsRespJson = appsResp.json()

        if appsRespJson and "next" in appsRespJson and appsRespJson["next"]:
            appsRespJson = getAllInstallableAppsOffsets(
                appsRespJson, appsRespJson["next"]
            )

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


@api_tool_decorator()
def getdeviceapps(deviceid, createAppList=True, useEnterprise=False):
    """Retrieves List Of Installed Apps"""
    applist = []
    extention = (
        Globals.DEVICE_ENTERPRISE_APP_LIST_REQUEST_EXTENSION
        if useEnterprise
        else Globals.DEVICE_APP_LIST_REQUEST_EXTENSION
    )
    json_resp = getInfo(extention, deviceid)
    if (
        json_resp
        and "results" in json_resp
        and len(json_resp["results"])
        and createAppList
    ):
        for app in json_resp["results"]:
            if (
                "install_state" in app and "uninstall" in app["install_state"].lower()
            ) or (
                hasattr(app, "install_state")
                and "uninstall" in app.install_state.lower()
            ):
                continue
            entry = None
            if "application" in app:
                if app["application"]["package_name"] in Globals.BLACKLIST_PACKAGE_NAME:
                    continue
                entry = getAppDictEntry(app, False)
                version = (
                    app["application"]["version"]["version_code"][
                        1 : len(app["application"]["version"]["version_code"])
                    ]
                    if (
                        app["application"]["version"]["version_code"]
                        and app["application"]["version"]["version_code"].startswith(
                            "v"
                        )
                    )
                    else app["application"]["version"]["version_code"]
                )

                appName = app["application"]["application_name"]
                pkgName = app["application"]["package_name"]
                applist.append(constructAppPkgVerStr(appName, pkgName, version))
            else:
                if app["package_name"] in Globals.BLACKLIST_PACKAGE_NAME:
                    continue
                entry = getAppDictEntry(app, False)
                version = (
                    app["version_code"][1 : len(app["version_code"])]
                    if app["version_code"].startswith("v")
                    else app["version_code"]
                )
                applist.append(
                    constructAppPkgVerStr(app["app_name"], app["package_name"], version)
                )
            if entry not in Globals.frame.sidePanel.selectedDeviceApps and (
                "isValid" in entry and entry["isValid"]
            ):
                Globals.frame.sidePanel.selectedDeviceApps.append(entry)
    return applist, json_resp


def constructAppPkgVerStr(appName, pkgName, version):
    appPkgVerStr = ""
    if appName:
        appPkgVerStr += appName
    else:
        appPkgVerStr += "Invalid App Name - "
    if Globals.SHOW_PKG_NAME:
        if pkgName:
            appPkgVerStr += " (%s) v" % pkgName
        else:
            appPkgVerStr += " (Invalid Package Name) v"
    else:
        appPkgVerStr += " v"
    if version:
        appPkgVerStr += version
    else:
        appPkgVerStr += "Unknown Version"
    return appPkgVerStr


@api_tool_decorator()
def uploadApplicationForHost(config, enterprise_id, file, maxAttempt=Globals.MAX_RETRY):
    try:
        api_instance = esperclient.ApplicationApi(esperclient.ApiClient(config))
        api_response = None
        for attempt in range(maxAttempt):
            try:
                api_response = api_instance.upload(enterprise_id, file)
                ApiToolLog().LogApiRequestOccurrence(
                    "uploadApplicationForHost",
                    api_instance.upload,
                    Globals.PRINT_API_LOGS,
                )
                break
            except Exception as e:
                if attempt == maxAttempt - 1:
                    ApiToolLog().LogError(e)
                    raise e
                time.sleep(Globals.RETRY_SLEEP)
        return api_response
    except ApiException as e:
        raise Exception("Exception when calling ApplicationApi->upload: %s\n" % e)


@api_tool_decorator()
def uploadApplication(file, maxAttempt=Globals.MAX_RETRY):
    try:
        api_instance = esperclient.ApplicationApi(
            esperclient.ApiClient(Globals.configuration)
        )
        enterprise_id = Globals.enterprise_id
        api_response = None
        for attempt in range(maxAttempt):
            try:
                api_response = api_instance.upload(enterprise_id, file)
                break
            except Exception as e:
                if (
                    attempt == maxAttempt - 1
                    or "App Upload failed as this version already exists" in str(e)
                ):
                    ApiToolLog().LogError(e)
                    raise e
                time.sleep(Globals.RETRY_SLEEP)
        return api_response
    except ApiException as e:
        raise Exception("Exception when calling ApplicationApi->upload: %s\n" % e)


@api_tool_decorator()
def getAllApplications(maxAttempt=Globals.MAX_RETRY):
    """ Make a API call to get all Applications belonging to the Enterprise """
    if Globals.USE_ENTERPRISE_APP:
        try:
            api_instance = esperclient.ApplicationApi(
                esperclient.ApiClient(Globals.configuration)
            )
            api_response = None
            for attempt in range(maxAttempt):
                try:
                    api_response = api_instance.get_all_applications(
                        Globals.enterprise_id,
                        limit=Globals.limit,
                        offset=Globals.offset,
                        is_hidden=False,
                    )
                    ApiToolLog().LogApiRequestOccurrence(
                        "getAllApplications",
                        api_instance.get_all_applications,
                        Globals.PRINT_API_LOGS,
                    )
                    break
                except Exception as e:
                    if attempt == maxAttempt - 1:
                        ApiToolLog().LogError(e)
                        raise e
                    time.sleep(Globals.RETRY_SLEEP)
            postEventToFrame(EventUtility.myEVT_LOG, "---> App API Request Finished")
            return api_response
        except ApiException as e:
            raise Exception(
                "Exception when calling ApplicationApi->get_all_applications: %s\n" % e
            )
    else:
        return getAppsEnterpriseAndPlayStore()


@api_tool_decorator()
def getAllApplicationsForHost(
    config,
    enterprise_id,
    application_name="",
    package_name="",
    maxAttempt=Globals.MAX_RETRY,
):
    """ Make a API call to get all Applications belonging to the Enterprise """
    try:
        api_instance = esperclient.ApplicationApi(esperclient.ApiClient(config))
        api_response = None
        for attempt in range(maxAttempt):
            try:
                api_response = api_instance.get_all_applications(
                    enterprise_id,
                    limit=Globals.limit,
                    application_name=application_name,
                    package_name=package_name,
                    offset=0,
                    is_hidden=False,
                )
                ApiToolLog().LogApiRequestOccurrence(
                    "getAllApplicationsForHost",
                    api_instance.get_all_applications,
                    Globals.PRINT_API_LOGS,
                )
                break
            except Exception as e:
                if attempt == maxAttempt - 1:
                    ApiToolLog().LogError(e)
                    raise e
                time.sleep(Globals.RETRY_SLEEP)
        return api_response
    except Exception as e:
        raise Exception(
            "Exception when calling ApplicationApi->get_all_applications: %s\n" % e
        )


@api_tool_decorator()
def getAllAppVersionsForHost(
    config,
    enterprise_id,
    app_id,
    maxAttempt=Globals.MAX_RETRY,
):
    """ Make a API call to get all Applications belonging to the Enterprise """
    try:
        api_instance = esperclient.ApplicationApi(esperclient.ApiClient(config))
        api_response = None
        for attempt in range(maxAttempt):
            try:
                api_response = api_instance.get_app_versions(
                    app_id,
                    enterprise_id,
                    limit=Globals.limit,
                    offset=0,
                    # is_hidden=False,
                )
                ApiToolLog().LogApiRequestOccurrence(
                    "getAllAppVersionsForHost",
                    api_instance.get_app_versions,
                    Globals.PRINT_API_LOGS,
                )
                break
            except Exception as e:
                if attempt == maxAttempt - 1:
                    ApiToolLog().LogError(e)
                    raise e
                time.sleep(Globals.RETRY_SLEEP)
        return api_response
    except Exception as e:
        raise Exception(
            "Exception when calling ApplicationApi->get_app_versions: %s\n" % e
        )


@api_tool_decorator()
def clearAppData(frame, device):
    json_resp = None
    try:
        appToUse = frame.sidePanel.selectedAppEntry["pkgName"]
        _, apps = getdeviceapps(
            device.id, createAppList=False, useEnterprise=Globals.USE_ENTERPRISE_APP
        )
        cmdArgs = {}
        for app in apps["results"]:
            if app["package_name"] == appToUse:
                cmdArgs["package_name"] = app["package_name"]
                cmdArgs["application_name"] = app["app_name"]
                cmdArgs["version_code"] = app["version_code"]
                cmdArgs["version_name"] = app["version_name"]
                if app["app_type"] == "GOOGLE":
                    cmdArgs["is_g_play"] = True
                else:
                    cmdArgs["is_g_play"] = False
                break

        if cmdArgs:
            reqData = {
                "command_type": "DEVICE",
                "command_args": cmdArgs,
                "devices": [device.id],
                "groups": [],
                "device_type": Globals.CMD_DEVICE_TYPE,
                "command": "CLEAR_APP_DATA",
            }
            resp, json_resp = postEsperCommand(reqData)
            logBadResponse(resp.request.url, resp, json_resp)
            if resp.status_code > 300:
                postEventToFrame(eventUtil.myEVT_ON_FAILED, device)
            if resp.status_code < 300:
                frame.Logging(
                    "---> Clear %s App Data Command has been sent to %s"
                    % (cmdArgs["application_name"], device.device_name)
                )
        else:
            frame.Logging(
                "ERROR: Failed to send Clear %s App Data Command to %s"
                % (
                    frame.sidePanel.selectedAppEntry["name"],
                    device.device_name,
                )
            )
    except Exception as e:
        ApiToolLog().LogError(e)
        frame.Logging(
            "ERROR: Failed to send Clear App Data Command to %s" % (device.device_name)
        )
        postEventToFrame(eventUtil.myEVT_ON_FAILED, device)
    return json_resp


def getApplication(application_id):
    api_instance = esperclient.ApplicationApi(
        esperclient.ApiClient(Globals.configuration)
    )
    enterprise_id = Globals.enterprise_id
    try:
        # Get application information
        api_response = api_instance.get_application(application_id, enterprise_id)
        ApiToolLog().LogApiRequestOccurrence(
            "getApplication", api_instance.get_application, Globals.PRINT_API_LOGS
        )
        return api_response
    except ApiException as e:
        print("Exception when calling ApplicationApi->get_application: %s\n" % e)


def getAppVersions(
    application_id,
    version_code="",
    build_number="",
    getPlayStore=False,
    maxAttempt=Globals.MAX_RETRY,
):
    if Globals.USE_ENTERPRISE_APP and not getPlayStore:
        api_instance = esperclient.ApplicationApi(
            esperclient.ApiClient(Globals.configuration)
        )
        enterprise_id = Globals.enterprise_id
        for attempt in range(maxAttempt):
            try:
                api_response = api_instance.get_app_versions(
                    application_id,
                    enterprise_id,
                    version_code=version_code,
                    build_number=build_number,
                    limit=Globals.limit,
                    offset=Globals.offset,
                )
                ApiToolLog().LogApiRequestOccurrence(
                    "getAppVersions",
                    api_instance.get_app_versions,
                    Globals.PRINT_API_LOGS,
                )
                return api_response
            except Exception as e:
                if attempt == maxAttempt - 1:
                    ApiToolLog().LogError(e)
                    print(
                        "Exception when calling ApplicationApi->get_app_versions: %s\n"
                        % e
                    )
                    raise e
                time.sleep(1)
    else:
        return getAppVersionsEnterpriseAndPlayStore(application_id)


def getAppVersionsEnterpriseAndPlayStore(application_id):
    url = "https://{tenant}-api.esper.cloud/api/v1/enterprise/{ent_id}/application/{app_id}/version/".format(
        tenant=Globals.configuration.host.split("-api")[0].replace("https://", ""),
        ent_id=Globals.enterprise_id,
        app_id=application_id,
    )
    resp = performGetRequestWithRetry(url, headers=getHeader())
    jsonResp = resp.json()
    logBadResponse(url, resp, jsonResp, displayMsgBox=True)
    return jsonResp


def getAppsEnterpriseAndPlayStore(package_name=""):
    url = ""
    jsonResp = {}
    if package_name:
        url = "https://{tenant}-api.esper.cloud/api/v1/enterprise/{ent_id}/application/?package_name={pkg}".format(
            tenant=Globals.configuration.host.split("-api")[0].replace("https://", ""),
            ent_id=Globals.enterprise_id,
            pkg=package_name,
        )
        resp = performGetRequestWithRetry(url, headers=getHeader())
        jsonResp = resp.json()
        logBadResponse(url, resp, jsonResp, displayMsgBox=True)
    else:
        jsonResp = getAllInstallableApps()
    return jsonResp


def getInstallDevices(version_id, application_id, maxAttempt=Globals.MAX_RETRY):
    api_instance = esperclient.ApplicationApi(
        esperclient.ApiClient(Globals.configuration)
    )
    enterprise_id = Globals.enterprise_id
    for attempt in range(maxAttempt):
        try:
            # List install devices
            api_response = api_instance.get_install_devices(
                version_id,
                application_id,
                enterprise_id,
                limit=Globals.limit,
                offset=Globals.offset,
            )
            ApiToolLog().LogApiRequestOccurrence(
                "getInstallDevices",
                api_instance.get_install_devices,
                Globals.PRINT_API_LOGS,
            )
            return api_response
        except ApiException as e:
            if attempt == maxAttempt - 1:
                ApiToolLog().LogError(e)
                print(
                    "Exception when calling ApplicationApi->get_install_devices: %s\n"
                    % e
                )
                raise e
            time.sleep(1)


def getAppDictEntry(app, update=True):
    entry = None
    appName = None
    appPkgName = None

    if type(app) == dict and "application" in app:
        appName = app["application"]["application_name"]
        appPkgName = appName + (" (%s)" % app["application"]["package_name"])
        entry = {
            "app_name": app["application"]["application_name"],
            appName: app["application"]["package_name"],
            appPkgName: app["application"]["package_name"],
            "appPkgName": appPkgName,
            "packageName": app["application"]["package_name"],
            "id": app["id"],
            "app_state": None,
        }
    elif hasattr(app, "application_name"):
        appName = app.application_name
        appPkgName = appName + (" (%s)" % app.package_name)
        entry = {
            "app_name": app.application_name,
            appName: app.package_name,
            appPkgName: app.package_name,
            "appPkgName": appPkgName,
            "packageName": app.package_name,
            "versions": app.versions,
            "id": app.id,
        }
    elif type(app) == dict and "application_name" in app:
        appName = app["application_name"]
        appPkgName = appName + (" (%s)" % app["package_name"])
        entry = {
            "app_name": app["application_name"],
            appName: app["package_name"],
            appPkgName: app["package_name"],
            "appPkgName": appPkgName,
            "packageName": app["package_name"],
            "id": app["id"],
        }
    elif type(app) == dict and "app_name" in app:
        appName = app["app_name"]
        appPkgName = appName + (" (%s)" % app["package_name"])
        entry = {
            "app_name": app["app_name"],
            appName: app["package_name"],
            appPkgName: app["package_name"],
            "appPkgName": appPkgName,
            "packageName": app["package_name"],
            "app_state": app["state"],
            "id": app["id"],
        }

    validApp = None
    if type(app) == esperclient.models.application.Application:
        entry["isValid"] = True
    else:
        if (
            type(app) == dict
            and "id" in app
            and "install_state" not in app
            and "device" not in app
        ):
            entry["isValid"] = True
            # if (
            #     "latest_version" in app
            #     and app["latest_version"]
            #     and "icon_url" in app["latest_version"]
            #     and
            #     ((
            #         app["latest_version"]["icon_url"]
            #         and (
            #             "amazonaws" in app["latest_version"]["icon_url"]
            #             or "googleusercontent" in app["latest_version"]["icon_url"]
            #         )
            #     ) or "hash_string" in app["latest_version"])
            # ) or (
            #     "versions" in app
            #     and app["versions"]
            #     and "icon_url" in app["versions"]
            #     and app["versions"]["icon_url"]
            #     and "amazonaws" in app["versions"]["icon_url"]
            # ):
            #     entry["isValid"] = True
            # else:
            #     validApp = getApplication(entry["id"])
            #     if hasattr(validApp, "results"):
            #         validApp = validApp.results[0] if validApp.results else validApp

    if (
        hasattr(validApp, "id")
        or (type(validApp) == dict and "id" in validApp)
        or (type(app) == dict and "device" in app)
    ):
        entry["id"] = (
            validApp.id
            if hasattr(validApp, "id")
            else (
                validApp["id"]
                if (type(validApp) == dict and "id" in validApp)
                else entry["id"]
            )
        )
        entry["isValid"] = True

    if (
        Globals.frame
        and hasattr(Globals.frame, "sidePanel")
        and "isValid" in entry
        and update
    ):
        selectedDeviceAppsMatch = list(
            filter(
                lambda entry: entry["app_name"] == appName
                and entry["appPkgName"] == appPkgName,
                Globals.frame.sidePanel.selectedDeviceApps,
            )
        )
        enterpriseAppsMatch = list(
            filter(
                lambda entry: entry["app_name"] == appName
                and entry["appPkgName"] == appPkgName,
                Globals.frame.sidePanel.enterpriseApps,
            )
        )
        if selectedDeviceAppsMatch and "isValid" in entry:
            indx = Globals.frame.sidePanel.selectedDeviceApps.index(
                selectedDeviceAppsMatch[0]
            )
            oldEntry = Globals.frame.sidePanel.selectedDeviceApps[indx]
            if update:
                oldEntry.update(entry)
                Globals.frame.sidePanel.selectedDeviceApps[indx] = entry = oldEntry
        if enterpriseAppsMatch and "isValid" in entry:
            indx = Globals.frame.sidePanel.enterpriseApps.index(enterpriseAppsMatch[0])
            oldEntry = Globals.frame.sidePanel.enterpriseApps[indx]
            if update:
                oldEntry.update(entry)
                Globals.frame.sidePanel.enterpriseApps[indx] = entry = oldEntry

    return entry
