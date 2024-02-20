#!/usr/bin/env python

import math
import platform
import time
from datetime import datetime

import pytz
import wx
from esperclient.models.v0_command_args import V0CommandArgs
from esperclient.rest import ApiException

import Common.Globals as Globals
import Utility.API.EsperAPICalls as apiCalls
import Utility.EventUtility as eventUtil
import Utility.Threading.wxThread as wxThread
from Common.decorator import api_tool_decorator
from Common.enum import DeviceState, GeneralActions
from Utility.API.AppUtilities import (getDeviceAppsApiUrl, getInstallDevices,
                                      uploadApplication)
from Utility.API.CommandUtility import (executeCommandOnDevice,
                                        executeCommandOnGroup)
from Utility.API.DeviceUtility import (getAllDevices, getDeviceById,
                                       getDeviceDetail, getLatestEvent,
                                       getLatestEventApiUrl, searchForDevice)
from Utility.API.GroupUtility import fetchGroupName, getGroupByIdURL
from Utility.deviceInfo import constructNetworkInfo, getDeviceInitialTemplate
from Utility.GridActionUtility import iterateThroughGridRows
from Utility.GridUtilities import (constructDeviceAppRowEntry,
                                   createDataFrameFromDict)
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Resource import (checkIfCurrentThreadStopped, displayMessageBox,
                              getHeader, ipv6Tomac, postEventToFrame,
                              splitListIntoChunks, utc_to_local)
from Utility.Web.WebRequests import perform_web_requests


@api_tool_decorator()
def TakeAction(frame, input, action, isDevice=False):
    """Calls API To Perform Action And Logs Result To UI"""
    if not Globals.enterprise_id:
        frame.loadConfigPrompt()

    if frame:
        frame.menubar.disableConfigMenu()

    actionName = ""
    if (
        frame.sidePanel.actionChoice.GetValue() in Globals.GRID_ACTIONS
        or frame.sidePanel.actionChoice.GetValue() in Globals.GENERAL_ACTIONS
    ):
        actionName = '"%s"' % frame.sidePanel.actionChoice.GetValue()
    if input:
        frame.Logging("---> Starting Execution " + actionName + " on " + str(input))
    else:
        frame.Logging("---> Starting Execution " + actionName)

    if (
        action == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value
        or action == GeneralActions.GENERATE_APP_REPORT.value
        or action == GeneralActions.GENERATE_INFO_REPORT.value
        or action == GeneralActions.GENERATE_DEVICE_REPORT.value
    ):
        frame.gridPanel.EmptyGrids()
        frame.gridPanel.disableGridProperties()
        if platform.system() == "Windows":
            frame.gridPanel.freezeGrids()
        frame.SpreadsheetUploaded = False

    if action in Globals.GRID_ACTIONS:
        iterateThroughGridRows(frame, action)
    elif isDevice:
        frame.Logging("---> Making API Request")
        if action >= GeneralActions.SET_DEVICE_MODE.value:
            postEventToFrame(
                eventUtil.myEVT_FETCH,
                (action, Globals.enterprise_id, input),
            )
        else:
            api_response = getDeviceById(input, tolerance=1)
            iterateThroughDeviceList(frame, action, api_response, Globals.enterprise_id)
    else:
        if action >= GeneralActions.SET_DEVICE_MODE.value:
            postEventToFrame(
                eventUtil.myEVT_FETCH,
                (action, Globals.enterprise_id, input),
            )
        else:
            # Iterate Through Each Device in Group VIA Api Request
            try:
                frame.Logging("---> Making API Request")
                api_response = getAllDevices(input, tolarance=1)
                iterateThroughDeviceList(
                    frame, action, api_response, Globals.enterprise_id
                )
            except ApiException as e:
                print("Exception when calling DeviceApi->get_all_devices: %s\n" % e)
                ApiToolLog().LogError(e)


def getAdditionalDeviceInfo(deviceId, getApps, getLatestEvents, device, results=None,):
    appResp = latestEvent = None
    if getApps:
        if device.get("os") is not None and device.get("os").lower() == "android":
            appResp = perform_web_requests(
                (
                    getDeviceAppsApiUrl(deviceId, Globals.USE_ENTERPRISE_APP),
                    getHeader(),
                    "GET",
                    None,
                )
            )
        else:
            _, appResp = apiCalls.getIosDeviceApps(deviceId, createAppListArg=False)
            if "content" in appResp:
                appResp = appResp["content"]
            if appResp.get("results"):
                for app in appResp["results"]:
                    if app.get("app_type", "") != "VPP":
                        enterpriseApp = perform_web_requests(
                            (
                                "%s/v2/tenant-apps/%s/" % (
                                    Globals.configuration.host,
                                    app["app_id"]
                                ),
                                getHeader(),
                                "GET",
                                None,
                            )
                        )
                        enterpriseAppVersion = perform_web_requests(
                            (
                                "%s/v2/tenant-apps/%s/versions/%s" % (
                                    Globals.configuration.host,
                                    app["app_id"],
                                    app["app_version_id"]
                                ),
                                getHeader(),
                                "GET",
                                None,
                            )
                        )
                        app.update(enterpriseApp["content"])
                        app.update(enterpriseAppVersion["content"])
                    else:
                        vppResp = perform_web_requests(
                            (
                                "%s/v2/itunesapps/?app_id=%s" % (
                                    Globals.configuration.host,
                                    app["app_id"],
                                ),
                                getHeader(),
                                "GET",
                                None,
                            )
                        )
                        if "content" in vppResp:
                            vppResp = vppResp["content"]
                        if vppResp and "results" in vppResp:
                            vppApp = vppResp["results"][0]
                            app.update(vppApp)
    if getLatestEvents:
        latestEvent = perform_web_requests(
            (
                getLatestEventApiUrl(deviceId),
                getHeader(),
                "GET",
                None,
            )
        )
    if results is not None and type(results) is dict:
        results[deviceId] = {"app": appResp, "event": latestEvent}


