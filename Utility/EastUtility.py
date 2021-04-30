#!/usr/bin/env python

import time
import ast
import json
import math
import esperclient
import Common.Globals as Globals
import Utility.wxThread as wxThread
import threading
import wx
import platform
import Utility.EsperAPICalls as apiCalls

from Common.decorator import api_tool_decorator
from Common.enum import GeneralActions, GridActions

from GUI.Dialogs.CmdConfirmDialog import CmdConfirmDialog

from Utility.ApiToolLogging import ApiToolLog
from Utility.Resource import (
    displayMessageBox,
    joinThreadList,
    limitActiveThreads,
    postEventToFrame,
    ipv6Tomac,
    splitListIntoChunks,
)

from esperclient.rest import ApiException


####Perform Actions. Set Kiosk Mode, Multi App Mode, Tags, or Alias####
@api_tool_decorator
def TakeAction(frame, group, action, label, isDevice=False, isUpdate=False):
    """Calls API To Perform Action And Logs Result To UI"""
    if not Globals.enterprise_id:
        frame.loadConfigPrompt()

    if frame:
        frame.menubar.disableConfigMenu()

    logActionExecution(frame, action, group)
    if (action == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value) and not isUpdate:
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
            eventType=wxThread.myEVT_RESPONSE,
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
                    eventType=wxThread.myEVT_RESPONSE,
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
            postEventToFrame(wxThread.myEVT_UPDATE, deviceList)
        else:
            postEventToFrame(
                wxThread.myEVT_FETCH, (action, Globals.enterprise_id, deviceList)
            )


@api_tool_decorator
def iterateThroughGridRows(frame, action):
    """Iterates Through Each Device in the Displayed Grid And Performs A Specified Action"""
    if action == GridActions.MODIFY_ALIAS_AND_TAGS.value:
        modifyDevice(frame)
    if (
        action == GridActions.SET_APP_STATE_DISABLE.value
        or action == GridActions.SET_APP_STATE_HIDE.value
        or action == GridActions.SET_APP_STATE_SHOW.value
    ):
        setAppStateForAllAppsListed(action)
    if action == 50:
        setAppStateForSpecificAppListed(action)


@api_tool_decorator
def iterateThroughDeviceList(
    frame, action, api_response, entId, isDevice=False, isUpdate=False
):
    """Iterates Through Each Device And Performs A Specified Action"""
    if api_response:
        if hasattr(api_response, "next"):
            if api_response.next:
                frame.gridPanel.button_2.Enable(True)
            else:
                frame.gridPanel.button_2.Enable(False)
        else:
            frame.gridPanel.button_2.Enable(False)
        if hasattr(api_response, "previous"):
            if api_response.previous:
                frame.gridPanel.button_1.Enable(True)
            else:
                frame.gridPanel.button_1.Enable(False)
        else:
            frame.gridPanel.button_2.Enable(False)

    postEventToFrame(wxThread.myEVT_UPDATE_GAUGE, 33)

    if len(api_response.results):
        number_of_devices = 0
        if not isDevice and not isUpdate:
            splitResults = splitListIntoChunks(api_response.results)

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
                waitTillThreadsFinish,
                args=(
                    tuple(threads),
                    action,
                    entId,
                    1,
                    None,
                    len(api_response.results) * 3,
                ),
                name="waitTillThreadsFinish_1",
                eventType=wxThread.myEVT_FETCH,
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


