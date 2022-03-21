import threading
import time
import Common.Globals as Globals
import esperclient


from Common.decorator import api_tool_decorator
from Utility import EventUtility, wxThread
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.API.EsperAPICalls import getInfo, patchInfo
from Utility.Resource import getHeader, joinThreadList, limitActiveThreads, postEventToFrame

from esperclient.rest import ApiException

from Utility.Web.WebRequests import performGetRequestWithRetry


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
def getBlueprint(id):
    url = "{baseUrl}/v0/enterprise/{enterprise_id}/blueprint/{id}/".format(
        baseUrl=Globals.configuration.host,
        enterprise_id=Globals.enterprise_id,
        id=id
    )
    resp = performGetRequestWithRetry(url, headers=getHeader())
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
