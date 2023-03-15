#!/usr/bin/env python

import Common.Globals as Globals
from Common.decorator import api_tool_decorator
from Utility import EventUtility
from Utility.Resource import getHeader, logBadResponse, postEventToFrame
from Utility.Web.WebRequests import (
    performDeleteRequestWithRetry,
    performGetRequestWithRetry,
    performPatchRequestWithRetry,
    performPostRequestWithRetry,
)


@api_tool_decorator()
def preformEqlSearch(query, who, returnJson=False):
    # api/v0/enterprise/{ent-id}/collection/search/?q={eql_query}
    headers = getHeader()

    if not who:
        who = "collection"

    query = query.replace('"', "%22").replace(" ", "%20")

    url = "https://{host}-api.esper.cloud/api/v0/enterprise/{entId}/{whom}/search/?q={query}".format(
        host=Globals.configuration.host.split("-api")[0].replace("https://", ""),
        entId=Globals.enterprise_id,
        whom=who,
        query=query,
    )

    resp = performGetRequestWithRetry(url, headers=headers)
    jsonResp = resp.json()
    logBadResponse(url, resp, jsonResp, displayMsgBox=True)

    if returnJson:
        return jsonResp
    else:
        return resp


def checkCollectionIsEnabled():
    enabled = False
    resp = fetchCollectionList(returnResp=True)
    if hasattr(resp, "status_code") and resp.status_code < 300:
        enabled = True
    return enabled


@api_tool_decorator()
def fetchCollectionList(returnResp=False):
    # GET /api/v0/enterprise/{enterprise_id}/collection/
    headers = getHeader()
    if not headers:
        return None

    url = "https://{host}-api.esper.cloud/api/v0/enterprise/{enterprise_id}/collection/".format(
        host=Globals.configuration.host.split("-api")[0].replace("https://", ""),
        enterprise_id=Globals.enterprise_id,
    )

    resp = performGetRequestWithRetry(url, headers=headers)
    jsonResp = resp.json() if resp else None
    logBadResponse(url, resp, jsonResp, displayMsgBox=True)

    if returnResp:
        return resp

    res = []
    if jsonResp:
        [res.append(x["name"]) for x in jsonResp["results"] if x["name"] not in res]
    return jsonResp, res


@api_tool_decorator()
def createCollection(jsonData, returnJson=False):
    # POST /api/v0/enterprise/{enterprise_id}/collection/
    headers = getHeader()

    url = "https://{host}-api.esper.cloud/api/v0/enterprise/{enterprise_id}/collection/".format(
        host=Globals.configuration.host.split("-api")[0].replace("https://", ""),
        enterprise_id=Globals.enterprise_id,
    )

    resp = performPostRequestWithRetry(url, headers=headers, json=jsonData)
    jsonResp = None
    try:
        jsonResp = resp.json()
    except:
        pass
    logBadResponse(url, resp, jsonResp, displayMsgBox=True)
    postEventToFrame(EventUtility.EVT_AUDIT, {
        "operation": "CreateCollection",
        "data": jsonData,
        "resp": resp
    })

    if returnJson:
        return jsonResp
    else:
        return resp


# @api_tool_decorator()
# def retrieveCollection(collectionId, returnJson=False):
#     # GET /api/v0/enterprise/{enterprise_id}/collection/<id>
#     headers = getHeader()

#     url = "https://{host}-api.esper.cloud/api/v0/enterprise/{enterprise_id}/collection/{id}".format(
#         host=Globals.configuration.host.split("-api")[0].replace("https://", ""),
#         enterprise_id=Globals.enterprise_id,
#         id=collectionId,
#     )

#     resp = performGetRequestWithRetry(url, headers=headers)
#     jsonResp = None
#     try:
#         jsonResp = resp.json()
#     except:
#         pass
#     logBadResponse(url, resp, jsonResp, displayMsgBox=True)

#     if returnJson:
#         return jsonResp
#     else:
#         return resp


@api_tool_decorator()
def updateCollection(collectionId, jsonData, returnJson=False):
    # PATCH  /api/v0/enterprise/{enterprise_id}/collection/<id>
    headers = getHeader()

    url = "https://{host}-api.esper.cloud/api/v0/enterprise/{enterprise_id}/collection/{id}".format(
        host=Globals.configuration.host.split("-api")[0].replace("https://", ""),
        enterprise_id=Globals.enterprise_id,
        id=collectionId,
    )

    resp = performPatchRequestWithRetry(url, headers=headers, json=jsonData)
    jsonResp = None
    try:
        jsonResp = resp.json()
    except:
        pass
    logBadResponse(url, resp, jsonResp, displayMsgBox=True)
    postEventToFrame(EventUtility.EVT_AUDIT, {
        "operation": "UpdateCollection",
        "data": jsonData,
        "resp": resp
    })

    if returnJson:
        return jsonResp
    else:
        return resp


@api_tool_decorator()
def deleteCollection(collectionId, returnJson=False):
    # DELETE /api/v0/enterprise/{enterprise_id}/collection/<id>
    headers = getHeader()

    url = "https://{host}-api.esper.cloud/api/v0/enterprise/{enterprise_id}/collection/{id}".format(
        host=Globals.configuration.host.split("-api")[0].replace("https://", ""),
        enterprise_id=Globals.enterprise_id,
        id=collectionId,
    )

    resp = performDeleteRequestWithRetry(url, headers=headers)
    jsonResp = None
    try:
        jsonResp = resp.json()
    except:
        pass
    logBadResponse(url, resp, jsonResp, displayMsgBox=True)
    postEventToFrame(EventUtility.EVT_AUDIT, {
        "operation": "DeleteCollection",
        "data": collectionId,
        "resp": resp
    })

    if returnJson:
        return jsonResp
    else:
        return resp
