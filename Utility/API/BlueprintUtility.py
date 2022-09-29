
import Common.Globals as Globals
import Utility.EventUtility as eventUtil
import os
import wx

from Common.decorator import api_tool_decorator
from GUI.Dialogs.CheckboxMessageBox import CheckboxMessageBox
from Utility import EventUtility
from Utility.API.AppUtilities import (
    getAllAppVersionsForHost,
    getAllApplicationsForHost,
    uploadApplicationForHost,
)
from Utility.API.CommandUtility import postEsperCommand
from Utility.API.ContentUtility import getAllContentFromHost, uploadContentToHost
from Utility.API.FeatureFlag import getFeatureFlags, getFeatureFlagsForTenant
from Utility.API.WallpaperUtility import uploadWallpaper
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Resource import (
    deleteFile,
    displayMessageBox,
    download,
    getEsperConfig,
    getHeader,
    postEventToFrame,
)

from Utility.Web.WebRequests import (
    getAllFromOffsetsRequests,
    performGetRequestWithRetry,
    performPostRequestWithRetry,
)

from esperclient import InlineResponse201


def checkBlueprintsIsEnabled():
    enabled = False
    resp = getFeatureFlags()
    if hasattr(resp, "status_code") and resp.status_code < 300:
        jsonResp = resp.json()
        if "esper.cloud.onboarding" in jsonResp and jsonResp["esper.cloud.onboarding"]:
            return True
    return enabled


def checkBlueprintEnabled(data):
    isBlueprintEnabled = checkBlueprintsIsEnabledForTenant(
        data["apiHost"],
        {
            "Authorization": "Bearer %s" % data["apiKey"],
            "Content-Type": "application/json",
        },
    )
    data["isBlueprintsEnabled"] = isBlueprintEnabled


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
        baseUrl=Globals.configuration.host, enterprise_id=Globals.enterprise_id
    )
    resp = performGetRequestWithRetry(url, headers=getHeader())
    if resp:
        respJson = resp.json()
        blueprints = getAllFromOffsetsRequests(respJson)
        if type(blueprints) is dict and "results" in blueprints:
            respJson["results"] = respJson["results"] + blueprints["results"]
            respJson["next"] = None
            respJson["prev"] = None
        return respJson
    return resp


