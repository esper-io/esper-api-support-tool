#!/usr/bin/env python

import time

import esperclient

import Common.Globals as Globals
import Utility.API.EsperAPICalls as apiCalls
import Utility.EventUtility as eventUtil
from Common.decorator import api_tool_decorator
from Common.enum import GridActions
from Utility.API.AppUtilities import installAppOnDevices, uninstallAppOnDevice
from Utility.API.DeviceUtility import setDeviceDisabled, setdevicetags
from Utility.API.GroupUtility import getAllGroups, moveGroup
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Resource import (
    enforceRateLimit,
    isApiKey,
    postEventToFrame,
    splitListIntoChunks,
)
from Utility.Threading import wxThread


@api_tool_decorator()
def iterateThroughGridRows(frame, action):
    """Iterates Through Each Device in the Displayed Grid And Performs A Specified Action"""
    if action == GridActions.MODIFY_ALIAS.value:
        modifyDevice(frame, GridActions.MODIFY_ALIAS.value)
    if action == GridActions.MODIFY_TAGS.value:
        modifyDevice(frame, GridActions.MODIFY_TAGS.value)
    if action == GridActions.MOVE_GROUP.value:
        relocateDeviceToNewGroup(frame)
    if action == GridActions.SET_APP_STATE.value:
        setAppStateForAllAppsListed(action)
    if action == GridActions.INSTALL_APP.value:
        installApp(frame)
    if action == GridActions.UNINSTALL_APP.value:
        uninstallApp(frame)
    if action == GridActions.SET_DEVICE_DISABLED.value:
        setDevicesDisabled()


@api_tool_decorator()
def modifyDevice(frame, action):
    """ Start a thread that will attempt to modify device data """
    Globals.THREAD_POOL.enqueue(executeDeviceModification, frame, action)


@api_tool_decorator()
def executeDeviceModification(frame, action, maxAttempt=Globals.MAX_RETRY):
    """ Attempt to modify device data according to what has been changed in the Grid """
    rowTaglist = aliasList = None
    maxGaugeAction = 0
    if action == GridActions.MODIFY_TAGS.value:
        rowTaglist = frame.gridPanel.getDeviceTagsFromGrid()
        maxGaugeAction = len(rowTaglist)
    else:
        aliasList = frame.gridPanel.getDeviceAliasFromList()
        if aliasList:
            maxGaugeAction = len(aliasList)
    frame.statusBar.gauge.SetValue(1)

    postEventToFrame(
        eventUtil.myEVT_AUDIT,
        {
            "operation": "ChangeTags"
            if action == GridActions.MODIFY_TAGS.value
            else "ChangeAlias",
            "data": {"tags": rowTaglist}
            if action == GridActions.MODIFY_TAGS.value
            else {"alias": aliasList},
        },
    )
    devices = obtainEsperDeviceEntriesFromList(
        rowTaglist if action == GridActions.MODIFY_TAGS.value else aliasList
    )
    splitResults = splitListIntoChunks(devices)

    for chunk in splitResults:
        Globals.THREAD_POOL.enqueue(
            processDeviceModificationForList,
            action,
            chunk,
            rowTaglist,
            aliasList,
            maxGaugeAction,
        )

    Globals.THREAD_POOL.enqueue(
        wxThread.waitTillThreadsFinish,
        Globals.THREAD_POOL.threads,
        action,
        -1,
        2,
        tolerance=1,
    )


def obtainEsperDeviceEntriesFromList(iterList):
    devices = []
    for row in iterList:
        if type(row) is dict and "Esper Id" in row.keys() and row["Esper Id"]:
            devices.append(row["Esper Id"])
            continue

        api_response = apiCalls.searchForMatchingDevices(row)
        if api_response:
            devices += api_response.results
            api_response = None
        else:
            postEventToFrame(
                eventUtil.myEVT_LOG,
                "---> ERROR: Failed to find device with these details: %s" % row,
            )
    return devices


