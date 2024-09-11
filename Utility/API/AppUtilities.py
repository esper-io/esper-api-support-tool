#!/usr/bin/env python

import string
import time

import esperclient

import Common.Globals as Globals
import Utility.EventUtility as eventUtil
from Common.decorator import api_tool_decorator
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Resource import (
    enforceRateLimit,
    getHeader,
    logBadResponse,
    postEventToFrame,
)
from Utility.Web.WebRequests import (
    getAllFromOffsetsRequests,
    handleRequestError,
    performGetRequestWithRetry,
)


@api_tool_decorator()
def getAllInstallableApps(tolerance=0):
    androidApps = getAllAndroidInstallableApps(tolerance=tolerance)
    iosApps = getAllIosInstallableApps(tolerance=tolerance)

    resp = {
        "results": androidApps["results"] + iosApps["results"],
    }
    return resp


@api_tool_decorator()
def getAllAndroidInstallableApps(tolerance=0):
    tenant = Globals.configuration.host.replace("https://", "").replace(
        "-api.esper.cloud/api", ""
    )
    url = (
        "https://%s-api.esper.cloud/api/v1/enterprise/%s/application/?limit=%s&without_download_url=true&format=json&is_hidden=false"
        % (tenant, Globals.enterprise_id, Globals.limit)
    )
    resp = performGetRequestWithRetry(url, headers=getHeader())
    if resp:
        respJson = resp.json()
        appsResp = getAllFromOffsetsRequests(respJson, tolarance=tolerance)
        if type(appsResp) is dict and "results" in appsResp:
            respJson["results"] = respJson["results"] + appsResp["results"]
            respJson["next"] = None
            respJson["prev"] = None
        return respJson
    return resp


@api_tool_decorator()
def getAllIosInstallableApps(tolerance=0):
    enterprise_apps = getEnterpriseIosApps(tolerance=tolerance)
    # vppAppsUrl = "https://{host}-api.esper.cloud/api/apps/v0/vpp/"
    # vppAppDetailUrl = "https://{host}-api.esper.cloud/api/v2/itunesapps/?apple_app_id=%s"
    return enterprise_apps


@api_tool_decorator()
def getEnterpriseIosApps(limit=None, offset=0, app_name="", tolerance=0):
    esperIosAppsUrl = (
        "%s/v2/tenant-apps?format=json&limit=%s&offset=%s&app_name=%s"
        % (
            Globals.configuration.host,
            limit if limit else Globals.limit,
            offset,
            app_name,
        )
    )
    resp = performGetRequestWithRetry(esperIosAppsUrl, headers=getHeader())
    if resp:
        resp_json = resp.json()
        content = resp_json["content"]
        appsResp = getAllFromOffsetsRequests(content, tolarance=tolerance)
        if (
            type(appsResp) is dict
            and "content" in appsResp
            and "results" in appsResp["content"]
        ):
            content["results"] = (
                content["results"] + appsResp["content"]["results"]
            )
            content["next"] = None
            content["prev"] = None
        app_res = {"results": []}
        for app in content["results"]:
            app_details_url = (
                "%s/v2/tenant-apps/%s/versions?format=json&limit=1&offset=0"
                % (Globals.configuration.host, app["id"])
            )
            details_resp = performGetRequestWithRetry(
                app_details_url, headers=getHeader()
            )
            if details_resp:
                details_json = details_resp.json()
                details_json["content"]["results"][0]["version_id"] = (
                    details_json["content"]["results"][0]["id"]
                )
                details_json["content"]["results"][0].update(app)
                app_res["results"].append(details_json["content"]["results"][0])

        return app_res
    return resp


def constructAppPkgVerStr(appName, pkgName, version):
    appPkgVerStr = ""
    if appName:
        appPkgVerStr += appName
    else:
        appPkgVerStr += "Invalid App Name - "
    if Globals.SHOW_PKG_NAME:
        if pkgName:
            appPkgVerStr += " (%s) v" % pkgName
        else:
            appPkgVerStr += " (Invalid Package Name) v"
    else:
        appPkgVerStr += " v"
    if version:
        appPkgVerStr += version
    else:
        appPkgVerStr += "Unknown Version"
    return appPkgVerStr


@api_tool_decorator()
def uploadApplicationForHost(
    config, enterprise_id, file, maxAttempt=Globals.MAX_RETRY
):
    return uploadApplication(file, config, enterprise_id, maxAttempt)


