#!/usr/bin/env python


import json
import string
import time
from datetime import datetime, timedelta

import esperclient
from esperclient.rest import ApiException

import Common.Globals as Globals
from Common.decorator import api_tool_decorator
from Utility.API.AppUtilities import constructAppPkgVerStr, getAppDictEntry
from Utility.API.CommandUtility import postEsperCommand, waitForCommandToFinish
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Resource import enforceRateLimit, getHeader, logBadResponse
from Utility.Web.WebRequests import (
    handleRequestError,
    performGetRequestWithRetry,
    performPatchRequestWithRetry,
)


@api_tool_decorator()
def getInfo(request_extension, deviceid):
    """Sends Request For Device Info JSON"""
    headers = getHeader()
    url = (
        Globals.BASE_DEVICE_URL.format(
            configuration_host=Globals.configuration.host,
            enterprise_id=Globals.enterprise_id,
            device_id=deviceid,
        )
        + request_extension
    )
    resp = performGetRequestWithRetry(url, headers=headers)
    json_resp = None
    try:
        json_resp = resp.json()
    except:
        pass
    logBadResponse(url, resp, json_resp)

    return json_resp


@api_tool_decorator()
def patchInfo(request_extension, deviceid, data=None, jsonData=None, tags=None):
    """Pushes Data To Device Info JSON"""
    headers = getHeader()
    url = (
        Globals.BASE_DEVICE_URL.format(
            configuration_host=Globals.configuration.host,
            enterprise_id=Globals.enterprise_id,
            device_id=deviceid,
        )
        + request_extension
    )
    requestData = data
    if tags:
        try:
            requestData = json.dumps({"tags": tags})
        except Exception as e:
            print(e)

    resp = performPatchRequestWithRetry(
        url, headers=headers, data=requestData, json=jsonData
    )
    json_resp = resp.json()
    logBadResponse(url, resp, json_resp)
    return json_resp


@api_tool_decorator()
def setdevicename(
    deviceid,
    devicename,
    ignoreQueue,
    timeout=Globals.COMMAND_TIMEOUT,
    maxAttempt=Globals.MAX_RETRY,
):
    """Pushes New Name To Name"""
    args = esperclient.V0CommandArgs(device_alias_name=devicename)
    now = datetime.now()
    start = now + timedelta(minutes=1)
    end = now + timedelta(days=14, minutes=1)
    startDate = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    endDate = end.strftime("%Y-%m-%dT%H:%M:%SZ")
    startTime = end.strftime("%H:%M:%S")
    endTime = end.strftime("%H:%M:%S")
    command = esperclient.V0CommandRequest(
        command_type="DEVICE",
        devices=[deviceid],
        command="UPDATE_DEVICE_CONFIG",
        command_args=args,
        device_type=Globals.CMD_DEVICE_TYPE,
        schedule=esperclient.V0CommandScheduleEnum.WINDOW,
        schedule_args=esperclient.V0CommandScheduleArgs(
            days=[
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ],
            name="%s_%s_%s" % (deviceid, devicename, datetime.now()),
            time_type="device",
            start_datetime=startDate,
            end_datetime=endDate,
            window_end_time=startTime,
            window_start_time=endTime,
        ),
    )
    resp, status = postEsperCommand(command.to_dict(), maxAttempt=maxAttempt)
    return resp.json(), waitForCommandToFinish(
        status["id"], ignoreQueue=ignoreQueue
    )


@api_tool_decorator()
def validateConfiguration(
    host, entId, key, prefix="Bearer", maxAttempt=Globals.MAX_RETRY
):
    configuration = esperclient.Configuration()
    configuration.host = host
    configuration.api_key["Authorization"] = key
    configuration.api_key_prefix["Authorization"] = prefix

    api_instance = esperclient.EnterpriseApi(
        esperclient.ApiClient(configuration)
    )
    enterprise_id = entId

    try:
        api_response = None
        for attempt in range(maxAttempt):
            try:
                enforceRateLimit()
                api_response = api_instance.get_enterprise(enterprise_id)
                ApiToolLog().LogApiRequestOccurrence(
                    "validateConfiguration",
                    api_instance.get_enterprise,
                    Globals.PRINT_API_LOGS,
                )
                ApiToolLog().Log(str(api_response))
                break
            except Exception as e:
                handleRequestError(attempt, e, maxAttempt, raiseError=True)
        if hasattr(api_response, "id"):
            return True
    except ApiException as e:
        print("Exception when calling EnterpriseApi->get_enterprise: %s\n" % e)
        ApiToolLog().LogError(e, postIssue=False)
    return False


