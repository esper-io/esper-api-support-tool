#!/usr/bin/env python

from Utility.AppUtilities import (
    getdeviceapps,
    installAppOnDevices,
    uninstallAppOnDevice,
)
import time

import esperclient
from Common import Globals

from Utility.ApiToolLogging import ApiToolLog
from Utility.DeviceUtility import setDeviceDisabled, setdevicetags
from Utility.Resource import (
    isApiKey,
    joinThreadList,
    limitActiveThreads,
    postEventToFrame,
    splitListIntoChunks,
)
from Utility import wxThread
from Utility.GroupUtility import getAllGroups, moveGroup
import Utility.EsperAPICalls as apiCalls

from Common.decorator import api_tool_decorator
from Common.enum import GridActions
import Common.Globals as Globals
import Utility.EventUtility as eventUtil


@api_tool_decorator()
def iterateThroughGridRows(frame, action):
    """Iterates Through Each Device in the Displayed Grid And Performs A Specified Action"""
    if action == GridActions.MODIFY_ALIAS_AND_TAGS.value:
        modifyDevice(frame)
    if action == GridActions.SET_APP_STATE.value:
        setAppStateForAllAppsListed(action)
    if action == 50:
        setAppStateForSpecificAppListed(action)
    if action == GridActions.MOVE_GROUP.value:
        relocateDeviceToNewGroup(frame)
    if action == GridActions.INSTALL_LATEST_APP.value:
        installListedLatestApp(frame)
    if action == GridActions.UNINSTALL_LISTED_APP.value:
        uninstallListedApp(frame)
    if action == GridActions.INSTALL_APP.value:
        installApp(frame)
    if action == GridActions.UNINSTALL_APP.value:
        uninstallApp(frame)
    if action == GridActions.SET_DEVICE_DISABLED.value:
        setDevicesDisabled()


@api_tool_decorator()
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


@api_tool_decorator()
def executeDeviceModification(frame, maxAttempt=Globals.MAX_RETRY):
    """ Attempt to modify device data according to what has been changed in the Grid """
    tagsFromGrid, rowTaglist = frame.gridPanel.getDeviceTagsFromGrid()
    aliasDic = frame.gridPanel.getDeviceAliasFromList()
    frame.gauge.SetValue(1)
    maxGaugeAction = len(tagsFromGrid.keys()) + len(aliasDic.keys())

    devices = []
    for row in rowTaglist.keys():
        entry = rowTaglist[row]

        api_instance = esperclient.DeviceApi(
            esperclient.ApiClient(Globals.configuration)
        )
        api_response = None
        identifier = None
        for attempt in range(maxAttempt):
            try:
                if "esperName" in entry.keys():
                    identifier = entry["esperName"]
                    api_response = api_instance.get_all_devices(
                        Globals.enterprise_id,
                        name=identifier,
                        limit=Globals.limit,
                        offset=Globals.offset,
                    )
                elif "sn" in entry.keys():
                    identifier = entry["sn"]
                    api_response = api_instance.get_all_devices(
                        Globals.enterprise_id,
                        serial=identifier,
                        limit=Globals.limit,
                        offset=Globals.offset,
                    )
                elif "csn" in entry.keys():
                    identifier = entry["csn"]
                    api_response = api_instance.get_all_devices(
                        Globals.enterprise_id,
                        search=identifier,
                        limit=Globals.limit,
                        offset=Globals.offset,
                    )
                elif "imei1" in entry.keys():
                    identifier = entry["imei1"]
                    api_response = api_instance.get_all_devices(
                        Globals.enterprise_id,
                        imei=identifier,
                        limit=Globals.limit,
                        offset=Globals.offset,
                    )
                elif "imei2" in entry.keys():
                    identifier = entry["imei2"]
                    api_response = api_instance.get_all_devices(
                        Globals.enterprise_id,
                        imei=identifier,
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
                    ApiToolLog().LogError(e)
                    raise e
                time.sleep(Globals.RETRY_SLEEP)
        if api_response:
            devices += api_response.results
            api_response = None
        else:
            postEventToFrame(
                eventUtil.myEVT_LOG,
                "---> ERROR: Failed to find device with identifer: %s" % identifier,
            )

    splitResults = splitListIntoChunks(devices)

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
        limitActiveThreads(threads)

    t = wxThread.GUIThread(
        frame,
        wxThread.waitTillThreadsFinish,
        args=(tuple(threads), -1, -1, 2),
        name="waitTillThreadsFinish",
    )
    t.start()


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
            changeSucceeded += t.result[0]
            if len(t.result) > 1 and t.result[1]:
                tagStatus.append(t.result[1])
        if t2.result:
            numNewName += t2.result[0]
            succeeded += t2.result[1]
            if len(t2.result) > 2 and t2.result[2]:
                aliasStatus.append(t2.result[2])

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

    return (changeSucceeded, succeeded, numNewName, tagsFromGrid, status)


@api_tool_decorator()
def changeAliasForDevice(device, aliasDic, frame, maxGaugeAction):
    numNewName = 0
    succeeded = 0
    logString = ""
    status = None
    # Alias modification
    if (
        device.device_name in aliasDic.keys()
        or (
            "serialNumber" in device.hardware_info
            and device.hardware_info["serialNumber"] in aliasDic.keys()
        )
        or (
            "customSerialNumber" in device.hardware_info
            and device.hardware_info["customSerialNumber"] in aliasDic.keys()
        )
    ):
        newName = None
        if device.device_name in aliasDic:
            newName = aliasDic[device.device_name]
        elif (
            "serialNumber" in device.hardware_info
            and device.hardware_info["serialNumber"] in aliasDic
        ):
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
            status = {
                "Device Name": device.device_name,
                "Device Id": device.id,
                "Alias Status": "No alias to set",
            }
            return (numNewName, succeeded, status)
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
                "Device Name": device.device_name,
                "Device Id": device.id,
                "Alias Status": "Alias Name already set",
            }
        if "Success" in logString or "Queued" in logString:
            postEventToFrame(eventUtil.myEVT_UPDATE_GRID_CONTENT, (device, "alias"))
        postEventToFrame(
            eventUtil.myEVT_UPDATE_GAUGE,
            int(frame.gauge.GetValue() + 1 / maxGaugeAction * 100),
        )
        postEventToFrame(eventUtil.myEVT_LOG, logString)
    if type(status) != dict:
        status = {
            "Device Name": device.device_name,
            "Device Id": device.id,
            "Alias Status": status if status else "No alias to set",
        }
    return (numNewName, succeeded, status)


