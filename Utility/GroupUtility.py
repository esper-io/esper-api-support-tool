#!/usr/bin/env python

import json
import time

from esperclient.rest import ApiException
from Utility.ApiToolLogging import ApiToolLog
import esperclient
import Common.Globals as Globals

from Utility.Resource import getHeader, performPatchRequestWithRetry


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
