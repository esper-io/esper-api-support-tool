#!/usr/bin/env python


from re import search
import esperclient
from esperclient.models.v0_command_args import V0CommandArgs
import Common.Globals as Globals
import Utility.wxThread as wxThread
import threading
import wx
import platform
import Utility.EsperAPICalls as apiCalls
import Utility.EventUtility as eventUtil

from Common.decorator import api_tool_decorator
from Common.enum import GeneralActions

from Utility.CommandUtility import executeCommandOnDevice
from Utility.GridActionUtility import iterateThroughGridRows
from Utility.ApiToolLogging import ApiToolLog
from Utility.Resource import (
    displayMessageBox,
    joinThreadList,
    postEventToFrame,
    ipv6Tomac,
    splitListIntoChunks,
)

from esperclient.rest import ApiException

knownGroups = {}

####Perform Actions. Set Kiosk Mode, Multi App Mode, Tags, or Alias####
@api_tool_decorator()
def TakeAction(frame, group, action, label, isDevice=False, isUpdate=False):
    """Calls API To Perform Action And Logs Result To UI"""
    if not Globals.enterprise_id:
        frame.loadConfigPrompt()

    if frame:
        frame.menubar.disableConfigMenu()

    logActionExecution(frame, action, group)
    if (action == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value) and not isUpdate:
        frame.gridPanel.button_2.Enable(False)
        frame.gridPanel.button_1.Enable(False)
        frame.gridPanel.emptyDeviceGrid()
        frame.gridPanel.emptyNetworkGrid()
        frame.gridPanel.disableGridProperties()
        if platform.system() == "Windows":
            frame.gridPanel.grid_1.Freeze()
            frame.gridPanel.grid_2.Freeze()
        frame.CSVUploaded = False

    deviceList = None
    if isDevice:
        deviceToUse = group
        frame.Logging("---> Making API Request")
        wxThread.doAPICallInThread(
            frame,
            apiCalls.getDeviceById,
            args=(deviceToUse),
            eventType=eventUtil.myEVT_RESPONSE,
            callback=iterateThroughDeviceList,
            callbackArgs=(frame, action),
            optCallbackArgs=(Globals.enterprise_id, False, isUpdate),
            waitForJoin=False,
            name="iterateThroughDeviceListForDevice",
        )
    elif action in Globals.GRID_ACTIONS:
        iterateThroughGridRows(frame, action)
    else:
        # Iterate Through Each Device in Group VIA Api Request
        try:
            groupToUse = group
            frame.Logging("---> Making API Request")
            if isUpdate:
                api_response = apiCalls.getAllDevices(groupToUse)
                deviceList = iterateThroughDeviceList(
                    frame, action, api_response, Globals.enterprise_id, isUpdate=True
                )
            else:
                wxThread.doAPICallInThread(
                    frame,
                    apiCalls.getAllDevices,
                    args=(groupToUse),
                    eventType=eventUtil.myEVT_RESPONSE,
                    callback=iterateThroughDeviceList,
                    callbackArgs=(frame, action),
                    optCallbackArgs=(Globals.enterprise_id),
                    waitForJoin=False,
                    name="iterateThroughDeviceListForGroup",
                )
        except ApiException as e:
            print("Exception when calling DeviceApi->get_all_devices: %s\n" % e)
            ApiToolLog().LogError(e)

    if deviceList:
        if isUpdate:
            postEventToFrame(eventUtil.myEVT_UPDATE, deviceList)
        else:
            postEventToFrame(
                eventUtil.myEVT_FETCH, (action, Globals.enterprise_id, deviceList)
            )


@api_tool_decorator()
def iterateThroughDeviceList(
    frame, action, api_response, entId, isDevice=False, isUpdate=False
):
    """Iterates Through Each Device And Performs A Specified Action"""
    if api_response:
        if hasattr(api_response, "next"):
            if api_response.next:
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
        else:
            frame.gridArrowState["prev"] = False

    postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 33)

    if hasattr(api_response, "results") and len(api_response.results):
        number_of_devices = 0
        if not isDevice and not isUpdate:
            splitResults = splitListIntoChunks(
                api_response.results, maxThread=int(Globals.MAX_THREAD_COUNT * (2 / 3))
            )

            threads = []
            for chunk in splitResults:
                t = wxThread.GUIThread(
                    frame,
                    processDevices,
                    args=(
                        chunk,
                        number_of_devices,
                        action,
                    ),
                    name="processDevices",
                )
                threads.append(t)
                t.start()
                number_of_devices += len(chunk)

            t = wxThread.GUIThread(
                frame,
                wxThread.waitTillThreadsFinish,
                args=(
                    tuple(threads),
                    action,
                    entId,
                    1,
                    None,
                    len(api_response.results) * 3,
                ),
                name="waitTillThreadsFinish_1",
                eventType=eventUtil.myEVT_FETCH,
            )
            t.start()
        else:
            deviceList = processDevices(
                api_response.results, number_of_devices, action, isUpdate=isUpdate
            )[1]
            return deviceList
    else:
        if hasattr(threading.current_thread(), "isStopped"):
            if threading.current_thread().isStopped():
                return
        frame.Logging("---> No devices found for group")
        frame.isRunning = False
        displayMessageBox(("No devices found for group.", wx.ICON_INFORMATION))
        postEventToFrame(eventUtil.myEVT_COMPLETE, (True))