@api_tool_decorator()
def changeTagsForDevice(device, tagsFromGrid, frame, maxGaugeAction):
    # Tag modification
    changeSucceeded = 0
    if (
        device.device_name in tagsFromGrid.keys()
        or (
            "serialNumber" in device.hardware_info
            and device.hardware_info["serialNumber"] in tagsFromGrid.keys()
        )
        or (
            "customSerialNumber" in device.hardware_info
            and device.hardware_info["customSerialNumber"] in tagsFromGrid.keys()
        )
    ):
        tagsFromCell = None
        key = None
        if device.device_name in tagsFromGrid:
            key = device.device_name
        elif (
            "serialNumber" in device.hardware_info
            and device.hardware_info["serialNumber"] in tagsFromGrid
        ):
            key = device.hardware_info["serialNumber"]
        elif (
            "customSerialNumber" in device.hardware_info
            and device.hardware_info["customSerialNumber"] in tagsFromGrid
        ):
            key = device.hardware_info["customSerialNumber"]
        tagsFromCell = tagsFromGrid[key]
        try:
            tags = setdevicetags(device.id, tagsFromCell)
        except Exception as e:
            ApiToolLog().LogError(e)
        if tags == tagsFromGrid[key]:
            changeSucceeded += 1
        postEventToFrame(eventUtil.myEVT_UPDATE_GRID_CONTENT, (device, "tags"))
        postEventToFrame(eventUtil.myEVT_UPDATE_TAG_CELL, (device.device_name, tags))
        postEventToFrame(
            eventUtil.myEVT_UPDATE_GAUGE,
            int(frame.gauge.GetValue() + 1 / maxGaugeAction * 100),
        )
        status = {
            "Device Name": device.device_name,
            "Device Id": device.id,
            "Tags": tags,
        }
    return changeSucceeded, status


@api_tool_decorator()
def setAppStateForAllAppsListed(state, maxAttempt=Globals.MAX_RETRY):
    deviceIdentifers = Globals.frame.gridPanel.getDeviceIdentifersFromGrid()
    devices = getDevicesFromGrid(deviceIdentifers=deviceIdentifers)
    if devices:
        threads = []
        for device in devices:
            t = wxThread.GUIThread(
                Globals.frame,
                setAllAppsState,
                args=(Globals.frame, device, Globals.frame.AppState),
                name="setAllAppsState",
            )
            threads.append(t)
            t.start()
            limitActiveThreads(threads)
        t = wxThread.GUIThread(
            Globals.frame,
            wxThread.waitTillThreadsFinish,
            args=(tuple(threads), state, -1, 4),
            name="waitTillThreadsFinish%s" % state,
        )
        t.start()


