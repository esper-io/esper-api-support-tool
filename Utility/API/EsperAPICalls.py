#!/usr/bin/env python


from datetime import datetime, timedelta
import esperclient
import time
import json

import Common.Globals as Globals
from Utility.API.AppUtilities import constructAppPkgVerStr, getAppDictEntry
import Utility.EventUtility as eventUtil

from Common.decorator import api_tool_decorator

from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.API.CommandUtility import (
    getCommandsApiInstance,
    postEsperCommand,
    waitForCommandToFinish,
)
from Utility.Resource import (
    getHeader,
    logBadResponse,
    postEventToFrame,
)

from Utility.Web.WebRequests import (
    performGetRequestWithRetry,
    performPatchRequestWithRetry,
)

from esperclient.rest import ApiException
from esperclient.models.v0_command_args import V0CommandArgs


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
    timeout=Globals.COMMAND_TIMEOUT,
    maxAttempt=Globals.MAX_RETRY,
):
    """Toggles Kiosk Mode On/Off"""
    api_instance = getCommandsApiInstance()
    if isKiosk:
        command_args = esperclient.V0CommandArgs(package_name=appToUse)
    else:
        command_args = {}
    command = esperclient.V0CommandRequest(
        enterprise=Globals.enterprise_id,
        command_type="DEVICE",
        device_type=Globals.CMD_DEVICE_TYPE,
        devices=[deviceid],
        command="SET_KIOSK_APP",
        command_args=command_args,
    )
    api_response = None
    for attempt in range(maxAttempt):
        try:
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
                ApiToolLog().LogError(e)
                raise e
            time.sleep(Globals.RETRY_SLEEP)
    response = None
    for attempt in range(maxAttempt):
        try:
            response = api_instance.get_command_request_status(
                Globals.enterprise_id, api_response.id
            )
            break
        except Exception as e:
            if attempt == maxAttempt - 1:
                ApiToolLog().LogError(e)
                raise e
            time.sleep(Globals.RETRY_SLEEP)
    status = response.results[0].state
    ignoreQueued = False if Globals.REACH_QUEUED_ONLY else True
    status = waitForCommandToFinish(
        api_response.id, ignoreQueue=ignoreQueued, timeout=timeout
    )
    return status


