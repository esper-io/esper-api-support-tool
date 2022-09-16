#!/usr/bin/env python

from Utility.API.AppUtilities import (
    installAppOnDevices,
    uninstallAppOnDevice,
)
import time

import esperclient
import Common.Globals as Globals

import Utility.API.EsperAPICalls as apiCalls
import Utility.EventUtility as eventUtil

from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.API.DeviceUtility import setDeviceDisabled, setdevicetags
from Utility.Resource import (
    enforceRateLimit,
    isApiKey,
    postEventToFrame,
    splitListIntoChunks,
)
from Utility.Threading import wxThread
from Utility.API.GroupUtility import getAllGroups, moveGroup

from Common.decorator import api_tool_decorator
from Common.enum import GridActions


@api_tool_decorator()
def iterateThroughGridRows(frame, action):
    """Iterates Through Each Device in the Displayed Grid And Performs A Specified Action"""
    if action == GridActions.MODIFY_ALIAS_AND_TAGS.value:
        modifyDevice(frame)
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
def modifyDevice(frame):
    """ Start a thread that will attempt to modify device data """
    Globals.THREAD_POOL.enqueue(executeDeviceModification, frame)


@api_tool_decorator()
def executeDeviceModification(frame, maxAttempt=Globals.MAX_RETRY):
    """ Attempt to modify device data according to what has been changed in the Grid """
    tagsFromGrid, rowTaglist = frame.gridPanel.getDeviceTagsFromGrid()
    aliasDic = frame.gridPanel.getDeviceAliasFromList()
    frame.statusBar.gauge.SetValue(1)
    maxGaugeAction = len(tagsFromGrid.keys()) + len(aliasDic.keys())

    devices = []
    for row in rowTaglist.keys():
        entry = rowTaglist[row]
        identifier = entry

        if "id" in entry.keys():
            identifier = entry["id"]
            devices.append(identifier)
        else:
            if "esperName" in entry.keys():
                identifier = entry["esperName"]
            elif "sn" in entry.keys():
                identifier = entry["sn"]
            elif "csn" in entry.keys():
                identifier = entry["csn"]
            elif "imei1" in entry.keys():
                identifier = entry["imei1"]
            elif "imei2" in entry.keys():
                identifier = entry["imei2"]

            api_response = apiCalls.searchForMatchingDevices(entry)
            if api_response:
                devices += api_response.results
                api_response = None
            else:
                postEventToFrame(
                    eventUtil.myEVT_LOG,
                    "---> ERROR: Failed to find device with identifer: %s" % identifier,
                )

    splitResults = splitListIntoChunks(devices)

    for chunk in splitResults:
        Globals.THREAD_POOL.enqueue(
            processDeviceModificationForList,
            frame,
            chunk,
            tagsFromGrid,
            aliasDic,
            maxGaugeAction,
        )

    Globals.THREAD_POOL.enqueue(
        wxThread.waitTillThreadsFinish,
        Globals.THREAD_POOL.threads,
        -1,
        -1,
        2,
        tolerance=1,
    )


@api_tool_decorator()
def processDeviceModificationForList(
    frame, chunk, tagsFromGrid, aliasDic, maxGaugeAction
):
    changeSucceeded = 0
    succeeded = 0
    numNewName = 0
    status = []
    aliasStatus = []
    tagStatus = []
    for device in chunk:
        numSucceeded, tagStatusMsg = changeTagsForDevice(
            device, tagsFromGrid, frame, maxGaugeAction
        )
        numNameChanged, numSuccess, aliasStatusMsg = changeAliasForDevice(
            device, aliasDic, frame, maxGaugeAction
        )
        changeSucceeded += numSucceeded
        tagStatus.append(tagStatusMsg)
        numNewName += numNameChanged
        succeeded += numSuccess
        aliasStatus.append(aliasStatusMsg)
    tmp = []
    for entry in aliasStatus:
        match = list(
            filter(
                lambda x: x["Device Name"] == entry["Device Name"],
                tagStatus,
            )
        )
        newEntry = {}
        for m in match:
            newEntry.update(m)
        newEntry.update(entry)
        if newEntry not in tmp:
            tmp.append(newEntry)

    for entry in tagStatus:
        match = list(
            filter(
                lambda x: x["Device Name"] == entry["Device Name"],
                tmp,
            )
        )
        newEntry = {}
        for m in match:
            newEntry.update(m)
        newEntry.update(entry)
        if newEntry not in status:
            status.append(newEntry)

    return (changeSucceeded, succeeded, numNewName, chunk, status)