def populateDeviceList(device, deviceInfo, appData, latestData, deviceList, indx):
    populateDeviceInfoDictionaryComplieData(device, deviceInfo, appData, latestData)
    deviceInfo["num"] = indx
    deviceList[indx] = deviceInfo


@api_tool_decorator()
def iterateThroughDeviceList(frame, action, api_response, entId):
    """Iterates Through Each Device And Performs A Specified Action"""
    postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 33)

    getApps = (
        action == GeneralActions.GENERATE_APP_REPORT.value
        or action == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value
        or "Applications" in Globals.CSV_TAG_ATTR_NAME.keys()
    ) and (
        action != GeneralActions.GENERATE_DEVICE_REPORT.value
        and action < GeneralActions.SET_DEVICE_MODE.value
    )
    getLatestEvents = (
        action == GeneralActions.GENERATE_INFO_REPORT.value
        or action == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value
    )

    if hasattr(api_response, "results") and len(api_response.results):
        if not Globals.SHOW_DISABLED_DEVICES:
            api_response.results = list(filter(filterDeviceList, api_response.results))

        deviceList = {}
        indx = 0
        Globals.THREAD_POOL.enqueue(
            updateGaugeForObtainingDeviceInfo, deviceList, api_response.results
        )
        for device in api_response.results:
            Globals.THREAD_POOL.enqueue(
                processDeviceInDeviceList,
                device,
                device.id,
                getApps,
                getLatestEvents,
                deviceList,
                indx,
            )
            indx += 1

        Globals.THREAD_POOL.join(tolerance=1)

        postEventToFrame(
            eventUtil.myEVT_FETCH,
            (action, entId, deviceList),
        )
    elif (
        type(api_response) is dict
        and "results" in api_response
        and api_response["results"]
    ):
        if not Globals.SHOW_DISABLED_DEVICES:
            api_response["results"] = list(
                filter(filterDeviceList, api_response["results"])
            )

        deviceList = {}
        indx = 0
        Globals.THREAD_POOL.enqueue(
            updateGaugeForObtainingDeviceInfo, deviceList, api_response["results"]
        )
        for device in api_response["results"]:
            Globals.THREAD_POOL.enqueue(
                processDeviceInDeviceList,
                device,
                device["id"],
                getApps,
                getLatestEvents,
                deviceList,
                indx,
            )
            indx += 1

        Globals.THREAD_POOL.join(tolerance=1)

        postEventToFrame(
            eventUtil.myEVT_FETCH,
            (action, entId, deviceList),
        )
    else:
        if checkIfCurrentThreadStopped():
            return
        frame.Logging("---> No devices found for group")
        frame.isRunning = False
        displayMessageBox(("No devices found for group.", wx.ICON_INFORMATION))
        postEventToFrame(eventUtil.myEVT_COMPLETE, (True))


def processDeviceInDeviceList(
    device, deviceId, getApps, getLatestEvents, deviceList, indx, maxDevices=None
):
    additionalInfo = {}
    getAdditionalDeviceInfo(deviceId, getApps, getLatestEvents, device, additionalInfo)
    deviceInfo = {}
    latestData = appData = None
    if deviceId in additionalInfo:
        latestData = additionalInfo[deviceId]["event"]
        appData = additionalInfo[deviceId]["app"]
    if latestData and "results" in latestData and latestData["results"]:
        latestData = latestData["results"][0]["data"]
    populateDeviceList(
        device,
        deviceInfo,
        appData,
        latestData,
        deviceList,
        indx,
    )
    if maxDevices:
        postEventToFrame(
            eventUtil.myEVT_UPDATE_GAUGE, (int(len(deviceList) / maxDevices * 15)) + 10
        )


def updateGaugeForObtainingDeviceInfo(processed, deviceList):
    initProgress = 33
    progress = initProgress
    while progress < 66:
        rate = len(processed) / len(deviceList)
        adjustedRate = rate * (66 - initProgress)
        percent = int(adjustedRate + initProgress)
        if percent > initProgress:
            progress = percent
            postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, percent)
            time.sleep(0.1)


def filterDeviceList(device):
    deviceStatus = DeviceState.DISABLED.value
    if hasattr(device, "state"):
        deviceStatus = device.status
    elif type(device) == dict and "state" in device:
        deviceStatus = device["state"]
    if not Globals.SHOW_DISABLED_DEVICES and deviceStatus == DeviceState.DISABLED.value:
        return False
    return True


