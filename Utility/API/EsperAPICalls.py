#!/usr/bin/env python


import json
import string
import time
from datetime import datetime, timedelta

import esperclient
from esperclient.models.v0_command_args import V0CommandArgs
from esperclient.rest import ApiException

import Common.Globals as Globals
import Utility.EventUtility as eventUtil
from Common.decorator import api_tool_decorator
from Utility.API.AppUtilities import constructAppPkgVerStr, getAppDictEntry
from Utility.API.CommandUtility import (
    getCommandsApiInstance,
    postEsperCommand,
    waitForCommandToFinish,
)
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Resource import (
    enforceRateLimit,
    getHeader,
    logBadResponse,
    postEventToFrame,
)
from Utility.Web.WebRequests import (
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
def toggleKioskMode(
    frame,
    deviceid,
    appToUse,
    isKiosk,
    isGroup=False,
    timeout=Globals.COMMAND_TIMEOUT,
    maxAttempt=Globals.MAX_RETRY,
):
    """Toggles Kiosk Mode On/Off"""
    api_instance = getCommandsApiInstance()
    if isKiosk:
        command_args = esperclient.V0CommandArgs(package_name=appToUse)
    else:
        command_args = {}
    command = None
    if isGroup:
        command = esperclient.V0CommandRequest(
            enterprise=Globals.enterprise_id,
            command_type="GROUP",
            device_type=Globals.CMD_DEVICE_TYPE,
            groups=[deviceid] if type(deviceid) is str else deviceid,
            command="SET_KIOSK_APP",
            command_args=command_args,
        )
    else:
        command = esperclient.V0CommandRequest(
            enterprise=Globals.enterprise_id,
            command_type="DEVICE",
            device_type=Globals.CMD_DEVICE_TYPE,
            devices=[deviceid] if type(deviceid) is str else deviceid,
            command="SET_KIOSK_APP",
            command_args=command_args,
        )
    api_response = None
    for attempt in range(maxAttempt):
        try:
            enforceRateLimit()
            api_response = api_instance.create_command(Globals.enterprise_id, command)
            ApiToolLog().LogApiRequestOccurrence(
                "toggleKioskMode",
                api_instance.create_command.__name__,
                Globals.PRINT_API_LOGS,
            )
            break
        except Exception as e:
            if hasattr(e, "body") and "invalid device id" in e.body:
                logBadResponse("create command api", api_response, None)
                return None
            if attempt == maxAttempt - 1:
                ApiToolLog().LogError(e, postIssue=False)
                raise e
            if "429" not in str(e) and "Too Many Requests" not in str(e):
                time.sleep(Globals.RETRY_SLEEP)
            else:
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * (attempt + 1)
                )  # Sleep for a minute * retry number
    response = None
    for attempt in range(maxAttempt):
        try:
            enforceRateLimit()
            response = api_instance.get_command_request_status(
                Globals.enterprise_id, api_response.id
            )
            break
        except Exception as e:
            if attempt == maxAttempt - 1:
                ApiToolLog().LogError(e, postIssue=False)
                raise e
            if "429" not in str(e) and "Too Many Requests" not in str(e):
                time.sleep(Globals.RETRY_SLEEP)
            else:
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * (attempt + 1)
                )  # Sleep for a minute * retry number
    status = response.results[0].state
    ignoreQueued = False if Globals.REACH_QUEUED_ONLY else True
    status = waitForCommandToFinish(
        api_response.id, ignoreQueue=ignoreQueued, timeout=timeout
    )
    return status


@api_tool_decorator()
def setdevicename(
    deviceid,
    devicename,
    ignoreQueue,
    timeout=Globals.COMMAND_TIMEOUT,
    maxAttempt=Globals.MAX_RETRY,
):
    """Pushes New Name To Name"""
    api_instance = getCommandsApiInstance()
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
    api_response = None
    for attempt in range(maxAttempt):
        try:
            enforceRateLimit()
            api_response = api_instance.create_command(Globals.enterprise_id, command)
            ApiToolLog().LogApiRequestOccurrence(
                "setdevicename", api_instance.create_command, Globals.PRINT_API_LOGS
            )
            break
        except Exception as e:
            if hasattr(e, "body") and "invalid device id" in e.body:
                logBadResponse("create command api", api_response, None)
                return None
            if attempt == maxAttempt - 1:
                ApiToolLog().LogError(e, postIssue=False)
                raise e
            if "429" not in str(e) and "Too Many Requests" not in str(e):
                time.sleep(Globals.RETRY_SLEEP)
            else:
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * (attempt + 1)
                )  # Sleep for a minute * retry number
    response = None
    for attempt in range(maxAttempt):
        try:
            enforceRateLimit()
            response = api_instance.get_command_request_status(
                Globals.enterprise_id, api_response.id
            )
            ApiToolLog().LogApiRequestOccurrence(
                "setdevicename",
                api_instance.get_command_request_status,
                Globals.PRINT_API_LOGS,
            )
            break
        except Exception as e:
            if attempt == maxAttempt - 1:
                ApiToolLog().LogError(e, postIssue=False)
                raise e
            if "429" not in str(e) and "Too Many Requests" not in str(e):
                time.sleep(Globals.RETRY_SLEEP)
            else:
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * (attempt + 1)
                )  # Sleep for a minute * retry number
    if response.results:
        status = response.results[0].state
    status = waitForCommandToFinish(api_response.id, ignoreQueue, timeout)
    if status == "No status found":
        status = status + ": %s" % str(api_response)
    return status


