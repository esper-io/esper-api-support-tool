import Common.Globals as Globals

from Common.decorator import api_tool_decorator
from Utility.Resource import getHeader

from Utility.Web.WebRequests import performGetRequestWithRetry, performPostRequestWithRetry


def checkBlueprintsIsEnabled():
    enabled = False
    resp = getAllBlueprints()
    if hasattr(resp, "status_code") and resp.status_code < 300:
        enabled = True
    return enabled


@api_tool_decorator()
def getAllBlueprints():
    url = "{baseUrl}/v0/enterprise/{enterprise_id}/blueprint/".format(
        baseUrl=Globals.configuration.host,
        enterprise_id=Globals.enterprise_id
    )
    resp = performGetRequestWithRetry(url, headers=getHeader())
    return resp


@api_tool_decorator()
def getAllBlueprintsFromHost(host, key, enterprise):
    url = "{baseUrl}/v0/enterprise/{enterprise_id}/blueprint/".format(
        baseUrl=host,
        enterprise_id=enterprise
    )
    resp = performGetRequestWithRetry(url, headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    })
    return resp


@api_tool_decorator()
def getBlueprint(id):
    url = "{baseUrl}/v0/enterprise/{enterprise_id}/blueprint/{id}/".format(
        baseUrl=Globals.configuration.host,
        enterprise_id=Globals.enterprise_id,
        id=id
    )
    resp = performGetRequestWithRetry(url, headers=getHeader())
    return resp



@api_tool_decorator()
def getAllBlueprintFromHost(host, key, enterprise, id):
    url = "{baseUrl}/v0/enterprise/{enterprise_id}/blueprint/{id}".format(
        baseUrl=host,
        enterprise_id=enterprise,
        id=id
    )
    resp = performGetRequestWithRetry(url, headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    })
    return resp


@api_tool_decorator()
def getBlueprintRevisions(id):
    url = "{baseUrl}/v0/enterprise/{enterprise_id}/blueprint/{id}/revisions/".format(
        baseUrl=Globals.configuration.host,
        enterprise_id=Globals.enterprise_id,
        id=id
    )
    resp = performGetRequestWithRetry(url, headers=getHeader())
    return resp


@api_tool_decorator()
def getBlueprintRevision(blueprint_id, revision_id):
    url = "{baseUrl}/v0/enterprise/{enterprise_id}/blueprint/{blueprintId}/revisions/{revisionId}/".format(
        baseUrl=Globals.configuration.host,
        enterprise_id=Globals.enterprise_id,
        blueprintId=blueprint_id,
        revisionId=revision_id
    )
    resp = performGetRequestWithRetry(url, headers=getHeader())
    return resp


@api_tool_decorator()
def getBlueprintRevision(groupId):
    url = "{baseUrl}/enterprise/{enterprise_id}/devicegroup/{group_id}/blueprint/".format(
        baseUrl=Globals.configuration.host,
        enterprise_id=Globals.enterprise_id,
        group_id=groupId
    )
    resp = performGetRequestWithRetry(url, headers=getHeader())
    return resp


@api_tool_decorator()
def getGroupBlueprint(host, key, enterprise, groupId):
    url = "{baseUrl}/enterprise/{enterprise_id}/devicegroup/{group_id}/blueprint/".format(
        baseUrl=host,
        enterprise_id=enterprise,
        group_id=groupId
    )
    resp = performGetRequestWithRetry(url, headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    })
    return resp


@api_tool_decorator()
def getGroupBlueprintDetail(host, key, enterprise, groupId, blueprintId):
    url = "{baseUrl}/enterprise/{enterprise_id}/devicegroup/{group_id}/blueprint/{blueprint_id}".format(
        baseUrl=host,
        enterprise_id=enterprise,
        group_id=groupId,
        blueprint_id=blueprintId
    )
    resp = performGetRequestWithRetry(url, headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    })
    return resp


@api_tool_decorator()
def createBlueprintForHost(host, key, enterprise, groupId, body):
    url = "{baseUrl}/enterprise/{enterprise_id}/devicegroup/{group_id}/blueprint/".format(
        baseUrl=host,
        enterprise_id=enterprise,
        group_id=groupId
    )
    resp = performPostRequestWithRetry(url, headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }, json=body)
    return resp