def fetchInstalledDevices(app, version, inFile):
    Globals.THREAD_POOL.results()  # reset results to ensure no additional data is processed
    resp = getInstallDevices(version, app, tolarance=1)
    res = []
    for r in resp.results:
        if r and hasattr(r, "to_dict"):
            res.append(r.to_dict())
        elif r and type(r) is dict:
            res.append(r)
    postEventToFrame(
        eventUtil.myEVT_LOG,
        "---> Get Installed Devices API Request Finished. Gathering Device Info...",
    )
    postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 20)
    if res:
        # Get Basic Device Info
        newDeviceList = processInstallDevices(res)
        postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 40)
        if newDeviceList:
            maxThread = int(Globals.MAX_THREAD_COUNT * (2 / 3))
            splitResults = splitListIntoChunks(newDeviceList, maxThread=maxThread)
            # Get Extended Device Info & Compile
            if splitResults:
                number_of_devices = 0
                postEventToFrame(
                    eventUtil.myEVT_LOG, "---> Gathering Device's Network and App Info"
                )
                for chunk in splitResults:
                    Globals.THREAD_POOL.enqueue(
                        fillInDeviceInfoDict, chunk, number_of_devices, True, False
                    )
                    number_of_devices += len(chunk)
            Globals.THREAD_POOL.join(tolerance=1)
            postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 60)
            # Write to CSV
            deviceList = Globals.THREAD_POOL.results()
            if deviceList:
                devices = {}
                for num in range(len(deviceList)):
                    devices.update(deviceList[num])
                deviceList = devices
                # Populate app grid
                input = []
                for data in deviceList.values():
                    input.extend(data["AppsEntry"])
                df = createDataFrameFromDict(Globals.CSV_APP_ATTR_NAME, input)
                Globals.frame.gridPanel.app_grid.applyNewDataFrame(
                    df, checkColumns=False, resetPosition=True
                )
                Globals.frame.gridPanel.app_grid_contents = df.copy(deep=True)

                postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 80)
                Globals.frame.saveGridData(
                    inFile,
                    action=GeneralActions.GENERATE_APP_REPORT.value,
                    tolarance=1,
                    renameAppCsv=False,
                )
                Globals.frame.sleepInhibitor.uninhibit()
                postEventToFrame(eventUtil.myEVT_COMPLETE, (True, -1))
    else:
        displayMessageBox(
            (
                "No devices with the selected app version(s) found",
                wx.ICON_INFORMATION,
            )
        )
        postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE_LATER, (3000, 0))
        Globals.frame.setCursorDefault()
        Globals.frame.toggleEnabledState(True)


def processInstallDevices(deviceList):
    postEventToFrame(
        eventUtil.myEVT_LOG, "---> Getting Device Info for Installed Devices"
    )
    postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 33)
    newDeviceList = []
    for device in deviceList:
        Globals.THREAD_POOL.enqueue(
            processInstallDevicesHelper, device, newDeviceList, Globals.MAX_THREAD_COUNT
        )
    time.sleep(1)
    Globals.THREAD_POOL.join(tolerance=1)
    postEventToFrame(
        eventUtil.myEVT_LOG, "---> Gathered Basic Device Info for Installed Devices"
    )
    postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 50)
    # processCollectionDevices({"results": newDeviceList})
    return newDeviceList


def processInstallDevicesHelper(device, newDeviceList, tolerance=1):
    id = device["id"]
    deviceListing = getDeviceById(id, tolerance=tolerance, log=False)
    newDeviceList.append(deviceListing)


@api_tool_decorator()
def processCollectionDevices(collectionList):
    if "results" in collectionList and collectionList["results"]:
        maxThread = int(Globals.MAX_THREAD_COUNT * (2 / 3))
        splitResults = splitListIntoChunks(
            collectionList["results"], maxThread=maxThread
        )
        if splitResults:
            number_of_devices = 0
            postEventToFrame(
                eventUtil.myEVT_LOG, "---> Gathering Device's Network and App Info"
            )
            for chunk in splitResults:
                Globals.THREAD_POOL.enqueue(
                    fillInDeviceInfoDict, chunk, number_of_devices
                )
                number_of_devices += len(chunk)

            res = wxThread.waitTillThreadsFinish(
                Globals.THREAD_POOL.threads,
                GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value,
                Globals.enterprise_id,
                3,
                tolerance=1,
            )
            postEventToFrame(
                eventUtil.myEVT_FETCH,
                res,
            )
    else:
        if Globals.frame:
            Globals.frame.Logging("---> No devices found for EQL query")
            Globals.frame.isRunning = False
        postEventToFrame(
            eventUtil.myEVT_MESSAGE_BOX,
            ("No devices found for EQL query.", wx.ICON_INFORMATION),
        )
        postEventToFrame(eventUtil.myEVT_COMPLETE, (True))


@api_tool_decorator()
def fillInDeviceInfoDict(chunk, number_of_devices, getApps=True, getLatestEvent=True):
    deviceList = {}
    for device in chunk:
        if checkIfCurrentThreadStopped():
            return
        try:
            deviceInfo = {}
            deviceInfo = populateDeviceInfoDictionary(
                device, deviceInfo, getApps, getLatestEvent
            )
            if deviceInfo:
                deviceList[number_of_devices] = deviceInfo
                number_of_devices += 1
        except Exception as e:
            print(e)
            ApiToolLog().LogError(e)
    return deviceList


@api_tool_decorator()
def unpackageDict(deviceInfo, deviceDict):
    """ Try to merge dicts into one dict, in a single layer """
    if not deviceDict:
        return deviceInfo
    flatDict = flatten_dict(deviceDict)
    for k, v in flatDict.items():
        deviceInfo[k] = v
    return deviceInfo


