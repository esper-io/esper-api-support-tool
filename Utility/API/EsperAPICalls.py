#!/usr/bin/env python


import json
import string
from datetime import datetime, timedelta

import esperclient
from esperclient.rest import ApiException

import Common.Globals as Globals
from Common.decorator import api_tool_decorator
from Utility.API.AppUtilities import constructAppPkgVerStr
from Utility.API.CommandUtility import postEsperCommand, waitForCommandToFinish
from Utility.API.DeviceUtility import get_all_ios_devices_helper, getInfo
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Resource import enforceRateLimit, getHeader
from Utility.Web.WebRequests import (handleRequestError,
                                     performGetRequestWithRetry)


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
    return resp.json(), waitForCommandToFinish(status["id"], ignoreQueue=ignoreQueue)


@api_tool_decorator()
def validateConfiguration(host, entId, key, prefix="Bearer", maxAttempt=Globals.MAX_RETRY):
    configuration = esperclient.Configuration()
    configuration.host = host
    configuration.api_key["Authorization"] = key
    configuration.api_key_prefix["Authorization"] = prefix

    api_instance = esperclient.EnterpriseApi(esperclient.ApiClient(configuration))
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
        ApiToolLog().LogError(e, postStatus=False)
    return False


def getCompanySettings(maxAttempt=Globals.MAX_RETRY):
    api_instance = esperclient.EnterpriseApi(esperclient.ApiClient(Globals.configuration))
    try:
        api_response = None
        for attempt in range(maxAttempt):
            try:
                enforceRateLimit()
                api_response = api_instance.get_enterprise(Globals.enterprise_id)
                ApiToolLog().LogApiRequestOccurrence(
                    "validateConfiguration",
                    api_instance.get_enterprise,
                    Globals.PRINT_API_LOGS,
                )
                break
            except Exception as e:
                handleRequestError(attempt, e, maxAttempt, raiseError=True)
    except ApiException as e:
        print("Exception when calling EnterpriseApi->get_enterprise: %s\n" % e)
        ApiToolLog().LogError(e, postStatus=False)
    return api_response


@api_tool_decorator()
def getIosDeviceApps(deviceId, limit=None, offset=0, appType=None, createAppListArg=True):
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
        Globals.DEVICE_ENTERPRISE_APP_LIST_REQUEST_EXTENSION if useEnterprise else Globals.DEVICE_APP_LIST_REQUEST_EXTENSION
    )
    hasFormat = [tup[1] for tup in string.Formatter().parse(extention) if tup[1] is not None]
    if hasFormat:
        if "limit" in hasFormat:
            extention = extention.format(limit=Globals.limit)
    json_resp = getInfo(extention, deviceid)
    applist = createAppList(json_resp) if createAppListArg else []
    return applist, json_resp