@api_tool_decorator
def waitTillThreadsFinish(threads, action, entId, source, event=None, maxGauge=None):
    """ Wait till all threads have finished then send a signal back to the Main thread """
    joinThreadList(threads)
    if source == 1:
        deviceList = {}
        initPercent = Globals.frame.gauge.GetValue()
        initVal = 0
        if maxGauge:
            initVal = math.ceil((initPercent / 100) * maxGauge)
        for thread in threads:
            if type(thread.result) == tuple:
                deviceList = {**deviceList, **thread.result[1]}
                if maxGauge:
                    val = int((initVal + len(deviceList)) / maxGauge * 100)
                    postEventToFrame(
                        wxThread.myEVT_UPDATE_GAUGE,
                        val,
                    )
        postEventToFrame(event, action)
        return (action, entId, deviceList, True, len(deviceList) * 3)
    if source == 2:
        postEventToFrame(wxThread.myEVT_COMPLETE, None)
        changeSucceeded = succeeded = numNewName = 0
        tagsFromGrid = None
        for thread in threads:
            if type(thread.result) == tuple:
                changeSucceeded += thread.result[0]
                succeeded += thread.result[1]
                numNewName += thread.result[2]
                tagsFromGrid = thread.result[3]
        msg = (
            "Successfully changed tags for %s of %s devices and aliases for %s of %s devices."
            % (changeSucceeded, len(tagsFromGrid.keys()), succeeded, numNewName)
        )
        postEventToFrame(wxThread.myEVT_LOG, msg)
        postEventToFrame(
            wxThread.myEVT_MESSAGE_BOX,
            (msg, wx.ICON_INFORMATION),
        )
    if source == 3:
        deviceList = {}
        for thread in threads:
            if type(thread.result) == dict:
                deviceList = {**deviceList, **thread.result}
        return (
            GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value,
            Globals.enterprise_id,
            deviceList,
            True,
            len(deviceList) * 3,
        )
    if source == 4:
        postEventToFrame(wxThread.myEVT_THREAD_WAIT, (threads, 3, action))


def processInstallDevices(deviceList):
    newDeviceList = []
    for device in deviceList:
        id = device["id"]
        deviceListing = apiCalls.getDeviceById(id)
        newDeviceList.append(deviceListing)
    processCollectionDevices({"results": newDeviceList})


@api_tool_decorator
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
                waitTillThreadsFinish,
                args=(
                    tuple(threads),
                    GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value,
                    Globals.enterprise_id,
                    3,
                ),
                eventType=wxThread.myEVT_FETCH,
                name="waitTillThreadsFinish3",
            )
            t.start()
    else:
        if Globals.frame:
            Globals.frame.Logging("---> No devices found for EQL query")
            Globals.frame.isRunning = False
        postEventToFrame(
            wxThread.myEVT_MESSAGE_BOX,
            ("No devices found for EQL query.", wx.ICON_INFORMATION),
        )
        postEventToFrame(wxThread.myEVT_COMPLETE, (True))


@api_tool_decorator
def fillInDeviceInfoDict(chunk, number_of_devices, maxGauge):
    deviceList = {}
    for device in chunk:
        try:
            deviceInfo = {}
            deviceInfo = populateDeviceInfoDictionary(device, deviceInfo)
            deviceList[number_of_devices] = [device, deviceInfo]
        except Exception as e:
            print(e)
            ApiToolLog().LogError(e)
    return deviceList


@api_tool_decorator
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
            # if deviceInfo not in Globals.GRID_DEVICE_INFO_LIST:
            #    Globals.GRID_DEVICE_INFO_LIST.append(deviceInfo)
        except Exception as e:
            print(e)
            ApiToolLog().LogError(e)

    return (action, deviceList)


@api_tool_decorator
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


@api_tool_decorator
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
        if type(deviceGroups) == list:
            for groupURL in deviceGroups:
                groupName = apiCalls.fetchGroupName(groupURL)
                if groupName:
                    groupNames.append(groupName)
        elif type(deviceGroups) == dict and "name" in deviceGroups:
            groupNames.append(deviceGroups["name"])
        if len(groupNames) == 1:
            deviceInfo["groups"] = groupNames[0]
        elif len(groupNames) == 0:
            deviceInfo["groups"] = ""
        else:
            deviceInfo["groups"] = groupNames

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
        for ip in deviceInfo[ipKey]:
            if ip.endswith("/24"):
                deviceInfo["ipv4Address"].append(ip)
            elif ip.endswith("/64"):
                deviceInfo["ipv6Address"].append(ip)
                deviceInfo["macAddress"].append(ipv6Tomac(ip))

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

    return deviceInfo


@api_tool_decorator
def getValueFromLatestEvent(respData, eventName):
    event = ""
    if respData and eventName in respData:
        event = respData[eventName]
    return event


@api_tool_decorator
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