def flatten_dict(d: dict):
    return dict(_flatten_dict_gen(d))


def _flatten_dict_gen(d):
    if type(d) is dict:
        for k, v in d.items():
            if isinstance(v, dict):
                yield from flatten_dict(v).items()
            else:
                yield k, v


@api_tool_decorator()
def populateDeviceInfoDictionaryComplieData(
    device, deviceInfo, appData, latestEventData
):
    """Populates Device Info Dictionary"""
    if type(device) == dict:
        deviceStatus = device["state"]
        if (
            not Globals.SHOW_DISABLED_DEVICES
            and deviceStatus == DeviceState.DISABLED.value
        ):
            return
        unpackageDict(deviceInfo, device)

    if device.get("os") is not None and device.get("os").lower() == "android":
        androidDeviceInfo = getDeviceById(device.get("id"), do_join=False)
        unpackageDict(deviceInfo, androidDeviceInfo)

    deviceInfo = compileDeviceGroupData(deviceInfo)
    deviceInfo = compileDeviceHardwareData(device, deviceInfo, latestEventData)
    deviceInfo = compileDeviceAppData(deviceInfo, appData)
    deviceInfo = compileDeviceNetworkData(device, deviceInfo, latestEventData)
    deviceInfo = enforceGridData(device, deviceInfo, latestEventData, appData)

    return deviceInfo


def compileDeviceGroupData(deviceInfo):
    deviceGroups = None
    if "groups" in deviceInfo:
        deviceGroups = deviceInfo["groups"]
    elif "group" in deviceInfo:
        deviceGroups = deviceInfo["group"]
    elif "group_id" in deviceInfo:
        deviceGroups = deviceInfo["group_id"]
    if deviceGroups:
        groupNames = []
        group = groupName = ""
        if type(deviceGroups) == list:
            for groupURL in deviceGroups:
                group = None
                groupName = None
                groupId = groupURL.split("/")[-2]
                deviceInfo["groupId"] = groupId
                if groupId in Globals.knownGroups:
                    group = Globals.knownGroups[groupId]
                else:
                    groupName = fetchGroupName(groupURL, True)
                    Globals.knownGroups[groupId] = groupName
                    groupName = groupName["name"]

                if type(group) == list and len(group) == 1:
                    groupName = group[0]
                elif Globals.SHOW_GROUP_PATH and type(group) == dict:
                    groupName = group["path"]
                elif type(group) == dict:
                    groupName = group["name"]
                elif Globals.SHOW_GROUP_PATH and hasattr(group, "path"):
                    groupName = group.path
                elif hasattr(group, "name"):
                    groupName = group.name

                if groupName:
                    groupNames.append(groupName)
        elif (
            type(deviceGroups) == dict
            and Globals.SHOW_GROUP_PATH
            and "name" in deviceGroups
        ):
            groupNames.append(deviceGroups["path"])
        elif type(deviceGroups) == dict and "name" in deviceGroups:
            groupNames.append(deviceGroups["name"])
        elif type(deviceGroups) == str:
            if deviceGroups in Globals.knownGroups:
                group = Globals.knownGroups[deviceGroups]
            else:
                groupName = fetchGroupName(getGroupByIdURL(deviceGroups), True)
                Globals.knownGroups[groupId] = groupName
                groupName = groupName["name"]

            if type(group) == list and len(group) == 1:
                groupName = group[0]
            elif Globals.SHOW_GROUP_PATH and type(group) == dict:
                groupName = group["path"]
            elif type(group) == dict:
                groupName = group["name"]
            elif Globals.SHOW_GROUP_PATH and hasattr(group, "path"):
                groupName = group.path
            elif hasattr(group, "name"):
                groupName = group.name

            if groupName:
                groupNames.append(groupName)

        if len(groupNames) == 1:
            if type(groupNames[0]) == list:
                deviceInfo["groups"] = groupNames[0][0]
            else:
                deviceInfo["groups"] = groupNames[0]
        elif len(groupNames) == 0:
            deviceInfo["groups"] = ""
        else:
            deviceInfo["groups"] = groupNames

    if "isSupervisorPluginActive" not in deviceInfo:
        deviceInfo["isSupervisorPluginActive"] = "N/A"
    elif not deviceInfo["isSupervisorPluginActive"]:
        deviceInfo["isSupervisorPluginActive"] = "False"

    if "isKnoxActive" not in deviceInfo:
        deviceInfo["isKnoxActive"] = "N/A"
    elif "isSupervisorPluginActive" not in deviceInfo:
        deviceInfo["isSupervisorPluginActive"] = "N/A"

    if "isCSDKActive" not in deviceInfo:
        deviceInfo["isCSDKActive"] = "N/A"
    elif not deviceInfo["isCSDKActive"]:
        deviceInfo["isCSDKActive"] = "False"

    return deviceInfo


