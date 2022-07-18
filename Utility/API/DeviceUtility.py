import threading
import time
import Common.Globals as Globals


from Common.decorator import api_tool_decorator
from Utility import EventUtility
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.API.EsperAPICalls import getInfo, patchInfo
from Utility.Resource import (
    getHeader,
    joinThreadList,
    limitActiveThreads,
    postEventToFrame,
)

from esperclient.rest import ApiException

from Utility.Web.WebRequests import (
    getAllFromOffsetsRequests,
    performGetRequestWithRetry,
)


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
def getAllDevices(
    groupToUse,
    limit=None,
    offset=None,
    fetchAll=False,
    maxAttempt=Globals.MAX_RETRY,
    tolarance=0,
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
                groupToUse, limit, offset, fetchAll, maxAttempt, tolarance
            )
        else:
            api_response = get_all_devices(
                groupToUse, limit, offset, fetchAll, maxAttempt, tolarance
            )
        postEventToFrame(EventUtility.myEVT_LOG, "---> Device API Request Finished")
        return api_response
    except ApiException as e:
        raise Exception("Exception when calling DeviceApi->get_all_devices: %s\n" % e)


def get_all_devices_helper(
    groupToUse, limit, offset, maxAttempt=Globals.MAX_RETRY, responses=None
):
    extention = "device/?limit=%s&offset=%s" % (limit, offset)
    if groupToUse:
        extention = "device/?group=%s&limit=%s&offset=%s" % (groupToUse, limit, offset)
    url = (
        Globals.BASE_REQUEST_URL.format(
            configuration_host=Globals.configuration.host,
            enterprise_id=Globals.enterprise_id,
        )
        + extention
    )
    api_response = performGetRequestWithRetry(url, getHeader(), maxRetry=maxAttempt)
    if api_response.status_code < 300:
        api_response = api_response.json()
        if type(responses) == list:
            responses.append(api_response)
    return api_response


def get_all_devices(
    groupToUse, limit, offset, fetchAll=False, maxAttempt=Globals.MAX_RETRY, tolarance=0
):
    response = get_all_devices_helper(groupToUse, limit, offset, maxAttempt)
    if Globals.GROUP_FETCH_ALL or fetchAll:
        devices = getAllFromOffsetsRequests(response, None, tolarance)
        if hasattr(response, "results"):
            response.results = response.results + devices
            response.next = None
            response.prev = None
        elif type(response) is dict and "results" in response:
            response["next"] = None
            response["prev"] = None
            for device in devices:
                if device not in response["results"]:
                    response["results"].append(device)
    return response


def fetchDevicesFromGroup(
    groupToUse, limit, offset, fetchAll=False, maxAttempt=Globals.MAX_RETRY, tolarance=0
):
    api_response = None
    for group in groupToUse:
        resp = fetchDevicesFromGroupHelper(
            group, limit, offset, fetchAll, maxAttempt, tolarance
        )

        if not api_response:
            api_response = resp
        elif hasattr(api_response, "result") and hasattr(
            api_response.result, "results"
        ):
            api_response.results += resp.results
        else:
            for device in resp["results"]:
                if device not in api_response["results"]:
                    api_response["results"].append(device)

    return api_response


def fetchDevicesFromGroupHelper(
    group, limit, offset, fetchAll=False, maxAttempt=Globals.MAX_RETRY, tolarance=0
):
    api_response = None
    for _ in range(maxAttempt):
        response = get_all_devices(
            group, limit, offset, fetchAll, maxAttempt, tolarance
        )
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
def getDeviceById(deviceToUse, maxAttempt=Globals.MAX_RETRY, tolerance=0):
    """ Make a API call to get a Device belonging to the Enterprise by its Id """
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
            api_response, api_response_list = getDeviceByIdHelper(
                deviceToUse, api_response_list, api_response, maxAttempt
            )
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
        postEventToFrame(EventUtility.myEVT_LOG, "---> Device API Request Finished")
        return api_response
    except ApiException as e:
        print("Exception when calling DeviceApi->get_device_by_id: %s\n" % e)
        ApiToolLog().LogError(e)


def getDeviceByIdHelper(
    device, api_response_list, api_response, maxAttempt=Globals.MAX_RETRY
):
    for attempt in range(maxAttempt):
        try:
            url = Globals.BASE_DEVICE_URL.format(
                configuration_host=Globals.configuration.host,
                enterprise_id=Globals.enterprise_id,
                device_id=device,
            )
            api_response = performGetRequestWithRetry(
                url, getHeader(), maxRetry=maxAttempt
            )
            if api_response.status_code < 300:
                api_response = api_response.json()
            break
        except Exception as e:
            if attempt == maxAttempt - 1:
                ApiToolLog().LogError(e)
                raise e
            if "429" not in str(e) and "Too Many Requests" not in str(e):
                time.sleep(Globals.RETRY_SLEEP)
            else:
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * (attempt + 1)
                )  # Sleep for a minute * retry number
    if api_response:
        api_response_list.append(api_response)

    return api_response, api_response_list


def setDeviceDisabled(deviceId):
    return patchInfo("", deviceId, jsonData={"state": 20})
