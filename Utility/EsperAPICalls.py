#!/usr/bin/env python


from datetime import datetime, timedelta
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
    try:
        json_resp = resp.json()
    except:
        pass
    logBadResponse(url, resp, json_resp)

    return json_resp


@api_tool_decorator()
def getDeviceDetail(deviceId):
    return getInfo("/?format=json&show_policy=true", deviceId)


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


@api_tool_decorator()
def iskioskmode(deviceid):
    """Checks If Device Is In Kiosk Mode"""
    kioskmode = False
    json_resp = getInfo(Globals.BASE_REQUEST_EXTENSION, deviceid)
    if json_resp["current_app_mode"] == 0:
        kioskmode = True
    return kioskmode


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
def getdevicetags(deviceid):
    """Retrieves Device Tags"""
    tags = ""
    json_resp = getInfo(Globals.BASE_REQUEST_EXTENSION, deviceid)
    if "tags" in json_resp:
        tags = json_resp["tags"]
    return tags


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
                if entry not in Globals.frame.sidePanel.selectedDeviceApps and (
                    "isValid" in entry and entry["isValid"]
                ):
                    Globals.frame.sidePanel.selectedDeviceApps.append(entry)
                if entry not in Globals.frame.sidePanel.enterpriseApps and (
                    "isValid" in entry and entry["isValid"]
                ):
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
                entry = getAppDictEntry(app, False)
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
            if (
                entry
                and entry not in Globals.frame.sidePanel.knownApps
                and not Globals.frame.sidePanel.selectedDevicesList
                and ("isValid" in entry and entry["isValid"])
            ):
                Globals.frame.sidePanel.knownApps.append(entry)
    return applist, json_resp


@api_tool_decorator()
def getLatestEvent(deviceId):
    json_resp = getInfo(Globals.DEVICE_STATUS_REQUEST_EXTENSION, deviceId)
    respData = None
    if json_resp and "results" in json_resp and json_resp["results"]:
        respData = json_resp["results"][0]["data"]
    return respData


@api_tool_decorator()
def getkioskmodeapp(deviceid):
    """Retrieves The Kiosk Mode Application ID"""
    json_resp = getInfo(Globals.DEVICE_STATUS_REQUEST_EXTENSION, deviceid)
    respData = None
    if json_resp and "results" in json_resp and json_resp["results"]:
        respData = json_resp["results"][0]["data"]
    appName = ""
    if respData and "kioskAppName" in respData:
        appName = respData["kioskAppName"]
    return appName


@api_tool_decorator()
def getNetworkInfo(deviceid):
    """Retrieves The Kiosk Mode Application ID"""
    json_resp = getInfo(Globals.DEVICE_STATUS_REQUEST_EXTENSION, deviceid)
    respData = None
    if json_resp and "results" in json_resp and json_resp["results"]:
        respData = json_resp["results"][0]["data"]
    network_event = ""
    if respData and "networkEvent" in respData:
        network_event = respData["networkEvent"]
    return network_event


@api_tool_decorator()
def getLocationInfo(deviceid):
    """Retrieves The Kiosk Mode Application ID"""
    json_resp = getInfo(Globals.DEVICE_STATUS_REQUEST_EXTENSION, deviceid)
    respData = None
    if json_resp and "results" in json_resp and json_resp["results"]:
        respData = json_resp["results"][0]["data"]
    location_event = ""
    if respData and "locationEvent" in respData:
        location_event = respData["locationEvent"]
    return location_event, respData


@api_tool_decorator()
def setdevicetags(deviceid, tags):
    """Pushes New Tag To Device"""
    json_resp = patchInfo(Globals.BASE_REQUEST_EXTENSION, deviceid, tags)
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
                ApiToolLog().LogApiRequestOccurrence(
                    "getDeviceGroupForHost",
                    api_instance.get_group_by_id,
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
def getAllDevices(groupToUse, limit=None, offset=None, maxAttempt=Globals.MAX_RETRY):
    """ Make a API call to get all Devices belonging to the Enterprise """
    if not limit:
        limit = Globals.limit
    if not offset:
        offset = Globals.offset
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
                            limit = int(limit / 4)
                            Globals.limit = limit
                            postEventToFrame(
                                eventUtil.myEVT_LOG,
                                "---> Encountered a 504 error, retrying with lower limit: %s"
                                % limit,
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
                        limit = int(limit / 4)
                        Globals.limit = limit
                        postEventToFrame(
                            eventUtil.myEVT_LOG,
                            "---> Encountered a 504 error, retrying with lower limit: %s"
                            % limit,
                        )
                    time.sleep(Globals.RETRY_SLEEP)
        postEventToFrame(eventUtil.myEVT_LOG, "---> Device API Request Finished")
        return api_response
    except ApiException as e:
        raise Exception("Exception when calling DeviceApi->get_all_devices: %s\n" % e)


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
            postEventToFrame(eventUtil.myEVT_LOG, "---> App API Request Finished")
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
                    is_hidden=False,
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
        else:
            for attempt in range(maxAttempt):
                try:
                    api_response = api_instance.get_device_by_id(
                        Globals.enterprise_id, device_id=deviceToUse
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
        if api_response and api_response_list:
            api_response.results = api_response_list
        elif api_response:
            api_response.results = [api_response]
        postEventToFrame(eventUtil.myEVT_LOG, "---> Device API Request Finished")
        return api_response
    except ApiException as e:
        print("Exception when calling DeviceApi->get_device_by_id: %s\n" % e)
        ApiToolLog().LogError(e)


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


@api_tool_decorator()
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


@api_tool_decorator()
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
    if package_name:
        url = "https://{tenant}-api.esper.cloud/api/v1/enterprise/{ent_id}/application/?package_name={pkg}".format(
            tenant=Globals.configuration.host.split("-api")[0].replace("https://", ""),
            ent_id=Globals.enterprise_id,
            pkg=package_name,
        )
    else:
        url = "https://{tenant}-api.esper.cloud/api/v1/enterprise/{ent_id}/application/".format(
            tenant=Globals.configuration.host.split("-api")[0].replace("https://", ""),
            ent_id=Globals.enterprise_id,
        )
    resp = performGetRequestWithRetry(url, headers=getHeader())
    jsonResp = resp.json()
    logBadResponse(url, resp, jsonResp, displayMsgBox=True)
    return jsonResp


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
            ApiToolLog().LogApiRequestOccurrence(
                "getAppVersion", api_instance.get_app_version, Globals.PRINT_API_LOGS
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
        if len(group) == 36 and "-" in group:
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
            if (
                "latest_version" in app
                and "icon_url" in app["latest_version"]
                and app["latest_version"]["icon_url"]
                and "amazonaws" in app["latest_version"]["icon_url"]
            ) or (
                "versions" in app
                and "icon_url" in app["versions"]
                and app["versions"]["icon_url"]
                and "amazonaws" in app["versions"]["icon_url"]
            ):
                entry["isValid"] = True
            else:
                validApp = getApplication(entry["id"])
                if hasattr(validApp, "results"):
                    validApp = validApp.results[0] if validApp.results else validApp

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