def compileDeviceNetworkData(device, deviceInfo, latestEvent):
    location_info = getValueFromLatestEvent(latestEvent, "locationEvent")
    network_info = getValueFromLatestEvent(latestEvent, "networkEvent")
    unpackageDict(deviceInfo, latestEvent)

    if "audioSettings" in deviceInfo:
        for audio in deviceInfo["audioSettings"]:
            if "audioStream" in audio and "volumeLevel" in audio:
                deviceInfo[audio["audioStream"]] = audio["volumeLevel"]

    if location_info:
        if (
            "n/a" not in location_info["locationAlts"].lower()
            and "n/a" not in location_info["locationLats"].lower()
            and "n/a" not in location_info["locationLongs"].lower()
        ):
            location_info = "%s, %s, %s" % (
                location_info["locationAlts"],
                location_info["locationLats"],
                location_info["locationLongs"],
            )
        else:
            location_info = "Unknown"
    else:
        location_info = "Unknown"

    deviceInfo["location_info"] = location_info
    deviceInfo["network_event"] = network_info

    if "gpsState" not in deviceInfo or not deviceInfo["gpsState"]:
        deviceInfo["gpsState"] = "No data available"

    if network_info and "createTime" in network_info:
        deviceInfo["last_seen"] = parseLastSeen(network_info["createTime"])
    elif "last_seen" in deviceInfo and deviceInfo["last_seen"]:
        deviceInfo["last_seen"] = parseLastSeen(deviceInfo["last_seen"])
    else:
        deviceInfo["last_seen"] = "No data available"

    deviceInfo["macAddress"] = []
    ipKey = None
    if "ipAddress" in deviceInfo:
        ipKey = "ipAddress"
    elif "ip_address" in deviceInfo:
        ipKey = "ip_address"
    if ipKey:
        deviceInfo["ipv4Address"] = []
        deviceInfo["ipv6Address"] = []
        if ipKey in deviceInfo and deviceInfo[ipKey]:
            for ip in deviceInfo[ipKey]:
                if ":" not in ip:
                    deviceInfo["ipv4Address"].append(ip)
                else:
                    deviceInfo["ipv6Address"].append(ip)
                    deviceInfo["macAddress"].append(ipv6Tomac(ip))

    if "bluetooth_state" in deviceInfo:
        deviceInfo["bluetoothState"] = deviceInfo["bluetooth_state"]
    if "paired_devices" in deviceInfo:
        deviceInfo["pairedDevices"] = deviceInfo["paired_devices"]
    if "connected_devices" in deviceInfo:
        deviceInfo["connectedDevices"] = deviceInfo["connected_devices"]
    if "mac_address" in deviceInfo:
        deviceInfo["wifiMacAddress"] = deviceInfo["mac_address"]

    if "memoryEvents" in deviceInfo and deviceInfo["memoryEvents"]:
        for event in deviceInfo["memoryEvents"]:
            if "eventType" in event and "countInMb" in event:
                deviceInfo[event["eventType"]] = event["countInMb"]

    deviceInfo["network_info"] = constructNetworkInfo(device, deviceInfo)

    return deviceInfo


def compileDeviceHardwareData(device, deviceInfo, latestEventData):
    deviceId = device["id"]
    deviceStatus = device["state"]
    deviceTags = device.get("tags", [])

    deviceAlias = None
    if "alias_name" in device:
        deviceAlias = device["alias_name"]
    elif "alias" in device:
        deviceAlias = device["alias"]

    deviceHardware = None
    if "hardwareInfo" in device:
        deviceHardware = device["hardwareInfo"]
    elif "hardware" in device:
        deviceHardware = device["hardware"]

    if "device_name" in device:
        deviceInfo["EsperName"] = device["device_name"]
    elif "name" in device:
        deviceInfo["EsperName"] = device["name"]

    isTemplate = True
    if Globals.frame:
        isTemplate = not Globals.frame.blueprintsEnabled

    if Globals.GET_DEVICE_LANGUAGE and isTemplate:
        deviceInfo["templateDeviceLocale"] = "N/A"
        resp = getDeviceInitialTemplate(deviceId)
        if "template" in resp:
            if "device_locale" in resp["template"]["settings"]:
                deviceInfo["templateDeviceLocale"] = resp["template"]["settings"][
                    "device_locale"
                ]
            else:
                deviceInfo["templateDeviceLocale"] = "N/A"
        else:
            deviceInfo["templateDeviceLocale"] = "N/A"
    elif not isTemplate:
        deviceInfo["templateDeviceLocale"] = "Not Fetched/Incompatible Field"
    else:
        deviceInfo["templateDeviceLocale"] = "Not Fetched"

    if bool(deviceAlias):
        deviceInfo["Alias"] = deviceAlias
    else:
        deviceInfo["Alias"] = ""

    deviceState = parseDeviceState(deviceStatus)
    if deviceState:
        deviceInfo["Status"] = deviceState
    else:
        return

    kioskMode = None
    if "current_app_mode" in deviceInfo:
        kioskMode = deviceInfo["current_app_mode"]
        if kioskMode == 0:
            deviceInfo["Mode"] = "Kiosk"
        else:
            deviceInfo["Mode"] = "Multi"

    hdwareKey = None
    if deviceHardware and "serial_number" in deviceHardware:
        hdwareKey = "serial_number"
    elif deviceHardware and "serialNumber" in deviceHardware:
        hdwareKey = "serialNumber"

    custHdwareKey = None
    if deviceHardware and "custom_serial_number" in deviceHardware:
        custHdwareKey = "custom_serial_number"
    elif deviceHardware and "customSerialNumber" in deviceHardware:
        custHdwareKey = "customSerialNumber"

    if Globals.REPLACE_SERIAL:
        if custHdwareKey and bool(deviceHardware[custHdwareKey]):
            deviceInfo["Serial"] = str(deviceHardware[custHdwareKey])
        elif hdwareKey and bool(deviceHardware[hdwareKey]):
            deviceInfo["Serial"] = str(deviceHardware[hdwareKey])
        else:
            deviceInfo["Serial"] = ""
    else:
        if hdwareKey and bool(deviceHardware[hdwareKey]):
            deviceInfo["Serial"] = str(deviceHardware[hdwareKey])
        else:
            deviceInfo["Serial"] = ""

    if Globals.REPLACE_SERIAL:
        deviceInfo["Custom Serial"] = ""
    else:
        if custHdwareKey and bool(deviceHardware[custHdwareKey]):
            deviceInfo["Custom Serial"] = str(deviceHardware[custHdwareKey])
        else:
            deviceInfo["Custom Serial"] = ""

    if bool(deviceTags):
        # Add Functionality For Modifying Multiple Tags
        deviceInfo["Tags"] = deviceTags
    else:
        deviceInfo["Tags"] = ""

        if hasattr(device, "tags") and (
            device.tags is None or (type(device.tags) is list and not device.tags)
        ):
            device.tags = []
        elif (
            device
            and hasattr(device, "__iter__")
            and "tags" in device
            and (
                device["tags"] is None
                or (type(device["tags"]) is list and not device["tags"])
            )
        ):
            device["tags"] = []

    if kioskMode == 0:
        kioskModeApp = getValueFromLatestEvent(latestEventData, "kioskAppName")
        deviceInfo["KioskApp"] = str(kioskModeApp)
    else:
        deviceInfo["KioskApp"] = ""

    if "lockdown_state" in deviceInfo:
        deviceInfo["lockdown_state"] = not bool(deviceInfo["lockdown_state"])

    if device and hasattr(device, "provisioned_on") and device.provisioned_on:
        provisionedOnDate = utc_to_local(device.provisioned_on)
        deviceInfo["provisioned_on"] = str(provisionedOnDate)

    if "eeaVersion" not in deviceInfo:
        deviceInfo["eeaVersion"] = "Non-Foundation"

    if "emm_device" not in deviceInfo:
        deviceInfo["emm_device"] = None

    deviceInfo["is_emm"] = False
    if "user" in deviceInfo:
        if deviceInfo["user"]:
            deviceInfo["is_emm"] = True

    return deviceInfo