@api_tool_decorator()
def processDeviceModificationForList(
    action, chunk, tagsFromGrid, aliasDic, maxGaugeAction
):
    changeSucceeded = 0
    succeeded = 0
    numNewName = 0
    status = []
    aliasStatus = []
    tagStatus = []
    for device in chunk:
        if action == GridActions.MODIFY_TAGS.value:
            numSucceeded, tagStatusMsg = changeTagsForDevice(
                device, tagsFromGrid, maxGaugeAction
            )
            changeSucceeded += numSucceeded
            tagStatus.append(tagStatusMsg)
        else:
            numNameChanged, numSuccess, aliasStatusMsg = changeAliasForDevice(
                device, aliasDic, maxGaugeAction
            )
            numNewName += numNameChanged
            succeeded += numSuccess
            aliasStatus.append(aliasStatusMsg)

    tmp = tagStatus if action == GridActions.MODIFY_TAGS.value else aliasStatus
    for stat in tmp:
        if stat not in status:
            status.append(stat)
    return (changeSucceeded, succeeded, numNewName, chunk, status)


@api_tool_decorator()
def changeAliasForDevice(device, aliasList, maxGaugeAction):
    numNewName = 0
    succeeded = 0
    logString = ""
    status = deviceName = deviceId = aliasName = serial = imei1 = imei2 = None
    if hasattr(device, "device_name"):
        deviceName = device.device_name
        deviceId = device.id
        aliasName = device.alias_name
        hardware = device.hardware_info
        network = device.network_info
        serial = hardware["serialNumber"] if "serialNumber" in hardware else None
        imei1 = network["imei1"] if "imei1" in network else None
        imei2 = network["imei2"] if "imei2" in network else None
    elif type(device) is dict:
        deviceName = device["device_name"]
        deviceId = device["id"]
        aliasName = device["alias_name"]
        hardware = device["hardware_info"]
        network = device["network_info"]
        serial = hardware["serialNumber"] if "serialNumber" in hardware else None
        imei1 = network["imei1"] if "imei1" in network else None
        imei2 = network["imei2"] if "imei2" in network else None

    match = list(
        filter(
            lambda x: x["Esper Name"] == deviceName
            or x["Esper Id"] == device
            or x["Serial Number"] == serial
            or x["Custom Serial Number"] == serial
            or x["IMEI 1"] == imei1
            or x["IMEI 2"] == imei2,
            aliasList,
        )
    )
    # Alias modification
    if match:
        match = match[0]
        deviceName = (
            match["Esper Name"]
            if "Esper Name" in match and match["Esper Name"]
            else deviceName
        )
        deviceId = (
            match["Esper Id"] if "Esper Id" in match and match["Esper Id"] else deviceId
        )
        newName = match["Alias"] if "Alias" in match else ""

        logString = str("--->" + str(deviceName) + " : " + str(newName) + "--->")
        if not newName:
            # Return if no alias specified
            status = {
                "Device Name": deviceName,
                "Device Id": deviceId,
                "Alias Status": "No alias to set",
            }
            return (numNewName, succeeded, status)

        if newName != str(aliasName):
            # Change alias if it differs than what is already set (as retrieved by API)
            numNewName += 1
            status = ""
            try:
                ignoreQueued = False if Globals.REACH_QUEUED_ONLY else True
                status = apiCalls.setdevicename(deviceId, newName, ignoreQueued)
            except Exception as e:
                ApiToolLog().LogError(e)
            if hasattr(status, "to_dict"):
                status = status.to_dict()
            if "Success" in str(status):
                logString = logString + " <success>"
                succeeded += 1
            elif "Queued" in str(status):
                logString = logString + " <Queued> Make sure device is online."
            elif "Scheduled" in str(status):
                logString = logString + " <Scheduled> Make sure device is online."
            else:
                logString = logString + " <failed>"
        else:
            logString = logString + " (Alias Name already set)"
            status = {
                "device": deviceName,
                "id": deviceId,
                "reason": "Alias Name already set",
                "request": None,
                "state": None,
            }
        if "Success" in logString or "Queued" in logString:
            postEventToFrame(eventUtil.myEVT_UPDATE_GRID_CONTENT, (device, "alias"))
        postEventToFrame(
            eventUtil.myEVT_UPDATE_GAUGE,
            int(Globals.frame.statusBar.gauge.GetValue() + 1 / maxGaugeAction * 100),
        )
        postEventToFrame(eventUtil.myEVT_LOG, logString)
    statusResp = {
        "Device Name": deviceName,
        "Device Id": deviceId,
        "Alias Status": status if status else "No alias to set",
    }
    if status:
        statusResp["Alias Status"] = {
            "id": status["id"],
            "request": status["request"],
            "device": status["device"],
            "state": status["state"],
            "reason": status["reason"],
        }
    else:
        statusResp["Alias Status"] = "No alias to set"
    return (numNewName, succeeded, statusResp)


