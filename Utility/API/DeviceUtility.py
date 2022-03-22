import threading
import time
import Common.Globals as Globals
import esperclient


from Common.decorator import api_tool_decorator
from Utility import EventUtility, wxThread
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.API.EsperAPICalls import getInfo, patchInfo
from Utility.Resource import enforceRateLimit, getHeader, joinThreadList, limitActiveThreads, postEventToFrame

from esperclient.rest import ApiException

from Utility.Web.WebRequests import performGetRequestWithRetry

@api_tool_decorator()
def getDeviceDetail(deviceId):
    return getInfo("?format=json&show_policy=true", deviceId)


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
        postEventToFrame(EventUtility.myEVT_LOG, "---> Device API Request Finished")
        return api_response
    except ApiException as e:
        raise Exception("Exception when calling DeviceApi->get_all_devices: %s\n" % e)


def get_all_devices_helper(
    groupToUse, limit, offset, maxAttempt=Globals.MAX_RETRY, responses=None
):
    url = (
        Globals.BASE_REQUEST_URL.format(
            configuration_host=Globals.configuration.host,
            enterprise_id=Globals.enterprise_id,
        )
        + "device/?limit=%s&offset=%s" % (limit, offset)
    )
    api_response = performGetRequestWithRetry(url, getHeader(), maxRetry=maxAttempt)
    if api_response.status_code < 300:
        api_response = api_response.json()
        if type(responses) == list:
            responses.append(api_response)
    return api_response


def get_all_devices(
    groupToUse, limit, offset, fetchAll=False, maxAttempt=Globals.MAX_RETRY
):
    response = get_all_devices_helper(groupToUse, limit, offset, maxAttempt)
    if Globals.GROUP_FETCH_ALL or fetchAll:
        devices = getAllDevicesFromOffsets(response, groupToUse, maxAttempt)
        if hasattr(response, "results"):
            response.results = response.results + devices
            response.next = None
            response.prev = None
        elif type(response) is dict and "results" in response:
            response["results"] = response["results"] + devices
            response["next"] = None
            response["prev"] = None
            print(len(response["results"]))
    return response


def fetchDevicesFromGroup(
    groupToUse, limit, offset, fetchAll=False, maxAttempt=Globals.MAX_RETRY
):
    threads = []
    api_response = None
    for group in groupToUse:
        thread = wxThread.GUIThread(
            None,
            fetchDevicesFromGroupHelper,
            (group, limit, offset, fetchAll, maxAttempt),
            name="fetchDevicesFromGroupHelper",
        )
        thread.start()
        threads.append(thread)
        limitActiveThreads(threads, max_alive=(Globals.MAX_THREAD_COUNT))
    joinThreadList(threads)

    for thread in threads:
        if api_response is None:
            api_response = thread.result
        elif hasattr(thread.result, "results"):
            api_response.results += thread.result.results
        else:
            api_response["results"] += thread.result["results"]

    return api_response


def fetchDevicesFromGroupHelper(
    group, limit, offset, fetchAll=False, maxAttempt=Globals.MAX_RETRY
):
    api_response = None
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
    count = None
    if hasattr(api_response, "count"):
        count = api_response.count
    elif type(api_response) is dict and "count" in api_response:
        count = api_response["count"]
    apiNext = None
    if hasattr(api_response, "next"):
        apiNext = api_response.next
    elif type(api_response) is dict and "next" in api_response:
        apiNext = api_response["next"]
    if apiNext:
        respOffset = apiNext.split("offset=")[-1].split("&")[0]
        respOffsetInt = int(respOffset)
        respLimit = apiNext.split("limit=")[-1].split("&")[0]
        while int(respOffsetInt) < count and int(respLimit) < count:
            thread = threading.Thread(
                target=get_all_devices_helper,
                args=(group, respLimit, str(respOffsetInt), maxAttempt, responses),
            )
            threads.append(thread)
            thread.start()
            respOffsetInt += int(respLimit)
            limitActiveThreads(threads, max_alive=(Globals.MAX_THREAD_COUNT))
        joinThreadList(threads)
        obtained = sum(len(v["results"]) for v in responses) + int(respOffset)
        remainder = count - obtained
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
        if resp and hasattr(resp, "results") and resp.results:
            devices += resp.results
        elif type(resp) is dict and "results" in resp and resp["results"]:
            devices += resp["results"]
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
        postEventToFrame(EventUtility.myEVT_LOG, "---> Device API Request Finished")
        return api_response
    except ApiException as e:
        print("Exception when calling DeviceApi->get_device_by_id: %s\n" % e)
        ApiToolLog().LogError(e)


def getDeviceByIdHelper(
    device, api_instance, api_response_list, api_response, maxAttempt=Globals.MAX_RETRY
):
    for attempt in range(maxAttempt):
        try:
            enforceRateLimit()
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


def setDeviceDisabled(deviceId):
    return patchInfo("", deviceId, jsonData={"state": 20})