@api_tool_decorator()
def iterateThroughAllGroups(frame, action, api_instance, group=None):
    groupToUse = None
    if group:
        groupToUse = group[0]
    try:
        frame.Logging("---> Making API Request")
        wxThread.doAPICallInThread(
            frame,
            apiCalls.getAllDevices,
            args=(groupToUse),
            eventType=eventUtil.myEVT_RESPONSE,
            callback=iterateThroughDeviceList,
            callbackArgs=(frame, action, Globals.enterprise_id),
            optCallbackArgs=(Globals.enterprise_id),
            waitForJoin=False,
            name="iterateThroughDeviceListForAllDeviceGroup",
        )
    except ApiException as e:
        print("Exception when calling DeviceApi->get_all_devices: %s\n" % e)
        ApiToolLog().LogError(e)


def processInstallDevices(deviceList):
    newDeviceList = []
    for device in deviceList:
        id = device["id"]
        deviceListing = apiCalls.getDeviceById(id)
        newDeviceList.append(deviceListing)
    processCollectionDevices({"results": newDeviceList})


@api_tool_decorator()
def processCollectionDevices(collectionList):
    if collectionList["results"]:
        splitResults = splitListIntoChunks(collectionList["results"])
        if splitResults:
            threads = []
            number_of_devices = 0
            for chunk in splitResults:
                t = wxThread.GUIThread(
                    Globals.frame,
                    fillInDeviceInfoDict,
                    args=(chunk, number_of_devices, len(collectionList["results"] * 2)),
                    name="fillInDeviceInfoDict",
                )
                threads.append(t)
                t.start()
                number_of_devices += len(chunk)

            t = wxThread.GUIThread(
                Globals.frame,
                wxThread.waitTillThreadsFinish,
                args=(
                    tuple(threads),
                    GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value,
                    Globals.enterprise_id,
                    3,
                ),
                eventType=eventUtil.myEVT_FETCH,
                name="waitTillThreadsFinish3",
            )
            t.start()
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
def fillInDeviceInfoDict(chunk, number_of_devices, maxGauge):
    deviceList = {}
    for device in chunk:
        try:
            deviceInfo = {}
            deviceInfo = populateDeviceInfoDictionary(device, deviceInfo)
            deviceList[number_of_devices] = [device, deviceInfo]
            number_of_devices += 1
        except Exception as e:
            print(e)
            ApiToolLog().LogError(e)
    return deviceList


@api_tool_decorator()
def processDevices(chunk, number_of_devices, action, isUpdate=False):
    """ Try to obtain more device info for a given device """
    deviceList = {}
    for device in chunk:
        try:
            number_of_devices = number_of_devices + 1
            deviceInfo = {}
            deviceInfo.update({"num": number_of_devices})
            deviceInfo = populateDeviceInfoDictionary(device, deviceInfo)

            deviceList[number_of_devices] = [device, deviceInfo]
        except Exception as e:
            print(e)
            ApiToolLog().LogError(e)

    return (action, deviceList)


@api_tool_decorator()
def unpackageDict(deviceInfo, deviceDict):
    """ Try to merge dicts into one dict, in a single layer """
    if not deviceDict:
        return deviceInfo
    for key in deviceDict.keys():
        if type(deviceDict[key]) is dict:
            unpackageDict(deviceInfo, deviceDict[key])
        else:
            if key.startswith("_"):
                deviceInfo[key[1 : len(key)]] = deviceDict[key]
            else:
                deviceInfo[key] = deviceDict[key]
    return deviceInfo


