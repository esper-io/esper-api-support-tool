#!/usr/bin/env python


from datetime import datetime, timedelta
import threading
import esperclient
import time
import json

import Common.Globals as Globals
import Utility.EventUtility as eventUtil

from Common.decorator import api_tool_decorator

from Utility.ApiToolLogging import ApiToolLog
from Utility.CommandUtility import (
    getCommandsApiInstance,
    waitForCommandToFinish,
)
from Utility.Resource import (
    getHeader,
    logBadResponse,
    performGetRequestWithRetry,
    performPatchRequestWithRetry,
    postEventToFrame,
)

from esperclient.rest import ApiException
from esperclient.models.v0_command_args import V0CommandArgs

####Esper API Requests####


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
def setAppState(
    device_id, pkg_name, appVer=None, state="HIDE", maxAttempt=Globals.MAX_RETRY
):
    pkgName = pkg_name
    if not appVer:
        _, app = getdeviceapps(
            device_id, createAppList=False, useEnterprise=Globals.USE_ENTERPRISE_APP
        )
        if app["results"] and "application" in app["results"][0]:
            app = list(
                filter(
                    lambda x: x["application"]["package_name"] == pkg_name,
                    app["results"],
                )
            )
        else:
            app = list(
                filter(
                    lambda x: x["package_name"] == pkg_name,
                    app["results"],
                )
            )
        if app:
            app = app[0]
        if "application" in app:
            appVer = app["application"]["version"]["version_code"]
        elif "version_code" in app:
            appVer = app["version_code"]
    if pkgName and appVer:
        args = V0CommandArgs(
            app_state=state,
            app_version=appVer,
            package_name=pkgName,
        )
        args.version_code = appVer
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
