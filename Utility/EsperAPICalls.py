#!/usr/bin/env python

from datetime import datetime, timedelta
import esperclient
import time
import json
import Common.Globals as Globals
import Utility.wxThread as wxThread

from Common.decorator import api_tool_decorator

from Utility.ApiToolLogging import ApiToolLog
from Utility.EastUtility import iterateThroughDeviceList
from Utility.Resource import (
    logBadResponse,
    performGetRequestWithRetry,
    performPatchRequestWithRetry,
    performPostRequestWithRetry,
    postEventToFrame,
)

from esperclient.rest import ApiException
from esperclient.models.v0_command_args import V0CommandArgs

####Esper API Requests####
@api_tool_decorator
def getHeader():
    if (
        Globals.configuration
        and Globals.configuration.api_key
        and "Authorization" in Globals.configuration.api_key
    ):
        return {
            "Authorization": f"Bearer {Globals.configuration.api_key['Authorization']}",
            "Content-Type": "application/json",
        }
    else:
        return {}


@api_tool_decorator
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
    json_resp = resp.json()
    logBadResponse(url, resp, json_resp)

    return json_resp


@api_tool_decorator
def getDeviceDetail(deviceId):
    return getInfo("/?format=json&show_policy=true", deviceId)


@api_tool_decorator
def fetchGroupName(groupURL):
    headers = getHeader()
    resp = performGetRequestWithRetry(groupURL, headers=headers)
    try:
        if resp.status_code < 300:
            json_resp = resp.json()
            logBadResponse(groupURL, resp, json_resp)

            if "name" in json_resp:
                return json_resp["name"]
    except Exception as e:
        ApiToolLog().LogError(e)
        logBadResponse(groupURL, resp, None)
    return None


@api_tool_decorator
def patchInfo(request_extension, deviceid, tags):
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
    resp = performPatchRequestWithRetry(
        url, headers=headers, data=json.dumps({"tags": tags})
    )
    json_resp = resp.json()
    logBadResponse(url, resp, json_resp)
    return json_resp


@api_tool_decorator
def iskioskmode(deviceid):
    """Checks If Device Is In Kiosk Mode"""
    kioskmode = False
    json_resp = getInfo(Globals.BASE_REQUEST_EXTENSION, deviceid)
    if json_resp["current_app_mode"] == 0:
        kioskmode = True
    return kioskmode


@api_tool_decorator
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


@api_tool_decorator
def getdevicetags(deviceid):
    """Retrieves Device Tags"""
    tags = ""
    json_resp = getInfo(Globals.BASE_REQUEST_EXTENSION, deviceid)
    if "tags" in json_resp:
        tags = json_resp["tags"]
    return tags


@api_tool_decorator
def getdeviceapps(deviceid, createAppList=True, useEnterprise=False):
    """Retrieves List Of Installed Apps"""
    applist = []
    extention = (
        Globals.DEVICE_ENTERPRISE_APP_LIST_REQUEST_EXTENSION
        if useEnterprise
        else Globals.DEVICE_APP_LIST_REQUEST_EXTENSION
    )
    json_resp = getInfo(extention, deviceid)
    if len(json_resp["results"]) and createAppList:
        for app in json_resp["results"]:
            entry = None
            if "application" in app:
                if app["application"]["package_name"] in Globals.BLACKLIST_PACKAGE_NAME:
                    continue
                appName = app["application"]["application_name"]
                appPkgName = appName + (" (%s)" % app["application"]["package_name"])
                entry = {
                    "app_name": app["application"]["application_name"],
                    appName: app["application"]["package_name"],
                    appPkgName: app["application"]["package_name"],
                }
                if entry not in Globals.frame.sidePanel.selectedDeviceApps:
                    Globals.frame.sidePanel.selectedDeviceApps.append(entry)
                if entry not in Globals.frame.sidePanel.enterpriseApps:
                    Globals.frame.sidePanel.enterpriseApps.append(entry)
                version = (
                    app["application"]["version"]["version_code"][
                        1 : len(app["application"]["version"]["version_code"])
                    ]
                    if app["application"]["version"]["version_code"].startswith("v")
                    else app["application"]["version"]["version_code"]
                )
                applist.append(
                    app["application"]["application_name"]
                    + (
                        " (%s) v" % app["application"]["package_name"]
                        if Globals.SHOW_PKG_NAME
                        else " v"
                    )
                    + version
                )
            else:
                if app["package_name"] in Globals.BLACKLIST_PACKAGE_NAME:
                    continue
                appName = app["app_name"]
                appPkgName = appName + (" (%s)" % app["package_name"])
                entry = {
                    "app_name": app["app_name"],
                    appName: app["package_name"],
                    appPkgName: app["package_name"],
                    "app_state": app["state"],
                }
                version = (
                    app["version_code"][1 : len(app["version_code"])]
                    if app["version_code"].startswith("v")
                    else app["version_code"]
                )
                applist.append(
                    app["app_name"]
                    + (
                        " (%s) v" % app["package_name"]
                        if Globals.SHOW_PKG_NAME
                        else " v"
                    )
                    + version
                )
            if entry and entry not in Globals.frame.sidePanel.knownApps:
                Globals.frame.sidePanel.knownApps.append(entry)
    return applist, json_resp