@api_tool_decorator()
def changeTagsForDevice(device, tagsFromGrid, maxGaugeAction):
    # Tag modification
    changeSucceeded = 0
    status = deviceName = deviceId = serial = imei1 = imei2 = None
    if hasattr(device, "device_name"):
        deviceName = device.device_name
        deviceId = device.id
        hardware = device.hardware_info
        network = device.network_info
        serial = hardware["serialNumber"] if "serialNumber" in hardware else None
        imei1 = network["imei1"] if "imei1" in network else None
        imei2 = network["imei2"] if "imei2" in network else None
    elif type(device) is dict:
        deviceName = device["device_name"]
        deviceId = device["id"]
        hardware = device["hardware_info"]
        network = device["network_info"]
        serial = hardware["serialNumber"] if "serialNumber" in hardware else None
        imei1 = network["imei1"] if "imei1" in network else None
        imei2 = network["imei2"] if "imei2" in network else None

    match = list(
        filter(
            lambda x: x["Esper Name"] == deviceName
            or x["Esper Id"] == device
            or x["Serial Number"] == serial
            or x["Custom Serial Number"] == serial
            or x["IMEI 1"] == imei1
            or x["IMEI 2"] == imei2,
            tagsFromGrid,
        )
    )
    if match:
        match = match[0]
        deviceName = (
            match["Esper Name"]
            if "Esper Name" in match and match["Esper Name"]
            else deviceName
        )
        deviceId = (
            match["Esper Id"] if "Esper Id" in match and match["Esper Id"] else deviceId
        )
        tagsFromCell = match["Tags"] if "Tags" in match else []

        try:
            tags = setdevicetags(deviceId, tagsFromCell)
        except Exception as e:
            ApiToolLog().LogError(e)
        if tags == tagsFromCell:
            changeSucceeded += 1
        postEventToFrame(eventUtil.myEVT_UPDATE_GRID_CONTENT, (device, "tags"))
        postEventToFrame(
            eventUtil.myEVT_UPDATE_GAUGE,
            int(Globals.frame.statusBar.gauge.GetValue() + 1 / maxGaugeAction * 100),
        )
    status = {
        "Device Name": deviceName,
        "Device Id": deviceId,
        "Tags": tags,
    }
    return changeSucceeded, status


@api_tool_decorator()
def setAppStateForAllAppsListed(state):
    deviceIdentifers = Globals.frame.gridPanel.getDeviceIdentifersFromGrid(tolerance=1)
    devices = getDevicesFromGrid(deviceIdentifers=deviceIdentifers, tolerance=1)
    if devices:
        deviceList = getDeviceIdFromGridDevices(devices)

        for device in deviceList:
            Globals.THREAD_POOL.enqueue(setAllAppsState, device, Globals.frame.AppState)

        Globals.THREAD_POOL.enqueue(
            wxThread.waitTillThreadsFinish,
            Globals.THREAD_POOL.threads,
            state,
            -1,
            4,
            tolerance=1,
        )


