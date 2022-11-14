#!/usr/bin/env python

import math
import platform
import time
from datetime import datetime

import Common.Globals as Globals
import pytz
import wx
from Common.decorator import api_tool_decorator
from Common.enum import DeviceState, GeneralActions
from esperclient.models.v0_command_args import V0CommandArgs
from esperclient.rest import ApiException

import Utility.API.EsperAPICalls as apiCalls
import Utility.EventUtility as eventUtil
import Utility.Threading.wxThread as wxThread
from Utility.API.AppUtilities import getDeviceAppsApiUrl, uploadApplication
from Utility.API.CommandUtility import executeCommandOnDevice, executeCommandOnGroup
from Utility.API.DeviceUtility import (
    getAllDevices,
    getDeviceById,
    getDeviceDetail,
    getLatestEvent,
    getLatestEventApiUrl,
    searchForDevice,
)
from Utility.API.GroupUtility import fetchGroupName
from Utility.deviceInfo import constructNetworkInfo
from Utility.GridActionUtility import iterateThroughGridRows
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Resource import (
    checkIfCurrentThreadStopped,
    displayMessageBox,
    getHeader,
    ipv6Tomac,
    postEventToFrame,
    splitListIntoChunks,
    utc_to_local,
)
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
        frame.gridPanel.button_2.Enable(False)
        frame.gridPanel.button_1.Enable(False)
        frame.gridPanel.emptyDeviceGrid()
        frame.gridPanel.emptyNetworkGrid()
        frame.gridPanel.emptyAppGrid()
        frame.gridPanel.disableGridProperties()
        if platform.system() == "Windows":
            frame.gridPanel.grid_1.Freeze()
            frame.gridPanel.grid_2.Freeze()
            frame.gridPanel.grid_3.Freeze()
        frame.CSVUploaded = False

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


def getAdditionalDeviceInfo(deviceId, getApps, getLatestEvents, results=None):
    appResp = latestEvent = None
    if getApps:
        appResp = perform_web_requests(
            (
                getDeviceAppsApiUrl(deviceId, Globals.USE_ENTERPRISE_APP),
                getHeader(),
                "GET",
                None,
            )
        )
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
    deviceList[indx] = [device, deviceInfo]


@api_tool_decorator()
def iterateThroughDeviceList(frame, action, api_response, entId):
    """Iterates Through Each Device And Performs A Specified Action"""
    if hasattr(Globals.frame, "start_time"):
        print("Fetch Device time: %s" % (time.time() - Globals.frame.start_time))
    if api_response:
        if hasattr(api_response, "next"):
            if api_response.next:
                frame.gridArrowState["next"] = True
            else:
                frame.gridArrowState["next"] = False
        elif type(api_response) is dict and "next" in api_response:
            if api_response["next"]:
                frame.gridArrowState["next"] = True
            else:
                frame.gridArrowState["next"] = False
        else:
            frame.gridArrowState["next"] = False
        if hasattr(api_response, "previous"):
            if api_response.previous:
                frame.gridArrowState["prev"] = True
            else:
                frame.gridArrowState["prev"] = False
        elif type(api_response) is dict and "previous" in api_response:
            if api_response["previous"]:
                frame.gridArrowState["prev"] = True
            else:
                frame.gridArrowState["prev"] = False
        else:
            frame.gridArrowState["prev"] = False

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
    getAdditionalDeviceInfo(deviceId, getApps, getLatestEvents, additionalInfo)
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
        postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, (int(len(deviceList) / maxDevices * 5)) + 10)


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
    if hasattr(device, "status"):
        deviceStatus = device.status
    elif type(device) == dict and "status" in device:
        deviceStatus = device["status"]
    if not Globals.SHOW_DISABLED_DEVICES and deviceStatus == DeviceState.DISABLED.value:
        return False
    return True


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
    processCollectionDevices({"results": newDeviceList})


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
                deviceList[number_of_devices] = [device, deviceInfo]
                number_of_devices += 1
        except Exception as e:
            print(e)
            ApiToolLog().LogError(e)
    return deviceList