@api_tool_decorator()
def getTokenInfo(maxAttempt=Globals.MAX_RETRY):
    api_instance = esperclient.TokenApi(esperclient.ApiClient(Globals.configuration))
    try:
        api_response = None
        for attempt in range(maxAttempt):
            try:
                enforceRateLimit()
                api_response = api_instance.get_token_info()
                ApiToolLog().LogApiRequestOccurrence(
                    "getTokenInfo", api_instance.get_token_info, Globals.PRINT_API_LOGS
                )
                break
            except Exception as e:
                if attempt == maxAttempt - 1:
                    ApiToolLog().LogError(e, postIssue=False)
                    raise e
                if "429" not in str(e) and "Too Many Requests" not in str(e):
                    time.sleep(Globals.RETRY_SLEEP)
                else:
                    time.sleep(
                        Globals.RETRY_SLEEP * 20 * (attempt + 1)
                    )  # Sleep for a minute * retry number
        return api_response
    except ApiException as e:
        print("Exception when calling TokenApi->get_token_info: %s\n" % e)
        ApiToolLog().LogError(e, postIssue=False)
        return e


@api_tool_decorator()
def setKiosk(frame, device, deviceInfo, isGroup=False):
    """Toggles Kiosk Mode With Specified App"""
    logString = ""
    failed = False
    warning = False
    appSelection = frame.sidePanel.selectedAppEntry
    if not appSelection or "pkgName" not in appSelection:
        return {}
    appToUse = appSelection["pkgName"]

    deviceName = None
    deviceId = None
    aliasName = None
    if hasattr(device, "device_name"):
        aliasName = device.alias_name
        deviceName = device.device_name
        deviceId = device.id
    elif type(device) is dict:
        deviceName = device["device_name"]
        deviceId = device["id"]
        aliasName = device["alias_name"]
    else:
        deviceName = "List of devices"
        aliasName = ""
        deviceId = device

    logString = (
        str("--->" + str(deviceName) + " " + str(aliasName))
        + " -> Kiosk ->"
        + str(appToUse)
    )
    timeout = Globals.COMMAND_TIMEOUT
    if Globals.SET_APP_STATE_AS_SHOW:
        stateStatus = setAppState(deviceId, appToUse, state="SHOW", isGroup=isGroup)
        postEventToFrame(
            eventUtil.myEVT_AUDIT,
            {
                "operation": "SetAppState",
                "data": {"id": deviceId, "app": appToUse, "state": "SHOW"},
                "resp": stateStatus,
            },
        )
        timeout = (
            Globals.COMMAND_TIMEOUT if "Command Success" in str(stateStatus) else 0
        )
    status = toggleKioskMode(frame, deviceId, appToUse, True, timeout, isGroup=isGroup)
    if status:
        if "Success" in str(status):
            logString = logString + " <success>"
        elif "Queued" in str(status):
            logString = (
                logString + " <warning, check back on the device (%s)>" % deviceName
            )
            warning = True
        else:
            logString = logString + " <failed>"
            failed = True
        if deviceInfo and deviceInfo["Status"] != "Online":
            logString = logString + " (Device offline)"
        postEventToFrame(eventUtil.myEVT_LOG, logString)
        if failed:
            postEventToFrame(eventUtil.myEVT_ON_FAILED, deviceInfo)
        if warning:
            postEventToFrame(eventUtil.myEVT_ON_FAILED, (device, "Queued"))
        if status and hasattr(status, "state"):
            entry = {
                "Esper Name": deviceName,
                "Device Id": deviceId,
            }
            if hasattr(status, "id"):
                entry["Command Id"] = status.id
            entry["Status"] = status.state
            if hasattr(status, "reason"):
                entry["Reason"] = status.reason
            return entry
        elif status:
            return {
                "Esper Name": deviceName,
                "Device Id": deviceId,
                "Status": status,
            }
        else:
            return {
                "Esper Name": deviceName,
                "Device Id": deviceId,
                "Status": "Already Kiosk mode",
            }