def parseDeviceState(state):
    returnVal = ""
    stringState = str(state)

    if isinstance(state, str):
        state = state.lower()

    if stringState == "online" or stringState == "active"  or state == DeviceState.ACTIVE.value:
        returnVal = "Active"
    elif "unspecified" in stringState or state == DeviceState.DEVICE_STATE_UNSPECIFIED.value:
        returnVal = "Unspecified"
    elif ("provisioning" in stringState 
          or (
              state >= DeviceState.PROVISIONING_BEGIN.value 
              and state < DeviceState.INACTIVE.value
            ) 
          or (
            state >= DeviceState.ONBOARDING_IN_PROGRESS.value
            and state <= DeviceState.ONBOARDED.value
        )):
        returnVal = "Onboarding"
    elif ("blueprint" in stringState or (
            state >= DeviceState.AFW_ACCOUNT_ADDED.value
            and state <= DeviceState.CUSTOM_SETTINGS_PROCESSED.value
        )):
        returnVal = "Applying Blueprint"
    elif stringState == "offline" or stringState == "inactive"  or state == DeviceState.INACTIVE.value:
        returnVal = "Inactive"
    elif "wipe" in stringState or state == DeviceState.WIPE_IN_PROGRESS.value:
        returnVal = "Wipe In-Progress"
    elif stringState == "disabled"  or state == DeviceState.DISABLED.value:
        returnVal = "Disabled"
    else:
        returnVal = "Unknown"

    if (
        not Globals.SHOW_DISABLED_DEVICES
        and returnVal == "Disabled"
    ):
        return None
    return returnVal


def parseLastSeen(date):
    returnVal = ""
    datePattern = "%Y-%m-%dT%H:%M:%S.%fZ" if "." in date else "%Y-%m-%dT%H:%MZ"
    if Globals.LAST_SEEN_AS_DATE:
        returnVal = str(
            datetime.strptime(date, datePattern)
        )
    else:
        dt = datetime.strptime(date, datePattern)
        utc_date_time = dt.astimezone(pytz.utc)
        updatedOnDate = utc_to_local(utc_date_time)

        time_delta = utc_to_local(datetime.now()) - updatedOnDate
        total_seconds = time_delta.total_seconds()
        minutes = total_seconds / 60
        if minutes < 0:
            returnVal = "Less than 1 minute ago"
        elif minutes > 0 and minutes < 60:
            returnVal = "%s minutes ago" % minutes
        elif minutes > 60 and minutes < 1440:
            hours = int(math.ceil(minutes / 60))
            returnVal = "%s hours ago" % hours
        elif minutes > 1440:
            days = int(math.ceil(minutes / 1440))
            returnVal = "%s days ago" % days
    return returnVal


def compileDeviceAppData(deviceInfo, appData):
    apps = (
        apiCalls.createAppList(
            appData,
            obtainAppDictEntry=False,
            filterData=True
            if Globals.APP_COL_FILTER
            and not any(len(s) == 0 for s in Globals.APP_COL_FILTER)
            else False,
        )
        if appData
        else []
    )
    json = appData if appData else ""
    deviceInfo["Apps"] = str(apps)
    deviceInfo["appObj"] = json

    return deviceInfo