@api_tool_decorator()
def populateDeviceInfoDictionary(device, deviceInfo):
    """Populates Device Info Dictionary"""
    deviceId = None
    deviceName = None
    deviceGroups = None
    deviceAlias = None
    deviceStatus = None
    deviceHardware = None
    deviceTags = None
    if type(device) == dict:
        deviceId = device["id"]
        deviceName = device["name"]
        deviceGroups = device["group"]
        deviceAlias = device["alias"]
        deviceStatus = device["status"]
        deviceHardware = device["hardware"]
        deviceTags = device["tags"]
        unpackageDict(deviceInfo, device)
    else:
        deviceId = device.id
        deviceName = device.device_name
        deviceGroups = device.groups
        deviceAlias = device.alias_name
        deviceStatus = device.status
        deviceHardware = device.hardware_info
        deviceTags = device.tags
        deviceDict = device.__dict__
        unpackageDict(deviceInfo, deviceDict)
    appThread = wxThread.GUIThread(
        Globals.frame,
        apiCalls.getdeviceapps,
        (deviceId, True, Globals.USE_ENTERPRISE_APP),
    )
    appThread.start()
    eventThread = wxThread.GUIThread(
        Globals.frame,
        apiCalls.getLatestEvent,
        (deviceId),
    )
    eventThread.start()
    latestEvent = None
    deviceInfo.update({"EsperName": deviceName})

    detailInfo = apiCalls.getDeviceDetail(deviceId)
    unpackageDict(deviceInfo, detailInfo)

    if deviceGroups:
        groupNames = []
        global knownGroups
        if type(deviceGroups) == list:
            for groupURL in deviceGroups:
                groupName = None
                if groupURL in knownGroups:
                    groupName = knownGroups[groupURL]
                    if type(groupName) == list and len(groupName) == 1:
                        groupName = groupName[0]
                else:
                    groupName = apiCalls.fetchGroupName(groupURL)
                if groupName:
                    groupNames.append(groupName)
                if groupURL not in knownGroups:
                    knownGroups[groupURL] = groupName
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

    if Globals.frame and deviceGroups:
        subgroupsIds = []
        urlFormat = None
        for group in deviceGroups:
            groupId = Globals.frame.groupManage.getGroupIdFromURL(group)
            if not urlFormat:
                urlFormat = deviceGroups[0].replace(groupId, "{id}")
            if knownGroups[group].lower() != "all devices":
                subgroupsIds += Globals.frame.groupManage.getSubGroups(groupId)
            else:
                subgroupsIds += ["<All Device Groups>"]
        deviceInfo["subgroups"] = []
        for id in subgroupsIds:
            if id == "<All Device Groups>":
                deviceInfo["subgroups"].append(id)
            else:
                url = urlFormat.format(id=id)
                groupName = None
                if url in knownGroups:
                    groupName = knownGroups[url]
                    if type(groupName) == list and len(groupName) == 1:
                        groupName = groupName[0]
                else:
                    groupName = apiCalls.fetchGroupName(url)
                if groupName:
                    deviceInfo["subgroups"].append(groupName)
                if url not in knownGroups:
                    knownGroups[url] = groupName

    if bool(deviceAlias):
        deviceInfo.update({"Alias": deviceAlias})
    else:
        deviceInfo.update({"Alias": ""})

    if isinstance(deviceStatus, str):
        if deviceStatus.lower() == "online":
            deviceInfo.update({"Status": "Online"})
        elif "unspecified" in deviceStatus.lower():
            deviceInfo.update({"Status": "Unspecified"})
        elif "provisioning" in deviceStatus.lower():
            deviceInfo.update({"Status": "Provisioning"})
        elif deviceStatus.lower() == "offline":
            deviceInfo.update({"Status": "Offline"})
        elif "wipe" in deviceStatus.lower():
            deviceInfo.update({"Status": "Wipe In-Progress"})
        else:
            deviceInfo.update({"Status": "Unknown"})
    else:
        if deviceStatus == 1:
            deviceInfo.update({"Status": "Online"})
        elif deviceStatus == 0:
            deviceInfo.update({"Status": "Unspecified"})
        elif deviceStatus > 1 and deviceStatus < 60:
            deviceInfo.update({"Status": "Provisioning"})
        elif deviceStatus == 60:
            deviceInfo.update({"Status": "Offline"})
        elif deviceStatus == 70:
            deviceInfo.update({"Status": "Wipe In-Progress"})
        else:
            deviceInfo.update({"Status": "Unknown"})

    kioskMode = deviceInfo["current_app_mode"]
    if kioskMode == 0:
        deviceInfo.update({"Mode": "Kiosk"})
    else:
        deviceInfo.update({"Mode": "Multi"})

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

    if hdwareKey and bool(deviceHardware[hdwareKey]):
        deviceInfo.update({"Serial": str(deviceHardware[hdwareKey])})
    else:
        deviceInfo.update({"Serial": ""})

    if custHdwareKey and bool(deviceHardware[custHdwareKey]):
        deviceInfo.update({"Custom Serial": str(deviceHardware[custHdwareKey])})
    else:
        deviceInfo.update({"Custom Serial": ""})

    if bool(deviceTags):
        # Add Functionality For Modifying Multiple Tags
        deviceInfo.update({"Tags": deviceTags})
    else:
        deviceInfo.update({"Tags": ""})

        if hasattr(device, "tags") and device.tags is None:
            device.tags = []

    appThread.join()
    apps, _ = appThread.result
    deviceInfo.update({"Apps": str(apps)})

    if kioskMode == 0:
        eventThread.join()
        latestEvent = eventThread.result
        kioskModeApp = getValueFromLatestEvent(latestEvent, "kioskAppName")
        deviceInfo.update({"KioskApp": str(kioskModeApp)})
    else:
        deviceInfo.update({"KioskApp": ""})

    if eventThread.is_alive():
        eventThread.join()
    latestEvent = eventThread.result
    location_info = getValueFromLatestEvent(latestEvent, "locationEvent")
    network_info = getValueFromLatestEvent(latestEvent, "networkEvent")
    unpackageDict(deviceInfo, latestEvent)

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
                elif ip.endswith("/64"):
                    deviceInfo["ipv6Address"].append(ip)
                    deviceInfo["macAddress"].append(ipv6Tomac(ip))

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

    deviceInfo.update({"location_info": location_info})
    deviceInfo.update({"network_event": network_info})

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

    return deviceInfo