def getCompanySettings(maxAttempt=Globals.MAX_RETRY):
    api_instance = esperclient.EnterpriseApi(
        esperclient.ApiClient(Globals.configuration)
    )
    try:
        api_response = None
        for attempt in range(maxAttempt):
            try:
                enforceRateLimit()
                api_response = api_instance.get_enterprise(
                    Globals.enterprise_id
                )
                ApiToolLog().LogApiRequestOccurrence(
                    "validateConfiguration",
                    api_instance.get_enterprise,
                    Globals.PRINT_API_LOGS,
                )
                ApiToolLog().Log(str(api_response))
                break
            except Exception as e:
                handleRequestError(attempt, e, maxAttempt, raiseError=True)
    except ApiException as e:
        print("Exception when calling EnterpriseApi->get_enterprise: %s\n" % e)
        ApiToolLog().LogError(e, postIssue=False)
    return api_response


@api_tool_decorator()
def getIosDeviceApps(
    deviceId, limit=None, offset=0, appType=None, createAppListArg=True
):
    url = "%s/v2/devices/%s/device-apps/" % (
        Globals.configuration.host,
        deviceId,
    )
    extention = "?limit=%s&offset=%s" % (
        limit if limit else Globals.limit,
        offset,
    )
    if appType:
        extention = extention + "&app_type=%s" % appType
    url = url + extention
    resp = performGetRequestWithRetry(url, headers=getHeader())
    json_resp = resp.json()
    applist = createAppList(json_resp["content"]) if createAppListArg else []
    return applist, json_resp


@api_tool_decorator()
def getAndroidDeviceApps(deviceid, createAppListArg=True, useEnterprise=False):
    """Retrieves List Of Installed Apps"""
    extention = (
        Globals.DEVICE_ENTERPRISE_APP_LIST_REQUEST_EXTENSION
        if useEnterprise
        else Globals.DEVICE_APP_LIST_REQUEST_EXTENSION
    )
    hasFormat = [
        tup[1]
        for tup in string.Formatter().parse(extention)
        if tup[1] is not None
    ]
    if hasFormat:
        if "limit" in hasFormat:
            extention = extention.format(limit=Globals.limit)
    json_resp = getInfo(extention, deviceid)
    applist = createAppList(json_resp) if createAppListArg else []
    return applist, json_resp