@api_tool_decorator()
def setMulti(frame, device, deviceInfo, isGroup=False):
    """Toggles Multi App Mode"""
    deviceName = None
    deviceId = None
    aliasName = None
    if hasattr(device, "device_name"):
        aliasName = device.alias_name
        deviceName = device.device_name
        deviceId = device.id
    elif type(device) is dict:
        deviceName = device["device_name"]
        deviceId = device["id"]
        aliasName = device["alias_name"]
    elif type(device) is list:
        deviceName = "List of devices"
        aliasName = ""
        deviceId = device

    logString = str("--->" + str(deviceName) + " " + str(aliasName)) + " -> Multi ->"
    failed = False
    warning = False
    status = None
    if deviceInfo and deviceInfo["Mode"] == "Kiosk":
        status = toggleKioskMode(frame, deviceId, {}, False, isGroup=isGroup)
        if status:
            if "Success" in str(status):
                logString = logString + " <success>"
            elif "Queued" in str(status):
                logString = (
                    logString + " <warning, check back on the device (%s)>" % deviceName
                )
                warning = True
            else:
                logString = logString + " <failed>"
                failed = True
    else:
        logString = logString + " (Already Multi mode, skipping)"
    if deviceInfo and deviceInfo["Status"] != "Online":
        logString = logString + " (Device offline)"
    postEventToFrame(eventUtil.myEVT_LOG, logString)
    if failed:
        postEventToFrame(eventUtil.myEVT_ON_FAILED, deviceInfo)
    if warning:
        postEventToFrame(eventUtil.myEVT_ON_FAILED, (device, "Queued"))
    if status and hasattr(status, "state"):
        entry = {
            "Esper Name": deviceName,
            "Device Id": deviceId,
        }
        if hasattr(status, "id"):
            entry["Command Id"] = status.id
        entry["Status"] = status.state
        if hasattr(status, "reason"):
            entry["Reason"] = status.reason
        return entry
    elif status:
        return {
            "Esper Name": deviceName,
            "Device Id": deviceId,
            "Status": status,
        }
    else:
        return {
            "Esper Name": deviceName,
            "Device Id": deviceId,
            "Status": "Already Multi mode",
        }


@api_tool_decorator()
def validateConfiguration(
    host, entId, key, prefix="Bearer", maxAttempt=Globals.MAX_RETRY
):
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
                break
            except Exception as e:
                if attempt == maxAttempt - 1:
                    ApiToolLog().LogError(e, postIssue=False)
                    raise e
                if "429" not in str(e) and "Too Many Requests" not in str(e):
                    time.sleep(Globals.RETRY_SLEEP)
                else:
                    time.sleep(
                        Globals.RETRY_SLEEP * 20 * (attempt + 1)
                    )  # Sleep for a minute * retry number
        if hasattr(api_response, "id"):
            return True
    except ApiException as e:
        print("Exception when calling EnterpriseApi->get_enterprise: %s\n" % e)
        ApiToolLog().LogError(e, postIssue=False)
    return False


def factoryResetDevice(
    deviceId, maxAttempt=Globals.MAX_RETRY, timeout=Globals.COMMAND_TIMEOUT
):
    api_instance = getCommandsApiInstance()
    command_args = {"wipe_FRP": True, "wipe_external_storage": True}
    command = esperclient.V0CommandRequest(
        enterprise=Globals.enterprise_id,
        command_type="DEVICE",
        device_type=Globals.CMD_DEVICE_TYPE,
        devices=[deviceId],
        command="WIPE",
        command_args=command_args,
    )

    api_response = None
    for attempt in range(maxAttempt):
        try:
            enforceRateLimit()
            api_response = api_instance.create_command(Globals.enterprise_id, command)
            ApiToolLog().LogApiRequestOccurrence(
                "toggleKioskMode",
                api_instance.create_command.__name__,
                Globals.PRINT_API_LOGS,
            )
            break
        except Exception as e:
            if hasattr(e, "body") and "invalid device id" in e.body:
                logBadResponse("create command api", api_response, None)
                return None
            if attempt == maxAttempt - 1:
                ApiToolLog().LogError(e, postIssue=False)
                raise e
            if "429" not in str(e) and "Too Many Requests" not in str(e):
                time.sleep(Globals.RETRY_SLEEP)
            else:
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * (attempt + 1)
                )  # Sleep for a minute * retry number
    response = None
    for attempt in range(maxAttempt):
        try:
            enforceRateLimit()
            response = api_instance.get_command_request_status(
                Globals.enterprise_id, api_response.id
            )
            break
        except Exception as e:
            if attempt == maxAttempt - 1:
                ApiToolLog().LogError(e, postIssue=False)
                raise e
            if "429" not in str(e) and "Too Many Requests" not in str(e):
                time.sleep(Globals.RETRY_SLEEP)
            else:
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * (attempt + 1)
                )  # Sleep for a minute * retry number
    status = response.results[0].state
    ignoreQueued = False if Globals.REACH_QUEUED_ONLY else True
    status = waitForCommandToFinish(
        api_response.id, ignoreQueue=ignoreQueued, timeout=timeout
    )
    return status