@api_tool_decorator
def modifyDevice(frame):
    """ Start a thread that will attempt to modify device data """
    t = wxThread.GUIThread(
        frame,
        executeDeviceModification,
        args=(frame),
        eventType=None,
        name="executeDeviceModification",
    )
    t.start()
    return t


@api_tool_decorator
def executeDeviceModification(frame, maxAttempt=Globals.MAX_RETRY):
    """ Attempt to modify device data according to what has been changed in the Grid """
    api_instance = esperclient.DeviceApi(esperclient.ApiClient(Globals.configuration))
    api_response = None
    for attempt in range(maxAttempt):
        try:
            api_response = api_instance.get_all_devices(
                Globals.enterprise_id,
                limit=Globals.limit,
                offset=Globals.offset,
            )
            break
        except Exception as e:
            if attempt == maxAttempt - 1:
                postEventToFrame(
                    wxThread.myEVT_LOG,
                    "---> ERROR: Failed to get devices ids to modify tags and aliases",
                )
                print(e)
                ApiToolLog().LogError(e)
                return
            time.sleep(Globals.RETRY_SLEEP)

    tagsFromGrid = frame.gridPanel.getDeviceTagsFromGrid()
    aliasDic = frame.gridPanel.getDeviceAliasFromList()
    frame.gauge.SetValue(1)

    maxGaugeAction = len(tagsFromGrid.keys()) + len(aliasDic.keys())
    if api_response:
        tempRes = []
        for device in api_response.results:
            if (
                device.device_name in tagsFromGrid.keys()
                or device.hardware_info["serialNumber"] in tagsFromGrid.keys()
                or (
                    "customSerialNumber" in device.hardware_info
                    and device.hardware_info["customSerialNumber"]
                    in tagsFromGrid.keys()
                )
            ):
                tempRes.append(device)
        if tempRes:
            api_response.results = tempRes

        splitResults = splitListIntoChunks(api_response.results)

        threads = []
        for chunk in splitResults:
            t = wxThread.GUIThread(
                frame,
                processDeviceModificationForList,
                args=(frame, chunk, tagsFromGrid, aliasDic, maxGaugeAction),
                name="processDeviceModificationForList",
            )
            threads.append(t)
            t.start()

        t = wxThread.GUIThread(
            frame,
            waitTillThreadsFinish,
            args=(tuple(threads), -1, -1, 2),
            name="waitTillThreadsFinish",
        )
        t.start()


@api_tool_decorator
def processDeviceModificationForList(
    frame, chunk, tagsFromGrid, aliasDic, maxGaugeAction
):
    changeSucceeded = 0
    succeeded = 0
    numNewName = 0
    for device in chunk:
        t = wxThread.GUIThread(
            frame,
            changeTagsForDevice,
            args=(device, tagsFromGrid, frame, maxGaugeAction),
            name="changeTagsForDevice",
        )
        t.start()
        t2 = wxThread.GUIThread(
            frame,
            changeAliasForDevice,
            args=(device, aliasDic, frame, maxGaugeAction),
            name="changeAliasForDevice",
        )
        t2.start()
        joinThreadList([t, t2])
        if t.result:
            changeSucceeded += t.result
        if t2.result:
            numNewName += t2.result[0]
            succeeded += t2.result[1]

    return (changeSucceeded, succeeded, numNewName, tagsFromGrid)


