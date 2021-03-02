import Common.Globals as Globals
import requests

from Utility.EsperAPICalls import getHeader, logBadResponse


def preformEqlSearch(query, who, returnJson=False):
    headers = getHeader()

    url = "https://{host}-api.esper.cloud/api/v0/{whom}/search/?q={query}".format(
        host=Globals.configuration.host.split("-api")[0].replace("https://", ""),
        whom=who,
        query=query,
    )

    resp = requests.get(url, headers=headers)
    jsonResp = resp.json()
    logBadResponse(url, resp, jsonResp)

    if returnJson:
        return jsonResp
    else:
        return resp


def fetchCollectionList():
    # GET /api/v0/enterprise/{enterprise_id}/collection/
    headers = getHeader()

    url = "https://{host}-api.esper.cloud/api/v0/enterprise/{enterprise_id}/collection/".format(
        host=Globals.configuration.host.split("-api")[0].replace("https://", ""),
        enterprise_id=Globals.enterprise_id,
    )

    resp = requests.get(url, headers=headers)
    jsonResp = resp.json()
    logBadResponse(url, resp, jsonResp)

    res = []
    [res.append(x["name"]) for x in jsonResp["results"] if x["name"] not in res]
    return jsonResp, res


def createCollection(jsonData, returnJson=False):
    # POST /api/v0/enterprise/{enterprise_id}/collection/
    headers = getHeader()

    url = "https://{host}-api.esper.cloud/api/v0/enterprise/{enterprise_id}/collection/".format(
        host=Globals.configuration.host.split("-api")[0].replace("https://", ""),
        enterprise_id=Globals.enterprise_id,
    )

    resp = requests.post(url, headers=headers, json=jsonData)
    jsonResp = resp.json()
    logBadResponse(url, resp, jsonResp)

    if returnJson:
        return jsonResp
    else:
        return resp


def retrieveCollection(collectionId, returnJson=False):
    # GET /api/v0/enterprise/{enterprise_id}/collection/<id>
    headers = getHeader()

    url = "https://{host}-api.esper.cloud/api/v0/enterprise/{enterprise_id}/collection/{id}".format(
        host=Globals.configuration.host.split("-api")[0].replace("https://", ""),
        enterprise_id=Globals.enterprise_id,
        id=collectionId,
    )

    resp = requests.get(url, headers=headers)
    jsonResp = resp.json()
    logBadResponse(url, resp, jsonResp)

    if returnJson:
        return jsonResp
    else:
        return resp


def updateCollection(collectionId, jsonData, returnJson=False):
    # PUT /api/v0/enterprise/{enterprise_id}/collection/<id>
    headers = getHeader()

    url = "https://{host}-api.esper.cloud/api/v0/enterprise/{enterprise_id}/collection/{id}".format(
        host=Globals.configuration.host.split("-api")[0].replace("https://", ""),
        enterprise_id=Globals.enterprise_id,
        id=collectionId,
    )

    resp = requests.post(url, headers=headers, json=jsonData)
    jsonResp = resp.json()
    logBadResponse(url, resp, jsonResp)

    if returnJson:
        return jsonResp
    else:
        return resp


def deleteCollection(collectionId, returnJson=False):
    # DELETE /api/v0/enterprise/{enterprise_id}/collection/<id>
    headers = getHeader()

    url = "https://{host}-api.esper.cloud/api/v0/enterprise/{enterprise_id}/collection/{id}".format(
        host=Globals.configuration.host.split("-api")[0].replace("https://", ""),
        enterprise_id=Globals.enterprise_id,
        id=collectionId,
    )

    resp = requests.delete(url, headers=headers)
    jsonResp = resp.json()
    logBadResponse(url, resp, jsonResp)

    if returnJson:
        return jsonResp
    else:
        return resp
