import Common.Globals as Globals
import os
import wx

from Common.decorator import api_tool_decorator
from GUI.Dialogs.CheckboxMessageBox import CheckboxMessageBox
from Utility import EventUtility
from Utility.API.AppUtilities import getAllAppVersionsForHost, getAllApplicationsForHost, uploadApplicationForHost
from Utility.API.ContentUtility import getAllContentFromHost, uploadContentToHost
from Utility.API.FeatureFlag import getFeatureFlags, getFeatureFlagsForTenant
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Resource import deleteFile, displayMessageBox, download, getAllFromOffsets, getEsperConfig, getHeader, postEventToFrame

from Utility.Web.WebRequests import performGetRequestWithRetry, performPostRequestWithRetry

from esperclient import InlineResponse201


def checkBlueprintsIsEnabled():
    enabled = False
    resp = getFeatureFlags()
    if hasattr(resp, "status_code") and resp.status_code < 300:
        jsonResp = resp.json()
        if "esper.cloud.onboarding" in jsonResp and jsonResp["esper.cloud.onboarding"]:
            return True
    return enabled


def checkBlueprintsIsEnabledForTenant(host, header):
    enabled = False
    resp = getFeatureFlagsForTenant(host, header)
    if hasattr(resp, "status_code") and resp.status_code < 300:
        jsonResp = resp.json()
        if "esper.cloud.onboarding" in jsonResp and jsonResp["esper.cloud.onboarding"]:
            return True
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
    response = getAllBlueprintsFromHostHelper(host, key, enterprise, Globals.limit, 0)
    blueprints = getAllFromOffsets(getAllBlueprintsFromHostHelper, None, response)
    if hasattr(response, "results"):
        response.results = response.results + blueprints
        response.next = None
        response.prev = None
    elif type(response) is dict and "results" in response:
        response["results"] = response["results"] + blueprints
        response["next"] = None
        response["prev"] = None
        print(len(response["results"]))
    return response


