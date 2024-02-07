#!/usr/bin/env python

import Common.Globals as Globals
from Utility import EventUtility
from Utility.API.GroupUtility import getAllGroups
from Utility.Resource import getHeader, isApiKey, postEventToFrame
from Utility.Web.WebRequests import (getAllFromOffsetsRequests,
                                     performDeleteRequestWithRetry,
                                     performGetRequestWithRetry,
                                     performPatchRequestWithRetry,
                                     performPostRequestWithRetry)


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
    if user["password"]:
        body["password"] = user["password"]
    body["profile"] = {}
    body["email"] = user["email"]
    body["is_active"] = True
    body["is_endpoint_creator"] = False
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
            if resp and hasattr(resp, "results") and resp.results:
                for gp in resp.results:
                    groups.append(gp.id)
            elif resp and type(resp) is dict and "results" in resp and resp["results"]:
                for gp in resp["results"]:
                    groups.append(gp["id"])
    body["profile"]["groups"] = groups
    body["profile"]["enterprise"] = Globals.enterprise_id
    body["profile"]["is_customer"] = True
    return body


def createNewUser(user):
    tenant = Globals.configuration.host.replace("https://", "").replace(
        "-api.esper.cloud/api", ""
    )
    url = "https://{tenant}-api.esper.cloud/api/user/".format(tenant=tenant)
    body = getUserBody(user)
    resp = performPostRequestWithRetry(url, headers=getHeader(), json=body)
    postEventToFrame(
        EventUtility.myEVT_AUDIT,
        {"operation": "CreateUser", "data": body, "resp": resp},
    )
    return resp


def modifyUser(allUsers, user):
    tenant = Globals.configuration.host.replace("https://", "").replace(
        "-api.esper.cloud/api", ""
    )
    userId = ""
    for usr in allUsers["results"]:
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
        postEventToFrame(
            EventUtility.myEVT_AUDIT,
            {"operation": "ModifyUser", "data": body, "resp": resp},
        )
    return resp


def deleteUser(allUsers, user):
    tenant = Globals.configuration.host.replace("https://", "").replace(
        "-api.esper.cloud/api", ""
    )
    userId = ""
    for usr in allUsers["results"]:
        if usr["username"] == user["username"]:
            userId = usr["id"]
            break
    resp = None
    if userId:
        url = "https://{tenant}-api.esper.cloud/api/user/{id}/".format(
            tenant=tenant, id=userId
        )
        resp = performDeleteRequestWithRetry(url, headers=getHeader())
        postEventToFrame(
            EventUtility.myEVT_AUDIT,
            {"operation": "DeleteUser", "data": user, "resp": resp},
        )
    return resp


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
    if usersResp and hasattr(usersResp, "status_code") and usersResp.status_code < 300:
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
    if usersResp and hasattr(usersResp, "status_code") and usersResp.status_code < 300:
        resp = usersResp.json()
    if resp and responses is not None:
        responses.append(resp)
    return resp


def getSpecificUser(
    id,
    limit=Globals.limit,
    offset=0,
    maxAttempt=Globals.MAX_RETRY,
):
    tenant = Globals.configuration.host.replace("https://", "").replace(
        "-api.esper.cloud/api", ""
    )
    url = "https://{tenant}-api.esper.cloud/api/user/{user_id}/?limit={limit}&offset={offset}".format(
        tenant=tenant,
        user_id=id,
        limit=limit,
        offset=offset,
    )
    usersResp = performGetRequestWithRetry(
        url, headers=getHeader(), maxRetry=maxAttempt
    )
    resp = None
    if usersResp and hasattr(usersResp, "status_code") and usersResp.status_code < 300:
        resp = usersResp.json()
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

def getUserInfo():
    tenant = Globals.configuration.host.replace("https://", "").replace(
        "-api.esper.cloud/api", ""
    )
    url = "https://{tenant}-api.esper.cloud/api/user_info/".format(
        tenant=tenant
    )
    userResp = performGetRequestWithRetry(
        url, headers=getHeader()
    )
    resp = None
    if userResp and hasattr(userResp, "json"):
        resp = userResp.json()
    return resp