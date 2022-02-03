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
    isApiKey,
    joinThreadList,
    limitActiveThreads,
    logBadResponse,
    performDeleteRequestWithRetry,
    performGetRequestWithRetry,
    performPatchRequestWithRetry,
    performPostRequestWithRetry,
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
def getDeviceDetail(deviceId):
    return getInfo("?format=json&show_policy=true", deviceId)


@api_tool_decorator()
def fetchGroupName(groupURL, returnJson=False):
    headers = getHeader()
    resp = performGetRequestWithRetry(groupURL, headers=headers)
    try:
        if resp and resp.status_code < 300:
            json_resp = resp.json()
            logBadResponse(groupURL, resp, json_resp)

            if "name" in json_resp:
                if returnJson:
                    return json_resp
                else:
                    return json_resp["name"]
    except Exception as e:
        ApiToolLog().LogError(e)
        logBadResponse(groupURL, resp, None)
    return None


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
def getLatestEvent(deviceId):
    json_resp = getInfo(Globals.DEVICE_STATUS_REQUEST_EXTENSION, deviceId)
    respData = None
    if json_resp and "results" in json_resp and json_resp["results"]:
        respData = json_resp["results"][0]["data"]
    return respData


@api_tool_decorator()
def setdevicetags(deviceid, tags):
    """Pushes New Tag To Device"""
    json_resp = patchInfo(Globals.BASE_REQUEST_EXTENSION, deviceid, tags=tags)
    if json_resp and "tags" in json_resp:
        tags = json_resp["tags"]
    return tags


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
def getAllGroups(name="", limit=None, offset=None, maxAttempt=Globals.MAX_RETRY):
    """ Make a API call to get all Groups belonging to the Enterprise """
    if not limit:
        limit = Globals.limit
    if not offset:
        offset = Globals.offset
    try:
        api_instance = esperclient.DeviceGroupApi(
            esperclient.ApiClient(Globals.configuration)
        )
        api_response = None
        for attempt in range(maxAttempt):
            try:
                api_response = api_instance.get_all_groups(
                    Globals.enterprise_id,
                    name=name,
                    limit=limit,
                    offset=offset,
                )
                ApiToolLog().LogApiRequestOccurrence(
                    "getAllGroups", api_instance.get_all_groups, Globals.PRINT_API_LOGS
                )
                break
            except Exception as e:
                if attempt == maxAttempt - 1:
                    ApiToolLog().LogError(e)
                    raise e
                time.sleep(Globals.RETRY_SLEEP)
        postEventToFrame(eventUtil.myEVT_LOG, "---> Group API Request Finished")
        return api_response
    except ApiException as e:
        raise Exception(
            "Exception when calling DeviceGroupApi->get_all_groups: %s\n" % e
        )