@api_tool_decorator()
def setAllAppsState(frame, device, state):
    stateStatuses = []
    _, resp = getdeviceapps(device.id, False, Globals.USE_ENTERPRISE_APP)
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
        if state == "DISABLE":
            stateStatus = apiCalls.setAppState(
                device.id,
                package_name,
                appVer=app_version,
                state="DISABLE",
            )
        if state == "HIDE":
            stateStatus = apiCalls.setAppState(
                device.id,
                package_name,
                appVer=app_version,
                state="HIDE",
            )
        if state == "SHOW":
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


@api_tool_decorator()
def setAppStateForSpecificAppListed(action, maxAttempt=Globals.MAX_RETRY):
    api_response = getDevicesFromGrid()
    state = None
    if action == 50:
        state == "HIDE"

    appList = Globals.frame.gridPanel.getDeviceAppFromGrid()
    if api_response:
        tempRes = []
        for device in api_response.results:
            for deviceIds in appList.keys():
                if (
                    device.device_name in deviceIds
                    or (
                        "serialNumber" in device.hardware_info
                        and device.hardware_info["serialNumber"] in deviceIds
                    )
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
                or (
                    "serialNumber" in device.hardware_info
                    and device.hardware_info["serialNumber"] in appList.keys()
                )
                or (
                    "customSerialNumber" in device.hardware_info
                    and device.hardware_info["customSerialNumber"] in appList.keys()
                )
            ):
                package_names = None
                if device.device_name in appList.keys():
                    package_names = appList[device.device_name]
                elif (
                    "serialNumber" in device.hardware_info
                    and device.hardware_info["serialNumber"] in appList.keys()
                ):
                    package_names = appList[device.hardware_info["serialNumber"]]
                elif (
                    "customSerialNumber" in device.hardware_info
                    and device.hardware_info["customSerialNumber"] in appList.keys()
                ):
                    package_names = appList[device.hardware_info["customSerialNumber"]]
                package_names = package_names.split(",")
                if package_names:
                    for package_name in package_names:
                        if package_name.strip():
                            t = wxThread.GUIThread(
                                Globals.frame,
                                apiCalls.setAppState,
                                args=(
                                    device.id,
                                    package_name.strip(),
                                    state,
                                ),
                                name="setAllAppsState",
                            )
                            threads.append(t)
                            t.start()
                        limitActiveThreads(threads)
        t = wxThread.GUIThread(
            Globals.frame,
            wxThread.waitTillThreadsFinish,
            args=(tuple(threads), state, -1, 4),
            name="waitTillThreadsFinish%s" % state,
        )
        t.start()


@api_tool_decorator()
def getDevicesFromGrid(deviceIdentifers=None, maxAttempt=Globals.MAX_RETRY):
    if not deviceIdentifers:
        deviceIdentifers = Globals.frame.gridPanel.getDeviceIdentifersFromGrid()
    devices = []
    api_instance = esperclient.DeviceApi(esperclient.ApiClient(Globals.configuration))
    splitResults = splitListIntoChunks(deviceIdentifers)
    threads = []
    for chunk in splitResults:
        t = wxThread.GUIThread(
            Globals.frame,
            getDevicesFromGridHelper,
            args=(chunk, api_instance, devices),
            name="getDevicesFromGridHelper",
        )
        threads.append(t)
        t.start()
        limitActiveThreads(threads)
    joinThreadList(threads)
    return devices