@api_tool_decorator()
def setAllAppsState(device, state):
    stateStatuses = []
    deviceName = None
    deviceId = None
    if hasattr(device, "device_name"):
        deviceName = device.device_name
        deviceId = device.id
    elif type(device) is dict:
        deviceName = device["device_name"]
        deviceId = device["id"]
    else:
        deviceName = device
        deviceId = device
    _, resp = apiCalls.getdeviceapps(deviceId, False, Globals.USE_ENTERPRISE_APP)
    if resp and "results" in resp:
        for app in resp["results"]:
            stateStatus = None
            package_name = None
            if "application" in app:
                package_name = app["application"]["package_name"]
                if app["application"]["package_name"] in Globals.BLACKLIST_PACKAGE_NAME:
                    continue
            else:
                package_name = app["package_name"]
                if app["package_name"] in Globals.BLACKLIST_PACKAGE_NAME:
                    continue
            if state == "DISABLE":
                stateStatus = apiCalls.setAppState(
                    deviceId,
                    package_name,
                    state="DISABLE",
                )
            if state == "HIDE":
                stateStatus = apiCalls.setAppState(
                    deviceId,
                    package_name,
                    state="HIDE",
                )
            if state == "SHOW":
                stateStatus = apiCalls.setAppState(
                    deviceId,
                    package_name,
                    state="SHOW",
                )
            postEventToFrame(
                eventUtil.myEVT_AUDIT,
                {
                    "operation": "SetAppState",
                    "data": {"id": deviceId, "app": package_name, "state": state},
                    "resp": stateStatus,
                },
            )
            if stateStatus and hasattr(stateStatus, "state"):
                entry = {
                    "Device Name": deviceName,
                    "Device id": deviceId,
                    "State Status": stateStatus.state,
                }
                if hasattr(stateStatus, "reason"):
                    entry["Reason"] = stateStatus.reason
                stateStatuses.append(entry)
            else:
                stateStatuses.append(
                    {
                        "Device Name": deviceName,
                        "Device id": deviceId,
                        "State Status": stateStatus,
                    }
                )
    else:
        stateStatuses.append(
            {
                "Device Name": deviceName,
                "Device id": deviceId,
                "State Status": "Failed to obtain device apps: %s" % resp,
            }
        )
    return stateStatuses


@api_tool_decorator()
def getDevicesFromGrid(deviceIdentifers=None, tolerance=0):
    if not deviceIdentifers:
        deviceIdentifers = Globals.frame.gridPanel.getDeviceIdentifersFromGrid(
            tolerance=tolerance
        )
    devices = []
    splitResults = splitListIntoChunks(deviceIdentifers)
    for chunk in splitResults:
        Globals.THREAD_POOL.enqueue(getDevicesFromGridHelper, chunk, devices)
    Globals.THREAD_POOL.join(tolerance)
    return devices


def getDevicesFromGridHelper(deviceIdentifers, devices, maxAttempt=Globals.MAX_RETRY):
    for entry in deviceIdentifers:
        api_response = apiCalls.searchForMatchingDevices(entry)
        if api_response:
            devices += api_response.results
        else:
            postEventToFrame(
                eventUtil.myEVT_LOG,
                "---> ERROR: Failed to find device with identifer: %s" % entry,
            )


@api_tool_decorator()
def relocateDeviceToNewGroup(frame):
    newGroupList = frame.gridPanel.getDeviceGroupFromGrid()
    devices = getDevicesFromGrid(
        newGroupList, tolerance=Globals.THREAD_POOL.getNumberOfActiveThreads()
    )

    splitResults = splitListIntoChunks(devices)

    for chunk in splitResults:
        Globals.THREAD_POOL.enqueue(
            processDeviceGroupMove, chunk, newGroupList, tolerance=2
        )

    Globals.THREAD_POOL.enqueue(
        wxThread.waitTillThreadsFinish,
        Globals.THREAD_POOL.threads,
        GridActions.MOVE_GROUP.value,
        -1,
        5,
        tolerance=Globals.THREAD_POOL.getNumberOfActiveThreads(),
    )