def createAppList(json_resp, filterData=False):
    applist = []
    if json_resp and "results" in json_resp and json_resp["results"] and len(json_resp["results"]):
        for app in json_resp["results"]:
            if ("install_state" in app and "uninstall" in app["install_state"].lower()) or (
                hasattr(app, "install_state") and "uninstall" in app.install_state.lower()
            ):
                continue
            if "application" in app:
                # Safe nested dictionary access
                try:
                    pkgName = app["application"].get("package_name", "")
                    if pkgName in Globals.BLACKLIST_PACKAGE_NAME or (filterData and pkgName not in Globals.APP_COL_FILTER):
                        continue
                    
                    version_info = app["application"].get("version", {})
                    if Globals.VERSON_NAME_INSTEAD_OF_CODE:
                        version_name = version_info.get("version_name", "")
                        if version_name and version_name.startswith("v") and len(version_name) > 1:
                            version = version_name[1:]
                        else:
                            version = version_name
                    else:
                        version_code = version_info.get("version_code", "")
                        if version_code and version_code.startswith("v") and len(version_code) > 1:
                            version = version_code[1:]
                        else:
                            version = version_code

                    appName = app["application"].get("application_name", "Unknown")
                    applist.append(constructAppPkgVerStr(appName, pkgName, version))
                except (KeyError, TypeError, AttributeError):
                    # Skip malformed app entries
                    continue
            elif app.get("package_name") is not None and not isAppleApp(app):
                try:
                    pkgName = app.get("package_name", "")
                    if pkgName in Globals.BLACKLIST_PACKAGE_NAME or (
                        filterData and pkgName not in Globals.APP_COL_FILTER
                    ):
                        continue
                    version = None
                    if Globals.VERSON_NAME_INSTEAD_OF_CODE:
                        version_name = app.get("version_name", "")
                        if version_name and version_name.startswith("v") and len(version_name) > 1:
                            version = version_name[1:]
                        else:
                            version = version_name
                    else:
                        version_code = app.get("version_code", "")
                        if version_code and version_code.startswith("v") and len(version_code) > 1:
                            version = version_code[1:]
                        else:
                            version = version_code
                    applist.append(constructAppPkgVerStr(app.get("app_name", "Unknown"), pkgName, version))
                except (KeyError, TypeError, AttributeError):
                    # Skip malformed app entries
                    continue
            elif app.get("package_name") is not None and isAppleApp(app):
                try:
                    pkgName = app.get("package_name", "")
                    if pkgName in Globals.BLACKLIST_PACKAGE_NAME or (
                        filterData and pkgName not in Globals.APP_COL_FILTER
                    ):
                        continue
                    applist.append(
                        constructAppPkgVerStr(
                            app.get("app_name", "Unknown"),
                            pkgName,
                            app.get("version_name", ""),
                        )
                    )
                except (KeyError, TypeError, AttributeError):
                    # Skip malformed app entries
                    continue
            elif app.get("bundle_id") is not None and isAppleApp(app):
                try:
                    bundleId = app.get("bundle_id", "")
                    if bundleId in Globals.BLACKLIST_PACKAGE_NAME or (
                        filterData and bundleId not in Globals.APP_COL_FILTER
                    ):
                        continue
                    applist.append(
                        constructAppPkgVerStr(
                            app.get("app_name", "Unknown"),
                            bundleId,
                            app.get("apple_app_version", ""),
                        )
                    )
                except (KeyError, TypeError, AttributeError):
                    # Skip malformed app entries
                    continue
    return applist


def isAppleApp(app):
    return (
        app.get("platform", "").lower() == "apple"
        or "device_families" in app
        or app.get("app_type", "").lower() in Globals.APPLE_APP_TYPES
    )


def searchForMatchingDevices(entry, maxAttempt=Globals.MAX_RETRY):    
    api_response = None
    # OPTIMIZED: Determine search parameters once before retry loop
    search_params = {}
    
    # OPTIMIZED: Use dict lookup instead of if-elif chain
    if isinstance(entry, dict):
        identifier_map = {
            "Esper Name": "search",
            "Serial Number": "serial",
            "Custom Serial Number": "search",
            "IMEI 1": "search",
            "IMEI 2": "search"
        }
        
        for key, param_name in identifier_map.items():
            if key in entry:
                search_params[param_name] = entry.get(key, "")
                break
        else:
            # No specific key found, use generic search
            search_params['search'] = entry
    else:
        search_params['search'] = entry
    
    for attempt in range(maxAttempt):
        try:
            enforceRateLimit()
            api_response = get_all_ios_devices_helper("", Globals.limit, 0, searchParamsDict=search_params)
            break
        except Exception as e:
            handleRequestError(attempt, e, maxAttempt, raiseError=True)
    return api_response


def getTenantTags(searchTag=None):
    url = "%s/enterprise/%s/tags/?ordering=tag" % (Globals.configuration.host, Globals.enterprise_id)
    if searchTag:
        url += "&search=%s" % searchTag
    resp = performGetRequestWithRetry(url, headers=getHeader())
    if resp:
        json_resp = resp.json()
        if "results" in json_resp:
            return json_resp["results"]
    return []


def getTenantTagById(tagId):
    url = "%s/enterprise/%s/tags/%s/" % (Globals.configuration.host, Globals.enterprise_id, tagId)
    resp = performGetRequestWithRetry(url, headers=getHeader())
    if resp:
        json_resp = resp.json()
        return json_resp
    return None
