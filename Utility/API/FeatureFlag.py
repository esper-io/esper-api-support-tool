import Common.Globals as Globals

from Common.decorator import api_tool_decorator
from Utility.Resource import getHeader
from Utility.Web.WebRequests import performGetRequestWithRetry


@api_tool_decorator()
def getFeatureFlags(returnJson=False):
    url = "{baseUrl}/feature-flags/".format(baseUrl=Globals.configuration.host)
    resp = performGetRequestWithRetry(url, headers=getHeader())

    if returnJson:
        return resp.json()
    else:
        return resp


@api_tool_decorator()
def getFeatureFlagsForTenant(host, header, returnJson=False):
    url = "{baseUrl}/feature-flags/".format(baseUrl=host)
    resp = performGetRequestWithRetry(url, headers=header, maxRetry=2)

    if returnJson:
        return resp.json()
    else:
        return resp
