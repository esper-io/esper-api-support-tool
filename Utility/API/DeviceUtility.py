#!/usr/bin/env python


import Common.Globals as Globals
from Common.decorator import api_tool_decorator
from Utility import EventUtility
from Utility.API.EsperAPICalls import getInfo, patchInfo
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Resource import getHeader, is_uuid, postEventToFrame
from Utility.Web.WebRequests import (getAllFromOffsetsRequests,
                                     handleRequestError,
                                     performGetRequestWithRetry)


@api_tool_decorator()
def getDeviceDetail(deviceId):
    return getInfo("?format=json&show_policy=true", deviceId)


def getLatestEventApiUrl(deviceId):
    return (
        Globals.BASE_DEVICE_URL.format(
            configuration_host=Globals.configuration.host,
            enterprise_id=Globals.enterprise_id,
            device_id=deviceId,
        )
        + Globals.DEVICE_STATUS_REQUEST_EXTENSION
    )


@api_tool_decorator()
def getLatestEvent(deviceId):
    json_resp = getInfo(Globals.DEVICE_STATUS_REQUEST_EXTENSION, deviceId)
    respData = None
    if json_resp and "results" in json_resp and json_resp["results"]:
        results = json_resp["results"]
        if len(results) > 0 and isinstance(results[0], dict) and "data" in results[0]:
            respData = results[0]["data"]
    return respData


@api_tool_decorator()
def setdevicetags(deviceid, tags):
    """Pushes New Tag To Device"""
    json_resp = patchInfo(Globals.BASE_REQUEST_EXTENSION, deviceid, tags=tags)
    if json_resp and "tags" in json_resp:
        tags = json_resp["tags"]
    return tags


@api_tool_decorator()
def getAllDevices(
    groupToUse,
    limit=None,
    offset=None,
    fetchAll=True,
    maxAttempt=Globals.MAX_RETRY,
    tolarance=0,
    timeout=-1,
):
    """Make a API call to get all Devices belonging to the Enterprise"""
    if not limit:
        limit = Globals.limit
    if not offset:
        offset = Globals.offset
    try:
        api_response = None
        if type(groupToUse) == list:
            api_response = fetchDevicesFromGroup(
                groupToUse,
                limit,
                offset,
                fetchAll,
                maxAttempt,
                tolarance,
                timeout,
            )
        else:
            api_response = get_all_devices(
                groupToUse,
                limit,
                offset,
                fetchAll,
                maxAttempt,
                tolarance,
                timeout,
            )
        postEventToFrame(EventUtility.myEVT_LOG, "---> Device API Request Finished")
        return api_response
    except Exception as e:
        raise Exception("Exception when calling DeviceApi->get_all_devices: %s\n" % e)


def get_all_devices_helper(groupToUse, limit, offset, maxAttempt=Globals.MAX_RETRY, responses=None):
    # Safe access to frame configuration
    iosEnabled = False
    try:
        if (Globals.frame and 
            hasattr(Globals.frame, 'sidePanel') and 
            hasattr(Globals.frame.sidePanel, 'configChoice') and
            hasattr(Globals.frame, 'configMenuItem') and
            Globals.frame.configMenuItem):
            
            config_name = Globals.frame.configMenuItem.GetItemLabelText()
            config = Globals.frame.sidePanel.configChoice.get(config_name, {})
            iosEnabled = config.get("isIosEnabled", False)
    except (AttributeError, KeyError, TypeError) as e:
        ApiToolLog().LogError(f"Error accessing configuration: {str(e)}")
        iosEnabled = False

    if iosEnabled and Globals.PULL_APPLE_DEVICES:
        return get_all_ios_devices_helper(groupToUse, limit, offset, maxAttempt, responses)
    else:
        return get_all_android_devices_helper(groupToUse, limit, offset, maxAttempt, responses)