@api_tool_decorator()
def processDeviceGroupMove(deviceChunk, groupList, tolerance=0):
    groupId = None
    results = {}
    for device in deviceChunk:
        groupName = None
        deviceName = None
        deviceId = None
        hardware = None
        network = None
        if hasattr(device, "device_name"):
            deviceName = device.device_name
            deviceId = device.id
            hardware = device.hardware_info
            network = device.network_info
            serial = hardware["serialNumber"] if "serialNumber" in hardware else None
            imei1 = network["imei1"] if "imei1" in network else None
            imei2 = network["imei2"] if "imei2" in network else None
        elif type(device) is dict:
            deviceName = device["device_name"] if "device_name" in device else ""
            deviceId = device["id"] if "id" in device else ""
            hardware = device["hardware_info"] if "hardware_info" in device else ""
            network = device["network_info"] if "network_info" in device else ""
            serial = hardware["serialNumber"] if "serialNumber" in hardware else None
            imei1 = network["imei1"] if "imei1" in network else None
            imei2 = network["imei2"] if "imei2" in network else None
        elif type(device) is str:
            deviceId = device

        match = list(
            filter(
                lambda x: x["Esper Name"] == deviceName
                or x["Esper Id"] == deviceId
                or x["Serial Number"] == serial
                or x["Custom Serial Number"] == serial
                or x["IMEI 1"] == imei1
                or x["IMEI 2"] == imei2,
                groupList,
            )
        )
        if match:
            match = match[0]
            groupName = match["Group"].strip()

        if groupName:
            if isApiKey(groupName):
                resp = moveGroup(groupName, deviceId)
                respText = resp.text if hasattr(resp, "text") else str(resp)
                results[deviceName] = {
                    "Device Name": deviceName,
                    "Device Id": deviceId,
                    "Status Code": resp.status_code
                    if hasattr(resp, "status_code")
                    else None,
                    "Response": resp.json() if hasattr(resp, "json") else respText,
                }
            else:
                # Look up group to see if we know it already, if we don't query it
                groupId = None
                for group in Globals.knownGroups.values():
                    if (
                        type(group) is dict
                        and "name" in group
                        and groupName == group["name"]
                    ):
                        groupId = group["id"]
                        break
                    elif hasattr(group, "name") and groupName == group.name:
                        groupId = group.id
                        break

                if not groupId:
                    groups = getAllGroups(
                        name=groupName,
                        tolerance=Globals.THREAD_POOL.getNumberOfActiveThreads(),
                    )
                    if hasattr(groups, "results"):
                        groups = groups.results
                    elif type(groups) is dict and "results" in groups:
                        groups = groups["results"]
                    if groups:
                        if hasattr(groups[0], "id"):
                            groupId = groups[0].id
                        elif type(groups[0]) is dict and "id" in groups[0]:
                            groupId = groups[0]["id"]
                    else:
                        results[deviceName] = {
                            "Device Name": deviceName,
                            "Device Id": deviceId,
                            "Error": "Invalid Group Name given, no matches found, '%s'"
                            % groupName,
                        }

                if groupId:
                    resp = moveGroup(groupId, deviceId)
                    respText = resp.text if hasattr(resp, "text") else str(resp)
                    results[deviceName] = {
                        "Device Name": deviceName,
                        "Device Id": deviceId,
                        "Status Code": resp.status_code
                        if hasattr(resp, "status_code")
                        else None,
                        "Response": resp.json() if hasattr(resp, "json") else respText,
                    }
        else:
            results[deviceName] = {
                "Device Name": deviceName,
                "Device Id": deviceId,
                "Error": "Invalid Group Name given, '%s'" % groupName,
            }

    if not results:
        results["error"] = {"Error": "Failed to find devices to move, check tenant."}
    return results


@api_tool_decorator()
def processInstallLatestApp(devices, app):
    status = []
    resp = installAppOnDevices(app["pkgName"], version=app["version"], devices=devices)
    if type(resp) == dict and "Error" in resp.keys():
        status.append(
            {
                "Devices": devices,
                "Error": resp["Error"],
            }
        )
    else:
        status += resp
    return status


@api_tool_decorator()
def processUninstallApp(devices, app):
    status = []
    resp = uninstallAppOnDevice(app["pkgName"], device=devices)
    if type(resp) == dict and "Error" in resp.keys():
        status.append(
            {
                "Devices": devices,
                "Error": resp["Error"],
            }
        )
    else:
        status += resp
    return status


