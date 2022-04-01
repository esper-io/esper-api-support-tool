#!/usr/bin/env python

import Common.Globals as Globals
from Utility.API.GroupUtility import getAllGroups

from Utility.Resource import (
    getHeader,
    isApiKey,
)

from Utility.Web.WebRequests import (
    performDeleteRequestWithRetry,
    performGetRequestWithRetry,
    performPatchRequestWithRetry,
    performPostRequestWithRetry,
)


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
            if resp and resp.results:
                for gp in resp.results:
                    groups.append(gp.id)
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