def get_all_android_devices_helper(groupToUse, limit, offset, maxAttempt=Globals.MAX_RETRY, responses=None):
    extention = "device/?limit=%s&offset=%s" % (limit, offset)
    if groupToUse.strip():
        extention = "device/?group=%s&limit=%s&offset=%s" % (
            groupToUse.strip(),
            limit,
            offset,
        )
    url = (
        Globals.BASE_REQUEST_URL.format(
            configuration_host=Globals.configuration.host,
            enterprise_id=Globals.enterprise_id,
        )
        + extention
    )
    api_response = performGetRequestWithRetry(url, getHeader(), maxRetry=maxAttempt)
    if api_response and api_response.status_code < 300:
        try:
            api_response = api_response.json()
            if type(responses) == list:
                responses.append(api_response)
        except (ValueError, TypeError, AttributeError) as e:
            ApiToolLog().LogError(f"Failed to parse device response JSON: {str(e)}")
            raise Exception(f"Failed to parse JSON response: {str(e)}")
    else:
        status_code = getattr(api_response, 'status_code', 'Unknown')
        content = getattr(api_response, 'content', 'No content')
        raise Exception("HTTP Response %s:\t\n%s" % (status_code, content))
    return api_response


def get_all_ios_devices_helper(groupToUse, limit, offset, maxAttempt=Globals.MAX_RETRY, responses=None):
    extention = "?limit=%s&offset=%s" % (limit, offset)
    if groupToUse.strip():
        extention += "&group_multi=%s" % (groupToUse.strip(),)
    url = "%s/v2/devices/%s" % (Globals.configuration.host, extention)
    api_response = performGetRequestWithRetry(url, getHeader(), maxRetry=maxAttempt)
    if api_response.status_code < 300:
        try:
            api_response = api_response.json()
            if "content" in api_response:
                api_response = api_response["content"]
        except (ValueError, TypeError, AttributeError) as e:
            ApiToolLog().LogError(f"Failed to parse iOS device response JSON: {str(e)}")
            raise Exception(f"Failed to parse JSON response: {str(e)}")
        if type(responses) == list:
            responses.append(api_response)
    else:
        raise Exception("HTTP Response %s:\t\n%s" % (api_response.status_code, api_response.content))
    return api_response


def get_all_devices(
    groupToUse,
    limit,
    offset,
    fetchAll=True,
    maxAttempt=Globals.MAX_RETRY,
    tolarance=0,
    timeout=-1,
):
    response = get_all_devices_helper(groupToUse, limit, offset, maxAttempt)
    if fetchAll:
        devices = getAllFromOffsetsRequests(response, None, tolarance, timeout)
        if type(response) is dict and "results" in response:
            response["next"] = None
            response["prev"] = None
            response["results"] = response["results"] + devices
    return response


def fetchDevicesFromGroup(
    groupToUse,
    limit,
    offset,
    fetchAll=True,
    maxAttempt=Globals.MAX_RETRY,
    tolarance=0,
    timeout=-1,
):
    api_response = None
    for group in groupToUse:
        resp = fetchDevicesFromGroupHelper(group, limit, offset, fetchAll, maxAttempt, tolarance, timeout)

        if not api_response:
            api_response = resp
        elif hasattr(api_response, "result") and hasattr(api_response.result, "results"):
            api_response.results += resp.results
        else:
            if resp and "content" in resp:
                resp = resp["content"]
            if resp and "results" in resp:
                for device in resp["results"]:
                    if device not in api_response["results"]:
                        api_response["results"].append(device)

    return api_response


def fetchDevicesFromGroupHelper(
    group,
    limit,
    offset,
    fetchAll=False,
    maxAttempt=Globals.MAX_RETRY,
    tolarance=0,
    timeout=-1,
):
    api_response = None
    for _ in range(maxAttempt):
        response = get_all_devices(group, limit, offset, fetchAll, maxAttempt, tolarance, timeout)
        if api_response:
            for device in response.results:
                if device not in api_response.results:
                    api_response.results.append(device)
            api_response.count = len(api_response.results)
        else:
            api_response = response
        break
    return api_response


