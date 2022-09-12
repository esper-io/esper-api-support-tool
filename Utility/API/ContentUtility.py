import Common.Globals as Globals
from Common.decorator import api_tool_decorator
from Utility.Resource import getHeader
from Utility.Web.WebRequests import (
    performGetRequestWithRetry,
    performPostRequestWithRetry,
)


@api_tool_decorator()
def getAllContent():
    url = "{baseUrl}/v0/enterprise/{enterprise_id}/content/".format(
        baseUrl=Globals.configuration.host, enterprise_id=Globals.enterprise_id
    )
    resp = performGetRequestWithRetry(url, headers=getHeader())
    return resp


@api_tool_decorator()
def getAllContentFromHost(host, enterprise, key):
    url = "{baseUrl}/v0/enterprise/{enterprise_id}/content/".format(
        baseUrl=host, enterprise_id=enterprise
    )
    resp = performGetRequestWithRetry(
        url,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    return resp


def uploadContentToHost(host, enterprise, key, file):
    url = "{baseUrl}/v0/enterprise/{enterprise_id}/content/upload/".format(
        baseUrl=host, enterprise_id=enterprise
    )
    resp = performPostRequestWithRetry(
        url,
        headers={
            "Authorization": "Bearer %s" % key,
        },
        files={"key": open(file, "rb")},
    )
    return resp