@api_tool_decorator
def changeAliasForDevice(device, aliasDic, frame, maxGaugeAction):
    numNewName = 0
    succeeded = 0
    logString = ""
    # Alias modification
    if (
        device.device_name in aliasDic.keys()
        or device.hardware_info["serialNumber"] in aliasDic.keys()
        or (
            "customSerialNumber" in device.hardware_info
            and device.hardware_info["customSerialNumber"] in aliasDic.keys()
        )
    ):
        newName = None
        if device.device_name in aliasDic:
            newName = aliasDic[device.device_name]
        elif device.hardware_info["serialNumber"] in aliasDic:
            newName = aliasDic[device.hardware_info["serialNumber"]]
        elif (
            "customSerialNumber" in device.hardware_info
            and device.hardware_info["customSerialNumber"] in aliasDic
        ):
            newName = aliasDic[device.hardware_info["customSerialNumber"]]
        logString = str(
            "--->" + str(device.device_name) + " : " + str(newName) + "--->"
        )
        if not newName and not device.alias_name:
            return
        if newName != str(device.alias_name):
            numNewName += 1
            status = ""
            try:
                ignoreQueued = False if Globals.REACH_QUEUED_ONLY else True
                status = apiCalls.setdevicename(frame, device.id, newName, ignoreQueued)
            except Exception as e:
                ApiToolLog().LogError(e)
            if "Success" in str(status):
                logString = logString + " <success>"
                succeeded += 1
            elif "Queued" in str(status):
                logString = logString + " <Queued> Make sure device is online."
                postEventToFrame(wxThread.myEVT_ON_FAILED, (device, "Queued"))
            elif "Scheduled" in str(status):
                logString = logString + " <Scheduled> Make sure device is online."
                postEventToFrame(wxThread.myEVT_ON_FAILED, (device, "Scheduled"))
            else:
                logString = logString + " <failed>"
                postEventToFrame(wxThread.myEVT_ON_FAILED, device)
        else:
            logString = logString + " (Alias Name already set)"
        if "Success" in logString or "Queued" in logString:
            postEventToFrame(wxThread.myEVT_UPDATE_GRID_CONTENT, (device, "alias"))
        postEventToFrame(
            wxThread.myEVT_UPDATE_GAUGE,
            int(frame.gauge.GetValue() + 1 / maxGaugeAction * 100),
        )
        postEventToFrame(wxThread.myEVT_LOG, logString)
    return (numNewName, succeeded)


@api_tool_decorator
def changeTagsForDevice(device, tagsFromGrid, frame, maxGaugeAction):
    # Tag modification
    changeSucceeded = 0
    if (
        device.device_name in tagsFromGrid.keys()
        or device.hardware_info["serialNumber"] in tagsFromGrid.keys()
        or (
            "customSerialNumber" in device.hardware_info
            and device.hardware_info["customSerialNumber"] in tagsFromGrid.keys()
        )
    ):
        tagsFromCell = None
        key = None
        if device.device_name in tagsFromGrid:
            key = device.device_name
        elif device.hardware_info["serialNumber"] in tagsFromGrid:
            key = device.hardware_info["serialNumber"]
        elif (
            "customSerialNumber" in device.hardware_info
            and device.hardware_info["customSerialNumber"] in tagsFromGrid
        ):
            key = device.hardware_info["customSerialNumber"]
        tagsFromCell = tagsFromGrid[key]
        tags = apiCalls.setdevicetags(device.id, tagsFromCell)
        if tags == tagsFromGrid[key]:
            changeSucceeded += 1
        postEventToFrame(wxThread.myEVT_UPDATE_GRID_CONTENT, (device, "tags"))
        postEventToFrame(wxThread.myEVT_UPDATE_TAG_CELL, (device.device_name, tags))
        postEventToFrame(
            wxThread.myEVT_UPDATE_GAUGE,
            int(frame.gauge.GetValue() + 1 / maxGaugeAction * 100),
        )
    return changeSucceeded


@api_tool_decorator
def setAppStateForAllAppsListed(state, maxAttempt=Globals.MAX_RETRY):
    api_instance = esperclient.DeviceApi(esperclient.ApiClient(Globals.configuration))
    api_response = None
    for attempt in range(maxAttempt):
        try:
            api_response = api_instance.get_all_devices(
                Globals.enterprise_id,
                limit=Globals.limit,
                offset=Globals.offset,
            )
            break
        except Exception as e:
            if attempt == maxAttempt - 1:
                postEventToFrame(
                    wxThread.myEVT_LOG,
                    "---> ERROR: Failed to get devices ids to modify tags and aliases",
                )
                print(e)
                ApiToolLog().LogError(e)
                return
            time.sleep(Globals.RETRY_SLEEP)

    deviceIdentifers = Globals.frame.gridPanel.getDeviceIdentifersFromGrid()
    if api_response:
        tempRes = []
        for device in api_response.results:
            for deviceIds in deviceIdentifers:
                if (
                    device.device_name in deviceIds
                    or device.hardware_info["serialNumber"] in deviceIds
                    or (
                        "customSerialNumber" in device.hardware_info
                        and device.hardware_info["customSerialNumber"] in deviceIds
                    )
                ):
                    tempRes.append(device)
        if tempRes:
            api_response.results = tempRes
        threads = []
        for device in api_response.results:
            if (
                device.device_name in deviceIdentifers
                or device.hardware_info["serialNumber"] in deviceIdentifers
                or (
                    "customSerialNumber" in device.hardware_info
                    and device.hardware_info["customSerialNumber"] in deviceIdentifers
                )
            ):
                t = wxThread.GUIThread(
                    Globals.frame,
                    setAllAppsState,
                    args=(Globals.frame, device, state),
                    name="setAllAppsState",
                )
                threads.append(t)
                t.start()
                limitActiveThreads(threads)
        t = wxThread.GUIThread(
            Globals.frame,
            waitTillThreadsFinish,
            args=(tuple(threads), state, -1, 4),
            name="waitTillThreadsFinish%s" % state,
        )
        t.start()