@api_tool_decorator()
def getdeviceapps(deviceid, createAppListArg=True, useEnterprise=False):
    """Retrieves List Of Installed Apps"""
    extention = (
        Globals.DEVICE_ENTERPRISE_APP_LIST_REQUEST_EXTENSION
        if useEnterprise
        else Globals.DEVICE_APP_LIST_REQUEST_EXTENSION
    )
    hasFormat = [
        tup[1] for tup in string.Formatter().parse(extention) if tup[1] is not None
    ]
    if hasFormat:
        if "limit" in hasFormat:
            extention = extention.format(limit=Globals.limit)
    json_resp = getInfo(extention, deviceid)
    applist = createAppList(json_resp) if createAppListArg else []
    return applist, json_resp


def createAppList(json_resp, obtainAppDictEntry=True, filterData=False):
    applist = []
    if json_resp and "results" in json_resp and len(json_resp["results"]):
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
                pkgName = app["application"]["package_name"]
                if pkgName in Globals.BLACKLIST_PACKAGE_NAME or (
                    filterData and pkgName not in Globals.APP_COL_FILTER
                ):
                    continue
                if obtainAppDictEntry:
                    entry = getAppDictEntry(app, False)
                if Globals.VERSON_NAME_INSTEAD_OF_CODE:
                    version = (
                        app["application"]["version"]["version_name"][
                            1 : len(app["application"]["version"]["version_name"])
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
                            1 : len(app["application"]["version"]["version_code"])
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
            else:
                if app["package_name"] in Globals.BLACKLIST_PACKAGE_NAME or (
                    filterData and app["package_name"] not in Globals.APP_COL_FILTER
                ):
                    continue
                if obtainAppDictEntry:
                    entry = getAppDictEntry(app, False)
                version = None
                if Globals.VERSON_NAME_INSTEAD_OF_CODE:
                    version = (
                        app["version_name"][1 : len(app["version_name"])]
                        if app["version_name"] and app["version_name"].startswith("v")
                        else app["version_name"]
                    )
                else:
                    version = (
                        app["version_code"][1 : len(app["version_code"])]
                        if app["version_code"] and app["version_code"].startswith("v")
                        else app["version_code"]
                    )
                applist.append(
                    constructAppPkgVerStr(app["app_name"], app["package_name"], version)
                )
            if (
                entry is not None
                and entry not in Globals.frame.sidePanel.selectedDeviceApps
                and ("isValid" in entry and entry["isValid"])
            ):
                Globals.frame.sidePanel.selectedDeviceApps.append(entry)
    return applist


@api_tool_decorator()
def setAppState(
    device_id, pkg_name, state="HIDE", isGroup=False, maxAttempt=Globals.MAX_RETRY
):
    pkgName = pkg_name
    if pkgName:
        args = V0CommandArgs(
            app_state=state,
            package_name=pkgName,
        )
        request = None
        if not isGroup:
            request = esperclient.V0CommandRequest(
                enterprise=Globals.enterprise_id,
                command_type="DEVICE",
                device_type=Globals.CMD_DEVICE_TYPE,
                devices=[device_id] if type(device_id) != list else device_id,
                command="SET_APP_STATE",
                command_args=args,
            )
        else:
            request = esperclient.V0CommandRequest(
                enterprise=Globals.enterprise_id,
                command_type="GROUP",
                device_type=Globals.CMD_DEVICE_TYPE,
                groups=[device_id] if type(device_id) != list else device_id,
                command="SET_APP_STATE",
                command_args=args,
            )
        api_instance = getCommandsApiInstance()
        for attempt in range(maxAttempt):
            try:
                enforceRateLimit()
                api_response = api_instance.create_command(
                    Globals.enterprise_id, request
                )
                ApiToolLog().LogApiRequestOccurrence(
                    "setAppState", api_instance.create_command, Globals.PRINT_API_LOGS
                )
                break
            except Exception as e:
                if hasattr(e, "body") and (
                    "invalid device id" in e.body or "invalid group id" in e.body
                ):
                    return None
                if attempt == maxAttempt - 1:
                    ApiToolLog().LogError(e, postIssue=False)
                    raise e
                if "429" not in str(e) and "Too Many Requests" not in str(e):
                    time.sleep(Globals.RETRY_SLEEP)
                else:
                    time.sleep(
                        Globals.RETRY_SLEEP * 20 * (attempt + 1)
                    )  # Sleep for a minute * retry number
        ignoreQueued = False if Globals.REACH_QUEUED_ONLY else True
        return waitForCommandToFinish(api_response.id, ignoreQueue=ignoreQueued)


@api_tool_decorator()
def clearAppData(frame, device, isGroup=False):
    json_resp = None
    deviceName = None
    deviceId = None
    if hasattr(device, "device_name"):
        deviceName = device.device_name
        deviceId = device.id
    elif type(device) is dict:
        deviceName = device["device_name"]
        deviceId = device["id"]
    else:
        deviceName = ""
        deviceId = device
    try:
        appToUse = frame.sidePanel.selectedAppEntry["pkgName"]
        cmdArgs = {"package_name": appToUse}

        if cmdArgs:
            reqData = None
            if not isGroup:
                reqData = {
                    "command_type": "DEVICE",
                    "command_args": cmdArgs,
                    "devices": [deviceId] if type(deviceId) is str else deviceId,
                    "device_type": Globals.CMD_DEVICE_TYPE,
                    "command": "CLEAR_APP_DATA",
                }
            else:
                reqData = {
                    "command_type": "GROUP",
                    "command_args": cmdArgs,
                    "groups": [deviceId] if type(deviceId) is str else deviceId,
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
                    % (appToUse, deviceName)
                )
        else:
            frame.Logging(
                "ERROR: Failed to send Clear %s App Data Command to %s"
                % (
                    frame.sidePanel.selectedAppEntry["name"],
                    deviceName,
                )
            )
    except Exception as e:
        ApiToolLog().LogError(e, postIssue=False)
        frame.Logging(
            "ERROR: Failed to send Clear App Data Command to %s" % (deviceName)
        )
        postEventToFrame(eventUtil.myEVT_ON_FAILED, device)
    return json_resp


def searchForMatchingDevices(entry, maxAttempt=Globals.MAX_RETRY):
    api_instance = esperclient.DeviceApi(esperclient.ApiClient(Globals.configuration))
    api_response = None
    for attempt in range(maxAttempt):
        try:
            enforceRateLimit()
            if type(entry) is dict and "esperName" in entry.keys():
                identifier = entry["esperName"]
                api_response = api_instance.get_all_devices(
                    Globals.enterprise_id,
                    name=identifier,
                    limit=Globals.limit,
                    offset=Globals.offset,
                )
            elif type(entry) is dict and "sn" in entry.keys():
                identifier = entry["sn"]
                api_response = api_instance.get_all_devices(
                    Globals.enterprise_id,
                    serial=identifier,
                    limit=Globals.limit,
                    offset=Globals.offset,
                )
            elif type(entry) is dict and "csn" in entry.keys():
                identifier = entry["csn"]
                api_response = api_instance.get_all_devices(
                    Globals.enterprise_id,
                    search=identifier,
                    limit=Globals.limit,
                    offset=Globals.offset,
                )
            elif type(entry) is dict and "imei1" in entry.keys():
                identifier = entry["imei1"]
                api_response = api_instance.get_all_devices(
                    Globals.enterprise_id,
                    imei=identifier,
                    limit=Globals.limit,
                    offset=Globals.offset,
                )
            elif type(entry) is dict and "imei2" in entry.keys():
                identifier = entry["imei2"]
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
            if attempt == maxAttempt - 1:
                ApiToolLog().LogError(e, postIssue=False)
                raise e
            if "429" not in str(e) and "Too Many Requests" not in str(e):
                time.sleep(Globals.RETRY_SLEEP)
            else:
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * (attempt + 1)
                )  # Sleep for a minute * retry number
    return api_response
