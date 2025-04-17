#!/usr/bin/env python

import Common.Globals as Globals
from Utility.Resource import getHeader, getTenant
from Utility.Web.WebRequests import (fetchRequestWithOffsets,
                                     performGetRequestWithRetry)


def getUserAPIUrl(limit=Globals.limit, offset=0):
    url = "https://{tenant}-api.esper.cloud/api/user/?limit={limit}&offset={offset}&format=json&exclude_google_roles=true&exclude_enterprise_device_role=true&authn_user_id_null=false".format(
        tenant=getTenant(),
        limit=limit,
        offset=offset,
    )
    return url


def getPendingUsersAPIUrl(limit=Globals.limit, offset=0):
    url = "https://{tenant}-api.esper.cloud/api/authn2/v0/tenant/{enterprise_id}/invite?limit={limit}&offset={offset}&format=json&exclude_google_roles=true&exclude_enterprise_device_role=true&authn_user_id_null=true".format(
        tenant=getTenant(),
        enterprise_id=Globals.enterprise_id,
        limit=limit,
        offset=offset,
    )
    return url


def getAllUsers(limit=Globals.limit, offset=0, tolerance=0):
    url = getUserAPIUrl(limit=limit, offset=offset)
    return fetchRequestWithOffsets(url, tolerance=tolerance)


def getAllPendingUsers(limit=Globals.limit, offset=0, tolerance=0):
    url = getPendingUsersAPIUrl(limit=Globals.limit, offset=0)
    return fetchRequestWithOffsets(url, tolerance=tolerance)


def getUserInfo():
    url = "%s/user_info/" % Globals.configuration.host
    resp = performGetRequestWithRetry(url, headers=getHeader())

    return (
        resp.json()
        if resp and hasattr(resp, "status_code") and resp.status_code < 300
        else None
    )


def getAuthRoles(limit=None, offset=0):
    url = (
        "https://%s-api.esper.cloud/api/authz2/v1/roles/?limit=%s&offset=%s"
        % (
            Globals.configuration.host.replace("https://", "").replace(
                "-api.esper.cloud/api", ""
            ),
            limit if limit else Globals.limit,
            offset,
        )
    )
    resp = performGetRequestWithRetry(url, headers=getHeader())

    return (
        resp.json()
        if resp and hasattr(resp, "status_code") and resp.status_code < 300
        else None
    )


def getUserFromToken():
    try:
        user_info = getUserInfo()
        if user_info:
            Globals.TOKEN_USER = user_info
    except:
        pass