@api_tool_decorator()
def getDeviceById(
    deviceToUse,
    maxAttempt=Globals.MAX_RETRY,
    tolerance=0,
    log=True,
    do_join=True,
):
    """Make a API call to get a Device belonging to the Enterprise by its Id"""
    try:
        api_response_list = []
        api_response = None
        if type(deviceToUse) == list:
            for device in deviceToUse:
                Globals.THREAD_POOL.enqueue(
                    getDeviceByIdHelper,
                    device,
                    api_response_list,
                    api_response,
                    maxAttempt,
                )
        else:
            api_response, api_response_list = getDeviceByIdHelper(deviceToUse, api_response_list, api_response, maxAttempt)
        if do_join:
            Globals.THREAD_POOL.join(tolerance=tolerance)
        Globals.THREAD_POOL.results()
        if api_response and api_response_list and hasattr(api_response, "results"):
            api_response.results = api_response_list
        elif api_response and hasattr(api_response, "results"):
            api_response.results = [api_response]
        elif api_response and api_response_list and type(api_response) == dict:
            api_response["results"] = api_response_list
        elif api_response and type(api_response) == dict:
            api_response["results"] = [api_response]
        elif not api_response and api_response_list:
            api_response = {
                "results": api_response_list,
                "next": None,
                "previous": None,
            }
        if log:
            postEventToFrame(EventUtility.myEVT_LOG, "---> Device API Request Finished")
        return api_response
    except Exception as e:
        print("Exception when calling DeviceApi->get_device_by_id: %s\n" % e)
        ApiToolLog().LogError(e, postStatus=False)


def getDeviceByIdHelper(device, api_response_list, api_response, maxAttempt=Globals.MAX_RETRY):
    for attempt in range(maxAttempt):
        try:
            url = Globals.BASE_DEVICE_URL.format(
                configuration_host=Globals.configuration.host,
                enterprise_id=Globals.enterprise_id,
                device_id=device,
            )
            api_response = performGetRequestWithRetry(url, getHeader(), maxRetry=maxAttempt)
            if api_response.status_code < 300:
                api_response = api_response.json()
            break
        except Exception as e:
            handleRequestError(attempt, e, maxAttempt, raiseError=True)
    if api_response:
        api_response_list.append(api_response)

    return api_response, api_response_list


def searchForDevice(
    search=None,
    imei=None,
    serial=None,
    name=None,
    group=None,
    state=None,
    brand=None,
    gms=None,
    tags=None,
):
    extention = ""

    if search is not None:
        if "?limit=" not in extention:
            extention += "?limit=%s&search=%s" % (Globals.limit, search)
        else:
            extention += "&search=%s" % (search)
    if imei is not None:
        if "?limit=" not in extention:
            extention += "?limit=%s&imei=%s" % (Globals.limit, imei)
        else:
            extention += "&imei=%s" % (imei)
    if serial is not None:
        if "?limit=" not in extention:
            extention += "?limit=%s&serial=%s" % (Globals.limit, serial)
        else:
            extention += "&serial=%s" % (serial)
    if name is not None:
        if "?limit=" not in extention:
            extention += "?limit=%s&name=%s" % (Globals.limit, name)
        else:
            extention += "&name=%s" % (name)
    if group is not None:
        if "?limit=" not in extention:
            extention += "?limit=%s&group=%s" % (Globals.limit, group)
        else:
            extention += "&group=%s" % (group)
    if state is not None:
        if "?limit=" not in extention:
            extention += "?limit=%s&state=%s" % (Globals.limit, state)
        else:
            extention += "&state=%s" % (state)
    if brand is not None:
        if "?limit=" not in extention:
            extention += "?limit=%s&brand=%s" % (Globals.limit, brand)
        else:
            extention += "&brand=%s" % (brand)
    if gms is not None:
        if "?limit=" not in extention:
            extention += "?limit=%s&is_gms=%s" % (Globals.limit, gms)
        else:
            extention += "&is_gms=%s" % (gms)
    if tags is not None:
        if "?limit=" not in extention:
            extention += "?limit=%s&tags=%s" % (Globals.limit, tags)
        else:
            extention += "&tags=%s" % (tags)

    url = ("%s/v2/devices/" % Globals.configuration.host) + extention
    api_response = performGetRequestWithRetry(url, getHeader())
    if api_response.status_code < 300:
        api_response = api_response.json()
        if "content" in api_response:
            api_response = api_response["content"]
    else:
        raise Exception("HTTP Response %s:\t\n%s" % (api_response.status_code, api_response.content))
    return api_response


def getProperDeviceId(devices):
    properDeviceList = []
    for device in devices:
        if is_uuid(device):  # len(device.split("-")) == 5:
            properDeviceList.append(device)
        else:
            json_rsp = searchForDevice(search=device)
            if "results" in json_rsp and json_rsp["results"] and "id" in json_rsp["results"][0]["id"]:
                properDeviceList.append(json_rsp["results"][0]["id"])
    return devices