def enforceGridData(device, deviceInfo, latestEventData, appData):
    for attribute in Globals.CSV_TAG_ATTR_NAME:
        attrKey = Globals.CSV_TAG_ATTR_NAME[attribute]
        attrValue = ""
        if type(attrKey) is str:
            attrValue = (
                deviceInfo[Globals.CSV_TAG_ATTR_NAME[attribute]]
                if Globals.CSV_TAG_ATTR_NAME[attribute] in deviceInfo
                else ""
            )
            deviceInfo[Globals.CSV_TAG_ATTR_NAME[attribute]] = str(attrValue)
        elif type(attrKey) is list:
            for key in attrKey:
                if key in deviceInfo and deviceInfo[key] is not None and deviceInfo[key] != "" and not attrValue:
                    attrValue = deviceInfo[key]
                    deviceInfo[key] = str(attrValue)

    if latestEventData:
        for attribute in Globals.CSV_NETWORK_ATTR_NAME.keys():
            attrKey = Globals.CSV_NETWORK_ATTR_NAME[attribute]
            attrValue = ""
            if type(attrKey) is str:
                attrValue = (
                    deviceInfo["network_info"][attribute]
                    if attribute in deviceInfo["network_info"]
                    else ""
                )
                deviceInfo[Globals.CSV_NETWORK_ATTR_NAME[attribute]] = str(attrValue)
            elif type(attrKey) is list:
                for key in attrKey:
                    if key in deviceInfo and deviceInfo[key] is not None and deviceInfo[key] != "" and not attrValue:
                        attrValue = deviceInfo[key]
                        deviceInfo[key] = str(attrValue)
                    elif deviceInfo["network_info"] and key in deviceInfo["network_info"] and deviceInfo["network_info"][key] and not attrValue:
                        attrValue = deviceInfo["network_info"][key]
                        deviceInfo[key] = str(attrValue)

    if appData and "results" in deviceInfo["appObj"]:
        deviceInfo["AppsEntry"] = []
        constructDeviceAppRowEntry(device, deviceInfo)

    return deviceInfo


@api_tool_decorator()
def populateDeviceInfoDictionary(
    device, deviceInfo, getApps=True, getLatestEvents=True, action=None
):
    """Populates Device Info Dictionary"""
    deviceId = None
    # Handle response from Collections API
    if type(device) == dict:
        deviceId = device["id"]
        deviceStatus = device["status"]
        if (
            not Globals.SHOW_DISABLED_DEVICES
            and deviceStatus == DeviceState.DISABLED.value
        ):
            return
        unpackageDict(deviceInfo, device)
    appThread = None
    if getApps:
        if deviceInfo.get("os") is not None and deviceInfo.get("os").lower() == "android":
            appThread = apiCalls.getAndroidDeviceApps(deviceId, True, Globals.USE_ENTERPRISE_APP)
        else:
            appThread = apiCalls.getIosDeviceApps(deviceId, createAppListArg=True)
    eventThread = None
    if getLatestEvents:
        eventThread = getLatestEvent(deviceId)

    deviceInfo = compileDeviceGroupData(deviceInfo)

    latestEventData = None
    if hasattr(eventThread, "is_alive") and eventThread.is_alive():
        eventThread.join()
    if hasattr(eventThread, "result"):
        latestEventData = eventThread.result
    else:
        latestEventData = eventThread
    deviceInfo = compileDeviceHardwareData(device, deviceInfo, latestEventData)

    if action == GeneralActions.GENERATE_APP_REPORT.value:
        return deviceInfo

    if hasattr(appThread, "is_alive") and appThread.is_alive():
        appThread.join()
    apps = ""
    json = {}
    if hasattr(appThread, "result") and appThread.result:
        apps, json = appThread.result
    elif appThread and type(appThread) is tuple:
        apps, json = appThread
    deviceInfo["Apps"] = str(apps)
    deviceInfo["appObj"] = json

    deviceInfo = compileDeviceNetworkData(device, deviceInfo, latestEventData)

    deviceInfo = enforceGridData(
        device, deviceInfo, latestEventData, deviceInfo["appObj"]
    )

    return deviceInfo


@api_tool_decorator()
def getValueFromLatestEvent(respData, eventName):
    event = ""
    if respData and eventName in respData:
        event = respData[eventName]
    return event


def removeNonWhitelisted(deviceId, deviceInfo=None, isGroup=False):
    detailInfo = None
    if not deviceInfo:
        detailInfo = getDeviceDetail(deviceId)
    else:
        detailInfo = deviceInfo
    wifiAP = detailInfo["wifi_access_points"]
    removeList = []
    for ap in wifiAP:
        ssid = ap["wifi_ssid"]
        if ssid not in Globals.WHITELIST_AP:
            removeList.append(ssid)
    command_args = V0CommandArgs(
        wifi_access_points=removeList,
    )
    if isGroup:
        return executeCommandOnGroup(
            Globals.frame,
            command_args,
            command_type="REMOVE_WIFI_AP",
            groupIds=[deviceId] if type(deviceId) != list else deviceId,
        )
    else:
        return executeCommandOnDevice(
            Globals.frame,
            command_args,
            command_type="REMOVE_WIFI_AP",
            deviceIds=[deviceId] if type(deviceId) != list else deviceId,
        )


