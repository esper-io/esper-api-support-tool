#!/usr/bin/env python

import Common.Globals as Globals
import Utility.API.EsperAPICalls as apiCalls
import Utility.EventUtility as eventUtil
from Common.decorator import api_tool_decorator
from Common.enum import GridActions
from Utility.API.DeviceUtility import setdevicetags
from Utility.API.GroupUtility import getAllGroups, moveGroup
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Resource import isApiKey, postEventToFrame, splitListIntoChunks
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


@api_tool_decorator()
def modifyDevice(frame, action):
    """Start a thread that will attempt to modify device data"""
    Globals.THREAD_POOL.enqueue(executeDeviceModification, frame, action)


@api_tool_decorator()
def executeDeviceModification(frame, action, maxAttempt=Globals.MAX_RETRY):
    """Attempt to modify device data according to what has been changed in the Grid"""
    rowTaglist = aliasList = None
    maxGaugeAction = 0
    if action == GridActions.MODIFY_TAGS.value:
        rowTaglist = frame.gridPanel.getDeviceTagsFromGrid()
        maxGaugeAction = len(rowTaglist) if rowTaglist else 0
    else:
        aliasList = frame.gridPanel.getDeviceAliasFromList()
        if aliasList:
            maxGaugeAction = len(aliasList)
    postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 1)

    postEventToFrame(
        eventUtil.myEVT_AUDIT,
        {
            "operation": ("ChangeTags" if action == GridActions.MODIFY_TAGS.value else "ChangeAlias"),
            "data": ({"tags": rowTaglist} if action == GridActions.MODIFY_TAGS.value else {"alias": aliasList}),
        },
    )
    devices = obtainEsperDeviceEntriesFromList(rowTaglist if action == GridActions.MODIFY_TAGS.value else aliasList)
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
def processDeviceModificationForList(action, chunk, tagsFromGrid, aliasDic, maxGaugeAction):
    tracker = {
        "success": 0,
        "fail": 0,
        "progress": 0,
        "sent": 0,
        "skip": 0,
        "invalid": 0,
    }
    status = []
    for device in chunk:
        if action == GridActions.MODIFY_TAGS.value:
            tagStatusMsg = changeTagsForDevice(device, tagsFromGrid, maxGaugeAction, tracker)
            status.append(tagStatusMsg)
        else:
            aliasStatusMsg = changeAliasForDevice(device, aliasDic, maxGaugeAction, tracker)
            status.append(aliasStatusMsg)

    return (tracker, chunk, status)