@api_tool_decorator()
def uploadApplication(
    file, config=None, enterpriseId=None, maxAttempt=Globals.MAX_RETRY
):
    try:
        api_instance = esperclient.ApplicationApi(
            esperclient.ApiClient(
                Globals.configuration if not config else config
            )
        )
        enterprise_id = (
            Globals.enterprise_id if not enterpriseId else enterpriseId
        )
        api_response = None
        for attempt in range(maxAttempt):
            try:
                enforceRateLimit()
                api_response = api_instance.upload(enterprise_id, file)
                postEventToFrame(
                    eventUtil.myEVT_AUDIT,
                    {
                        "operation": "UploadApp",
                        "data": file,
                        "resp": api_response,
                    },
                )
                break
            except Exception as e:
                handleRequestError(attempt, e, maxAttempt, raiseError=True)
        return api_response
    except Exception as e:
        raise Exception(
            "Exception when calling ApplicationApi->upload: %s\n" % e
        )


@api_tool_decorator()
def getAllApplicationsForHost(
    config,
    enterprise_id,
    application_name="",
    package_name="",
    maxAttempt=Globals.MAX_RETRY,
):
    """Make a API call to get all Applications belonging to the Enterprise"""
    try:
        api_instance = esperclient.ApplicationApi(esperclient.ApiClient(config))
        api_response = None
        for attempt in range(maxAttempt):
            try:
                enforceRateLimit()
                api_response = api_instance.get_all_applications(
                    enterprise_id,
                    limit=Globals.limit,
                    application_name=application_name,
                    package_name=package_name,
                    offset=0,
                    is_hidden=False,
                )
                ApiToolLog().LogApiRequestOccurrence(
                    "getAllApplicationsForHost",
                    api_instance.get_all_applications,
                    Globals.PRINT_API_LOGS,
                )
                break
            except Exception as e:
                handleRequestError(attempt, e, maxAttempt, raiseError=True)
        return api_response
    except Exception as e:
        raise Exception(
            "Exception when calling ApplicationApi->get_all_applications: %s\n"
            % e
        )


@api_tool_decorator()
def getAllAppVersionsForHost(
    config,
    enterprise_id,
    app_id,
    maxAttempt=Globals.MAX_RETRY,
):
    """Make a API call to get all Applications belonging to the Enterprise"""
    try:
        api_response = None
        for attempt in range(maxAttempt):
            try:
                url = "{tenant}/v1/enterprise/{enterprise_id}/application/{appId}/version/".format(
                    tenant=config.host,
                    enterprise_id=enterprise_id,
                    appId=app_id,
                )
                header = {
                    "Authorization": f"Bearer {config.api_key['Authorization']}",
                    "Content-Type": "application/json",
                }
                api_response = performGetRequestWithRetry(url, header)
                if api_response and api_response.status_code < 300:
                    api_response = api_response.json()
                break
            except Exception as e:
                handleRequestError(attempt, e, maxAttempt, raiseError=True)
        return api_response
    except Exception as e:
        raise Exception(
            "Exception when calling ApplicationApi->get_app_versions: %s\n" % e
        )


def getAppVersions(
    application_id,
    getPlayStore=False,
    maxAttempt=Globals.MAX_RETRY,
):
    if Globals.USE_ENTERPRISE_APP and not getPlayStore:
        return getAllAppVersionsForHost(
            Globals.configuration,
            Globals.enterprise_id,
            application_id,
            maxAttempt,
        )
    else:
        return getAppVersionsEnterpriseAndPlayStore(application_id)


def getAppVersionsEnterpriseAndPlayStore(application_id):
    url = "https://{tenant}-api.esper.cloud/api/v1/enterprise/{ent_id}/application/{app_id}/version/".format(
        tenant=Globals.configuration.host.split("-api")[0].replace(
            "https://", ""
        ),
        ent_id=Globals.enterprise_id,
        app_id=application_id,
    )
    resp = performGetRequestWithRetry(url, headers=getHeader())
    jsonResp = resp.json()
    logBadResponse(url, resp, jsonResp, displayMsgBox=True)
    return jsonResp


def getAppsEnterpriseAndPlayStore(package_name=""):
    url = ""
    jsonResp = {}
    if package_name:
        url = "https://{tenant}-api.esper.cloud/api/v1/enterprise/{ent_id}/application/?package_name={pkg}".format(
            tenant=Globals.configuration.host.split("-api")[0].replace(
                "https://", ""
            ),
            ent_id=Globals.enterprise_id,
            pkg=package_name,
        )
        resp = performGetRequestWithRetry(url, headers=getHeader())
        jsonResp = resp.json()
        logBadResponse(url, resp, jsonResp, displayMsgBox=True)
    else:
        jsonResp = getAllInstallableApps()
    return jsonResp


def getInstallDevices(
    version_id, application_id, maxAttempt=Globals.MAX_RETRY, tolarance=0
):
    if type(version_id) is list:
        api_response = None
        for version in version_id:
            resp = get_installed_devices(
                version, application_id, maxAttempt, tolarance=tolarance
            )
            if api_response is None:
                api_response = resp
            else:
                api_response.results += resp.results
            no_dupe = []
            for device in api_response.results:
                if device not in no_dupe:
                    no_dupe.append(device)
            api_response.results = no_dupe
        return api_response
    else:
        return get_installed_devices(
            version_id, application_id, maxAttempt, tolarance=tolarance
        )