@api_tool_decorator()
def getAllBlueprintsFromHost(host, key, enterprise):
    response = getAllBlueprintsFromHostHelper(host, key, enterprise, Globals.limit, 0)
    blueprints = getAllFromOffsetsRequests(response, tolarance=1)
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
def getAllBlueprintsFromHostHelper(
    host, key, enterprise, limit=Globals.limit, offset=0, responses=None
):
    url = "{baseUrl}/v0/enterprise/{enterprise_id}/blueprint/?limit={limit}&offset={offset}".format(
        baseUrl=host, enterprise_id=enterprise, limit=limit, offset=offset
    )
    resp = performGetRequestWithRetry(
        url,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    if resp.status_code < 300 and responses is not None:
        api_response = resp.json()
        responses.append(api_response)
    return resp


@api_tool_decorator()
def getBlueprint(id):
    url = "{baseUrl}/v0/enterprise/{enterprise_id}/blueprint/{id}/".format(
        baseUrl=Globals.configuration.host, enterprise_id=Globals.enterprise_id, id=id
    )
    resp = performGetRequestWithRetry(url, headers=getHeader())
    return resp


@api_tool_decorator()
def getAllBlueprintFromHost(host, key, enterprise, id):
    url = "{baseUrl}/v0/enterprise/{enterprise_id}/blueprint/{id}".format(
        baseUrl=host, enterprise_id=enterprise, id=id
    )
    resp = performGetRequestWithRetry(
        url,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    return resp


@api_tool_decorator()
def getBlueprintRevisions(id):
    url = "{baseUrl}/v0/enterprise/{enterprise_id}/blueprint/{id}/revisions/".format(
        baseUrl=Globals.configuration.host, enterprise_id=Globals.enterprise_id, id=id
    )
    resp = performGetRequestWithRetry(url, headers=getHeader())
    return resp


@api_tool_decorator()
def getBlueprintRevision(blueprint_id, revision_id):
    url = "{baseUrl}/v0/enterprise/{enterprise_id}/blueprint/{blueprintId}/revisions/{revisionId}/".format(
        baseUrl=Globals.configuration.host,
        enterprise_id=Globals.enterprise_id,
        blueprintId=blueprint_id,
        revisionId=revision_id,
    )
    resp = performGetRequestWithRetry(url, headers=getHeader())
    return resp


@api_tool_decorator()
def getGroupBlueprintRevision(groupId):
    url = (
        "{baseUrl}/enterprise/{enterprise_id}/devicegroup/{group_id}/blueprint/".format(
            baseUrl=Globals.configuration.host,
            enterprise_id=Globals.enterprise_id,
            group_id=groupId,
        )
    )
    resp = performGetRequestWithRetry(url, headers=getHeader())
    return resp


@api_tool_decorator()
def getGroupBlueprint(host, key, enterprise, groupId):
    url = (
        "{baseUrl}/enterprise/{enterprise_id}/devicegroup/{group_id}/blueprint/".format(
            baseUrl=host, enterprise_id=enterprise, group_id=groupId
        )
    )
    resp = performGetRequestWithRetry(
        url,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    return resp


@api_tool_decorator()
def getGroupBlueprintDetailForHost(host, key, enterprise, groupId, blueprintId):
    url = "{baseUrl}/enterprise/{enterprise_id}/devicegroup/{group_id}/blueprint/{blueprint_id}".format(
        baseUrl=host,
        enterprise_id=enterprise,
        group_id=groupId,
        blueprint_id=blueprintId,
    )
    resp = performGetRequestWithRetry(
        url,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    return resp


@api_tool_decorator()
def getGroupBlueprintDetail(groupId, blueprintId):
    url = "{baseUrl}/enterprise/{enterprise_id}/devicegroup/{group_id}/blueprint/{blueprint_id}".format(
        baseUrl=Globals.configuration.host,
        enterprise_id=Globals.enterprise_id,
        group_id=groupId,
        blueprint_id=blueprintId,
    )
    resp = performGetRequestWithRetry(
        url,
        headers=getHeader(),
    )
    return resp


@api_tool_decorator()
def createBlueprintForHost(host, key, enterprise, groupId, body):
    url = (
        "{baseUrl}/enterprise/{enterprise_id}/devicegroup/{group_id}/blueprint/".format(
            baseUrl=host, enterprise_id=enterprise, group_id=groupId
        )
    )
    resp = performPostRequestWithRetry(
        url,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        json=body,
    )
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

    blueprint["latest_revision"]["security"]["minimum_password_length"] = (
        4
        if blueprint["latest_revision"]["security"]["password_quality"]
        == "PASSWORD_QUALITY_UNSPECIFIED"
        else blueprint["latest_revision"]["security"]["minimum_password_length"]
    )

    blueprint, missingApps, downloadLinks = checkFromMissingApps(
        blueprint, toConfig, fromConfig
    )
    blueprint, missingContent, downloadContentLinks = checkFromMissingContent(
        blueprint, toConfig, fromConfig
    )

    if Globals.SHOW_TEMPLATE_DIALOG:
        result = CheckboxMessageBox(
            "Confirmation",
            "The %s will attempt to clone to template.\nThe following apps are missing: %s\nThe following Content is missing: %s\n\nContinue?"
            % (
                Globals.TITLE,
                missingApps if missingApps else None,
                missingContent if missingContent else None,
            ),
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
            style=wx.PD_ELAPSED_TIME | wx.PD_AUTO_HIDE | wx.PD_ESTIMATED_TIME,
        )
        try:
            blueprint = uploadingMissingBlueprintApps(
                blueprint, downloadLinks, toConfig, fromConfig, progress
            )
            progress.Update(80, "Beinging Cloning Attempt...")
            postEventToFrame(EventUtility.myEVT_LOG, "Beinging Cloning Attempt...")
            blueprint = uploadMissingContentFiles(
                blueprint, downloadContentLinks, toConfig, fromConfig, progress
            )
            # TODO: Handle Wallpaper transfer
            blueprint = uploadMissingWallpaper(
                blueprint,
                toConfig["apiHost"],
                toConfig["apiKey"],
                toConfig["enterprise"],
                progress,
            )
            resp = createBlueprintForHost(
                toConfig["apiHost"],
                toConfig["apiKey"],
                toConfig["enterprise"],
                group,
                blueprint,
            )
            respJson = resp.json()
            if (
                "message" in respJson
                and "Enterprise not enrolled into EMM." in respJson["message"]
            ):
                if (
                    "managed_google_play_disabled"
                    in blueprint["latest_revision"]["google_services"]
                ):
                    del blueprint["latest_revision"]["google_services"][
                        "managed_google_play_disabled"
                    ]
                resp = createBlueprintForHost(
                    toConfig["apiHost"],
                    toConfig["apiKey"],
                    toConfig["enterprise"],
                    group,
                    blueprint,
                )
                respJson = resp.json()

            cloneResult = (
                "Success"
                if resp and hasattr(resp, "status_code")
                else "FAILED Reason: %s" % str(respJson)
            )
            progress.Update(100, "Cloning Attempt Done. Result: %s" % cloneResult)
            postEventToFrame(
                EventUtility.myEVT_LOG, "---> Cloning Blueprint: %s" % cloneResult
            )
            displayMessageBox(
                (
                    "Cloning Attempt Done. Result: %s" % cloneResult,
                    wx.OK | wx.ICON_INFORMATION,
                )
            )
        except Exception as e:
            progress.Close()
            progress.DestroyLater()
            raise e


def uploadMissingWallpaper(blueprint, host, key, enterprise, progress):
    if host and key and enterprise:
        postEventToFrame(EventUtility.myEVT_LOG, "Processing wallpapers in template...")
        progress.Update(
            50,
            "Attempting to process wallpapers",
        )
        if blueprint["latest_revision"]["display_branding"]["wallpapers"]:
            bgList = []
            numTotal = len(
                blueprint["latest_revision"]["display_branding"]["wallpapers"]
            )
            num = 1
            for bg in blueprint["latest_revision"]["display_branding"]["wallpapers"]:
                newBg = uploadWallpaper(host, key, enterprise, bg)
                if newBg:
                    newBg["enterprise"] = enterprise
                    newBg["wallpaper"] = newBg["id"]
                    newBg["orientations"] = bg["orientations"]
                    newBg["screen_types"] = bg["screen_types"]
                    bgList.append(newBg)
                    progress.Update(
                        int((num / numTotal) * 75),
                        "Attempting to process wallpapers",
                    )
            blueprint["latest_revision"]["display_branding"]["wallpapers"] = bgList
    progress.Update(75, "Finsihed processing wallpapers")
    return blueprint


def uploadingMissingBlueprintApps(
    blueprint, downloadLinks, toConfig, fromConfig, progress
):
    numTotal = len(downloadLinks) * 2
    num = 1
    for detail in downloadLinks:
        link = detail["link"]
        file = "%s.apk" % detail["version"]
        deleteFile(file)
        try:
            progress.Update(
                int((num / numTotal) * 25),
                "Attempting to download: %s" % detail["name"],
            )
            postEventToFrame(
                EventUtility.myEVT_LOG,
                "---> Cloning Blueprint: Downloading %s" % detail["name"],
            )
            download(link, file)
            ApiToolLog().LogApiRequestOccurrence(
                "download", link, Globals.PRINT_API_LOGS
            )
        except Exception as e:
            rsp = performGetRequestWithRetry(
                detail["version_url"],
                {
                    "Authorization": "Bearer %s" % fromConfig["apiKey"],
                    "Content-Type": "application/json",
                },
            )
            if rsp.status_code < 300:
                rsp = rsp.json()
                link = rsp["app_file"]
                download(link, file)
            else:
                raise e
        num += 1
        if os.path.exists(file):
            postEventToFrame(
                EventUtility.myEVT_LOG,
                "---> Cloning Blueprint: Uploading %s" % detail["name"],
            )
            res = uploadApplicationForHost(
                getEsperConfig(toConfig["apiHost"], toConfig["apiKey"]),
                toConfig["enterprise"],
                file,
            )
            if type(res) != InlineResponse201:
                progress.Update(
                    int((num / numTotal) * 25), "Failed uploading %s" % detail["name"]
                )
                postEventToFrame(
                    EventUtility.myEVT_LOG,
                    "---> Cloning Blueprint: Failed Uploading %s" % detail["name"],
                )
                deleteFile(file)
                raise Exception("Upload failed!")
            blueprint["latest_revision"]["application"]["apps"].append(
                {
                    "app_version": res.application.versions[0].id,
                    "package_name": res.application.package_name,
                    "application_name": res.application.application_name,
                    "is_g_play": False,
                    "installation_rule": detail["rule"],
                    "state": detail["state"],
                }
            )
        num += 1
        deleteFile(file)
    progress.Update(33, "Finished uploading missing applications.")
    postEventToFrame(
        EventUtility.myEVT_LOG, "---> Cloning Blueprint: Finished Uploading Apps"
    )
    return blueprint


def checkFromMissingApps(blueprint, toConfig, fromConfig):
    postEventToFrame(
        EventUtility.myEVT_LOG, "---> Cloning Blueprint: Fetching Applications"
    )
    toApps = getAllApplicationsForHost(
        getEsperConfig(toConfig["apiHost"], toConfig["apiKey"]), toConfig["enterprise"]
    )
    appsToAdd = []
    missingApps = ""
    downloadLink = []
    for app in blueprint["latest_revision"]["application"]["apps"]:
        match = list(
            filter(
                lambda x: x.package_name == app["package_name"],
                toApps.results,
            )
        )
        appAdded = False
        if match:
            toAppVersions = getAllAppVersionsForHost(
                getEsperConfig(toConfig["apiHost"], toConfig["apiKey"]),
                toConfig["enterprise"],
                match[0].id,
            )
            for version in toAppVersions.results:
                if (
                    version.version_code == app["version_codes"][0]
                    or version.build_number == app["version_codes"][0]
                ):
                    if app["is_g_play"] and version.is_g_play:
                        # TODO: Add properly
                        # Found matching Play Store app
                        appsToAdd.append(
                            {
                                "app_version": version.id,
                                "package_name": app["package_name"],
                                "application_name": app["application_name"],
                                "is_g_play": version.is_g_play,
                                "installation_rule": app["installation_rule"],
                                "state": app["state"],
                            }
                        )
                    elif not app["is_g_play"] and (
                        not hasattr(version, "is_g_play") or not version.is_g_play
                    ):
                        # Found matching enterprise version
                        appsToAdd.append(
                            {
                                "app_version": version.id,
                                "package_name": app["package_name"],
                                "application_name": app["application_name"],
                                "is_g_play": version.is_g_play
                                if hasattr(version, "is_g_play")
                                else False,
                                "version_codes": [version.build_number],
                                "installation_rule": app["installation_rule"],
                                "release_name": version.release_name,
                                "state": app["state"],
                            }
                        )
                        appAdded = True
        if not appAdded:
            postEventToFrame(
                EventUtility.myEVT_LOG,
                "---> Cloning Blueprint: Missing %s" % app["application_name"],
            )
            missingApps += "%s, " % app["application_name"]
            if "download_url" in app and app["download_url"]:
                downloadLink.append(
                    {
                        "name": app["application_name"],
                        "version": app["app_version"],
                        "link": app["download_url"],
                        "rule": app["installation_rule"],
                        "state": app["state"],
                        "version_url": app["app_version_url"],
                    }
                )
    blueprint["latest_revision"]["application"]["apps"] = appsToAdd
    return blueprint, missingApps, downloadLink


def checkFromMissingContent(blueprint, toConfig, fromConfig):
    postEventToFrame(EventUtility.myEVT_LOG, "---> Cloning Blueprint: Fetching Content")
    toContent = getAllContentFromHost(
        toConfig["apiHost"], toConfig["enterprise"], toConfig["apiKey"]
    )
    if toContent and hasattr(toContent, "status_code") and toContent.status_code < 300:
        toContent = toContent.json()
    contentToAdd = []
    missingContent = ""
    downloadContentLink = []
    for file in blueprint["latest_revision"]["content"]["files"]:
        match = list(
            filter(
                lambda x: x["hash"] == file["hash"],
                toContent["results"],
            )
        )
        if match:
            contentToAdd.append(
                {"file": match[0]["id"], "destination_path": file["destination_path"]}
            )
        else:
            missingContent += "%s, " % file["file"]
            if "url" in file and file["url"]:
                downloadContentLink.append(
                    {
                        "name": file["file"],
                        "link": file["url"],
                        "path": file["destination_path"],
                    }
                )
    blueprint["latest_revision"]["content"]["files"] = contentToAdd
    return blueprint, missingContent, downloadContentLink


def uploadMissingContentFiles(
    blueprint, downloadContentLinks, toConfig, fromConfig, progress
):
    numTotal = len(downloadContentLinks) * 2
    num = 1
    for detail in downloadContentLinks:
        link = detail["link"]
        try:
            fileExtension = link.split("?")[0].split("/")[-1].split(".")[-1]
            file = "%s.%s" % (detail["name"], fileExtension)
            progress.Update(
                int((num / numTotal) * 50),
                "Attempting to download: %s" % detail["name"],
            )
            postEventToFrame(
                EventUtility.myEVT_LOG,
                "---> Cloning Blueprint: Downloading %s" % detail["name"],
            )
            download(link, file)
            ApiToolLog().LogApiRequestOccurrence(
                "download", link, Globals.PRINT_API_LOGS
            )
        except Exception as e:
            url = "{host}v0/enterprise/{ent_id}/content/{id}".format(
                host=fromConfig["apiHost"],
                ent_id=fromConfig["enterprise"],
                id=detail["file"],
            )
            rsp = performGetRequestWithRetry(
                url,
                {
                    "Authorization": "Bearer %s" % fromConfig["apiKey"],
                    "Content-Type": "application/json",
                },
            )
            if rsp.status_code < 300:
                rsp = rsp.json()
                link = rsp["download_url"]
                download(link, file)
            else:
                raise e
        num += 1
        if os.path.exists(file):
            postEventToFrame(
                EventUtility.myEVT_LOG,
                "---> Cloning Blueprint: Uploading %s" % detail["name"],
            )
            res = uploadContentToHost(
                toConfig["apiHost"], toConfig["enterprise"], toConfig["apiKey"], file
            )
            if res and hasattr(res, "status_code") and res.status_code > 300:
                progress.Update(
                    int((num / numTotal) * 50), "Failed uploading %s" % detail["name"]
                )
                postEventToFrame(
                    EventUtility.myEVT_LOG,
                    "---> Cloning Blueprint: Failed Uploading %s" % detail["name"],
                )
                deleteFile(file)
                raise Exception("Upload failed!")
            else:
                res = res.json()
            blueprint["latest_revision"]["content"]["files"].append(
                {
                    "file": res["id"],
                    "destination_path": detail["path"],
                }
            )
        num += 1
        deleteFile(file)
    progress.Update(50, "Finished uploading missing content.")
    postEventToFrame(
        EventUtility.myEVT_LOG, "---> Cloning Blueprint: Finished Uploading Content"
    )
    return blueprint


def prepareBlueprintConversion(template, toConfig, fromConfig, group):
    template.pop("id", None)
    template.pop("locked", None)
    template.pop("created_on", None)
    template.pop("updated_on", None)
    template.pop("group", None)

    blueprint = convertTemplateToBlueprint(template)

    prepareBlueprintClone(blueprint, toConfig, fromConfig, group)


def convertTemplateToBlueprint(template):
    templateSection = template["template"]
    blueprint = {
        "name": template["name"],
        "description": template["description"],
        "latest_revision": {
            "locked": False,
            "current": True,
            "type": "Independent",
            "comments": "Cloned from Template",
            "connectivity": {},
            "sound": {},
            "display_branding": {},
            "application": {},
            "content": {"files": [], "locked": False, "section_type": "Independent"},
            "settings_app": {},
            "security": {},
            "google_services": {},
            "system_updates": {},
            "date_time": {},
            "hardware_settings": {},
        },
    }
    blueprint["latest_revision"]["connectivity"] = {
        "incoming_numbers": None
        if "phonePolicy" not in templateSection and templateSection["phonePolicy"]
        else templateSection["phonePolicy"]["incomingNumbers"],
        "outgoing_numbers": None
        if "phonePolicy" not in templateSection and templateSection["phonePolicy"]
        else templateSection["phonePolicy"]["outgoingNumbers"],
        "incoming_numbers_with_tags": None
        if "phonePolicy" not in templateSection and templateSection["phonePolicy"]
        else templateSection["phonePolicy"]["incomingNumbersWithTags"],
        "outgoing_numbers_with_tags": None
        if "phonePolicy" not in templateSection and templateSection["phonePolicy"]
        else templateSection["phonePolicy"]["outgoingNumbersWithTags"],
        "wifi_settings": templateSection["settings"]["wifiSettings"],
        "locked": False,
        "section_type": "Independent",
        "sms_disabled": templateSection["devicePolicy"]["smsDisabled"],
        "enable_bluetooth": templateSection["devicePolicy"]["enableBluetooth"],
        "nfc_beam_disabled": templateSection["devicePolicy"]["nfcBeamDisabled"],
        "wifi_state": templateSection["settings"]["wifiState"],
    }

    blueprint["latest_revision"]["sound"] = {
        "alarm_volume": templateSection["settings"]["alarmVolume"],
        "ring_volume": templateSection["settings"]["ringVolume"],
        "music_volume": templateSection["settings"]["musicVolume"],
        "notification_volume": templateSection["settings"]["notificationVolume"],
        "locked": False,
        "section_type": "Independent",
    }

    blueprint["latest_revision"]["display_branding"] = {
        "rotation_state": templateSection["settings"]["rotationState"],
        "wallpapers": None
        if "brand" not in templateSection and not templateSection["brand"]
        else templateSection["brand"]["wallpapers"],  # TODO
        "locked": False,
        "section_type": "Independent",
        "screenshot_disabled": templateSection["devicePolicy"]["screenshotDisabled"],
        "status_bar_disabled": templateSection["devicePolicy"]["statusBarDisabled"],
        "brightness_scale": templateSection["settings"]["brightnessScale"],
    }

    blueprint["latest_revision"]["application"] = {
        "apps": templateSection["application"]["apps"],
        "app_mode": templateSection["application"]["appMode"],
        "preload_apps": templateSection["application"]["preloadApps"],
        "launch_on_start": templateSection["application"]["launchOnStart"],
        "permission_policy": templateSection["securityPolicy"]["permissionPolicy"],
        "locked": False,
        "section_type": "Independent",
        "launcher_less_dpc": templateSection["launcherLessDpc"],
        "disable_local_app_install": templateSection["devicePolicy"][
            "disableLocalAppInstall"
        ],
        "app_uninstall_disabled": templateSection["devicePolicy"][
            "appUninstallDisabled"
        ],
        "start_on_boot": templateSection["application"]["startOnBoot"],
    }

    blueprint["latest_revision"]["settings_app"] = {
        "settings_access_level": templateSection["devicePolicy"]["settingsAccessLevel"],
        "esper_settings_app": {
            "esper_settings_app_policy": {
                "flashlight": templateSection["devicePolicy"]["esperSettingsApp"][
                    "flashlight"
                ],
                "wifi": templateSection["devicePolicy"]["esperSettingsApp"]["wifi"],
                "auto_rotation": templateSection["devicePolicy"]["esperSettingsApp"][
                    "autoRotation"
                ],
                "reboot": templateSection["devicePolicy"]["esperSettingsApp"]["reboot"],
                "clear_app_data": templateSection["devicePolicy"]["esperSettingsApp"][
                    "clearAppData"
                ],
                "kiosk_app_selection": templateSection["devicePolicy"][
                    "esperSettingsApp"
                ]["kioskAppSelection"],
                "esper_branding": templateSection["devicePolicy"]["esperSettingsApp"][
                    "esperBranding"
                ],
                "factory_reset": templateSection["devicePolicy"]["esperSettingsApp"][
                    "factoryReset"
                ],
                "about": templateSection["devicePolicy"]["esperSettingsApp"]["about"],
                "display": templateSection["devicePolicy"]["esperSettingsApp"][
                    "display"
                ],
                "sound": templateSection["devicePolicy"]["esperSettingsApp"]["sound"],
                "keyboard": templateSection["devicePolicy"]["esperSettingsApp"][
                    "keyboard"
                ],
                "input_selection": templateSection["devicePolicy"]["esperSettingsApp"][
                    "inputSelection"
                ],
                "accessibility": templateSection["devicePolicy"]["esperSettingsApp"][
                    "accessibility"
                ],
                "mobile_data": templateSection["devicePolicy"]["esperSettingsApp"][
                    "mobileData"
                ],
                "bluetooth": templateSection["devicePolicy"]["esperSettingsApp"][
                    "bluetooth"
                ],
                "language": templateSection["devicePolicy"]["esperSettingsApp"][
                    "language"
                ],
                "time_and_date": templateSection["devicePolicy"]["esperSettingsApp"][
                    "timeAndDate"
                ],
                "storage": templateSection["devicePolicy"]["esperSettingsApp"][
                    "storage"
                ],
            },
            "only_dock_accessible": templateSection["devicePolicy"]["esperSettingsApp"][
                "onlyDockAccessible"
            ],
            "admin_mode_password": templateSection["devicePolicy"]["esperSettingsApp"][
                "adminModePassword"
            ],
        },
        "locked": False,
        "section_type": "Independent",
        "enable_android_settings_app": templateSection["devicePolicy"][
            "enableAndroidSettingsApp"
        ],
        "config_json": templateSection["customSettingsConfig"]
        if "customSettingsConfig" in templateSection
        else {},
    }

    blueprint["latest_revision"]["security"] = {
        "password_quality": templateSection["securityPolicy"]["devicePasswordPolicy"][
            "passwordQuality"
        ],
        "minimum_password_length": templateSection["securityPolicy"][
            "devicePasswordPolicy"
        ]["minimumPasswordLength"],
        "locked": False,
        "section_type": "Independent",
        "adb_disabled": templateSection["settings"]["adbDisabled"],
        "screen_off_timeout": templateSection["settings"]["screenOffTimeout"],
        "factory_reset_disabled": templateSection["devicePolicy"][
            "factoryResetDisabled"
        ],
        "keyguard_disabled": templateSection["devicePolicy"]["keyguardDisabled"],
        "safe_boot_disabled": templateSection["devicePolicy"]["safeBootDisabled"],
    }

    blueprint["latest_revision"]["google_services"] = {
        "max_account": 0
        if "googleAccountPermission" not in templateSection["devicePolicy"]
        else templateSection["devicePolicy"]["googleAccountPermission"]["maxAccount"],
        "emails": None,
        "domains": None,
        "frp_googles": templateSection["securityPolicy"]["frpGoogles"],
        "locked": False,
        "section_type": "Independent",
        "disable_play_store": templateSection["devicePolicy"]["disablePlayStore"],
        "managed_google_play_disabled": templateSection["application"][
            "managedGooglePlayDisabled"
        ],
        "google_assistant_disabled": templateSection["devicePolicy"][
            "googleAssistantDisabled"
        ],
    }

    blueprint["latest_revision"]["system_updates"] = {
        "type": templateSection["securityPolicy"]["deviceUpdatePolicy"]["type"],
        "locked": False,
        "section_type": "Independent",
        "maintenance_start": templateSection["securityPolicy"]["deviceUpdatePolicy"][
            "maintenanceStart"
        ],
        "maintenance_end": templateSection["securityPolicy"]["deviceUpdatePolicy"][
            "maintenanceEnd"
        ],
    }

    blueprint["latest_revision"]["date_time"] = {
        "locked": False,
        "section_type": "Independent",
        "date_time_config_disabled": templateSection["devicePolicy"][
            "dateTimeConfigDisabled"
        ],
        "timezone_string": templateSection["settings"]["timezoneString"],
        "device_locale": templateSection["settings"]["deviceLocale"],
    }

    blueprint["latest_revision"]["hardware_settings"] = {
        "gps_state": templateSection["settings"]["gpsState"],
        "locked": False,
        "section_type": "Independent",
        "usb_file_transfer_disabled": templateSection["devicePolicy"][
            "usbFileTransferDisabled"
        ],
        "tethering_disabled": templateSection["devicePolicy"]["tetheringDisabled"],
        "camera_disabled": templateSection["devicePolicy"]["cameraDisabled"],
        "usb_connectivity_disabled": templateSection["devicePolicy"][
            "usbConnectivityDisabled"
        ],
    }

    return blueprint


def editBlueprintApps(groupId, body):
    url = "{tenant}/enterprise/{enterprise_id}/devicegroup/{group_id}/blueprint/".format(
        tenant=Globals.configuration.host,
        enterprise_id=Globals.enterprise_id,
        group_id=groupId,
    )
    # body = {
    #     "name": "JSON App Config",
    #     "description": "",
    #     "latest_revision": {
    #         "locked": False,
    #         "comments": "",
    #         "connectivity": {
    #             "sms_disabled": True,
    #             "enable_bluetooth": True,
    #             "wifi_state": True,
    #             "nfc_beam_disabled": True,
    #             "wifi_settings": [],
    #             "locked": False,
    #         },
    #         "sound": {
    #             "alarm_volume": 50,
    #             "music_volume": 50,
    #             "ring_volume": 50,
    #             "notification_volume": 50,
    #             "locked": False,
    #         },
    #         "display_branding": {
    #             "screenshot_disabled": False,
    #             "status_bar_disabled": False,
    #             "rotation_state": "AUTO",
    #             "brightness_scale": 75,
    #             "wallpapers": None,
    #             "locked": False,
    #         },
    #         "hardware_settings": {
    #             "gps_state": "LOCATION_MODE_HIGH_ACCURACY",
    #             "usb_file_transfer_disabled": True,
    #             "tethering_disabled": True,
    #             "camera_disabled": True,
    #             "usb_connectivity_disabled": True,
    #             "locked": False,
    #         },
    #         "date_time": {
    #             "timezone_string": None,
    #             "device_locale": None,
    #             "date_time_config_disabled": False,
    #             "locked": False,
    #         },
    #         "settings_app": {
    #             "enable_android_settings_app": True,
    #             "settings_access_level": "SHOONYA",
    #             "esper_settings_app": {
    #                 "only_dock_accessible": False,
    #                 "admin_mode_password": "1234",
    #                 "esper_settings_app_policy": {
    #                     "flashlight": "USER",
    #                     "wifi": "USER",
    #                     "auto_rotation": "USER",
    #                     "reboot": "USER",
    #                     "kiosk_app_selection": "USER",
    #                     "esper_branding": "USER",
    #                     "factory_reset": "USER",
    #                     "about": "USER",
    #                     "display": "USER",
    #                     "sound": "USER",
    #                     "keyboard": "USER",
    #                     "input_selection": "USER",
    #                     "accessibility": "USER",
    #                     "mobile_data": "USER",
    #                     "bluetooth": "USER",
    #                     "language": "USER",
    #                     "time_and_date": "USER",
    #                     "clear_app_data": "USER",
    #                     "storage": "USER",
    #                 },
    #             },
    #             "config_json": {
    #                 "managedAppConfigurations": {
    #                     "com.android.chrome": {
    #                         "URLAllowlist": [
    #                             "https://service.smartstartinc.com/User/Login"
    #                         ],
    #                         "URLBlocklist": ["*"],
    #                         "BrowserSignin": "0",
    #                         "HomepageLocation": "https://service.smartstartinc.com/User/Login",
    #                     }
    #                 }
    #             },
    #             "locked": False,
    #         },
    #         "system_updates": {
    #             "type": "TYPE_INSTALL_DISABLED",
    #             "locked": False,
    #             "maintenance_start": None,
    #             "maintenance_end": None,
    #         },
    #         "google_services": {
    #             "disable_play_store": True,
    #             "google_assistant_disabled": True,
    #             "managed_google_play_disabled": True,
    #             "max_account": 0,
    #             "emails": None,
    #             "domains": None,
    #             "frp_googles": [],
    #             "locked": False,
    #         },
    #         "security": {
    #             "password_quality": "PASSWORD_QUALITY_UNSPECIFIED",
    #             "minimum_password_length": 4,
    #             "adb_disabled": True,
    #             "safe_boot_disabled": True,
    #             "screen_off_timeout": 5000,
    #             "factory_reset_disabled": False,
    #             "keyguard_disabled": True,
    #             "locked": False,
    #         },
    #         "application": {
    #             "app_mode": "MULTI_APP",
    #             "disable_local_app_install": False,
    #             "launcher_less_dpc": False,
    #             "app_uninstall_disabled": False,
    #             "apps": [
    #                 {
    #                     "is_g_play": False,
    #                     "app_version": "14c0f0c2-a7e2-4843-bc2e-7096c27b3f7f",
    #                     "state": "SHOW",
    #                     "application_name": "Esper Blog",
    #                     "version_codes": ["1.0"],
    #                     "package_name": "com.esper.EsperBlog",
    #                     "installation_rule": "DURING",
    #                     "release_name": "0",
    #                 }
    #             ],
    #             "permission_policy": "PERMISSION_POLICY_AUTO_GRANT",
    #             "preload_apps": [
    #                 {"package_name": "com.android.chrome", "state": "SHOW"}
    #             ],
    #             "start_on_boot": None,
    #             "launch_on_start": None,
    #             "locked": False,
    #         },
    #         "content": {"files": [], "locked": False},
    #     },
    # }

    if body["latest_revision"]["security"]["password_quality"] == "PASSWORD_QUALITY_UNSPECIFIED" and "minimum_password_length" in body["latest_revision"]["security"]:
        del body["latest_revision"]["security"]["minimum_password_length"]

    resp = performPostRequestWithRetry(url, json=body, headers=getHeader())

    return resp


def pushBlueprintUpdate(blueprintId, groupId, schedule=None, schedule_type="IMMEDIATE"):
    body = {
        "command_type": "GROUP",
        "command_args": {
            "apply_all": True,
            # "group_url": "undefineddevicegroup/%s/" % groupId,
            "blueprint_revision_id": blueprintId,
        },
        "devices": [],
        "groups": [groupId] if type(groupId) is str else groupId,
        "device_type": "all",
        "command": "UPDATE_BLUEPRINT",
        "schedule": schedule_type,
        "schedule_args": schedule
    }
    resp, jsonResp = postEsperCommand(command_data=body)

    return resp, jsonResp


def modifyAppsInBlueprints(blueprints, apps, changedList, addToAppListIfNotPresent=True):
    success = 0
    total = 0
    for bp in blueprints["results"]:
        resp = getGroupBlueprintDetail(bp["group"], bp["id"])
        if resp:
            resp = resp.json()
            for app in apps:
                match = list(
                    filter(
                        lambda x: app["package"] == x["package_name"],
                        resp["latest_revision"]["application"]["apps"],
                    )
                )
                changed = False

                if match:
                    # Check each blueprint to see if app is present, update entry
                    appList = []
                    for bpApp in resp["latest_revision"]["application"]["apps"]:
                        if bpApp["package_name"] == app["package"]:
                            changed = True
                            appList.append({
                                "is_g_play": app["isPlayStore"],
                                "app_version": app["versionId"],
                                "state": bpApp["state"],
                                "application_name": app["name"],
                                "version_codes": app["codes"],
                                "package_name": app["package"],
                                "installation_rule": bpApp["installation_rule"],
                                "release_name": app["releaseName"],
                            })
                        else:
                            appList.append(bpApp)
                    resp["latest_revision"]["application"]["apps"] = appList
                elif addToAppListIfNotPresent:
                    # Go through and add or update app entry
                    resp["latest_revision"]["application"]["apps"].append({
                        "is_g_play": app["isPlayStore"],
                        "app_version": app["versionId"],
                        "state": "SHOW",
                        "application_name": app["name"],
                        "version_codes": app["codes"],
                        "package_name": app["package"],
                        "installation_rule": "DURING",
                        "release_name": app["releaseName"],
                    })
                    changed = True
            if changed:
                total += 1
                # updateResp = pushBlueprintUpdate(bp["group"], bp["id"])
                updateResp = editBlueprintApps(bp["group"], resp)
                if updateResp and updateResp.status_code < 300:
                    changedList.append(bp)
                    success += 1
    postEventToFrame(
        eventUtil.myEVT_PROCESS_FUNCTION,
        (Globals.frame.displayBlueprintActionDlg, (success, total)),
    )
    return success, total