def getDevicesFromGridHelper(
    deviceIdentifers, api_instance, devices, maxAttempt=Globals.MAX_RETRY
):
    for entry in deviceIdentifers:
        api_response = None
        identifier = None
        for attempt in range(maxAttempt):
            try:
                if type(entry) == tuple or type(entry) == list:
                    if entry[0]:
                        identifier = entry[0]
                        api_response = api_instance.get_all_devices(
                            Globals.enterprise_id,
                            name=identifier,
                            limit=Globals.limit,
                            offset=Globals.offset,
                        )
                    elif entry[1]:
                        identifier = entry[1]
                        api_response = api_instance.get_all_devices(
                            Globals.enterprise_id,
                            serial=identifier,
                            limit=Globals.limit,
                            offset=Globals.offset,
                        )
                    elif entry[2]:
                        identifier = entry[2]
                        api_response = api_instance.get_all_devices(
                            Globals.enterprise_id,
                            search=identifier,
                            limit=Globals.limit,
                            offset=Globals.offset,
                        )
                    elif entry[3]:
                        identifier = entry[3]
                        api_response = api_instance.get_all_devices(
                            Globals.enterprise_id,
                            imei=identifier,
                            limit=Globals.limit,
                            offset=Globals.offset,
                        )
                    elif entry[4]:
                        identifier = entry[4]
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
                    ApiToolLog().LogError(e)
                    raise e
                time.sleep(Globals.RETRY_SLEEP)
        if api_response:
            devices += api_response.results
            api_response = None
        else:
            postEventToFrame(
                eventUtil.myEVT_LOG,
                "---> ERROR: Failed to find device with identifer: %s" % identifier,
            )


@api_tool_decorator()
def relocateDeviceToNewGroup(frame, maxAttempt=Globals.MAX_RETRY):
    devices = getDevicesFromGrid()
    newGroupList = frame.gridPanel.getDeviceGroupFromGrid()

    splitResults = splitListIntoChunks(devices)
    threads = []

    for chunk in splitResults:
        t = wxThread.GUIThread(
            frame,
            processDeviceGroupMove,
            args=(chunk, newGroupList),
            name="processDeviceGroupMove",
        )
        threads.append(t)
        t.start()
        limitActiveThreads(threads)

    t = wxThread.GUIThread(
        frame,
        wxThread.waitTillThreadsFinish,
        args=(tuple(threads), GridActions.MOVE_GROUP.value, -1, 5),
        name="waitTillThreadsFinish",
    )
    t.start()


@api_tool_decorator()
def processDeviceGroupMove(deviceChunk, groupList):
    groupId = None
    results = {}
    groupListKeys = groupList.keys()
    for device in deviceChunk:
        groupName = None
        if device.device_name in groupListKeys:
            groupName = groupList[device.device_name]
        elif (
            "serialNumber" in device.hardware_info
            and device.hardware_info["serialNumber"] in groupListKeys
        ):
            groupName = groupList[device.hardware_info["serialNumber"]]
        elif (
            "customSerialNumber" in device.hardware_info
            and device.hardware_info["customSerialNumber"] in groupListKeys
        ):
            groupName = groupList[device.hardware_info["customSerialNumber"]]
        elif (
            hasattr(device, "network_info")
            and "imei1" in device.network_info
            and device.network_info["imei1"] in groupListKeys
        ):
            groupName = groupList[device.network_info["imei1"]]
        elif (
            hasattr(device, "network_info")
            and "imei2" in device.network_info
            and device.network_info["imei2"] in groupListKeys
        ):
            groupName = groupList[device.network_info["imei1"]]
        if groupName:
            if isApiKey(groupName):
                resp = moveGroup(groupName, device.id)
                respText = resp.text if hasattr(resp, "text") else str(resp)
                results[device.device_name] = {
                    "Device Name": device.device_name,
                    "Device Id": device.id,
                    "Status Code": resp.status_code
                    if hasattr(resp, "status_code")
                    else None,
                    "Response": resp.json() if hasattr(resp, "json") else respText,
                }
            else:
                groups = getAllGroups(name=groupName).results
                if groups:
                    groupId = groups[0].id
                    resp = moveGroup(groupId, device.id)
                    respText = resp.text if hasattr(resp, "text") else str(resp)
                    results[device.device_name] = {
                        "Device Name": device.device_name,
                        "Device Id": device.id,
                        "Status Code": resp.status_code
                        if hasattr(resp, "status_code")
                        else None,
                        "Response": resp.json() if hasattr(resp, "json") else respText,
                    }
                else:
                    results[device.device_name] = {
                        "Device Name": device.device_name,
                        "Device Id": device.id,
                        "Error": "Invalid Group Name given, no matches found, '%s'"
                        % groupName,
                    }
        else:
            results[device.device_name] = {
                "Device Name": device.device_name,
                "Device Id": device.id,
                "Error": "Invalid Group Name given, '%s'" % groupName,
            }

    if not results:
        results["error"] = {"Error": "Failed to find devices to move, check endpoint."}
    return results