@api_tool_decorator()
def processDevices(
    chunk,
    number_of_devices,
    action,
    getApps=True,
    getLatestEvents=True,
):
    """ Try to obtain more device info for a given device """
    deviceList = {}

    for device in chunk:
        if checkIfCurrentThreadStopped():
            return
        deviceInfo = {}
        deviceInfo = populateDeviceInfoDictionary(
            device, deviceInfo, getApps, getLatestEvents, action
        )
        if deviceInfo:
            number_of_devices = number_of_devices + 1
            deviceInfo["num"] = number_of_devices
            deviceList[number_of_devices] = [device, deviceInfo]

    return (action, deviceList)


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
    deviceId = None
    deviceName = None
    deviceGroups = None
    deviceAlias = None
    deviceStatus = None
    deviceHardware = None
    deviceTags = None
    # Handle response from Collections API
    if type(device) == dict:
        deviceId = device["id"]
        deviceName = device["device_name"]
        deviceGroups = device["groups"]
        deviceAlias = device["alias_name"]
        deviceStatus = device["status"]
        if (
            not Globals.SHOW_DISABLED_DEVICES
            and deviceStatus == DeviceState.DISABLED.value
        ):
            return
        deviceHardware = device["hardwareInfo"]
        deviceTags = device["tags"]
        unpackageDict(deviceInfo, device)
    else:
        # Handles response from Python API
        deviceId = device.id
        deviceName = device.device_name
        deviceGroups = device.groups
        deviceAlias = device.alias_name
        deviceStatus = device.status
        # Device is disabled return
        if (
            not Globals.SHOW_DISABLED_DEVICES
            and deviceStatus == DeviceState.DISABLED.value
        ):
            return
        deviceHardware = device.hardware_info
        deviceTags = device.tags
        deviceDict = device.__dict__
        unpackageDict(deviceInfo, deviceDict)
    latestEvent = None
    deviceInfo["EsperName"] = deviceName

    deviceInfo["id"] = deviceId

    if deviceGroups:
        groupNames = []
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
        if len(groupNames) == 1:
            if type(groupNames[0]) == list:
                deviceInfo["groups"] = groupNames[0][0]
            else:
                deviceInfo["groups"] = groupNames[0]
        elif len(groupNames) == 0:
            deviceInfo["groups"] = ""
        else:
            deviceInfo["groups"] = groupNames

    if bool(deviceAlias):
        deviceInfo["Alias"] = deviceAlias
    else:
        deviceInfo["Alias"] = ""

    if isinstance(deviceStatus, str):
        if deviceStatus.lower() == "online":
            deviceInfo["Status"] = "Online"
        elif "unspecified" in deviceStatus.lower():
            deviceInfo["Status"] = "Unspecified"
        elif "provisioning" in deviceStatus.lower():
            deviceInfo["Status"] = "Provisioning"
        elif deviceStatus.lower() == "offline":
            deviceInfo["Status"] = "Offline"
        elif "wipe" in deviceStatus.lower():
            deviceInfo["Status"] = "Wipe In-Progress"
        elif deviceStatus.lower() == "disabled":
            deviceInfo["Status"] = "Disabled"
        else:
            deviceInfo["Status"] = "Unknown"
    else:
        if (
            not Globals.SHOW_DISABLED_DEVICES
            and deviceStatus == DeviceState.DISABLED.value
        ):
            return

        if deviceStatus == DeviceState.DEVICE_STATE_UNSPECIFIED.value:
            deviceInfo["Status"] = "Unspecified"
        elif deviceStatus == DeviceState.ACTIVE.value:
            deviceInfo["Status"] = "Online"
        elif deviceStatus == DeviceState.DISABLED.value:
            deviceInfo["Status"] = "Disabled"
        elif (
            deviceStatus >= DeviceState.PROVISIONING_BEGIN.value
            and deviceStatus < DeviceState.INACTIVE.value
        ) or (
            deviceStatus >= DeviceState.ONBOARDING_IN_PROGRESS.value
            and deviceStatus <= DeviceState.ONBOARDED.value
        ):
            deviceInfo["Status"] = "Onboarding"
        elif (
            deviceStatus >= DeviceState.AFW_ACCOUNT_ADDED.value
            and deviceStatus <= DeviceState.CUSTOM_SETTINGS_PROCESSED.value
        ):
            deviceInfo["Status"] = "Applying Blueprint"
        elif deviceStatus == DeviceState.INACTIVE.value:
            deviceInfo["Status"] = "Offline"
        elif deviceStatus == DeviceState.WIPE_IN_PROGRESS.value:
            deviceInfo["Status"] = "Wipe In-Progress"
        else:
            deviceInfo["Status"] = "Unknown"

    kioskMode = None
    if "current_app_mode" in deviceInfo:
        kioskMode = deviceInfo["current_app_mode"]
        if kioskMode == 0:
            deviceInfo["Mode"] = "Kiosk"
        else:
            deviceInfo["Mode"] = "Multi"

    hdwareKey = None
    if "serial_number" in deviceHardware:
        hdwareKey = "serial_number"
    elif "serialNumber" in deviceHardware:
        hdwareKey = "serialNumber"

    custHdwareKey = None
    if "custom_serial_number" in deviceHardware:
        custHdwareKey = "custom_serial_number"
    elif "customSerialNumber" in deviceHardware:
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

    apps = (
        apiCalls.createAppList(appData, obtainAppDictEntry=False, filterData=True)
        if appData
        else []
    )
    json = appData if appData else ""
    deviceInfo["Apps"] = str(apps)
    deviceInfo["appObj"] = json

    latestEvent = latestEventData
    if kioskMode == 0:
        kioskModeApp = getValueFromLatestEvent(latestEvent, "kioskAppName")
        deviceInfo["KioskApp"] = str(kioskModeApp)
    else:
        deviceInfo["KioskApp"] = ""

    location_info = getValueFromLatestEvent(latestEvent, "locationEvent")
    network_info = getValueFromLatestEvent(latestEvent, "networkEvent")
    unpackageDict(deviceInfo, latestEvent)

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

    if network_info and "createTime" in network_info:
        if Globals.LAST_SEEN_AS_DATE:
            deviceInfo["last_seen"] = str(
                datetime.strptime(network_info["createTime"], "%Y-%m-%dT%H:%MZ")
            )
        else:
            dt = datetime.strptime(network_info["createTime"], "%Y-%m-%dT%H:%MZ")
            utc_date_time = dt.astimezone(pytz.utc)
            updatedOnDate = utc_to_local(utc_date_time)

            time_delta = utc_to_local(datetime.now()) - updatedOnDate
            total_seconds = time_delta.total_seconds()
            minutes = total_seconds / 60
            if minutes < 0:
                deviceInfo["last_seen"] = "Less than 1 minute ago"
            elif minutes > 0 and minutes < 60:
                deviceInfo["last_seen"] = "%s minute ago" % minutes
            elif minutes > 60 and minutes < 1440:
                hours = int(math.ceil(minutes / 60))
                deviceInfo["last_seen"] = "%s hours ago" % hours
            elif minutes > 1440:
                days = int(math.ceil(minutes / 1440))
                deviceInfo["last_seen"] = "%s days ago" % days
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

    if "lockdown_state" in deviceInfo:
        deviceInfo["lockdown_state"] = bool(deviceInfo["lockdown_state"])

    if "audioSettings" in deviceInfo:
        for audio in deviceInfo["audioSettings"]:
            if "audioStream" in audio and "volumeLevel" in audio:
                deviceInfo[audio["audioStream"]] = audio["volumeLevel"]
            elif "ringerMode" in audio:
                if audio["ringerMode"] == 0:
                    deviceInfo["ringerMode"] = "Silent"
                elif audio["ringerMode"] == 1:
                    deviceInfo["ringerMode"] = "Vibrate"
                elif audio["ringerMode"] == 2:
                    deviceInfo["ringerMode"] = "Normal"

    if "memoryEvents" in deviceInfo and deviceInfo["memoryEvents"]:
        for event in deviceInfo["memoryEvents"]:
            if "eventType" in event and "countInMb" in event:
                deviceInfo[event["eventType"]] = event["countInMb"]

    if device and hasattr(device, "provisioned_on") and device.provisioned_on:
        provisionedOnDate = utc_to_local(device.provisioned_on)
        deviceInfo["provisioned_on"] = str(provisionedOnDate)

    if "eeaVersion" not in deviceInfo:
        deviceInfo["eeaVersion"] = "NON EEA"

    if "emm_device" not in deviceInfo:
        deviceInfo["emm_device"] = None

    deviceInfo["is_emm"] = False
    if "user" in deviceInfo:
        if deviceInfo["user"]:
            deviceInfo["is_emm"] = True

    deviceInfo["network_info"] = constructNetworkInfo(device, deviceInfo)

    for attribute in Globals.CSV_TAG_ATTR_NAME:
        value = (
            deviceInfo[Globals.CSV_TAG_ATTR_NAME[attribute]]
            if Globals.CSV_TAG_ATTR_NAME[attribute] in deviceInfo
            else ""
        )
        deviceInfo[Globals.CSV_TAG_ATTR_NAME[attribute]] = str(value)

    if latestEventData:
        for attribute in Globals.CSV_NETWORK_ATTR_NAME.keys():
            value = (
                deviceInfo["network_info"][attribute]
                if attribute in deviceInfo["network_info"]
                else ""
            )
            deviceInfo[Globals.CSV_NETWORK_ATTR_NAME[attribute]] = str(value)

    if appData and "results" in deviceInfo["appObj"]:
        deviceInfo["AppsEntry"] = []
        info = {}
        for app in deviceInfo["appObj"]["results"]:
            if app["package_name"] not in Globals.BLACKLIST_PACKAGE_NAME:
                info = {
                    "Esper Name": device.device_name
                    if hasattr(device, "device_name")
                    else device["device_name"],
                    "Group": deviceInfo["groups"],
                    "Application Name": app["app_name"],
                    "Application Type": app["app_type"],
                    "Application Version Code": app["version_code"],
                    "Application Version Name": app["version_name"],
                    "Package Name": app["package_name"],
                    "State": app["state"],
                    "Whitelisted": app["whitelisted"],
                    "Can Clear Data": app["is_data_clearable"],
                    "Can Uninstall": app["is_uninstallable"],
                }
            if info and info not in deviceInfo["AppsEntry"]:
                deviceInfo["AppsEntry"].append(info)

    return deviceInfo


