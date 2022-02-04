import threading
import time
import Common.Globals as Globals
import esperclient


from Common.decorator import api_tool_decorator
from Utility import EventUtility
from Utility.ApiToolLogging import ApiToolLog
from Utility.EsperAPICalls import getInfo, patchInfo
from Utility.Resource import joinThreadList, limitActiveThreads, postEventToFrame

from esperclient.rest import ApiException


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
                    EventUtility.myEVT_LOG,
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
