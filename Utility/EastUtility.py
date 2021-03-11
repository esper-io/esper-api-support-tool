#!/usr/bin/env python

from Common.decorator import api_tool_decorator
import ast
import json
from GUI.Dialogs.CmdConfirmDialog import CmdConfirmDialog
from Common.enum import GeneralActions
import esperclient
import Common.Globals as Globals
import Utility.wxThread as wxThread
import threading
import wx
import Utility.EsperAPICalls as apiCalls

from Utility.ApiToolLogging import ApiToolLog
from Utility.Resource import (
    displayMessageBox,
    joinThreadList,
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
            for entry in deviceList.values():
                device = entry[0]
                deviceInfo = entry[1]
                if action == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value:
                    frame.gridPanel.addDeviceToDeviceGrid(deviceInfo)
                    frame.gridPanel.addDeviceToNetworkGrid(device, deviceInfo)
                elif action == GeneralActions.SET_KIOSK.value:
                    apiCalls.setKiosk(frame, device, deviceInfo)
                elif action == GeneralActions.SET_MULTI.value:
                    apiCalls.setMulti(frame, device, deviceInfo)
                elif action == GeneralActions.CLEAR_APP_DATA.value:
                    apiCalls.clearAppData(frame, device)
            postEventToFrame(wxThread.myEVT_COMPLETE, None)


@api_tool_decorator
def iterateThroughGridRows(frame, action):
    """Iterates Through Each Device in the Displayed Grid And Performs A Specified Action"""
    if action == Globals.MODIFY_ALIAS_AND_TAGS:
        modifyDevice(frame)


@api_tool_decorator
def iterateThroughDeviceListV2(
    action, api_response, entId, isDevice=False, isUpdate=False
):
    if len(api_response.results):
        number_of_devices = 0
        if not isDevice and not isUpdate:
            # n = int(len(api_response.results) / Globals.MAX_THREAD_COUNT)
            # if n == 0:
            #     n = len(api_response.results)
            # splitResults = [
            #     api_response.results[i * n : (i + 1) * n]
            #     for i in range((len(api_response.results) + n - 1) // n)
            # ]
            splitResults = splitListIntoChunks(api_response.results)

            threads = []
            for chunk in splitResults:
                t = wxThread.GUIThread(
                    Globals.frame,
                    processDevices,
                    args=(chunk, number_of_devices, action),
                    # eventType=wxThread.myEVT_FETCH,
                )
                threads.append(t)
                t.start()
                number_of_devices += len(chunk)

            t = wxThread.GUIThread(
                Globals.frame,
                waitTillThreadsFinish,
                args=(tuple(threads), action, entId, 1),
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
        if Globals.frame:
            Globals.frame.Logging("---> No devices found for group")
            displayMessageBox(("No devices found for group.", wx.ICON_INFORMATION))


@api_tool_decorator
def iterateThroughDeviceList(
    frame, action, api_response, entId, isDevice=False, isUpdate=False
):
    """Iterates Through Each Device And Performs A Specified Action"""
    if len(api_response.results):
        number_of_devices = 0
        if not isDevice and not isUpdate:
            # n = int(len(api_response.results) / Globals.MAX_THREAD_COUNT)
            # if n == 0:
            #     n = len(api_response.results)
            # splitResults = [
            #     api_response.results[i * n : (i + 1) * n]
            #     for i in range((len(api_response.results) + n - 1) // n)
            # ]
            splitResults = splitListIntoChunks(api_response.results)

            threads = []
            for chunk in splitResults:
                t = wxThread.GUIThread(
                    frame,
                    processDevices,
                    args=(chunk, number_of_devices, action),
                    # eventType=wxThread.myEVT_FETCH,
                )
                threads.append(t)
                t.start()
                number_of_devices += len(chunk)

            t = wxThread.GUIThread(
                frame,
                waitTillThreadsFinish,
                args=(tuple(threads), action, entId, 1),
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
        wx.MessageBox("No devices found for group.", style=wx.ICON_INFORMATION)


@api_tool_decorator
def waitTillThreadsFinish(threads, action, entId, source, event=None):
    """ Wait till all threads have finished then send a signal back to the Main thread """
    joinThreadList(threads)
    if source == 1:
        deviceList = {}
        for thread in threads:
            if type(thread.result) == tuple:
                deviceList = {**deviceList, **thread.result[1]}
        postEventToFrame(event, action)
        return (action, entId, deviceList)
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
        postEventToFrame(
            wxThread.myEVT_LOG,
            "Successfully changed tags for %s of %s devices and aliases for %s of %s devices."
            % (changeSucceeded, len(tagsFromGrid.keys()), succeeded, numNewName),
        )
    if source == 3:
        deviceList = {}
        for thread in threads:
            if type(thread.result) == dict:
                deviceList = {**deviceList, **thread.result}
        postEventToFrame(
            wxThread.myEVT_FETCH,
            (
                GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value,
                Globals.enterprise_id,
                deviceList,
                True,
                len(deviceList) * 2,
            ),
        )


@api_tool_decorator
def processCollectionDevices(collectionList):
    # n = int(len(collectionList["results"]) / Globals.MAX_THREAD_COUNT)
    # if n == 0:
    #     n = len(collectionList["results"])
    # splitResults = [
    #     collectionList["results"][i * n : (i + 1) * n]
    #     for i in range((len(collectionList["results"]) + n - 1) // n)
    # ]
    splitResults = splitListIntoChunks(collectionList["results"])
    if splitResults:
        threads = []
        number_of_devices = 0
        for chunk in splitResults:
            t = wxThread.GUIThread(
                Globals.frame,
                fillInDeviceInfoDict,
                args=(chunk, number_of_devices, len(collectionList["results"] * 2)),
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
        )
        t.start()
    else:
        if Globals.frame:
            Globals.frame.Logging("---> No devices found for EQL query")
        postEventToFrame(
            wxThread.myEVT_MESSAGE_BOX,
            ("No devices found for EQL query.", wx.ICON_INFORMATION),
        )


@api_tool_decorator
def fillInDeviceInfoDict(chunk, number_of_devices, maxGauge):
    deviceList = {}
    for device in chunk:
        try:
            deviceInfo = {}
            deviceInfo = populateDeviceInfoDictionary(device, deviceInfo)

            deviceList[number_of_devices] = [device, deviceInfo]
            number_of_devices += 1
            Globals.deviceInfo_lock.acquire()
            value = int(Globals.frame.gauge.GetValue() + 1 / maxGauge * 100)
            Globals.frame.setGaugeValue(value)
            Globals.deviceInfo_lock.release()
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
    kioskMode = apiCalls.iskioskmode(deviceId)
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

    if kioskMode == 1:
        deviceInfo.update({"Mode": "Kiosk"})
    else:
        deviceInfo.update({"Mode": "Multi"})

    hdwareKey = None
    if "serial_number" in deviceHardware:
        hdwareKey = "serial_number"
    elif "serialNumber" in deviceHardware:
        hdwareKey = "serialNumber"

    if hdwareKey and bool(deviceHardware[hdwareKey]):
        deviceInfo.update({"Serial": str(deviceHardware[hdwareKey])})
    else:
        deviceInfo.update({"Serial": ""})

    if bool(deviceTags):
        # Add Functionality For Modifying Multiple Tags
        deviceInfo.update({"Tags": deviceTags})
    else:
        deviceInfo.update({"Tags": ""})

        if hasattr(device, "tags") and device.tags is None:
            device.tags = []

    apps, _ = apiCalls.getdeviceapps(deviceId, True, Globals.USE_ENTERPRISE_APP)
    deviceInfo.update({"Apps": str(apps)})

    if kioskMode == 1 and deviceStatus == 1:
        deviceInfo.update({"KioskApp": str(apiCalls.getkioskmodeapp(deviceId))})
    else:
        deviceInfo.update({"KioskApp": ""})

    location_info, resp_json = apiCalls.getLocationInfo(deviceId)
    network_info = apiCalls.getNetworkInfo(deviceId)
    unpackageDict(deviceInfo, resp_json)

    deviceInfo["macAddress"] = []
    ipKey = None
    if "ipAddress" in deviceInfo:
        ipKey = "ipAddress"
    elif "ip_address" in deviceInfo:
        ipKey = "ip_address"
        deviceInfo["ipAddress"] = deviceInfo[ipKey]
    if ipKey:
        for ip in deviceInfo[ipKey]:
            if ip.endswith("/64"):
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
    )
    t.start()
    return t


@api_tool_decorator
def executeDeviceModification(frame):
    """ Attempt to modify device data according to what has been changed in the Grid """
    api_instance = esperclient.DeviceApi(esperclient.ApiClient(Globals.configuration))
    api_response = None
    try:
        api_response = api_instance.get_all_devices(
            Globals.enterprise_id,
            limit=Globals.limit,
            offset=Globals.offset,
        )
    except Exception as e:
        postEventToFrame(
            wxThread.myEVT_LOG,
            "---> ERROR: Failed to get devices ids to modify tags and aliases",
        )
        print(e)
        ApiToolLog().LogError(e)
        return

    tagsFromGrid = frame.gridPanel.getDeviceTagsFromGrid()
    aliasDic = frame.gridPanel.getDeviceAliasFromList()
    frame.gauge.SetValue(1)

    maxGaugeAction = len(tagsFromGrid.keys()) + len(aliasDic.keys())
    if api_response:
        api_response.results = list(
            filter(lambda x: x.device_name in tagsFromGrid.keys(), api_response.results)
        )
        # n = int(len(api_response.results) / Globals.MAX_THREAD_COUNT)
        # if n == 0:
        #     n = len(api_response.results)
        # splitResults = [
        #     api_response.results[i * n : (i + 1) * n]
        #     for i in range((len(api_response.results) + n - 1) // n)
        # ]
        splitResults = splitListIntoChunks(api_response.results)

        threads = []
        for chunk in splitResults:
            t = wxThread.GUIThread(
                frame,
                processDeviceModificationForList,
                args=(frame, chunk, tagsFromGrid, aliasDic, maxGaugeAction),
            )
            threads.append(t)
            t.start()

        t = wxThread.GUIThread(
            frame,
            waitTillThreadsFinish,
            args=(tuple(threads), -1, -1, 2),
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
        )
        t.start()
        t2 = wxThread.GUIThread(
            frame,
            changeAliasForDevice,
            args=(device, aliasDic, frame, maxGaugeAction),
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
    ):
        newName = None
        if device.device_name in aliasDic:
            newName = aliasDic[device.device_name]
        else:
            newName = aliasDic[device.hardware_info["serialNumber"]]
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
            else:
                logString = logString + " <failed>"
                postEventToFrame(wxThread.myEVT_ON_FAILED, device)
        else:
            logString = logString + " (Alias Name already set)"
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
    ):
        tagsFromCell = None
        key = None
        if device.device_name in tagsFromGrid:
            key = device.device_name
            tagsFromCell = tagsFromGrid[key]
        else:
            key = device.hardware_info["serialNumber"]
            tagsFromCell = tagsFromGrid[key]
        tags = apiCalls.setdevicetags(device.id, tagsFromCell)
        if tags == tagsFromGrid[key]:
            changeSucceeded += 1
        postEventToFrame(wxThread.myEVT_UPDATE_TAG_CELL, (device.device_name, tags))
        postEventToFrame(
            wxThread.myEVT_UPDATE_GAUGE,
            int(frame.gauge.GetValue() + 1 / maxGaugeAction * 100),
        )
    return changeSucceeded


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
        )
    elif result and not isGroup:
        t = wxThread.GUIThread(
            frame,
            apiCalls.executeCommandOnDevice,
            args=(frame, command_args, schedule, schType, commandType),
            eventType=wxThread.myEVT_COMMAND,
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