@api_tool_decorator
def setAllAppsState(frame, device, state):
    stateStatuses = []
    # for device in chunk:
    _, resp = apiCalls.getdeviceapps(device.id, False, Globals.USE_ENTERPRISE_APP)
    for app in resp["results"]:
        stateStatus = None
        package_name = None
        app_version = None
        if "application" in app:
            package_name = app["application"]["package_name"]
            app_version = app["application"]["version"]["version_code"]
            if app["application"]["package_name"] in Globals.BLACKLIST_PACKAGE_NAME:
                continue
        else:
            package_name = app["package_name"]
            app_version = app["version_code"]
            if app["package_name"] in Globals.BLACKLIST_PACKAGE_NAME:
                continue
        if state == GridActions.SET_APP_STATE_DISABLE.value:
            stateStatus = apiCalls.setAppState(
                device.id,
                package_name,
                appVer=app_version,
                state="DISABLE",
            )
        if state == GridActions.SET_APP_STATE_HIDE.value:
            stateStatus = apiCalls.setAppState(
                device.id,
                package_name,
                appVer=app_version,
                state="HIDE",
            )
        if state == GridActions.SET_APP_STATE_SHOW.value:
            stateStatus = apiCalls.setAppState(
                device.id,
                package_name,
                appVer=app_version,
                state="SHOW",
            )
        if stateStatus and hasattr(stateStatus, "state"):
            entry = {
                "Device Name": device.device_name,
                "Device id": device.id,
                "State Status": stateStatus.state,
            }
            if hasattr(stateStatus, "reason"):
                entry["Reason"] = stateStatus.reason
            stateStatuses.append(entry)
        else:
            stateStatuses.append(
                {
                    "Device Name": device.device_name,
                    "Device id": device.id,
                    "State Status": stateStatus,
                }
            )
    return stateStatuses


@api_tool_decorator
def createCommand(frame, command_args, commandType, schedule, schType):
    """ Attempt to apply a Command given user specifications """
    result, isGroup = confirmCommand(command_args, commandType, schedule, schType)

    if schType.lower() == "immediate":
        schType = esperclient.V0CommandScheduleEnum.IMMEDIATE
    elif schType.lower() == "window":
        schType = esperclient.V0CommandScheduleEnum.WINDOW
    elif schType.lower() == "recurring":
        schType = esperclient.V0CommandScheduleEnum.RECURRING
    t = None
    if result and isGroup:
        t = wxThread.GUIThread(
            frame,
            apiCalls.executeCommandOnGroup,
            args=(frame, command_args, schedule, schType, commandType),
            eventType=wxThread.myEVT_COMMAND,
            name="executeCommandOnGroup",
        )
    elif result and not isGroup:
        t = wxThread.GUIThread(
            frame,
            apiCalls.executeCommandOnDevice,
            args=(frame, command_args, schedule, schType, commandType),
            eventType=wxThread.myEVT_COMMAND,
            name="executeCommandOnDevice",
        )
    if t:
        frame.menubar.disableConfigMenu()
        frame.gauge.Pulse()
        t.start()