def clearKnownGroupsAndBlueprints():
    Globals.knownGroups.clear()
    Globals.knownBlueprints.clear()


def getAllDeviceInfo(frame, action=None, allDevices=True, tolarance=1):
    devices = []
    if len(Globals.frame.sidePanel.selectedDevicesList) > 0 and len(
        Globals.frame.sidePanel.selectedDevicesList
    ) < len(frame.sidePanel.devices):
        labels = list(
            filter(
                lambda key: frame.sidePanel.devices[key]
                in frame.sidePanel.selectedDevicesList,
                frame.sidePanel.devices,
            )
        )
        for label in labels:
            labelParts = label.split("~")
            Globals.THREAD_POOL.enqueue(
                searchForDeviceAndAppendToList, labelParts[2], devices
            )
        Globals.THREAD_POOL.join(tolerance=1, timeout=3 * 60)
    elif len(Globals.frame.sidePanel.selectedGroupsList) >= 0:
        api_response = getAllDevices(
            Globals.frame.sidePanel.selectedGroupsList
            if Globals.frame.sidePanel.selectedGroupsList and not allDevices
            else " ",
            tolarance=tolarance,
            timeout=3 * 60,
        )
        if api_response:
            if (
                api_response
                and hasattr(api_response, "results")
                and api_response.results
            ):
                devices += api_response.results
            elif type(api_response) is dict and "results" in api_response:
                devices += api_response["results"]
        else:
            postEventToFrame(
                eventUtil.myEVT_LOG,
                "---> ERROR: Failed to get devices",
            )

    if not Globals.SHOW_DISABLED_DEVICES:
        devices = list(filter(filterDeviceList, devices))

    postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 10)
    postEventToFrame(eventUtil.myEVT_LOG, "Finished fetching basic device information")

    getApps = False
    getLatestEvents = True

    if action == GeneralActions.GENERATE_APP_REPORT.value:
        getApps = True
        getLatestEvents = False
    elif action == GeneralActions.GENERATE_DEVICE_REPORT.value:
        getApps = False
        getLatestEvents = False
    elif action == GeneralActions.GENERATE_INFO_REPORT.value:
        getApps = False if not Globals.APPS_IN_DEVICE_GRID else True
        getLatestEvents = True
    elif action == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value:
        getApps = True
        getLatestEvents = True

    deviceList = {}
    indx = 0

    if getApps or getLatestEvents:
        postEventToFrame(eventUtil.myEVT_LOG, "Fetching extended device information")
    for device in devices:
        if type(device) is dict:
            Globals.THREAD_POOL.enqueue(
                processDeviceInDeviceList,
                device,
                device["id"],
                getApps,
                getLatestEvents,
                deviceList,
                indx,
                maxDevices=len(devices),
            )
        elif hasattr(device, "id"):
            Globals.THREAD_POOL.enqueue(
                processDeviceInDeviceList,
                device,
                device.id,
                getApps,
                getLatestEvents,
                deviceList,
                indx,
                maxDevices=len(devices),
            )
        indx += 1

    Globals.THREAD_POOL.join(tolerance=tolarance)
    postEventToFrame(
        eventUtil.myEVT_LOG, "Finished fetching extended device information"
    )
    postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 25)

    return deviceList


def searchForDeviceAndAppendToList(searchTerm, listToAppend):
    api_response = searchForDevice(search=searchTerm)
    if (
        type(api_response) is dict
        and "results" in api_response
        and api_response["results"]
    ):
        if len(api_response["results"]) == 1:
            listToAppend += api_response["results"]
        else:
            for device in api_response["results"]:
                if device["device_name"] == searchTerm:
                    listToAppend.append(device)
                    break


def getAllDevicesFromOffsets(api_response, devices=[], tolerance=0, timeout=-1):
    count = None
    apiNext = None
    if hasattr(api_response, "count"):
        count = api_response.count
        apiNext = api_response.next
    elif type(api_response) is dict:
        count = api_response["count"]
        apiNext = api_response["next"]
    if apiNext:
        respOffset = apiNext.split("offset=")[-1].split("&")[0]
        respOffsetInt = int(respOffset)
        respLimit = apiNext.split("limit=")[-1].split("&")[0]
        while int(respOffsetInt) < count and int(respLimit) < count:
            Globals.THREAD_POOL.enqueue(
                getAllDevices,
                Globals.frame.sidePanel.selectedGroupsList,
                respLimit,
                respOffset,
            )
            respOffsetInt += int(respLimit)
        Globals.THREAD_POOL.join(tolerance=tolerance, timeout=timeout)
    res = Globals.THREAD_POOL.results()
    for thread in res:
        if hasattr(thread, "results"):
            devices += thread.results
        elif type(thread) is dict:
            devices += thread["results"]
    return devices


def uploadAppToEndpoint(path):
    postEventToFrame(eventUtil.myEVT_LOG, "Attempting to upload app...")
    resp = uploadApplication(path)
    if resp:
        postEventToFrame(eventUtil.myEVT_LOG, "App upload succeed!")
        displayMessageBox(("Application has been uploaded", wx.ICON_INFORMATION))
    else:
        postEventToFrame(eventUtil.myEVT_LOG, "App upload FAILED!")
        displayMessageBox(
            (
                "ERROR: Failed to upload apk. Please try again!",
                wx.ICON_ERROR,
            )
        )
    postEventToFrame(eventUtil.myEVT_COMPLETE, True)