@api_tool_decorator()
def getValueFromLatestEvent(respData, eventName):
    event = ""
    if respData and eventName in respData:
        event = respData[eventName]
    return event


@api_tool_decorator()
def logActionExecution(frame, action, selection=None):
    actionName = ""
    if (
        frame.sidePanel.actionChoice.GetValue() in Globals.GRID_ACTIONS
        or frame.sidePanel.actionChoice.GetValue() in Globals.GENERAL_ACTIONS
    ):
        actionName = '"%s"' % frame.sidePanel.actionChoice.GetValue()
    if selection:
        frame.Logging("---> Starting Execution " + actionName + " on " + str(selection))
    else:
        frame.Logging("---> Starting Execution " + actionName)


def removeNonWhitelisted(deviceId, deviceInfo=None):
    detailInfo = None
    if not deviceInfo:
        detailInfo = apiCalls.getDeviceDetail(deviceId)
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
    return executeCommandOnDevice(
        Globals.frame, command_args, command_type="REMOVE_WIFI_AP", deviceIds=[deviceId]
    )


def clearKnownGroups():
    global knownGroups
    knownGroups.clear()


def getAllDeviceInfo(frame):
    devices = []
    if len(Globals.frame.sidePanel.selectedDevicesList) > 0:
        api_instance = esperclient.DeviceApi(
            esperclient.ApiClient(Globals.configuration)
        )
        labels = list(
            filter(
                lambda key: frame.sidePanel.devices[key]
                in frame.sidePanel.selectedDevicesList,
                frame.sidePanel.devices,
            )
        )
        for label in labels:
            api_response = api_instance.get_all_devices(
                Globals.enterprise_id,
                search=label,
                limit=Globals.limit,
                offset=Globals.offset,
            )
            if api_response and api_response.results:
                devices += api_response.results
    elif len(Globals.frame.sidePanel.selectedGroupsList) >= 0:
        api_response = apiCalls.getAllDevices(
            Globals.frame.sidePanel.selectedGroupsList
        )
        if api_response:
            devices += api_response.results
            while api_response and api_response.next:
                respOffset = api_response.next.split("&offset=")[-1]
                respLimit = api_response.next.split("?limit=")[-1].split("&")[0]
                api_response = apiCalls.getAllDevices(
                    Globals.frame.sidePanel.selectedGroupsList,
                    limit=respLimit,
                    offset=respOffset,
                )
                if api_response and api_response.results:
                    devices += api_response.results
        else:
            postEventToFrame(
                eventUtil.myEVT_LOG,
                "---> ERROR: Failed to get devices",
            )

    postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 25)
    postEventToFrame(eventUtil.myEVT_LOG, "Finished fetching device information")
    threads = []
    if devices:
        number_of_devices = 0
        splitResults = splitListIntoChunks(
            devices, maxThread=int(Globals.MAX_THREAD_COUNT * (2 / 3))
        )

        for chunk in splitResults:
            t = wxThread.GUIThread(
                frame,
                processDevices,
                args=(
                    chunk,
                    number_of_devices,
                    -1,
                ),
                name="processDevices",
            )
            threads.append(t)
            t.start()
            number_of_devices += len(chunk)

    joinThreadList(threads)

    deviceList = {}
    for thread in threads:
        if type(thread.result) == tuple:
            deviceList = {**deviceList, **thread.result[1]}

    return deviceList


def uploadAppToEndpoint(path):
    postEventToFrame(eventUtil.myEVT_LOG, "Attempting to upload app...")
    resp = apiCalls.uploadApplication(path)
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