def createAppList(json_resp, obtainAppDictEntry=True, filterData=False):
    applist = []
    if (
        json_resp
        and "results" in json_resp
        and json_resp["results"]
        and len(json_resp["results"])
    ):
        for app in json_resp["results"]:
            if (
                "install_state" in app
                and "uninstall" in app["install_state"].lower()
            ) or (
                hasattr(app, "install_state")
                and "uninstall" in app.install_state.lower()
            ):
                continue
            if "application" in app:
                pkgName = app["application"]["package_name"]
                if pkgName in Globals.BLACKLIST_PACKAGE_NAME or (
                    filterData and pkgName not in Globals.APP_COL_FILTER
                ):
                    continue
                if Globals.VERSON_NAME_INSTEAD_OF_CODE:
                    version = (
                        app["application"]["version"]["version_name"][
                            1 : len(
                                app["application"]["version"]["version_name"]
                            )
                        ]
                        if (
                            app["application"]["version"]["version_name"]
                            and app["application"]["version"][
                                "version_name"
                            ].startswith("v")
                        )
                        else app["application"]["version"]["version_name"]
                    )
                else:
                    version = (
                        app["application"]["version"]["version_code"][
                            1 : len(
                                app["application"]["version"]["version_code"]
                            )
                        ]
                        if (
                            app["application"]["version"]["version_code"]
                            and app["application"]["version"][
                                "version_code"
                            ].startswith("v")
                        )
                        else app["application"]["version"]["version_code"]
                    )

                appName = app["application"]["application_name"]
                applist.append(constructAppPkgVerStr(appName, pkgName, version))
            elif app.get("package_name") is not None and not isAppleApp(app):
                if app["package_name"] in Globals.BLACKLIST_PACKAGE_NAME or (
                    filterData
                    and app["package_name"] not in Globals.APP_COL_FILTER
                ):
                    continue
                version = None
                if Globals.VERSON_NAME_INSTEAD_OF_CODE:
                    version = (
                        app["version_name"][1 : len(app["version_name"])]
                        if app["version_name"]
                        and app["version_name"].startswith("v")
                        else app["version_name"]
                    )
                else:
                    version = (
                        app["version_code"][1 : len(app["version_code"])]
                        if app["version_code"]
                        and app["version_code"].startswith("v")
                        else app["version_code"]
                    )
                applist.append(
                    constructAppPkgVerStr(
                        app["app_name"], app["package_name"], version
                    )
                )
            elif app.get("package_name") is not None and isAppleApp(app):
                if app["package_name"] in Globals.BLACKLIST_PACKAGE_NAME or (
                    filterData
                    and app["package_name"] not in Globals.APP_COL_FILTER
                ):
                    continue
                applist.append(
                    constructAppPkgVerStr(
                        app["app_name"],
                        app["package_name"],
                        app["version_name"],
                    )
                )
            elif app.get("bundle_id") is not None and isAppleApp(app):
                if app["bundle_id"] in Globals.BLACKLIST_PACKAGE_NAME or (
                    filterData
                    and app["bundle_id"] not in Globals.APP_COL_FILTER
                ):
                    continue
                applist.append(
                    constructAppPkgVerStr(
                        app["app_name"],
                        app["bundle_id"],
                        app["apple_app_version"],
                    )
                )
    return applist


def isAppleApp(app):
    return (
        app.get("platform", "").lower() == "apple"
        or "device_families" in app
        or app.get("app_type", "").lower() in Globals.APPLE_APP_TYPES
    )


def searchForMatchingDevices(entry, maxAttempt=Globals.MAX_RETRY):
    api_instance = esperclient.DeviceApi(
        esperclient.ApiClient(Globals.configuration)
    )
    api_response = None
    for attempt in range(maxAttempt):
        try:
            enforceRateLimit()
            if type(entry) is dict and "Esper Name" in entry.keys():
                identifier = entry["Esper Name"]
                api_response = api_instance.get_all_devices(
                    Globals.enterprise_id,
                    name=identifier,
                    limit=Globals.limit,
                    offset=Globals.offset,
                )
            elif type(entry) is dict and "Serial Number" in entry.keys():
                identifier = entry["Serial Number"]
                api_response = api_instance.get_all_devices(
                    Globals.enterprise_id,
                    serial=identifier,
                    limit=Globals.limit,
                    offset=Globals.offset,
                )
            elif type(entry) is dict and "Custom Serial Number" in entry.keys():
                identifier = entry["Custom Serial Number"]
                api_response = api_instance.get_all_devices(
                    Globals.enterprise_id,
                    search=identifier,
                    limit=Globals.limit,
                    offset=Globals.offset,
                )
            elif type(entry) is dict and "IMEI 1" in entry.keys():
                identifier = entry["IMEI 1"]
                api_response = api_instance.get_all_devices(
                    Globals.enterprise_id,
                    imei=identifier,
                    limit=Globals.limit,
                    offset=Globals.offset,
                )
            elif type(entry) is dict and "IMEI 2" in entry.keys():
                identifier = entry["IMEI 2"]
                api_response = api_instance.get_all_devices(
                    Globals.enterprise_id,
                    imei=identifier,
                    limit=Globals.limit,
                    offset=Globals.offset,
                )
            else:
                api_response = api_instance.get_all_devices(
                    Globals.enterprise_id,
                    search=entry,
                    limit=Globals.limit,
                    offset=Globals.offset,
                )
            ApiToolLog().LogApiRequestOccurrence(
                "getAllDevices",
                api_instance.get_all_devices,
                Globals.PRINT_API_LOGS,
            )
            break
        except Exception as e:
            handleRequestError(attempt, e, maxAttempt, raiseError=True)
    return api_response