@api_tool_decorator
def getLatestEvent(deviceId):
    json_resp = getInfo(Globals.DEVICE_STATUS_REQUEST_EXTENSION, deviceId)
    respData = None
    if json_resp["results"]:
        respData = json_resp["results"][0]["data"]
    return respData


@api_tool_decorator
def getkioskmodeapp(deviceid):
    """Retrieves The Kiosk Mode Application ID"""
    json_resp = getInfo(Globals.DEVICE_STATUS_REQUEST_EXTENSION, deviceid)
    respData = None
    if json_resp["results"]:
        respData = json_resp["results"][0]["data"]
    appName = ""
    if respData and "kioskAppName" in respData:
        appName = respData["kioskAppName"]
    return appName


@api_tool_decorator
def getNetworkInfo(deviceid):
    """Retrieves The Kiosk Mode Application ID"""
    json_resp = getInfo(Globals.DEVICE_STATUS_REQUEST_EXTENSION, deviceid)
    respData = None
    if json_resp["results"]:
        respData = json_resp["results"][0]["data"]
    network_event = ""
    if respData and "networkEvent" in respData:
        network_event = respData["networkEvent"]
    return network_event


@api_tool_decorator
def getLocationInfo(deviceid):
    """Retrieves The Kiosk Mode Application ID"""
    json_resp = getInfo(Globals.DEVICE_STATUS_REQUEST_EXTENSION, deviceid)
    respData = None
    if json_resp["results"]:
        respData = json_resp["results"][0]["data"]
    location_event = ""
    if respData and "locationEvent" in respData:
        location_event = respData["locationEvent"]
    return location_event, respData


@api_tool_decorator
def setdevicetags(deviceid, tags):
    """Pushes New Tag To Device"""
    json_resp = patchInfo(Globals.BASE_REQUEST_EXTENSION, deviceid, tags)
    if json_resp and "tags" in json_resp:
        tags = json_resp["tags"]
    return tags


@api_tool_decorator
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
    status = waitForCommandToFinish(api_response.id, ignoreQueue, timeout)
    return status


@api_tool_decorator
def getAllGroups(maxAttempt=Globals.MAX_RETRY):
    """ Make a API call to get all Groups belonging to the Enterprise """
    try:
        api_instance = esperclient.DeviceGroupApi(
            esperclient.ApiClient(Globals.configuration)
        )
        api_response = None
        for attempt in range(maxAttempt):
            try:
                api_response = api_instance.get_all_groups(
                    Globals.enterprise_id, limit=Globals.limit, offset=Globals.offset
                )
                break
            except Exception as e:
                if attempt == maxAttempt - 1:
                    ApiToolLog().LogError(e)
                    raise e
                time.sleep(Globals.RETRY_SLEEP)
        postEventToFrame(wxThread.myEVT_LOG, "---> Group API Request Finished")
        return api_response
    except ApiException as e:
        raise Exception(
            "Exception when calling DeviceGroupApi->get_all_groups: %s\n" % e
        )


