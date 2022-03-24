#!/usr/bin/env python

import json
import time

from esperclient.rest import ApiException
from Common.decorator import api_tool_decorator
from Utility import EventUtility
from Utility.Logging.ApiToolLogging import ApiToolLog
import esperclient
import Common.Globals as Globals

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


def moveGroup(groupId, deviceList, maxAttempt=Globals.MAX_RETRY):
    tenant = Globals.configuration.host.replace("https://", "").replace(
        "-api.esper.cloud/api", ""
    )
    url = "https://{tenant}-api.esper.cloud/api/enterprise/{enterprise}/devicegroup/{group}/?action=add".format(
        tenant=tenant, enterprise=Globals.enterprise_id, group=groupId
    )
    resp = None

    if type(deviceList) == list:
        body = {"device_ids": deviceList}
        resp = performPatchRequestWithRetry(url, headers=getHeader(), json=body)
    elif type(deviceList) == str:
        body = {"device_ids": [deviceList]}
        resp = performPatchRequestWithRetry(url, headers=getHeader(), json=body)
    return resp


def createGroup(groupName, groupParent, maxAttempt=Globals.MAX_RETRY):
    api_instance = esperclient.DeviceGroupApi(
        esperclient.ApiClient(Globals.configuration)
    )
    data = esperclient.DeviceGroupUpdate(name=groupName, parent=groupParent)
    try:
        # Create a device group
        api_response = None
        for attempt in range(maxAttempt):
            try:
                api_response = api_instance.create_group(Globals.enterprise_id, data)
                ApiToolLog().LogApiRequestOccurrence(
                    "create_group", api_instance.create_group, Globals.PRINT_API_LOGS
                )
                break
            except Exception as e:
                if attempt == maxAttempt - 1:
                    ApiToolLog().LogError(e)
                    return json.loads(e.body)
                time.sleep(Globals.RETRY_SLEEP)
        return api_response
    except ApiException as e:
        print("Exception when calling DeviceGroupApi->create_group: %s\n" % e)


def deleteGroup(group_id, maxAttempt=Globals.MAX_RETRY):
    api_instance = esperclient.DeviceGroupApi(
        esperclient.ApiClient(Globals.configuration)
    )
    try:
        # Create a device group
        api_response = None
        for attempt in range(maxAttempt):
            try:
                api_instance.delete_group(group_id, Globals.enterprise_id)
                ApiToolLog().LogApiRequestOccurrence(
                    "getAllGroups", api_instance.get_all_groups, Globals.PRINT_API_LOGS
                )
                break
            except Exception as e:
                if attempt == maxAttempt - 1:
                    ApiToolLog().LogError(e)
                    return json.loads(e.body)
                time.sleep(Globals.RETRY_SLEEP)
        return api_response
    except ApiException as e:
        print("Exception when calling DeviceGroupApi->create_group: %s\n" % e)


def renameGroup(groupId, newName):
    tenant = Globals.configuration.host.replace("https://", "").replace(
        "-api.esper.cloud/api", ""
    )
    url = "https://{tenant}-api.esper.cloud/api/enterprise/{enterprise}/devicegroup/{group}/".format(
        tenant=tenant, enterprise=Globals.enterprise_id, group=groupId
    )
    body = {"name": newName}
    resp = performPatchRequestWithRetry(url, headers=getHeader(), json=body)
    return resp


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


@api_tool_decorator(locks=[Globals.token_lock])
def getAllGroups(name="", limit=None, offset=None, maxAttempt=Globals.MAX_RETRY):
    """ Make a API call to get all Groups belonging to the Enterprise """
    Globals.token_lock.acquire()
    Globals.token_lock.release()
    if not Globals.IS_TOKEN_VALID:
        return
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
        postEventToFrame(EventUtility.myEVT_LOG, "---> Group API Request Finished")
        return api_response
    except ApiException as e:
        raise Exception(
            "Exception when calling DeviceGroupApi->get_all_groups: %s\n" % e
        )


@api_tool_decorator()
def getGroupById(group_id, limit=None, offset=None, maxAttempt=Globals.MAX_RETRY):
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
                api_response = api_instance.get_group_by_id(
                    Globals.enterprise_id,
                    group_id=group_id,
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
        postEventToFrame(EventUtility.myEVT_LOG, "---> Group API Request Finished")
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