@api_tool_decorator()
def installListedLatestApp(frame):
    deviceIdentifers = frame.gridPanel.getDeviceIdentifersFromGrid()
    gridAppList, _ = frame.gridPanel.getAppsFromGrid()
    devices = getDevicesFromGrid(deviceIdentifers=deviceIdentifers)

    splitResults = splitListIntoChunks(devices)
    threads = []

    for chunk in splitResults:
        t = wxThread.GUIThread(
            frame,
            processInstallLatestAppChunk,
            args=(chunk, gridAppList),
            name="processInstallLatestAppChunk",
        )
        threads.append(t)
        t.start()
        limitActiveThreads(threads)

    t = wxThread.GUIThread(
        frame,
        wxThread.waitTillThreadsFinish,
        args=(tuple(threads), GridActions.INSTALL_LATEST_APP.value, -1, 5),
        name="waitTillThreadsFinish",
    )
    t.start()


@api_tool_decorator()
def processInstallLatestAppChunk(devices, appList, appChoice=False):
    status = []
    for device in devices:
        if not appChoice:
            package_name = None
            if device.id in appList.keys():
                package_name = appList[device.id]
            elif device.device_name in appList.keys():
                package_name = appList[device.device_name]
            elif (
                "serialNumber" in device.hardware_info
                and device.hardware_info["serialNumber"] in appList.keys()
            ):
                package_name = appList[device.hardware_info["serialNumber"]]
            elif (
                "customSerialNumber" in device.hardware_info
                and device.hardware_info["customSerialNumber"] in appList.keys()
            ):
                package_name = appList[device.hardware_info["customSerialNumber"]]
            if package_name:
                for package in package_name:
                    resp = installAppOnDevices(package, devices=[device.id])
                    if type(resp) == dict and "Error" in resp.keys():
                        status.append(
                            {
                                "Device Name": device.device_name,
                                "Device Id": device.id,
                                "Error": resp["Error"],
                            }
                        )
                    else:
                        status += resp
            else:
                status.append(
                    {
                        "Device Name": device.device_name,
                        "Device Id": device.id,
                        "Error": "No packages found to install",
                    }
                )
        else:
            version = None
            pkgName = None
            if "version" in appList:
                version = appList["version"]
            if "pkgName" in appList:
                pkgName = appList["pkgName"]
            if pkgName:
                resp = installAppOnDevices(
                    pkgName, version=version, devices=[device.id]
                )
                if type(resp) == dict and "Error" in resp.keys():
                    status.append(
                        {
                            "Device Name": device.device_name,
                            "Device Id": device.id,
                            "Error": resp["Error"],
                        }
                    )
                else:
                    status += resp
            else:
                status.append(
                    {
                        "Device Name": device.device_name,
                        "Device Id": device.id,
                        "Error": "Failed to get package name for %s"
                        % appList["app_name"],
                    }
                )
    return status


@api_tool_decorator()
def uninstallListedApp(frame):
    deviceIdentifers = frame.gridPanel.getDeviceIdentifersFromGrid()
    gridAppList, _ = frame.gridPanel.getAppsFromGrid()
    devices = getDevicesFromGrid(deviceIdentifers=deviceIdentifers)

    splitResults = splitListIntoChunks(devices)
    threads = []

    for chunk in splitResults:
        t = wxThread.GUIThread(
            frame,
            processUninstallAppChunk,
            args=(chunk, gridAppList),
            name="processUninstallAppChunk",
        )
        threads.append(t)
        t.start()
        limitActiveThreads(threads)

    t = wxThread.GUIThread(
        frame,
        wxThread.waitTillThreadsFinish,
        args=(tuple(threads), GridActions.UNINSTALL_LISTED_APP.value, -1, 5),
        name="waitTillThreadsFinish",
    )
    t.start()


@api_tool_decorator()
def processUninstallAppChunk(devices, appList, appChoice=False):
    status = []
    for device in devices:
        if not appChoice:
            package_name = None
            if device.id in appList.keys():
                package_name = appList[device.id]
            elif device.device_name in appList.keys():
                package_name = appList[device.device_name]
            elif (
                "serialNumber" in device.hardware_info
                and device.hardware_info["serialNumber"] in appList.keys()
            ):
                package_name = appList[device.hardware_info["serialNumber"]]
            elif (
                "customSerialNumber" in device.hardware_info
                and device.hardware_info["customSerialNumber"] in appList.keys()
            ):
                package_name = appList[device.hardware_info["customSerialNumber"]]
            if package_name:
                for package in package_name:
                    resp = uninstallAppOnDevice(package, device=[device.id])
                    status += resp
            else:
                status.append(
                    {
                        "Device Name": device.device_name,
                        "Device Id": device.id,
                        "Error": "No packages found to install",
                    }
                )
        else:
            pkgName = None
            if "pkgName" in appList:
                pkgName = appList["pkgName"]
            if pkgName:
                resp = uninstallAppOnDevice(pkgName, device=[device.id])
                status += resp
            else:
                status.append(
                    {
                        "Device Name": device.device_name,
                        "Device Id": device.id,
                        "Error": "Failed to get package name for %s"
                        % appList["app_name"],
                    }
                )
    return status


