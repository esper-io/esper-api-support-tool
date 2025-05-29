#!/usr/bin/env python

import json
import time

import esperclient
from esperclient.rest import ApiException

import Common.Globals as Globals
from Common.decorator import api_tool_decorator
from Utility import EventUtility
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Resource import (enforceRateLimit, getHeader, logBadResponse,
                              postEventToFrame)
from Utility.Web.WebRequests import (fetchRequestWithOffsets,
                                     handleRequestError,
                                     performGetRequestWithRetry,
                                     performPatchRequestWithRetry)


def moveGroup(groupId, deviceList, maxAttempt=Globals.MAX_RETRY):
    tenant = Globals.configuration.host.replace("https://", "").replace("-api.esper.cloud/api", "")
    url = "https://{tenant}-api.esper.cloud/api/enterprise/{enterprise}/devicegroup/{group}/?action=add".format(
        tenant=tenant, enterprise=Globals.enterprise_id, group=groupId
    )
    resp = None
    body = None
    if type(deviceList) == list:
        body = {"device_ids": deviceList}
        resp = performPatchRequestWithRetry(url, headers=getHeader(), json=body)
    elif type(deviceList) == str:
        body = {"device_ids": [deviceList]}
        resp = performPatchRequestWithRetry(url, headers=getHeader(), json=body)
    postEventToFrame(
        EventUtility.myEVT_AUDIT,
        {"operation": "moveGroup", "data": body, "resp": resp},
    )
    return resp


def getGroupByIdURL(groupId):
    return "{tenant}/enterprise/{enterprise}/devicegroup/{group}/".format(
        tenant=Globals.configuration.host,
        enterprise=Globals.enterprise_id,
        group=groupId,
    )


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
        ApiToolLog().LogError(e, postStatus=False)
        logBadResponse(groupURL, resp, None)
    return None


def getGroupApiUrl(limit=Globals.limit, offset=0, name=""):
    url = "{tenant}/enterprise/{enterprise}/devicegroup/?limit={lim}&offset={page}".format(
        tenant=Globals.configuration.host,
        enterprise=Globals.enterprise_id,
        lim=limit if limit else Globals.limit,
        page=offset if offset else 0,
    )
    if name:
        url += "&name={}".format(name)
    return url


@api_tool_decorator(locks=[Globals.token_lock])
def getAllGroups(name="", limit=Globals.limit, offset=0, maxAttempt=Globals.MAX_RETRY, tolerance=0):
    """Make a API call to get all Groups belonging to the Enterprise"""
    return get_all_groups(name, limit, offset, maxAttempt, tolerance=tolerance)


def get_all_groups(
    name="",
    limit=Globals.limit,
    offset=0,
    maxAttempt=Globals.MAX_RETRY,
    tolerance=0,
):
    url = getGroupApiUrl(limit, offset, name)
    return fetchRequestWithOffsets(url, tolerance=tolerance)


@api_tool_decorator()
def getGroupById(group_id, limit=None, offset=None, maxAttempt=Globals.MAX_RETRY):
    """Make a API call to get all Groups belonging to the Enterprise"""
    if not limit:
        limit = Globals.limit
    if not offset:
        offset = Globals.offset
    try:
        api_instance = esperclient.DeviceGroupApi(esperclient.ApiClient(Globals.configuration))
        api_response = None
        for attempt in range(maxAttempt):
            try:
                enforceRateLimit()
                api_response = api_instance.get_group_by_id(
                    enterprise_id=Globals.enterprise_id,
                    group_id=group_id,
                    limit=limit,
                    offset=offset,
                )
                ApiToolLog().LogApiRequestOccurrence(
                    "getAllGroups",
                    api_instance.get_all_groups,
                    Globals.PRINT_API_LOGS,
                )
                break
            except Exception as e:
                handleRequestError(attempt, e, maxAttempt, raiseError=True)
        postEventToFrame(EventUtility.myEVT_LOG, "---> Group API Request Finished")
        return api_response
    except ApiException as e:
        raise Exception("Exception when calling DeviceGroupApi->get_all_groups: %s\n" % e)


@api_tool_decorator()
def getDeviceGroupsForHost(config, enterprise_id, maxAttempt=Globals.MAX_RETRY, tolerance=0):
    try:
        api_response = getDeviceGroupsForHostHelper(config, enterprise_id)
        if api_response and hasattr(api_response, "next") and api_response.next:
            offset = Globals.limit
            while offset < api_response.count:
                Globals.THREAD_POOL.enqueue(
                    getDeviceGroupsForHostHelper,
                    config,
                    enterprise_id,
                    Globals.limit,
                    offset,
                    maxAttempt,
                )
                offset += Globals.limit
            Globals.THREAD_POOL.join(tolerance)
            res = Globals.THREAD_POOL.results()
            for threadRes in res:
                if threadRes and hasattr(threadRes, "next") and threadRes.next:
                    api_response.results += threadRes.results
            obtained = len(api_response.results)
            remainder = api_response.count - obtained
            if remainder > 0:
                offset -= int(Globals.limit)
                offset += 1
                resp = getDeviceGroupsForHostHelper(config, enterprise_id, Globals.limit, offset, maxAttempt)
                if resp and hasattr(resp, "next") and resp.next:
                    api_response.results += resp.results
        return api_response
    except Exception as e:
        raise e


def getDeviceGroupsForHostHelper(
    config,
    enterprise_id,
    limit=Globals.limit,
    offset=Globals.offset,
    maxAttempt=Globals.MAX_RETRY,
):
    try:
        api_instance = esperclient.DeviceGroupApi(esperclient.ApiClient(config))
        api_response = None
        for attempt in range(maxAttempt):
            try:
                api_response = api_instance.get_all_groups(enterprise_id, limit=limit, offset=offset)
                ApiToolLog().LogApiRequestOccurrence(
                    "getDeviceGroupsForHost",
                    api_instance.get_all_groups,
                    Globals.PRINT_API_LOGS,
                )
                break
            except Exception as e:
                handleRequestError(attempt, e, maxAttempt, raiseError=True)
        return api_response
    except Exception as e:
        raise e


@api_tool_decorator()
def createDeviceGroupForHost(config, enterprise_id, group, maxAttempt=Globals.MAX_RETRY):
    try:
        api_instance = esperclient.DeviceGroupApi(esperclient.ApiClient(config))
        api_response = None
        for attempt in range(maxAttempt):
            try:
                api_response = api_instance.create_group(enterprise_id, data={"name": group})
                ApiToolLog().LogApiRequestOccurrence(
                    "createDeviceGroupForHost",
                    api_instance.create_group,
                    Globals.PRINT_API_LOGS,
                )
                break
            except Exception as e:
                handleRequestError(attempt, e, maxAttempt, raiseError=True)
        return api_response
    except Exception as e:
        raise e


def getProperGroupId(groups):
    properGroupList = []
    for group in groups:
        if len(group.split("-")) == 5:
            properGroupList.append(group)
        else:
            json_rsp = get_all_groups(name=group)
            if "results" in json_rsp and json_rsp["results"] and "id" in json_rsp["results"][0]["id"]:
                properGroupList.append(json_rsp["results"][0]["id"])
    return properGroupList