def installApp(frame):
    deviceIdentifers = frame.gridPanel.getDeviceIdentifersFromGrid(tolerance=1)
    devices = getDevicesFromGrid(deviceIdentifers=deviceIdentifers, tolerance=1)

    devices = getDeviceIdFromGridDevices(devices)
    deviceList = splitListIntoChunks(devices, maxChunkSize=500)
    for entry in deviceList:
        Globals.THREAD_POOL.enqueue(
            processInstallLatestApp, entry, frame.sidePanel.selectedAppEntry
        )

    Globals.THREAD_POOL.enqueue(
        wxThread.waitTillThreadsFinish,
        Globals.THREAD_POOL.threads,
        GridActions.INSTALL_APP.value,
        -1,
        5,
        tolerance=1,
    )


def uninstallApp(frame):
    deviceIdentifers = frame.gridPanel.getDeviceIdentifersFromGrid(tolerance=1)
    devices = getDevicesFromGrid(deviceIdentifers=deviceIdentifers, tolerance=1)

    devices = getDeviceIdFromGridDevices(devices)
    deviceList = splitListIntoChunks(devices, maxChunkSize=500)
    for entry in deviceList:
        Globals.THREAD_POOL.enqueue(
            processUninstallApp, entry, frame.sidePanel.selectedAppEntry
        )

    Globals.THREAD_POOL.enqueue(
        wxThread.waitTillThreadsFinish,
        Globals.THREAD_POOL.threads,
        GridActions.UNINSTALL_APP.value,
        -1,
        5,
        tolerance=1,
    )


def processBulkFactoryReset(devices, numDevices, processed):
    status = []
    postEventToFrame(
        eventUtil.myEVT_AUDIT,
        {
            "operation": "WIPE",
            "data": devices,
        },
    )
    for device in devices:
        deviceId = None
        if hasattr(device, "device_name"):
            deviceId = deviceId
        else:
            deviceId = device["id"]
        if deviceId:
            resp = apiCalls.factoryResetDevice(deviceId)
            status.append(resp)
            processed.append(device)
        value = int(len(processed) / numDevices * 100)
        postEventToFrame(
            eventUtil.myEVT_UPDATE_GAUGE,
            value,
        )
    return status


def bulkFactoryReset(identifers):
    devices = getDevicesFromGrid(deviceIdentifers=identifers, tolerance=1)

    splitResults = splitListIntoChunks(devices)
    numDevices = len(devices)
    processed = []

    for chunk in splitResults:
        Globals.THREAD_POOL.enqueue(
            processBulkFactoryReset, chunk, numDevices, processed
        )

    Globals.THREAD_POOL.enqueue(
        wxThread.waitTillThreadsFinish,
        Globals.THREAD_POOL.threads,
        GridActions.FACTORY_RESET.value,
        -1,
        5,
        tolerance=1,
    )


def processSetDeviceDisabled(devices, numDevices, processed):
    status = []
    for device in devices:
        deviceId = None
        if hasattr(device, "device_name"):
            deviceId = deviceId
        else:
            deviceId = device["id"]
        if deviceId:
            resp = setDeviceDisabled(deviceId)
            status.append(resp)
            processed.append(device)
        value = int(len(processed) / numDevices * 100)
        postEventToFrame(
            eventUtil.myEVT_UPDATE_GAUGE,
            value,
        )
    postEventToFrame(
        eventUtil.myEVT_AUDIT,
        {
            "operation": "DisableDevice(s)",
            "data": devices,
        },
    )
    return status


def setDevicesDisabled():
    devices = getDevicesFromGrid(tolerance=1)

    splitResults = splitListIntoChunks(devices)
    numDevices = len(devices)
    processed = []

    for chunk in splitResults:
        Globals.THREAD_POOL.enqueue(
            processSetDeviceDisabled, chunk, numDevices, processed
        )

    Globals.THREAD_POOL.enqueue(
        wxThread.waitTillThreadsFinish,
        Globals.THREAD_POOL.threads,
        GridActions.SET_DEVICE_DISABLED.value,
        -1,
        5,
        tolerance=1,
    )


def getDeviceIdFromGridDevices(devices):
    deviceList = []
    for device in devices:
        if type(device) is str:
            deviceList.append(device)
        elif type(device) is dict and "id" in device:
            deviceList.append(device["id"])
        elif hasattr(device, "id"):
            deviceList.append(device.id)
    return deviceList