@api_tool_decorator()
def changeAliasForDevice(device, aliasList, maxGaugeAction, tracker):
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
        deviceName = match["Esper Name"] if "Esper Name" in match and match["Esper Name"] else deviceName
        deviceId = match["Esper Id"] if "Esper Id" in match and match["Esper Id"] else deviceId
        newName = match["Alias"] if "Alias" in match else ""

        logString = str("--->" + str(deviceName) + " : " + str(newName) + "--->")
        if not newName:
            # Return if no alias specified
            return {
                "Device Name": deviceName,
                "Device Id": deviceId,
                "Alias Status": "No alias to set",
            }

        stateStr = "Queued"
        if newName != str(aliasName):
            # Change alias if it differs than what is already set (as retrieved by API)
            status = ""
            try:
                ignoreQueued = False if Globals.REACH_QUEUED_ONLY else True
                resp, status = apiCalls.setdevicename(deviceId, newName, ignoreQueued)
                tracker["sent"] += 1
            except Exception as e:
                ApiToolLog().LogError(e)

            if hasattr(status, "to_dict"):
                status = status.to_dict()

            if type(status) is list:
                logString = logString + str(status)
                added = False
                for entry in status:
                    if type(entry) is dict and entry.get("state", ""):
                        state = entry["state"]
                        total = entry.get("total", 0)
                        if total > 0:
                            added = True
                        if "Success" in state:
                            tracker["success"] += total
                            if total > 0:
                                stateStr = "Success"
                        elif (
                            "Queued" in state
                            or "Scheduled" in state
                            or "Progress" in state
                            or "Initiated" in state
                            or "Acknowledged" in state
                        ):
                            tracker["progress"] += total
                            if total > 0:
                                stateStr = "In-Progress"
                        else:
                            tracker["fail"] += total
                            if total > 0:
                                stateStr = "Failed"
                if not added:
                    tracker["progress"] += 1
            elif "Success" in str(status):
                logString = logString + " <success>"
                tracker["success"] += 1
                stateStr = "Success"
            elif "Queued" in str(status):
                logString = logString + " <Queued> Make sure device is online."
                tracker["progress"] += 1
                stateStr = "In-Progress"
            elif "Scheduled" in str(status):
                logString = logString + " <Scheduled> Make sure device is online."
                tracker["progress"] += 1
                stateStr = "In-Progress"
            elif "in-progress" in str(status):
                logString = logString + " <In-Progress> Make sure device is online."
                tracker["progress"] += 1
                stateStr = "In-Progress"
            else:
                logString = logString + " <failed>"
                tracker["fail"] += 1
                stateStr = "Failed"
        else:
            tracker["skip"] += 1
            logString = logString + " (Alias Name already set)"
            stateStr = "Skipped"
            status = {
                "Device Name": deviceName,
                "Device Id": deviceId,
                "Reason": "Alias Name already set",
                "state": None,
            }
        if "Success" in logString or "Queued" in logString:
            postEventToFrame(eventUtil.myEVT_UPDATE_GRID_CONTENT, (device, "alias"))
        postEventToFrame(
            eventUtil.myEVT_UPDATE_GAUGE,
            int(Globals.frame.statusBar.gauge.GetValue() + 1 / maxGaugeAction * 100),
        )
        postEventToFrame(eventUtil.myEVT_LOG, logString)
    else:
        tracker["invalid"] += 1
    statusResp = {
        "Device Name": deviceName,
        "Device Id": deviceId,
        "Alias Status": status if status else "No alias to set",
    }
    if status:
        statusResp["Alias Status"] = {
            "Command Id": resp.get("content", {}).get("id", "Unknown ID"),
            "Device Name": deviceName,
            "Device Id": deviceId,
            "State": resp.get("content", {}).get("state", stateStr),
            "reason": resp.get("content", {}).get("reason", ""),
        }
    else:
        statusResp["Alias Status"] = "No alias to set"
    return statusResp


@api_tool_decorator()
def changeTagsForDevice(device, tagsFromGrid, maxGaugeAction, tracker):
    # Tag modification
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
        deviceName = match["Esper Name"] if "Esper Name" in match and match["Esper Name"] else deviceName
        deviceId = match["Esper Id"] if "Esper Id" in match and match["Esper Id"] else deviceId
        tagsFromCell = match["Tags"] if "Tags" in match else []

        try:
            tags = setdevicetags(deviceId, tagsFromCell)
            tracker["sent"] += 1
        except Exception as e:
            ApiToolLog().LogError(e)
        if tags == tagsFromCell or (not tags and not tagsFromCell):
            tracker["success"] += 1
        else:
            tracker["fail"] += 1
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
    else:
        tracker["invalid"] += 1
        status = {
            "Device Name": deviceName,
            "Device Id": deviceId,
            "Tags": "No tags to set",
        }
    return status


@api_tool_decorator()
def getDevicesFromGrid(deviceIdentifers=None, tolerance=0):
    if not deviceIdentifers:
        deviceIdentifers = Globals.frame.gridPanel.getDeviceIdentifersFromGrid(tolerance=tolerance)
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
    devices = getDevicesFromGrid(newGroupList, tolerance=Globals.THREAD_POOL.getNumberOfActiveThreads())

    splitResults = splitListIntoChunks(devices)

    for chunk in splitResults:
        Globals.THREAD_POOL.enqueue(processDeviceGroupMove, chunk, newGroupList, tolerance=2)

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
                    "Status Code": (resp.status_code if hasattr(resp, "status_code") else None),
                    "Response": (resp.json() if hasattr(resp, "json") else respText),
                }
            else:
                # Look up group to see if we know it already, if we don't query it
                groupId = None
                for group in Globals.knownGroups.values():
                    if type(group) is dict and "name" in group and groupName == group["name"]:
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
                            "Error": "Invalid Group Name given, no matches found, '%s'" % groupName,
                        }

                if groupId:
                    resp = moveGroup(groupId, deviceId)
                    respText = resp.text if hasattr(resp, "text") else str(resp)
                    results[deviceName] = {
                        "Device Name": deviceName,
                        "Device Id": deviceId,
                        "Status Code": (resp.status_code if hasattr(resp, "status_code") else None),
                        "Response": (resp.json() if hasattr(resp, "json") else respText),
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