@api_tool_decorator()
def changeAliasForDevice(device, aliasDic, frame, maxGaugeAction):
    numNewName = 0
    succeeded = 0
    logString = ""
    status = None
    deviceName = None
    deviceId = None
    aliasName = None
    hardware = None
    if hasattr(device, "device_name"):
        aliasName = device.alias_name
        deviceName = device.device_name
        deviceId = device.id
        hardware = device.hardware_info
    elif type(device) is dict:
        deviceName = device["device_name"]
        deviceId = device["id"]
        aliasName = device["alias_name"]
        hardware = device["hardwareInfo"]
    else:
        deviceName = ""
        deviceId = device
        aliasName = ""
        hardware = ""
    # Alias modification
    if (
        deviceName in aliasDic.keys()
        or ("serialNumber" in hardware and hardware["serialNumber"] in aliasDic.keys())
        or (
            "customSerialNumber" in hardware
            and hardware["customSerialNumber"] in aliasDic.keys()
        )
        or deviceId in aliasDic.keys()
    ):
        newName = None
        if deviceName in aliasDic:
            newName = aliasDic[deviceName]
        elif "serialNumber" in hardware and hardware["serialNumber"] in aliasDic:
            newName = aliasDic[hardware["serialNumber"]]
        elif (
            "customSerialNumber" in hardware
            and hardware["customSerialNumber"] in aliasDic
        ):
            newName = aliasDic[hardware["customSerialNumber"]]
        elif deviceId in aliasDic:
            newName = aliasDic[deviceId]
        logString = str("--->" + str(deviceName) + " : " + str(newName) + "--->")
        if not newName and not aliasName:
            status = {
                "Device Name": deviceName,
                "Device Id": deviceId,
                "Alias Status": "No alias to set",
            }
            return (numNewName, succeeded, status)
        if newName != str(aliasName):
            numNewName += 1
            status = ""
            try:
                ignoreQueued = False if Globals.REACH_QUEUED_ONLY else True
                status = apiCalls.setdevicename(frame, deviceId, newName, ignoreQueued)
            except Exception as e:
                ApiToolLog().LogError(e)
            if "Success" in str(status):
                logString = logString + " <success>"
                succeeded += 1
            elif "Queued" in str(status):
                logString = logString + " <Queued> Make sure device is online."
                postEventToFrame(eventUtil.myEVT_ON_FAILED, (device, "Queued"))
            elif "Scheduled" in str(status):
                logString = logString + " <Scheduled> Make sure device is online."
                postEventToFrame(eventUtil.myEVT_ON_FAILED, (device, "Scheduled"))
            else:
                logString = logString + " <failed>"
                postEventToFrame(eventUtil.myEVT_ON_FAILED, device)
        else:
            logString = logString + " (Alias Name already set)"
            status = {
                "Device Name": deviceName,
                "Device Id": deviceId,
                "Alias Status": "Alias Name already set",
            }
        if "Success" in logString or "Queued" in logString:
            postEventToFrame(eventUtil.myEVT_UPDATE_GRID_CONTENT, (device, "alias"))
        postEventToFrame(
            eventUtil.myEVT_UPDATE_GAUGE,
            int(frame.statusBar.gauge.GetValue() + 1 / maxGaugeAction * 100),
        )
        postEventToFrame(eventUtil.myEVT_LOG, logString)
    if type(status) != dict:
        status = {
            "Device Name": deviceName,
            "Device Id": deviceId,
            "Alias Status": status if status else "No alias to set",
        }
    return (numNewName, succeeded, status)


