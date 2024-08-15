#!/usr/bin/env python

import Common.Globals as Globals
from Utility import EventUtility
from Utility.API.GroupUtility import getAllGroups
from Utility.Resource import getHeader, isApiKey, postEventToFrame
from Utility.Web.WebRequests import (
    getAllFromOffsetsRequests,
    performDeleteRequestWithRetry,
    performGetRequestWithRetry,
    performPatchRequestWithRetry,
    performPostRequestWithRetry,
)


def getUsers(
    limit=Globals.limit,
    offset=0,
    maxAttempt=Globals.MAX_RETRY,
    responses=[],
):
    tenant = Globals.configuration.host.replace("https://", "").replace(
        "-api.esper.cloud/api", ""
    )
    url = "https://{tenant}-api.esper.cloud/api/user/?limit={limit}&offset={offset}&format=json&exclude_google_roles=true&exclude_enterprise_device_role=true&authn_user_id_null=false".format(
        tenant=tenant,
        limit=limit,
        offset=offset,
    )
    usersResp = performGetRequestWithRetry(
        url, headers=getHeader(), maxRetry=maxAttempt
    )
    resp = None
    if (
        usersResp
        and hasattr(usersResp, "status_code")
        and usersResp.status_code < 300
    ):
        resp = usersResp.json()
    if resp and responses is not None:
        responses.append(resp)
    return resp


def getPendingUsers(
    limit=Globals.limit,
    offset=0,
    maxAttempt=Globals.MAX_RETRY,
    responses=[],
):
    tenant = Globals.configuration.host.replace("https://", "").replace(
        "-api.esper.cloud/api", ""
    )
    url = "https://{tenant}-api.esper.cloud/api/authn2/v0/tenant/{enterprise_id}/invite?limit={limit}&offset={offset}&format=json&exclude_google_roles=true&exclude_enterprise_device_role=true&authn_user_id_null=true".format(
        tenant=tenant,
        enterprise_id=Globals.enterprise_id,
        limit=limit,
        offset=offset,
    )
    usersResp = performGetRequestWithRetry(
        url, headers=getHeader(), maxRetry=maxAttempt
    )
    resp = None
    if (
        usersResp
        and hasattr(usersResp, "status_code")
        and usersResp.status_code < 300
    ):
        resp = usersResp.json()
    if resp and responses is not None:
        responses.append(resp)
    return resp


def getAllUsers(tolerance=0):
    userResp = getUsers()
    users = getAllFromOffsetsRequests(userResp, tolarance=tolerance)
    if type(userResp) is dict and "results" in userResp:
        userResp["results"] = userResp["results"] + users
        userResp["next"] = None
        userResp["prev"] = None
    return userResp


def getAllPendingUsers(tolerance=0):
    userResp = getPendingUsers()
    users = getAllFromOffsetsRequests(userResp, tolarance=tolerance)
    if type(userResp) is dict and "userinvites" in userResp:
        userResp["userinvites"] = userResp["userinvites"] + users
        userResp["next"] = None
        userResp["prev"] = None
    return userResp