@api_tool_decorator
def confirmCommand(cmd, commandType, schedule, schType):
    """ Ask user to confirm the command they want to run """
    modal = None
    isGroup = False
    cmd_dict = ast.literal_eval(str(cmd).replace("\n", ""))
    sch_dict = ast.literal_eval(str(schedule).replace("\n", ""))
    cmdFormatted = json.dumps(cmd_dict, indent=2)
    schFormatted = json.dumps(sch_dict, indent=2)
    label = ""
    applyTo = ""
    commaSeperated = ", "
    if len(Globals.frame.sidePanel.selectedDevicesList) > 0:
        selections = Globals.frame.sidePanel.deviceMultiDialog.GetSelections()
        label = ""
        for device in selections:
            label += device + commaSeperated
        if label.endswith(", "):
            label = label[0 : len(label) - len(commaSeperated)]
        applyTo = "device"
    elif len(Globals.frame.sidePanel.selectedGroupsList) >= 0:
        selections = Globals.frame.sidePanel.groupMultiDialog.GetSelections()
        label = ""
        for group in selections:
            label += group + commaSeperated
        if label.endswith(", "):
            label = label[0 : len(label) - len(commaSeperated)]
        applyTo = "group"
        isGroup = True
    modal = wx.NO
    with CmdConfirmDialog(
        commandType, cmdFormatted, schType, schFormatted, applyTo, label
    ) as dialog:
        res = dialog.ShowModal()
        if res == wx.ID_OK:
            modal = wx.YES

    if modal == wx.YES:
        return True, isGroup
    else:
        return False, isGroup


def setAppStateForSpecificAppListed(action, maxAttempt=Globals.MAX_RETRY):
    api_instance = esperclient.DeviceApi(esperclient.ApiClient(Globals.configuration))
    api_response = None
    for attempt in range(maxAttempt):
        try:
            api_response = api_instance.get_all_devices(
                Globals.enterprise_id,
                limit=Globals.limit,
                offset=Globals.offset,
            )
            break
        except Exception as e:
            if attempt == maxAttempt - 1:
                postEventToFrame(
                    wxThread.myEVT_LOG,
                    "---> ERROR: Failed to get devices ids to modify tags and aliases",
                )
                print(e)
                ApiToolLog().LogError(e)
                return
            time.sleep(Globals.RETRY_SLEEP)
    state = None
    if action == 50:
        state == "HIDE"

    # deviceIdentifers = Globals.frame.gridPanel.getDeviceIdentifersFromGrid()
    appList = Globals.frame.gridPanel.getDeviceAppFromGrid()
    if api_response:
        tempRes = []
        for device in api_response.results:
            for deviceIds in appList.keys():
                if (
                    device.device_name in deviceIds
                    or device.hardware_info["serialNumber"] in deviceIds
                    or (
                        "customSerialNumber" in device.hardware_info
                        and device.hardware_info["customSerialNumber"] in deviceIds
                    )
                ):
                    tempRes.append(device)
        if tempRes:
            api_response.results = tempRes
        threads = []
        for device in api_response.results:
            if (
                device.device_name in appList.keys()
                or device.hardware_info["serialNumber"] in appList.keys()
                or (
                    "customSerialNumber" in device.hardware_info
                    and device.hardware_info["customSerialNumber"] in appList.keys()
                )
            ):
                package_names = None
                if device.device_name in appList.keys():
                    package_names = appList[device.device_name]
                elif device.hardware_info["serialNumber"] in appList.keys():
                    package_names = appList[device.hardware_info["serialNumber"]]
                elif (
                    "customSerialNumber" in device.hardware_info
                    and device.hardware_info["customSerialNumber"] in appList.keys()
                ):
                    package_names = appList[device.hardware_info["customSerialNumber"]]
                package_names = package_names.split(",")
                if package_names:
                    for package_name in package_names:
                        if package_name.trim():
                            t = wxThread.GUIThread(
                                Globals.frame,
                                apiCalls.setAppState,
                                args=(
                                    device.id,
                                    package_name.trim(),
                                    state,
                                ),
                                name="setAllAppsState",
                            )
                            threads.append(t)
                            t.start()
                        limitActiveThreads(threads)
        t = wxThread.GUIThread(
            Globals.frame,
            waitTillThreadsFinish,
            args=(tuple(threads), state, -1, 4),
            name="waitTillThreadsFinish%s" % state,
        )
        t.start()