@api_tool_decorator()
def changeTagsForDevice(device, tagsFromGrid, frame, maxGaugeAction):
    # Tag modification
    changeSucceeded = 0
    deviceName = None
    deviceId = None
    hardware = None
    if hasattr(device, "device_name"):
        deviceName = device.device_name
        deviceId = device.id
        hardware = device.hardware_info
    elif type(device) is dict:
        deviceName = device["device_name"]
        deviceId = device["id"]
        hardware = device["hardwareInfo"]
    else:
        deviceName = ""
        deviceId = device
        hardware = ""
    if (
        deviceName in tagsFromGrid.keys()
        or (
            "serialNumber" in hardware
            and hardware["serialNumber"] in tagsFromGrid.keys()
        )
        or (
            "customSerialNumber" in hardware
            and hardware["customSerialNumber"] in tagsFromGrid.keys()
        )
        or (
            deviceId in tagsFromGrid.keys()
        )
    ):
        tagsFromCell = None
        key = None
        if deviceName in tagsFromGrid:
            key = deviceName
        elif "serialNumber" in hardware and hardware["serialNumber"] in tagsFromGrid:
            key = hardware["serialNumber"]
        elif (
            "customSerialNumber" in hardware
            and hardware["customSerialNumber"] in tagsFromGrid
        ):
            key = hardware["customSerialNumber"]
        elif deviceId in tagsFromGrid:
            key = deviceId
        tagsFromCell = tagsFromGrid[key]
        try:
            tags = setdevicetags(deviceId, tagsFromCell)
        except Exception as e:
            ApiToolLog().LogError(e)
        if tags == tagsFromGrid[key]:
            changeSucceeded += 1
        postEventToFrame(eventUtil.myEVT_UPDATE_GRID_CONTENT, (device, "tags"))
        postEventToFrame(eventUtil.myEVT_UPDATE_TAG_CELL, (deviceName, tags))
        postEventToFrame(
            eventUtil.myEVT_UPDATE_GAUGE,
            int(frame.statusBar.gauge.GetValue() + 1 / maxGaugeAction * 100),
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
        # for device in devices:
        #     Globals.THREAD_POOL.enqueue(
        #         setAllAppsState, Globals.frame, device, Globals.frame.AppState
        #     )
        deviceList = getDeviceIdFromGridDevices(devices)

        Globals.THREAD_POOL.enqueue(
            setAllAppsState, Globals.frame, deviceList, Globals.frame.AppState
        )

        Globals.THREAD_POOL.enqueue(
            wxThread.waitTillThreadsFinish,
            Globals.THREAD_POOL.threads,
            state,
            -1,
            4,
            tolerance=1,
        )


@api_tool_decorator()
def setAllAppsState(frame, device, state):
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
    return stateStatuses


@api_tool_decorator()
def getDevicesFromGrid(deviceIdentifers=None, tolerance=0):
    if not deviceIdentifers:
        deviceIdentifers = Globals.frame.gridPanel.getDeviceIdentifersFromGrid(tolerance=tolerance)
    devices = []
    api_instance = esperclient.DeviceApi(esperclient.ApiClient(Globals.configuration))
    splitResults = splitListIntoChunks(deviceIdentifers)
    for chunk in splitResults:
        Globals.THREAD_POOL.enqueue(
            getDevicesFromGridHelper, chunk, api_instance, devices
        )
    Globals.THREAD_POOL.join(tolerance)
    return devices


def getDevicesFromGridHelper(
    deviceIdentifers, api_instance, devices, maxAttempt=Globals.MAX_RETRY
):
    for entry in deviceIdentifers:
        api_response = None
        identifier = None
        deviceHadId = False
        for attempt in range(maxAttempt):
            try:
                enforceRateLimit()
                if type(entry) == dict:
                    if entry["id"]:
                        devices.append(entry["id"])
                        deviceHadId = True
                        break

                    if entry["name"]:
                        identifier = entry["name"]
                        api_response = api_instance.get_all_devices(
                            Globals.enterprise_id,
                            name=identifier,
                            limit=Globals.limit,
                            offset=Globals.offset,
                        )
                    elif entry["serial"]:
                        identifier = entry["serial"]
                        api_response = api_instance.get_all_devices(
                            Globals.enterprise_id,
                            serial=identifier,
                            limit=Globals.limit,
                            offset=Globals.offset,
                        )
                    elif entry["custom"]:
                        identifier = entry["custom"]
                        api_response = api_instance.get_all_devices(
                            Globals.enterprise_id,
                            search=identifier,
                            limit=Globals.limit,
                            offset=Globals.offset,
                        )
                    elif entry["imei1"]:
                        identifier = entry["imei1"]
                        api_response = api_instance.get_all_devices(
                            Globals.enterprise_id,
                            imei=identifier,
                            limit=Globals.limit,
                            offset=Globals.offset,
                        )
                    elif entry["imei2"]:
                        identifier = entry["imei2"]
                        api_response = api_instance.get_all_devices(
                            Globals.enterprise_id,
                            imei=identifier,
                            limit=Globals.limit,
                            offset=Globals.offset,
                        )
                elif type(entry) == str:
                    api_response = api_instance.get_all_devices(
                        Globals.enterprise_id,
                        search=entry,
                        limit=Globals.limit,
                        offset=Globals.offset,
                    )
                ApiToolLog().LogApiRequestOccurrence(
                    "getAllDevices",
                    api_instance.get_all_devices,
                    Globals.PRINT_API_LOGS,
                )
                break
            except Exception as e:
                if attempt == maxAttempt - 1:
                    ApiToolLog().LogError(e, postIssue=False)
                    raise e
                if "429" not in str(e) and "Too Many Requests" not in str(e):
                    time.sleep(Globals.RETRY_SLEEP)
                else:
                    time.sleep(
                        Globals.RETRY_SLEEP * 20 * (attempt + 1)
                    )  # Sleep for a minute * retry number
        if api_response:
            devices += api_response.results
            api_response = None
        elif not deviceHadId:
            postEventToFrame(
                eventUtil.myEVT_LOG,
                "---> ERROR: Failed to find device with identifer: %s" % identifier,
            )


@api_tool_decorator()
def relocateDeviceToNewGroup(frame):
    devices = getDevicesFromGrid(tolerance=1)
    newGroupList = frame.gridPanel.getDeviceGroupFromGrid()

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
        tolerance=1,
    )