@api_tool_decorator()
def populateDeviceInfoDictionary(
    device, deviceInfo, getApps=True, getLatestEvents=True, action=None
):
    """Populates Device Info Dictionary"""
    deviceId = None
    deviceName = None
    deviceGroups = None
    deviceAlias = None
    deviceStatus = None
    deviceHardware = None
    deviceTags = None
    # Handle response from Collections API
    if type(device) == dict:
        deviceId = device["id"]
        deviceName = ""
        if "device_name" in device:
            deviceName = device["device_name"]
        elif "name" in device:
            deviceName = device["name"]
        deviceGroups = ""
        if "groups" in device:
            deviceGroups = device["groups"]
        elif "group" in device:
            deviceGroups = device["group"]
        deviceAlias = ""
        if "alias_name" in device:
            deviceAlias = device["alias_name"]
        elif "alias" in device:
            deviceAlias = device["alias"]
        deviceStatus = device["status"]
        if (
            not Globals.SHOW_DISABLED_DEVICES
            and deviceStatus == DeviceState.DISABLED.value
        ):
            return
        deviceHardware = ""
        if "hardwareInfo" in device:
            deviceHardware = device["hardwareInfo"]
        elif "hardware" in device:
            deviceHardware = device["hardware"]
        deviceTags = device["tags"]
        unpackageDict(deviceInfo, device)
    else:
        # Handles response from Python API
        deviceId = device.id
        deviceName = device.device_name
        deviceGroups = device.groups
        deviceAlias = device.alias_name
        deviceStatus = device.status
        # Device is disabled return
        if (
            not Globals.SHOW_DISABLED_DEVICES
            and deviceStatus == DeviceState.DISABLED.value
        ):
            return
        deviceHardware = device.hardware_info
        deviceTags = device.tags
        deviceDict = device.__dict__
        unpackageDict(deviceInfo, deviceDict)
    appThread = None
    if getApps:
        appThread = apiCalls.getdeviceapps(deviceId, True, Globals.USE_ENTERPRISE_APP)
    eventThread = None
    if getLatestEvents:
        eventThread = getLatestEvent(deviceId)
    latestEvent = None
    deviceInfo["EsperName"] = deviceName

    deviceInfo["id"] = deviceId

    if deviceGroups:
        groupNames = []
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
        if len(groupNames) == 1:
            if type(groupNames[0]) == list:
                deviceInfo["groups"] = groupNames[0][0]
            else:
                deviceInfo["groups"] = groupNames[0]
        elif len(groupNames) == 0:
            deviceInfo["groups"] = ""
        else:
            deviceInfo["groups"] = groupNames

    if action == GeneralActions.GENERATE_APP_REPORT.value:
        return deviceInfo

    if bool(deviceAlias):
        deviceInfo["Alias"] = deviceAlias
    else:
        deviceInfo["Alias"] = ""

    if isinstance(deviceStatus, str):
        if deviceStatus.lower() == "online":
            deviceInfo["Status"] = "Online"
        elif "unspecified" in deviceStatus.lower():
            deviceInfo["Status"] = "Unspecified"
        elif "provisioning" in deviceStatus.lower():
            deviceInfo["Status"] = "Provisioning"
        elif deviceStatus.lower() == "offline":
            deviceInfo["Status"] = "Offline"
        elif "wipe" in deviceStatus.lower():
            deviceInfo["Status"] = "Wipe In-Progress"
        elif deviceStatus.lower() == "disabled":
            deviceInfo["Status"] = "Disabled"
        else:
            deviceInfo["Status"] = "Unknown"
    else:
        if (
            not Globals.SHOW_DISABLED_DEVICES
            and deviceStatus == DeviceState.DISABLED.value
        ):
            return

        if deviceStatus == DeviceState.DEVICE_STATE_UNSPECIFIED.value:
            deviceInfo["Status"] = "Unspecified"
        elif deviceStatus == DeviceState.ACTIVE.value:
            deviceInfo["Status"] = "Online"
        elif deviceStatus == DeviceState.DISABLED.value:
            deviceInfo["Status"] = "Disabled"
        elif (
            deviceStatus >= DeviceState.PROVISIONING_BEGIN.value
            and deviceStatus < DeviceState.INACTIVE.value
        ):
            deviceInfo["Status"] = "Provisioning"
        elif deviceStatus == DeviceState.INACTIVE.value:
            deviceInfo["Status"] = "Offline"
        elif deviceStatus == DeviceState.WIPE_IN_PROGRESS.value:
            deviceInfo["Status"] = "Wipe In-Progress"
        else:
            deviceInfo["Status"] = "Unknown"

    kioskMode = None
    if "current_app_mode" in deviceInfo:
        kioskMode = deviceInfo["current_app_mode"]
        if kioskMode == 0:
            deviceInfo["Mode"] = "Kiosk"
        else:
            deviceInfo["Mode"] = "Multi"

    hdwareKey = None
    if "serial_number" in deviceHardware:
        hdwareKey = "serial_number"
    elif "serialNumber" in deviceHardware:
        hdwareKey = "serialNumber"

    custHdwareKey = None
    if "custom_serial_number" in deviceHardware:
        custHdwareKey = "custom_serial_number"
    elif "customSerialNumber" in deviceHardware:
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

    if hasattr(eventThread, "is_alive") and eventThread.is_alive():
        eventThread.join()
    if kioskMode == 0:
        if hasattr(eventThread, "result"):
            latestEvent = eventThread.result
        else:
            latestEvent = eventThread
        kioskModeApp = getValueFromLatestEvent(latestEvent, "kioskAppName")
        deviceInfo["KioskApp"] = str(kioskModeApp)
    else:
        deviceInfo["KioskApp"] = ""

    if hasattr(eventThread, "result"):
        latestEvent = eventThread.result
    else:
        latestEvent = eventThread
    location_info = getValueFromLatestEvent(latestEvent, "locationEvent")
    network_info = getValueFromLatestEvent(latestEvent, "networkEvent")
    unpackageDict(deviceInfo, latestEvent)

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

    if network_info and "createTime" in network_info:
        if Globals.LAST_SEEN_AS_DATE:
            deviceInfo["last_seen"] = str(
                datetime.strptime(network_info["createTime"], "%Y-%m-%dT%H:%MZ")
            )
        else:
            dt = datetime.strptime(network_info["createTime"], "%Y-%m-%dT%H:%MZ")
            utc_date_time = dt.astimezone(pytz.utc)
            updatedOnDate = utc_to_local(utc_date_time)

            time_delta = utc_to_local(datetime.now()) - updatedOnDate
            total_seconds = time_delta.total_seconds()
            minutes = total_seconds / 60
            if minutes < 0:
                deviceInfo["last_seen"] = "Less than 1 minute ago"
            elif minutes > 0 and minutes < 60:
                deviceInfo["last_seen"] = "%s minute ago" % minutes
            elif minutes > 60 and minutes < 1440:
                hours = int(math.ceil(minutes / 60))
                deviceInfo["last_seen"] = "%s hours ago" % hours
            elif minutes > 1440:
                days = int(math.ceil(minutes / 1440))
                deviceInfo["last_seen"] = "%s days ago" % days
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

    if "lockdown_state" in deviceInfo:
        deviceInfo["lockdown_state"] = bool(deviceInfo["lockdown_state"])

    if "audioSettings" in deviceInfo:
        for audio in deviceInfo["audioSettings"]:
            if "audioStream" in audio and "volumeLevel" in audio:
                deviceInfo[audio["audioStream"]] = audio["volumeLevel"]
            elif "ringerMode" in audio:
                if audio["ringerMode"] == 0:
                    deviceInfo["ringerMode"] = "Silent"
                elif audio["ringerMode"] == 1:
                    deviceInfo["ringerMode"] = "Vibrate"
                elif audio["ringerMode"] == 2:
                    deviceInfo["ringerMode"] = "Normal"

    if "memoryEvents" in deviceInfo and deviceInfo["memoryEvents"]:
        for event in deviceInfo["memoryEvents"]:
            if "eventType" in event and "countInMb" in event:
                deviceInfo[event["eventType"]] = event["countInMb"]

    if device and hasattr(device, "provisioned_on") and device.provisioned_on:
        provisionedOnDate = utc_to_local(device.provisioned_on)
        deviceInfo["provisioned_on"] = str(provisionedOnDate)

    if "eeaVersion" not in deviceInfo:
        deviceInfo["eeaVersion"] = "NON EEA"

    if "emm_device" not in deviceInfo:
        deviceInfo["emm_device"] = None

    deviceInfo["is_emm"] = False
    if "user" in deviceInfo:
        if deviceInfo["user"]:
            deviceInfo["is_emm"] = True

    deviceInfo["network_info"] = constructNetworkInfo(device, deviceInfo)

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


def clearKnownGroups():
    Globals.knownGroups.clear()


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
            timeout=3 * 60
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

    if hasattr(Globals.frame, "start_time"):
        print("Fetch Device time: %s" % (time.time() - Globals.frame.start_time))

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

    for device in devices:
        Globals.THREAD_POOL.enqueue(
            processDeviceInDeviceList,
            device,
            device["id"],
            getApps,
            getLatestEvents,
            deviceList,
            indx,
            maxDevices=len(devices)
        )
        indx += 1

    Globals.THREAD_POOL.join(tolerance=tolarance)
    postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 25)
    postEventToFrame(eventUtil.myEVT_LOG, "Finished fetching extended device information")

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