@api_tool_decorator
def uploadApplicationForHost(config, enterprise_id, file, maxAttempt=Globals.MAX_RETRY):
    try:
        api_instance = esperclient.ApplicationApi(esperclient.ApiClient(config))
        api_response = None
        for attempt in range(maxAttempt):
            try:
                api_response = api_instance.upload(enterprise_id, file)
                break
            except Exception as e:
                if attempt == maxAttempt - 1:
                    ApiToolLog().LogError(e)
                    raise e
                time.sleep(Globals.RETRY_SLEEP)
        return api_response
    except ApiException as e:
        raise Exception("Exception when calling ApplicationApi->upload: %s\n" % e)


@api_tool_decorator
def getDeviceGroupsForHost(config, enterprise_id, maxAttempt=Globals.MAX_RETRY):
    try:
        api_instance = esperclient.DeviceGroupApi(esperclient.ApiClient(config))
        api_response = None
        for attempt in range(maxAttempt):
            try:
                api_response = api_instance.get_all_groups(
                    enterprise_id, limit=Globals.limit, offset=Globals.offset
                )
                break
            except Exception as e:
                if attempt == maxAttempt - 1:
                    ApiToolLog().LogError(e)
                    raise e
                time.sleep(Globals.RETRY_SLEEP)
        return api_response
    except Exception as e:
        raise e


@api_tool_decorator
def createDeviceGroupForHost(
    config, enterprise_id, group, maxAttempt=Globals.MAX_RETRY
):
    try:
        api_instance = esperclient.DeviceGroupApi(esperclient.ApiClient(config))
        api_response = None
        for attempt in range(maxAttempt):
            try:
                api_response = api_instance.create_group(
                    enterprise_id, data={"name": group}
                )
                break
            except Exception as e:
                if attempt == maxAttempt - 1:
                    ApiToolLog().LogError(e)
                    raise e
                time.sleep(Globals.RETRY_SLEEP)
        return api_response
    except Exception as e:
        raise e


@api_tool_decorator
def getDeviceGroupForHost(
    config, enterprise_id, group_id, maxAttempt=Globals.MAX_RETRY
):
    try:
        api_instance = esperclient.DeviceGroupApi(esperclient.ApiClient(config))
        api_response = None
        for attempt in range(maxAttempt):
            try:
                api_response = api_instance.get_group_by_id(
                    group_id=group_id, enterprise_id=enterprise_id
                )
                break
            except Exception as e:
                if attempt == maxAttempt - 1:
                    ApiToolLog().LogError(e)
                    raise e
                time.sleep(Globals.RETRY_SLEEP)
        return api_response
    except Exception as e:
        raise e


@api_tool_decorator
def getAllDevices(groupToUse, maxAttempt=Globals.MAX_RETRY):
    """ Make a API call to get all Devices belonging to the Enterprise """
    if not groupToUse:
        return None
    try:
        api_instance = esperclient.DeviceApi(
            esperclient.ApiClient(Globals.configuration)
        )
        api_response = None
        if type(groupToUse) == list:
            for group in groupToUse:
                for attempt in range(maxAttempt):
                    try:
                        response = api_instance.get_all_devices(
                            Globals.enterprise_id,
                            group=group,
                            limit=Globals.limit,
                            offset=Globals.offset,
                        )
                        break
                    except Exception as e:
                        if attempt == maxAttempt - 1:
                            ApiToolLog().LogError(e)
                            raise e
                        if hasattr(e, "status") and e.status == 504:
                            Globals.limit = int(Globals.limit / 4)
                            postEventToFrame(
                                wxThread.myEVT_LOG,
                                "---> Encountered a 504 error, retrying with lower limit: %s"
                                % Globals.limit,
                            )
                        time.sleep(Globals.RETRY_SLEEP)
                if not api_response:
                    api_response = response
                else:
                    api_response.results = api_response.results + response.results
        else:
            for attempt in range(maxAttempt):
                try:
                    api_response = api_instance.get_all_devices(
                        Globals.enterprise_id,
                        group=groupToUse,
                        limit=Globals.limit,
                        offset=Globals.offset,
                    )
                    break
                except Exception as e:
                    if attempt == maxAttempt - 1:
                        ApiToolLog().LogError(e)
                        raise e
                    if hasattr(e, "status") and e.status == 504:
                        Globals.limit = int(Globals.limit / 4)
                        postEventToFrame(
                            wxThread.myEVT_LOG,
                            "---> Encountered a 504 error, retrying with lower limit: %s"
                            % Globals.limit,
                        )
                    time.sleep(Globals.RETRY_SLEEP)
        postEventToFrame(wxThread.myEVT_LOG, "---> Device API Request Finished")
        return api_response
    except ApiException as e:
        raise Exception("Exception when calling DeviceApi->get_all_devices: %s\n" % e)