def installApp(frame):
    deviceIdentifers = frame.gridPanel.getDeviceIdentifersFromGrid()
    devices = getDevicesFromGrid(deviceIdentifers=deviceIdentifers)
    splitResults = splitListIntoChunks(devices)
    threads = []

    for chunk in splitResults:
        t = wxThread.GUIThread(
            frame,
            processInstallLatestAppChunk,
            args=(chunk, frame.sidePanel.selectedAppEntry, True),
            name="processInstallLatestAppChunk",
        )
        threads.append(t)
        t.start()
        limitActiveThreads(threads)

    t = wxThread.GUIThread(
        frame,
        wxThread.waitTillThreadsFinish,
        args=(tuple(threads), GridActions.INSTALL_LATEST_APP.value, -1, 5),
        name="waitTillThreadsFinish",
    )
    t.start()


def uninstallApp(frame):
    deviceIdentifers = frame.gridPanel.getDeviceIdentifersFromGrid()
    devices = getDevicesFromGrid(deviceIdentifers=deviceIdentifers)

    splitResults = splitListIntoChunks(devices)
    threads = []

    for chunk in splitResults:
        t = wxThread.GUIThread(
            frame,
            processUninstallAppChunk,
            args=(chunk, frame.sidePanel.selectedAppEntry, True),
            name="processUninstallAppChunk",
        )
        threads.append(t)
        t.start()
        limitActiveThreads(threads)

    t = wxThread.GUIThread(
        frame,
        wxThread.waitTillThreadsFinish,
        args=(tuple(threads), GridActions.UNINSTALL_LISTED_APP.value, -1, 5),
        name="waitTillThreadsFinish",
    )
    t.start()


def processBulkFactoryReset(devices, numDevices, processed):
    status = []
    for device in devices:
        if device and hasattr(device, "id"):
            resp = apiCalls.factoryResetDevice(device.id)
            status.append(resp)
            processed.append(device)
        value = int(len(processed) / numDevices * 100)
        postEventToFrame(
            eventUtil.myEVT_UPDATE_GAUGE,
            value,
        )
    return status


def bulkFactoryReset(identifers):
    devices = getDevicesFromGrid(deviceIdentifers=identifers)

    splitResults = splitListIntoChunks(devices)
    threads = []
    numDevices = len(devices)
    processed = []

    for chunk in splitResults:
        t = wxThread.GUIThread(
            Globals.frame,
            processBulkFactoryReset,
            args=(chunk, numDevices, processed),
            name="processDeviceGroupMove",
        )
        threads.append(t)
        t.start()
        limitActiveThreads(threads)

    t = wxThread.GUIThread(
        Globals.frame,
        wxThread.waitTillThreadsFinish,
        args=(tuple(threads), GridActions.MOVE_GROUP.value, -1, 5),
        name="waitTillThreadsFinish",
    )
    t.start()


def processSetDeviceDisabled(devices, numDevices, processed):
    status = []
    for device in devices:
        if device and hasattr(device, "id"):
            resp = setDeviceDisabled(device.id)
            status.append(resp)
            processed.append(device)
        value = int(len(processed) / numDevices * 100)
        postEventToFrame(
            eventUtil.myEVT_UPDATE_GAUGE,
            value,
        )
    return status


def setDevicesDisabled():
    devices = getDevicesFromGrid()

    splitResults = splitListIntoChunks(devices)
    threads = []
    numDevices = len(devices)
    processed = []

    for chunk in splitResults:
        t = wxThread.GUIThread(
            Globals.frame,
            processSetDeviceDisabled,
            args=(chunk, numDevices, processed),
            name="processSetDeviceDisabled",
        )
        threads.append(t)
        t.start()
        limitActiveThreads(threads)

    t = wxThread.GUIThread(
        Globals.frame,
        wxThread.waitTillThreadsFinish,
        args=(tuple(threads), GridActions.MOVE_GROUP.value, -1, 5),
        name="waitTillThreadsFinish",
    )
    t.start()