@api_tool_decorator()
def getDeviceGroupsForHost(config, enterprise_id, maxAttempt=Globals.MAX_RETRY):
    try:
        api_instance = esperclient.DeviceGroupApi(esperclient.ApiClient(config))
        api_response = None
        for attempt in range(maxAttempt):
            try:
                api_response = api_instance.get_all_groups(
                    enterprise_id, limit=Globals.limit, offset=Globals.offset
                )
                ApiToolLog().LogApiRequestOccurrence(
                    "getDeviceGroupsForHost",
                    api_instance.get_all_groups,
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
        raise e


@api_tool_decorator()
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
                ApiToolLog().LogApiRequestOccurrence(
                    "createDeviceGroupForHost",
                    api_instance.create_group,
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
        raise e


@api_tool_decorator()
def getAllDevices(
    groupToUse, limit=None, offset=None, fetchAll=False, maxAttempt=Globals.MAX_RETRY
):
    """ Make a API call to get all Devices belonging to the Enterprise """
    if not limit:
        limit = Globals.limit
    if not offset:
        offset = Globals.offset
    if not groupToUse:
        return None
    try:
        api_response = None
        if type(groupToUse) == list:
            api_response = fetchDevicesFromGroup(
                groupToUse, limit, offset, fetchAll, maxAttempt
            )
        else:
            api_response = get_all_devices(
                groupToUse, limit, offset, fetchAll, maxAttempt
            )
        postEventToFrame(eventUtil.myEVT_LOG, "---> Device API Request Finished")
        return api_response
    except ApiException as e:
        raise Exception("Exception when calling DeviceApi->get_all_devices: %s\n" % e)


def get_all_devices_helper(
    groupToUse, limit, offset, maxAttempt=Globals.MAX_RETRY, responses=None
):
    api_instance = esperclient.DeviceApi(esperclient.ApiClient(Globals.configuration))
    api_response = None
    for attempt in range(maxAttempt):
        try:
            api_response = api_instance.get_all_devices(
                Globals.enterprise_id,
                group=groupToUse,
                limit=limit,
                offset=offset,
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
            if hasattr(e, "status") and e.status == 504:
                limit = int(int(limit) / 4)
                Globals.limit = limit
                postEventToFrame(
                    eventUtil.myEVT_LOG,
                    "---> Encountered a 504 error, retrying with lower limit: %s"
                    % limit,
                )
            time.sleep(Globals.RETRY_SLEEP)
    if type(responses) == list:
        responses.append(api_response)
    return api_response


def get_all_devices(
    groupToUse, limit, offset, fetchAll=False, maxAttempt=Globals.MAX_RETRY
):
    response = get_all_devices_helper(groupToUse, limit, offset, maxAttempt)
    if Globals.GROUP_FETCH_ALL or fetchAll:
        devices = getAllDevicesFromOffsets(response, groupToUse, maxAttempt)
        response.results = response.results + devices
        response.next = None
        response.prev = None
    return response


def fetchDevicesFromGroup(
    groupToUse, limit, offset, fetchAll=False, maxAttempt=Globals.MAX_RETRY
):
    api_response = None
    for group in groupToUse:
        for _ in range(maxAttempt):
            response = get_all_devices(group, limit, offset, fetchAll, maxAttempt)
            if api_response:
                for device in response.results:
                    if device not in api_response.results:
                        api_response.results.append(device)
                api_response.count = len(api_response.results)
            else:
                api_response = response
            break
    return api_response


def getAllDevicesFromOffsets(
    api_response, group, maxAttempt=Globals.MAX_RETRY, devices=[]
):
    threads = []
    responses = []
    count = api_response.count
    if api_response.next:
        respOffset = api_response.next.split("offset=")[-1].split("&")[0]
        respOffsetInt = int(respOffset)
        respLimit = api_response.next.split("limit=")[-1].split("&")[0]
        while int(respOffsetInt) < count and int(respLimit) < count:
            thread = threading.Thread(
                target=get_all_devices_helper,
                args=(group, respLimit, str(respOffsetInt), maxAttempt, responses),
            )
            threads.append(thread)
            thread.start()
            respOffsetInt += int(respLimit)
            limitActiveThreads(threads)
        remainder = count % int(respLimit)
        if remainder > 0:
            respOffsetInt -= int(respLimit)
            respOffsetInt += 1
            thread = threading.Thread(
                target=get_all_devices_helper,
                args=(group, respLimit, str(respOffsetInt), maxAttempt, responses),
            )
            threads.append(thread)
            thread.start()
            limitActiveThreads(threads)
    joinThreadList(threads)
    for resp in responses:
        if resp and resp.results:
            for entry in resp.results:
                if entry not in devices:
                    devices.append(entry)
    return devices


@api_tool_decorator()
def getDeviceById(deviceToUse, maxAttempt=Globals.MAX_RETRY):
    """ Make a API call to get a Device belonging to the Enterprise by its Id """
    try:
        api_instance = esperclient.DeviceApi(
            esperclient.ApiClient(Globals.configuration)
        )
        api_response_list = []
        api_response = None
        threads = []
        if type(deviceToUse) == list:
            num = 0
            for device in deviceToUse:
                if num == 0:
                    api_response, api_response_list = getDeviceByIdHelper(
                        device,
                        api_instance,
                        api_response_list,
                        api_response,
                        maxAttempt,
                    )
                else:
                    thread = threading.Thread(
                        target=getDeviceByIdHelper,
                        args=(
                            device,
                            api_instance,
                            api_response_list,
                            api_response,
                            maxAttempt,
                        ),
                    )
                    thread.start()
                    threads.append(thread)
                    limitActiveThreads(threads)
        else:
            api_response, api_response_list = getDeviceByIdHelper(
                deviceToUse, api_instance, api_response_list, api_response, maxAttempt
            )
        joinThreadList(threads)
        if api_response and api_response_list:
            api_response.results = api_response_list
        elif api_response:
            api_response.results = [api_response]
        postEventToFrame(eventUtil.myEVT_LOG, "---> Device API Request Finished")
        return api_response
    except ApiException as e:
        print("Exception when calling DeviceApi->get_device_by_id: %s\n" % e)
        ApiToolLog().LogError(e)


def getDeviceByIdHelper(
    device, api_instance, api_response_list, api_response, maxAttempt=Globals.MAX_RETRY
):
    for attempt in range(maxAttempt):
        try:
            api_response = api_instance.get_device_by_id(
                Globals.enterprise_id, device_id=device
            )
            ApiToolLog().LogApiRequestOccurrence(
                "getDeviceById",
                api_instance.get_device_by_id,
                Globals.PRINT_API_LOGS,
            )
            break
        except Exception as e:
            if attempt == maxAttempt - 1:
                ApiToolLog().LogError(e)
                raise e
            time.sleep(Globals.RETRY_SLEEP)
    if api_response:
        api_response_list.append(api_response)

    return api_response, api_response_list


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


def getUserBody(user):
    body = {}
    userKeys = user.keys()
    body["first_name"] = user["firstname"] if "firstname" in userKeys else ""
    body["last_name"] = user["lastname"] if "lastname" in userKeys else ""
    body["username"] = (
        user["username"]
        if "username" in userKeys
        else (body["first_name"] + body["last_name"])
    )
    body["password"] = user["password"]
    body["profile"] = {}
    body["email"] = user["email"]
    if "role" in userKeys:
        body["profile"]["role"] = user["role"]
    else:
        body["profile"]["role"] = "Group Viewer"
    body["profile"]["groups"] = user["groups"]
    if type(body["profile"]["groups"]) == str:
        body["profile"]["groups"] = list(body["profile"]["groups"])
    groups = []
    for group in body["profile"]["groups"]:
        if isApiKey(group):
            groups.append(group)
        else:
            resp = getAllGroups(name=group)
            if resp and resp.results:
                for gp in resp.results:
                    groups.append(gp.id)
    body["profile"]["groups"] = groups
    body["profile"]["enterprise"] = Globals.enterprise_id
    return body


def createNewUser(user):
    tenant = Globals.configuration.host.replace("https://", "").replace(
        "-api.esper.cloud/api", ""
    )
    url = "https://{tenant}-api.esper.cloud/api/user/".format(tenant=tenant)
    body = getUserBody(user)
    resp = performPostRequestWithRetry(url, headers=getHeader(), json=body)
    return resp


def modifyUser(user):
    tenant = Globals.configuration.host.replace("https://", "").replace(
        "-api.esper.cloud/api", ""
    )
    url = "https://{tenant}-api.esper.cloud/api/user/".format(tenant=tenant)
    users = performGetRequestWithRetry(url, headers=getHeader()).json()
    userId = ""
    for usr in users["results"]:
        if usr["username"] == user["username"]:
            userId = usr["id"]
            break
    resp = None
    if userId:
        url = "https://{tenant}-api.esper.cloud/api/user/{id}/".format(
            tenant=tenant, id=userId
        )
        body = getUserBody(user)
        resp = performPatchRequestWithRetry(url, headers=getHeader(), json=body)
    return resp


def deleteUser(user):
    tenant = Globals.configuration.host.replace("https://", "").replace(
        "-api.esper.cloud/api", ""
    )
    url = "https://{tenant}-api.esper.cloud/api/user/".format(tenant=tenant)
    users = performGetRequestWithRetry(url, headers=getHeader()).json()
    userId = ""
    for usr in users["results"]:
        if usr["username"] == user["username"]:
            userId = usr["id"]
            break
    resp = None
    if userId:
        url = "https://{tenant}-api.esper.cloud/api/user/{id}/".format(
            tenant=tenant, id=userId
        )
        resp = performDeleteRequestWithRetry(url, headers=getHeader())
    return resp


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


def setDeviceDisabled(deviceId):
    return patchInfo("", deviceId, jsonData={"state": 20})

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