def get_installed_devices(
    version_id, application_id, maxAttempt=Globals.MAX_RETRY, tolarance=0
):
    offset = 0
    response = get_installed_devices_api(
        version_id, application_id, Globals.limit, offset, maxAttempt
    )
    if len(response.results) != response.count:
        devices = getAllFromOffsetsRequests(response, None, tolarance)
        if hasattr(response, "results"):
            response.results = response.results + devices
            response.next = None
            response.prev = None
        elif type(response) is dict and "results" in response:
            response["next"] = None
            response["prev"] = None
            for device in devices:
                if device not in response["results"]:
                    response["results"].append(device)
    return response


def get_installed_devices_api(
    version_id, application_id, limit, offset, maxAttempt=Globals.MAX_RETRY
):
    api_instance = esperclient.ApplicationApi(
        esperclient.ApiClient(Globals.configuration)
    )
    enterprise_id = Globals.enterprise_id
    for attempt in range(maxAttempt):
        try:
            # List install devices
            enforceRateLimit()
            api_response = api_instance.get_install_devices(
                version_id,
                application_id,
                enterprise_id,
                limit=limit,
                offset=offset,
            )
            ApiToolLog().LogApiRequestOccurrence(
                "getInstallDevices",
                api_instance.get_install_devices,
                Globals.PRINT_API_LOGS,
            )
            return api_response
        except Exception as e:
            handleRequestError(attempt, e, maxAttempt, raiseError=True)


def getAppDictEntry(app, update=True):
    entry = None
    appName = None
    appPkgName = None

    if type(app) == dict and "application" in app:
        appName = app["application"]["application_name"]
        appPkgName = appName + (" (%s)" % app["application"]["package_name"])
        entry = {
            "app_name": app["application"]["application_name"],
            appName: app["application"]["package_name"],
            appPkgName: app["application"]["package_name"],
            "appPkgName": appPkgName,
            "packageName": app["application"]["package_name"],
            "id": app["id"],
            "app_state": None,
        }
    elif hasattr(app, "application_name"):
        appName = app.application_name
        appPkgName = appName + (" (%s)" % app.package_name)
        entry = {
            "app_name": app.application_name,
            appName: app.package_name,
            appPkgName: app.package_name,
            "appPkgName": appPkgName,
            "packageName": app.package_name,
            "versions": app.versions,
            "id": app.id,
        }
    elif type(app) == dict and "application_name" in app:
        appName = app["application_name"]
        appPkgName = appName + (" (%s)" % app["package_name"])
        entry = {
            "app_name": app["application_name"],
            appName: app["package_name"],
            appPkgName: app["package_name"],
            "appPkgName": appPkgName,
            "packageName": app["package_name"],
            "id": app["id"],
        }
    elif type(app) == dict and "app_name" in app:
        appName = app["app_name"]
        appPkgName = appName + (" (%s)" % app["package_name"])
        entry = {
            "app_name": app["app_name"],
            appName: app["package_name"],
            appPkgName: app["package_name"],
            "appPkgName": appPkgName,
            "packageName": app["package_name"],
            "app_state": app["state"] if "state" in app else "",
            "id": app["id"],
            "is_ios": app.get("platform", "").lower() == "apple",
        }

    validApp = None
    if type(app) == esperclient.models.application.Application:
        entry["isValid"] = True
    else:
        if (
            type(app) == dict
            and "id" in app
            and "install_state" not in app
            and "device" not in app
        ):
            entry["isValid"] = True

    if (
        hasattr(validApp, "id")
        or (type(validApp) == dict and "id" in validApp)
        or (type(app) == dict and "device" in app)
    ):
        entry["id"] = (
            validApp.id
            if hasattr(validApp, "id")
            else (
                validApp["id"]
                if (type(validApp) == dict and "id" in validApp)
                else entry["id"]
            )
        )
        entry["isValid"] = True

    return entry


def getDeviceAppsApiUrl(deviceid, useEnterprise=False):
    extention = (
        Globals.DEVICE_ENTERPRISE_APP_LIST_REQUEST_EXTENSION
        if useEnterprise
        else Globals.DEVICE_APP_LIST_REQUEST_EXTENSION
    )
    if Globals.APP_FILTER.lower() != "all":
        extention += "&state=%s" % Globals.APP_FILTER.upper()
    hasFormat = [
        tup[1]
        for tup in string.Formatter().parse(extention)
        if tup[1] is not None
    ]
    if hasFormat:
        if "limit" in hasFormat:
            extention = extention.format(limit=Globals.limit)
    url = (
        Globals.BASE_DEVICE_URL.format(
            configuration_host=Globals.configuration.host,
            enterprise_id=Globals.enterprise_id,
            device_id=deviceid,
        )
        + extention
    )
    return url
