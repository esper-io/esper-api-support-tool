#!/usr/bin/env python

from Common.decorator import api_tool_decorator
from Utility import EventUtility
from Utility.Resource import postEventToFrame
from Utility.Web.WebRequests import (
    performGetRequestWithRetry,
    performPostRequestWithRetry,
)


@api_tool_decorator()
def getAllContentFromHost(host, enterprise, key):
    url = "{baseUrl}/v0/enterprise/{enterprise_id}/content/".format(baseUrl=host, enterprise_id=enterprise)
    resp = performGetRequestWithRetry(
        url,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    return resp


def uploadContentToHost(host, enterprise, key, file):
    url = "{baseUrl}/v0/enterprise/{enterprise_id}/content/upload/".format(baseUrl=host, enterprise_id=enterprise)
    file = {
        "Content-Disposition": 'form-data; name="key"; filename="%s"' % file,
        "key": open(file, "rb"),
        "Content-Type": "application/json",
    }
    resp = performPostRequestWithRetry(
        url,
        headers={
            "Authorization": "Bearer %s" % key,
        },
        files=file,
    )
    postEventToFrame(
        EventUtility.myEVT_AUDIT,
        {"operation": "UploadContent", "data": file, "resp": resp},
    )
    return resp