@api_tool_decorator()
def setdevicename(
    frame,
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
                ApiToolLog().LogError(e)
                raise e
            time.sleep(Globals.RETRY_SLEEP)
    response = None
    for attempt in range(maxAttempt):
        try:
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
                ApiToolLog().LogError(e)
                raise e
            time.sleep(Globals.RETRY_SLEEP)
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
                api_response = api_instance.get_token_info()
                ApiToolLog().LogApiRequestOccurrence(
                    "getTokenInfo", api_instance.get_token_info, Globals.PRINT_API_LOGS
                )
                break
            except Exception as e:
                if attempt == maxAttempt - 1:
                    ApiToolLog().LogError(e)
                    raise e
                time.sleep(Globals.RETRY_SLEEP)
        return api_response
    except ApiException as e:
        print("Exception when calling TokenApi->get_token_info: %s\n" % e)
        ApiToolLog().LogError(e)
        return e


@api_tool_decorator()
def setKiosk(frame, device, deviceInfo):
    """Toggles Kiosk Mode With Specified App"""
    logString = ""
    failed = False
    warning = False
    appSelection = frame.sidePanel.selectedAppEntry
    if not appSelection or "pkgName" not in appSelection:
        return {}
    appToUse = appSelection["pkgName"]
    logString = (
        str("--->" + str(device.device_name) + " " + str(device.alias_name))
        + " -> Kiosk ->"
        + str(appToUse)
    )
    timeout = Globals.COMMAND_TIMEOUT
    if Globals.SET_APP_STATE_AS_SHOW:
        stateStatus = setAppState(device.id, appToUse, state="SHOW")
        timeout = (
            Globals.COMMAND_TIMEOUT if "Command Success" in str(stateStatus) else 0
        )
    status = toggleKioskMode(frame, device.id, appToUse, True, timeout)
    if status:
        if "Success" in str(status):
            logString = logString + " <success>"
        elif "Queued" in str(status):
            logString = (
                logString
                + " <warning, check back on the device (%s)>" % device.device_name
            )
            warning = True
        else:
            logString = logString + " <failed>"
            failed = True
        if deviceInfo["Status"] != "Online":
            logString = logString + " (Device offline)"
        postEventToFrame(eventUtil.myEVT_LOG, logString)
        if failed:
            postEventToFrame(eventUtil.myEVT_ON_FAILED, deviceInfo)
        if warning:
            postEventToFrame(eventUtil.myEVT_ON_FAILED, (device, "Queued"))
        if status and hasattr(status, "state"):
            entry = {
                "Esper Name": device.device_name,
                "Device Id": device.id,
            }
            if hasattr(status, "id"):
                entry["Command Id"] = status.id
            entry["Status"] = status.state
            if hasattr(status, "reason"):
                entry["Reason"] = status.reason
            return entry
        elif status:
            return {
                "Esper Name": device.device_name,
                "Device Id": device.id,
                "Status": status,
            }
        else:
            return {
                "Esper Name": device.device_name,
                "Device Id": device.id,
                "Status": "Already Kiosk mode",
            }


@api_tool_decorator()
def setMulti(frame, device, deviceInfo):
    """Toggles Multi App Mode"""
    logString = (
        str("--->" + str(device.device_name) + " " + str(device.alias_name))
        + " -> Multi ->"
    )
    failed = False
    warning = False
    status = None
    if deviceInfo["Mode"] == "Kiosk":
        status = toggleKioskMode(frame, device.id, {}, False)
        if status:
            if "Success" in str(status):
                logString = logString + " <success>"
            elif "Queued" in str(status):
                logString = (
                    logString
                    + " <warning, check back on the device (%s)>" % device.device_name
                )
                warning = True
            else:
                logString = logString + " <failed>"
                failed = True
    else:
        logString = logString + " (Already Multi mode, skipping)"
    if deviceInfo["Status"] != "Online":
        logString = logString + " (Device offline)"
    postEventToFrame(eventUtil.myEVT_LOG, logString)
    if failed:
        postEventToFrame(eventUtil.myEVT_ON_FAILED, deviceInfo)
    if warning:
        postEventToFrame(eventUtil.myEVT_ON_FAILED, (device, "Queued"))
    if status and hasattr(status, "state"):
        entry = {
            "Esper Name": device.device_name,
            "Device Id": device.id,
        }
        if hasattr(status, "id"):
            entry["Command Id"] = status.id
        entry["Status"] = status.state
        if hasattr(status, "reason"):
            entry["Reason"] = status.reason
        return entry
    elif status:
        return {
            "Esper Name": device.device_name,
            "Device Id": device.id,
            "Status": status,
        }
    else:
        return {
            "Esper Name": device.device_name,
            "Device Id": device.id,
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
                api_response = api_instance.get_enterprise(enterprise_id)
                ApiToolLog().LogApiRequestOccurrence(
                    "validateConfiguration",
                    api_instance.get_enterprise,
                    Globals.PRINT_API_LOGS,
                )
                break
            except Exception as e:
                if attempt == maxAttempt - 1:
                    ApiToolLog().LogError(e)
                    raise e
                time.sleep(Globals.RETRY_SLEEP)
        if hasattr(api_response, "id"):
            return True
    except ApiException as e:
        print("Exception when calling EnterpriseApi->get_enterprise: %s\n" % e)
        ApiToolLog().LogError(e)
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
                ApiToolLog().LogError(e)
                raise e
            time.sleep(Globals.RETRY_SLEEP)
    response = None
    for attempt in range(maxAttempt):
        try:
            response = api_instance.get_command_request_status(
                Globals.enterprise_id, api_response.id
            )
            break
        except Exception as e:
            if attempt == maxAttempt - 1:
                ApiToolLog().LogError(e)
                raise e
            time.sleep(Globals.RETRY_SLEEP)
    status = response.results[0].state
    ignoreQueued = False if Globals.REACH_QUEUED_ONLY else True
    status = waitForCommandToFinish(
        api_response.id, ignoreQueue=ignoreQueued, timeout=timeout
    )
    return status


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


@api_tool_decorator()
def setAppState(
    device_id, pkg_name, appVer=None, state="HIDE", maxAttempt=Globals.MAX_RETRY
):
    pkgName = pkg_name
    if pkgName:
        args = V0CommandArgs(
            app_state=state,
            package_name=pkgName,
        )
        request = esperclient.V0CommandRequest(
            enterprise=Globals.enterprise_id,
            command_type="DEVICE",
            device_type=Globals.CMD_DEVICE_TYPE,
            devices=[device_id],
            command="SET_APP_STATE",
            command_args=args,
        )
        api_instance = getCommandsApiInstance()
        for attempt in range(maxAttempt):
            try:
                api_response = api_instance.create_command(
                    Globals.enterprise_id, request
                )
                ApiToolLog().LogApiRequestOccurrence(
                    "setAppState", api_instance.create_command, Globals.PRINT_API_LOGS
                )
                break
            except Exception as e:
                if attempt == maxAttempt - 1:
                    ApiToolLog().LogError(e)
                    raise e
                time.sleep(1)
        ignoreQueued = False if Globals.REACH_QUEUED_ONLY else True
        return waitForCommandToFinish(api_response.id, ignoreQueue=ignoreQueued)


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


def searchForMatchingDevices(entry, maxAttempt=Globals.MAX_RETRY):
    api_instance = esperclient.DeviceApi(
        esperclient.ApiClient(Globals.configuration)
    )
    api_response = None
    for attempt in range(maxAttempt):
        try:
            if "esperName" in entry.keys():
                identifier = entry["esperName"]
                api_response = api_instance.get_all_devices(
                    Globals.enterprise_id,
                    name=identifier,
                    limit=Globals.limit,
                    offset=Globals.offset,
                )
            elif "sn" in entry.keys():
                identifier = entry["sn"]
                api_response = api_instance.get_all_devices(
                    Globals.enterprise_id,
                    serial=identifier,
                    limit=Globals.limit,
                    offset=Globals.offset,
                )
            elif "csn" in entry.keys():
                identifier = entry["csn"]
                api_response = api_instance.get_all_devices(
                    Globals.enterprise_id,
                    search=identifier,
                    limit=Globals.limit,
                    offset=Globals.offset,
                )
            elif "imei1" in entry.keys():
                identifier = entry["imei1"]
                api_response = api_instance.get_all_devices(
                    Globals.enterprise_id,
                    imei=identifier,
                    limit=Globals.limit,
                    offset=Globals.offset,
                )
            elif "imei2" in entry.keys():
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
                ApiToolLog().LogError(e)
                raise e
            time.sleep(Globals.RETRY_SLEEP)
    return api_response