@api_tool_decorator()
def processDeviceGroupMove(deviceChunk, groupList, tolerance=0):
    groupId = None
    results = {}
    groupListKeys = groupList.keys()
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
        else:
            deviceName = device["device_name"]
            deviceId = device["id"]
            hardware = device["hardwareInfo"]
        if deviceName in groupListKeys:
            groupName = groupList[deviceName]
        elif "serialNumber" in hardware and hardware["serialNumber"] in groupListKeys:
            groupName = groupList[hardware["serialNumber"]]
        elif (
            "customSerialNumber" in hardware
            and hardware["customSerialNumber"] in groupListKeys
        ):
            groupName = groupList[hardware["customSerialNumber"]]
        elif (
            hasattr(device, "network_info")
            and "imei1" in network
            and network["imei1"] in groupListKeys
        ):
            groupName = groupList[network["imei1"]]
        elif (
            hasattr(device, "network_info")
            and "imei2" in network
            and network["imei2"] in groupListKeys
        ):
            groupName = groupList[network["imei1"]]
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
                groups = getAllGroups(name=groupName, tolerance=tolerance).results
                if groups:
                    groupId = groups[0].id
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
                        "Error": "Invalid Group Name given, no matches found, '%s'"
                        % groupName,
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
    Globals.THREAD_POOL.enqueue(
        processInstallLatestApp, devices, frame.sidePanel.selectedAppEntry
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
    Globals.THREAD_POOL.enqueue(
        processUninstallApp, devices, frame.sidePanel.selectedAppEntry
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