@api_tool_decorator
def getAllApplications(maxAttempt=Globals.MAX_RETRY):
    """ Make a API call to get all Applications belonging to the Enterprise """
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
                break
            except Exception as e:
                if attempt == maxAttempt - 1:
                    ApiToolLog().LogError(e)
                    raise e
                time.sleep(Globals.RETRY_SLEEP)
        postEventToFrame(wxThread.myEVT_LOG, "---> App API Request Finished")
        return api_response
    except ApiException as e:
        raise Exception(
            "Exception when calling ApplicationApi->get_all_applications: %s\n" % e
        )


@api_tool_decorator
def getAllApplicationsForHost(config, enterprise_id, maxAttempt=Globals.MAX_RETRY):
    """ Make a API call to get all Applications belonging to the Enterprise """
    try:
        api_instance = esperclient.ApplicationApi(esperclient.ApiClient(config))
        api_response = None
        for attempt in range(maxAttempt):
            try:
                api_response = api_instance.get_all_applications(
                    enterprise_id,
                    limit=Globals.limit,
                    offset=0,
                    is_hidden=False,
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


@api_tool_decorator
def getDeviceById(deviceToUse, maxAttempt=Globals.MAX_RETRY):
    """ Make a API call to get a Device belonging to the Enterprise by its Id """
    try:
        api_instance = esperclient.DeviceApi(
            esperclient.ApiClient(Globals.configuration)
        )
        api_response_list = []
        api_response = None
        if type(deviceToUse) == list:
            for device in deviceToUse:
                for attempt in range(maxAttempt):
                    try:
                        api_response = api_instance.get_device_by_id(
                            Globals.enterprise_id, device_id=device
                        )
                        break
                    except Exception as e:
                        if attempt == maxAttempt - 1:
                            ApiToolLog().LogError(e)
                            raise e
                        time.sleep(Globals.RETRY_SLEEP)
                if api_response:
                    api_response_list.append(api_response)
        else:
            for attempt in range(maxAttempt):
                try:
                    api_response = api_instance.get_device_by_id(
                        Globals.enterprise_id, device_id=deviceToUse
                    )
                    break
                except Exception as e:
                    if attempt == maxAttempt - 1:
                        ApiToolLog().LogError(e)
                        raise e
                    time.sleep(Globals.RETRY_SLEEP)
        if api_response and api_response_list:
            api_response.results = api_response_list
        elif api_response:
            api_response.results = [api_response]
        postEventToFrame(wxThread.myEVT_LOG, "---> Device API Request Finished")
        return api_response
    except ApiException as e:
        print("Exception when calling DeviceApi->get_device_by_id: %s\n" % e)
        ApiToolLog().LogError(e)


@api_tool_decorator
def getTokenInfo(maxAttempt=Globals.MAX_RETRY):
    api_instance = esperclient.TokenApi(esperclient.ApiClient(Globals.configuration))
    try:
        api_response = None
        for attempt in range(maxAttempt):
            try:
                api_response = api_instance.get_token_info()
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


@api_tool_decorator
def iterateThroughAllGroups(frame, action, api_instance, group=None):
    groupToUse = None
    if group:
        groupToUse = group[0]
    try:
        frame.Logging("---> Making API Request")
        wxThread.doAPICallInThread(
            frame,
            getAllDevices,
            args=(groupToUse),
            eventType=wxThread.myEVT_RESPONSE,
            callback=iterateThroughDeviceList,
            callbackArgs=(frame, action, Globals.enterprise_id),
            optCallbackArgs=(Globals.enterprise_id),
            waitForJoin=False,
            name="iterateThroughDeviceListForAllDeviceGroup",
        )
    except ApiException as e:
        print("Exception when calling DeviceApi->get_all_devices: %s\n" % e)
        ApiToolLog().LogError(e)


@api_tool_decorator
def setKiosk(frame, device, deviceInfo):
    """Toggles Kiosk Mode With Specified App"""
    logString = ""
    failed = False
    warning = False
    appSelection = frame.sidePanel.appChoice.GetSelection()
    if appSelection < 0:
        return {}
    appToUse = frame.sidePanel.appChoice.GetClientData(appSelection)
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
        postEventToFrame(wxThread.myEVT_LOG, logString)
        if failed:
            postEventToFrame(wxThread.myEVT_ON_FAILED, deviceInfo)
        if warning:
            postEventToFrame(wxThread.myEVT_ON_FAILED, (device, "Queued"))
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


@api_tool_decorator
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
    postEventToFrame(wxThread.myEVT_LOG, logString)
    if failed:
        postEventToFrame(wxThread.myEVT_ON_FAILED, deviceInfo)
    if warning:
        postEventToFrame(wxThread.myEVT_ON_FAILED, (device, "Queued"))
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


@api_tool_decorator
def getCommandsApiInstance():
    """ Returns an instace of the Commands API """
    return esperclient.CommandsV2Api(esperclient.ApiClient(Globals.configuration))


def executeCommandAndWait(request, maxAttempt=Globals.MAX_RETRY):
    api_instance = getCommandsApiInstance()
    api_response = None
    for attempt in range(maxAttempt):
        try:
            api_response = api_instance.create_command(Globals.enterprise_id, request)
            break
        except Exception as e:
            if hasattr(e, "body") and (
                "invalid device id" in e.body or "invalid group id" in e.body
            ):
                logBadResponse("create command api", api_response, None)
                return None
            if attempt == maxAttempt - 1:
                ApiToolLog().LogError(e)
                raise e
            time.sleep(Globals.RETRY_SLEEP)
    ignoreQueued = False if Globals.REACH_QUEUED_ONLY else True
    last_status = waitForCommandToFinish(api_response.id, ignoreQueue=ignoreQueued)
    return last_status


@api_tool_decorator
def waitForCommandToFinish(
    request_id,
    ignoreQueue=False,
    timeout=Globals.COMMAND_TIMEOUT,
    maxAttempt=Globals.MAX_RETRY,
):
    """ Wait until a Command is done or it times out """
    api_instance = getCommandsApiInstance()
    response = None
    for attempt in range(maxAttempt):
        try:
            response = api_instance.get_command_request_status(
                Globals.enterprise_id, request_id
            )
            break
        except Exception as e:
            if attempt == maxAttempt - 1:
                ApiToolLog().LogError(e)
                raise e
            time.sleep(Globals.RETRY_SLEEP)
    if response and response.results:
        status = response.results[0]
        postEventToFrame(
            wxThread.myEVT_LOG, "---> Command state: %s" % str(status.state)
        )

        stateList = [
            "Command Success",
            "Command Failure",
            "Command TimeOut",
            "Command Cancelled",
            "Command Queued",
            "Command Scheduled",
        ]
        if ignoreQueue:
            stateList.remove("Command Queued")

        start = time.perf_counter()
        while status.state not in stateList:
            end = time.perf_counter()
            duration = end - start
            if duration >= timeout:
                postEventToFrame(
                    wxThread.myEVT_LOG,
                    "---> Skipping wait for Command, last logged Command state: %s (Device may be offline)"
                    % str(status.state),
                )
                break
            for attempt in range(maxAttempt):
                try:
                    response = api_instance.get_command_request_status(
                        Globals.enterprise_id, request_id
                    )
                    break
                except Exception as e:
                    if attempt == maxAttempt - 1:
                        ApiToolLog().LogError(e)
                        raise e
                    time.sleep(Globals.RETRY_SLEEP)
            if response and response.results:
                status = response.results[0]
            postEventToFrame(
                wxThread.myEVT_LOG, "---> Command state: %s" % str(status.state)
            )
            time.sleep(3)
        return status
    else:
        return response.results


@api_tool_decorator
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


@api_tool_decorator
def postEsperCommand(command_data, useV0=True):
    json_resp = None
    resp = None
    try:
        headers = getHeader()
        url = ""
        if useV0:
            url = "https://%s-api.esper.cloud/api/v0/enterprise/%s/command/" % (
                Globals.configuration.host.split("-api")[0].replace("https://", ""),
                Globals.enterprise_id,
            )
        else:
            url = "https://%s-api.esper.cloud/api/enterprise/%s/command/" % (
                Globals.configuration.host.split("-api")[0].replace("https://", ""),
                Globals.enterprise_id,
            )
        resp = performPostRequestWithRetry(url, headers=headers, json=command_data)
        json_resp = resp.json()
        logBadResponse(url, resp, json_resp)
    except Exception as e:
        ApiToolLog().LogError(e)
    return resp, json_resp


@api_tool_decorator
def clearAppData(frame, device):
    json_resp = None
    try:
        appToUse = frame.sidePanel.appChoice.GetClientData(
            frame.sidePanel.appChoice.GetSelection()
        )
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
                postEventToFrame(wxThread.myEVT_ON_FAILED, device)
            if resp.status_code < 300:
                frame.Logging(
                    "---> Clear %s App Data Command has been sent to %s"
                    % (cmdArgs["application_name"], device.device_name)
                )
        else:
            frame.Logging(
                "ERROR: Failed to send Clear %s App Data Command to %s"
                % (frame.sidePanel.appChoice.GetValue(), device.device_name)
            )
    except Exception as e:
        ApiToolLog().LogError(e)
        frame.Logging(
            "ERROR: Failed to send Clear App Data Command to %s" % (device.device_name)
        )
        postEventToFrame(wxThread.myEVT_ON_FAILED, device)
    return json_resp


@api_tool_decorator
def getDeviceApplicationById(device_id, application_id):
    try:
        headers = getHeader()
        url = "https://%s-api.esper.cloud/api/enterprise/%s/device/%s/app/%s" % (
            Globals.configuration.host.split("-api")[0].replace("https://", ""),
            Globals.enterprise_id,
            device_id,
            application_id,
        )
        resp = performGetRequestWithRetry(url, headers=headers)
        json_resp = resp.json()
        logBadResponse(url, resp, json_resp)
    except Exception as e:
        ApiToolLog().LogError(e)
    return resp, json_resp


@api_tool_decorator
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
                break
            except Exception as e:
                if attempt == maxAttempt - 1:
                    ApiToolLog().LogError(e)
                    raise e
                time.sleep(1)
        ignoreQueued = False if Globals.REACH_QUEUED_ONLY else True
        return waitForCommandToFinish(api_response.id, ignoreQueue=ignoreQueued)


def getApplication(application_id):
    api_instance = esperclient.ApplicationApi(
        esperclient.ApiClient(Globals.configuration)
    )
    enterprise_id = Globals.enterprise_id
    try:
        # Get application information
        api_response = api_instance.get_application(application_id, enterprise_id)
        return api_response
    except ApiException as e:
        print("Exception when calling ApplicationApi->get_application: %s\n" % e)


def getAppVersions(
    application_id, version_code="", build_number="", maxAttempt=Globals.MAX_RETRY
):
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
            return api_response
        except Exception as e:
            if attempt == maxAttempt - 1:
                ApiToolLog().LogError(e)
                print(
                    "Exception when calling ApplicationApi->get_app_versions: %s\n" % e
                )
                raise e
            time.sleep(1)


def getAppVersion(version_id, application_id, maxAttempt=Globals.MAX_RETRY):
    api_instance = esperclient.ApplicationApi(
        esperclient.ApiClient(Globals.configuration)
    )
    enterprise_id = Globals.enterprise_id
    for attempt in range(maxAttempt):
        try:
            # Get app version information
            api_response = api_instance.get_app_version(
                version_id, application_id, enterprise_id
            )
            return api_response
        except ApiException as e:
            if attempt == maxAttempt - 1:
                ApiToolLog().LogError(e)
                print(
                    "Exception when calling ApplicationApi->get_app_version: %s\n" % e
                )
                raise e
            time.sleep(1)


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