@api_tool_decorator()
def getAllBlueprintsFromHostHelper(host, key, enterprise, limit=Globals.limit, offset=0):
    url = "{baseUrl}/v0/enterprise/{enterprise_id}/blueprint/?limit={limit}&offset={offset}".format(
        baseUrl=host,
        enterprise_id=enterprise,
        limit=limit,
        offset=offset
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
def getGroupBlueprintRevision(groupId):
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


def prepareBlueprintClone(blueprint, toConfig, fromConfig, group):
    blueprint.pop("id", None)
    blueprint.pop("locked", None)
    blueprint.pop("created_on", None)
    blueprint.pop("updated_on", None)
    blueprint.pop("group", None)
    blueprint["latest_revision"].pop("id", None)
    blueprint["latest_revision"].pop("revision_id", None)
    blueprint["latest_revision"].pop("created_by", None)
    blueprint["latest_revision"].pop("current", None)
    blueprint["latest_revision"].pop("type", None)
    blueprint["latest_revision"].pop("created_on", None)
    blueprint["latest_revision"].pop("comments", None)

    blueprint["latest_revision"]["security"]["minimum_password_length"] = (4
                                                                           if blueprint["latest_revision"]["security"]["password_quality"] == "PASSWORD_QUALITY_UNSPECIFIED"
                                                                           else blueprint["latest_revision"]["security"]["minimum_password_length"])

    blueprint, missingApps, downloadLinks = checkFromMissingApps(blueprint, toConfig, fromConfig)
    blueprint, missingContent, downloadContentLinks = checkFromMissingContent(blueprint, toConfig, fromConfig)

    if Globals.SHOW_TEMPLATE_DIALOG:
        result = CheckboxMessageBox(
            "Confirmation",
            "The %s will attempt to clone to template.\nThe following apps are missing: %s\nThe following Content is missing: %s\n\nContinue?"
            % (Globals.TITLE, missingApps if missingApps else None, missingContent if missingContent else None),
        )
        res = result.ShowModal()

        if result and result.getCheckBoxValue():
            Globals.SHOW_TEMPLATE_DIALOG = False
            Globals.frame.preferences["templateDialog"] = Globals.SHOW_TEMPLATE_DIALOG
    else:
        res = wx.ID_OK
    if res == wx.ID_OK:
        progress = wx.ProgressDialog(
            "Cloning Blueprint",
            "Time remaining",
            100,
            style=wx.PD_CAN_ABORT
            | wx.PD_ELAPSED_TIME
            | wx.PD_AUTO_HIDE
            | wx.PD_ESTIMATED_TIME,
        )
        blueprint = uploadingMissingBlueprintApps(blueprint, downloadLinks, toConfig, fromConfig, progress)
        blueprint = uploadMissingContentFiles(blueprint, downloadContentLinks, toConfig, fromConfig, progress)
        resp = createBlueprintForHost(toConfig["apiHost"], toConfig["apiKey"], toConfig["enterprise"], group, blueprint)

        cloneResult = "Success" if resp and hasattr(resp, "status_code") else "FAILED Reason: %s" % str(resp)
        progress.Update(100, "Cloning Attempt Done. Result: %s" % cloneResult)
        postEventToFrame(EventUtility.myEVT_LOG, "---> Cloning Blueprint: %s" % cloneResult)
        displayMessageBox(
            (
                "Cloning Attempt Done. Result: %s" % cloneResult,
                wx.OK | wx.ICON_INFORMATION,
            )
        )


def uploadingMissingBlueprintApps(blueprint, downloadLinks, toConfig, fromConfig, progress):
    numTotal = len(downloadLinks) * 2
    num = 1
    for detail in downloadLinks:
        link = detail["link"]
        file = "%s.apk" % detail["version"]
        deleteFile(file)
        try:
            progress.Update(int((num / numTotal) * 33), "Attempting to download: %s" % detail["name"])
            postEventToFrame(EventUtility.myEVT_LOG, "---> Cloning Blueprint: Downloading %s" % detail["name"])
            download(link, file)
            ApiToolLog().LogApiRequestOccurrence(
                "download", link, Globals.PRINT_API_LOGS
            )
        except Exception as e:
            # TODO: download link might have expired reobtain and try again?
            ApiToolLog().LogError(e)
            print(e)
        num += 1
        if os.path.exists(file):
            postEventToFrame(EventUtility.myEVT_LOG, "---> Cloning Blueprint: Uploading %s" % detail["name"])
            res = uploadApplicationForHost(getEsperConfig(toConfig["apiHost"], toConfig["apiKey"]), toConfig["enterprise"], file)
            if type(res) != InlineResponse201:
                progress.Update(int((num / numTotal) * 33), "Failed uploading %s" % detail["name"])
                postEventToFrame(EventUtility.myEVT_LOG, "---> Cloning Blueprint: Failed Uploading %s" % detail["name"])
                deleteFile(file)
                raise Exception("Upload failed!")
            blueprint["latest_revision"]["application"]["apps"].append({
                'app_version': res["application"]["versions"][0]["id"],
                "package_name": res["application"]["package_name"],
                "application_name": res["application"]["application_name"],
                "is_g_play": False,
                "installation_rule": detail["rule"],
                "state": detail["state"]
            })
        num += 1
        deleteFile(file)
    progress.Update(33, "Finished uploading missing applications.")
    postEventToFrame(EventUtility.myEVT_LOG, "---> Cloning Blueprint: Finished Uploading Apps")
    return blueprint


def checkFromMissingApps(blueprint, toConfig, fromConfig):
    postEventToFrame(EventUtility.myEVT_LOG, "---> Cloning Blueprint: Fetching Applications")
    toApps = getAllApplicationsForHost(
        getEsperConfig(toConfig["apiHost"], toConfig["apiKey"]),
        toConfig["enterprise"]
    )
    appsToAdd = []
    missingApps = ""
    downloadLink = []
    for app in blueprint["latest_revision"]["application"]["apps"]:
        match = list(filter(
            lambda x: x.package_name == app["package_name"],
            toApps.results,
        ))
        appAdded = False
        if match:
            toAppVersions = getAllAppVersionsForHost(
                getEsperConfig(toConfig["apiHost"], toConfig["apiKey"]),
                toConfig["enterprise"],
                match[0].id,
            )
            for version in toAppVersions.results:
                if (version.version_code == app["version_codes"][0]
                        or version.build_number == app["version_codes"][0]):
                    if app["is_g_play"] and version.is_g_play:
                        # TODO: Add properly
                        # Found matching Play Store app
                        appsToAdd.append({
                            'app_version': version.id,
                            "package_name": app["package_name"],
                            "application_name": app["application_name"],
                            "is_g_play": version.is_g_play,
                            "installation_rule": app["installation_rule"],
                            "state": app["state"]
                        })
                    elif not app["is_g_play"] and (not hasattr(version, "is_g_play") or not version.is_g_play):
                        # Found matching enterprise version
                        appsToAdd.append({
                            'app_version': version.id,
                            "package_name": app["package_name"],
                            "application_name": app["application_name"],
                            "is_g_play": version.is_g_play if hasattr(version, "is_g_play") else False,
                            "version_codes": [
                                version.build_number
                            ],
                            "installation_rule": app["installation_rule"],
                            "release_name": version.release_name,
                            "state": app["state"]
                        })
                        appAdded = True
        if not appAdded:
            postEventToFrame(EventUtility.myEVT_LOG, "---> Cloning Blueprint: Missing %s" % app["application_name"])
            missingApps += "%s, " % app["application_name"]
            if "download_url" in app:
                downloadLink.append({
                    "name": app["application_name"],
                    "version": app["app_version"],
                    "link": app["download_url"],
                    "rule": app["installation_rule"],
                    "state": app["state"]
                })
    blueprint["latest_revision"]["application"]["apps"] = appsToAdd
    return blueprint, missingApps, downloadLink


def checkFromMissingContent(blueprint, toConfig, fromConfig):
    postEventToFrame(EventUtility.myEVT_LOG, "---> Cloning Blueprint: Fetching Content")
    toContent = getAllContentFromHost(toConfig["apiHost"], toConfig["enterprise"], toConfig["apiKey"])
    if toContent and hasattr(toContent, "status_code") and toContent.status_code < 300:
        toContent = toContent.json()
    contentToAdd = []
    missingContent = ""
    downloadContentLink = []
    for file in blueprint["latest_revision"]["content"]["files"]:
        match = list(filter(
            lambda x: x["hash"] == file["hash"],
            toContent["results"],
        ))
        if match:
            contentToAdd.append({
                "file": match[0]["id"],
                "destination_path": file["destination_path"]
            })
        else:
            missingContent += "%s, " % file["file"]
            if "url" in file:
                downloadContentLink.append({
                    "name": file["file"],
                    "link": file["url"],
                    "path": file["destination_path"]
                })
    blueprint["latest_revision"]["content"]["files"] = contentToAdd
    return blueprint, missingContent, downloadContentLink


def uploadMissingContentFiles(blueprint, downloadContentLinks, toConfig, fromConfig, progress):
    numTotal = len(downloadContentLinks) * 2
    num = 1
    for detail in downloadContentLinks:
        link = detail["link"]
        try:
            fileExtension = link.split("?")[0].split("/")[-1].split(".")[-1]
            file = "%s.%s" % (detail["name"], fileExtension)
            progress.Update(int((num / numTotal) * 66), "Attempting to download: %s" % detail["name"])
            postEventToFrame(EventUtility.myEVT_LOG, "---> Cloning Blueprint: Downloading %s" % detail["name"])
            download(link, file)
            ApiToolLog().LogApiRequestOccurrence(
                "download", link, Globals.PRINT_API_LOGS
            )
        except Exception as e:
            # TODO: download link might have expired reobtain and try again?
            ApiToolLog().LogError(e)
            print(e)
        num += 1
        if os.path.exists(file):
            postEventToFrame(EventUtility.myEVT_LOG, "---> Cloning Blueprint: Uploading %s" % detail["name"])
            res = uploadContentToHost(toConfig["apiHost"], toConfig["enterprise"], toConfig["apiKey"], file)
            if res and hasattr(res, "status_code") and res.status_code > 300:
                progress.Update(int((num / numTotal) * 66), "Failed uploading %s" % detail["name"])
                postEventToFrame(EventUtility.myEVT_LOG, "---> Cloning Blueprint: Failed Uploading %s" % detail["name"])
                deleteFile(file)
                raise Exception("Upload failed!")
            else:
                res = res.json()
            blueprint["latest_revision"]["content"]["files"].append({
                "file": res["id"],
                "destination_path": detail["path"],
            })
        num += 1
        deleteFile(file)
    progress.Update(66, "Finished uploading missing content.")
    postEventToFrame(EventUtility.myEVT_LOG, "---> Cloning Blueprint: Finished Uploading Content")
    return blueprint
