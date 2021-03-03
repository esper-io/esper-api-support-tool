#!/usr/bin/env python

from logging import exception
import requests
import esperclient
import time
import json
import Common.Globals as Globals
import Utility.wxThread as wxThread
import threading
import wx

from Common.decorator import api_tool_decorator

from Utility.ApiToolLogging import ApiToolLog
from Utility.Resource import joinThreadList, postEventToFrame, ipv6Tomac

from esperclient.rest import ApiException
from esperclient.models.v0_command_args import V0CommandArgs
from esperclient.models.v0_command_schedule_args import V0CommandScheduleArgs


####Esper API Requests####
def logBadResponse(url, resp, json_resp):
    if Globals.PRINT_RESPONSES or resp.status_code > 300:
        print(url)
        prettyReponse = "Response {result}".format(
            result=json.dumps(json_resp, indent=4, sort_keys=True)
        )
        print(prettyReponse)
        ApiToolLog().LogResponse(prettyReponse)


def getHeader():
    return {
        "Authorization": f"Bearer {Globals.configuration.api_key['Authorization']}",
        "Content-Type": "application/json",
    }


def getInfo(request_extension, deviceid):
    """Sends Request For Device Info JSON"""
    headers = getHeader()
    url = (
        Globals.BASE_DEVICE_URL.format(
            configuration_host=Globals.configuration.host,
            enterprise_id=Globals.enterprise_id,
            device_id=deviceid,
        )
        + request_extension
    )
    resp = requests.get(url, headers=headers)
    json_resp = resp.json()
    logBadResponse(url, resp, json_resp)

    return json_resp


def getDeviceDetail(deviceId):
    return getInfo("/?format=json&show_policy=true", deviceId)


def fetchGroupName(groupURL):
    headers = getHeader()
    resp = requests.get(groupURL, headers=headers)
    json_resp = resp.json()
    logBadResponse(groupURL, resp, json_resp)

    if "name" in json_resp:
        return json_resp["name"]
    return None


def patchInfo(request_extension, deviceid, tags):
    """Pushes Data To Device Info JSON"""
    headers = getHeader()
    url = (
        Globals.BASE_DEVICE_URL.format(
            configuration_host=Globals.configuration.host,
            enterprise_id=Globals.enterprise_id,
            device_id=deviceid,
        )
        + request_extension
    )
    resp = requests.patch(url, headers=headers, data=json.dumps({"tags": tags}))
    json_resp = resp.json()
    logBadResponse(url, resp, json_resp)
    return json_resp


def iskioskmode(deviceid):
    """Checks If Device Is In Kiosk Mode"""
    kioskmode = False
    json_resp = getInfo(Globals.BASE_REQUEST_EXTENSION, deviceid)
    if json_resp["current_app_mode"] == 0:
        kioskmode = True
    return kioskmode


def toggleKioskMode(
    frame, deviceid, appToUse, isKiosk, timeout=Globals.COMMAND_TIMEOUT
):
    """Toggles Kiosk Mode On/Off"""
    api_instance = getCommandsApiInstance()
    if isKiosk:
        command_args = esperclient.V0CommandArgs(package_name=appToUse)
    else:
        command_args = {}
    command = esperclient.V0CommandRequest(
        enterprise=Globals.enterprise_id,
        command_type="DEVICE",
        device_type="all",
        devices=[deviceid],
        command="SET_KIOSK_APP",
        command_args=command_args,
    )
    api_response = api_instance.create_command(Globals.enterprise_id, command)
    response = api_instance.get_command_request_status(
        Globals.enterprise_id, api_response.id
    )

    status = response.results[0].state
    ignoreQueued = False if Globals.REACH_QUEUED_ONLY else True
    status = waitForCommandToFinish(frame, api_response.id, ignoreQueue=ignoreQueued)
    return status


def getdevicetags(deviceid):
    """Retrieves Device Tags"""
    tags = ""
    json_resp = getInfo(Globals.BASE_REQUEST_EXTENSION, deviceid)
    if "tags" in json_resp:
        tags = json_resp["tags"]
    return tags


def getdeviceapps(deviceid, createAppList=True, useEnterprise=False):
    """Retrieves List Of Installed Apps"""
    applist = []
    extention = (
        Globals.DEVICE_ENTERPRISE_APP_LIST_REQUEST_EXTENSION
        if useEnterprise
        else Globals.DEVICE_APP_LIST_REQUEST_EXTENSION
    )
    json_resp = getInfo(extention, deviceid)
    if len(json_resp["results"]) and createAppList:
        for app in json_resp["results"]:
            entry = None
            if "application" in app:
                appName = app["application"]["application_name"]
                appPkgName = appName + (" (%s)" % app["application"]["package_name"])
                entry = {
                    "app_name": app["application"]["application_name"],
                    appName: app["application"]["package_name"],
                    appPkgName: app["application"]["package_name"],
                }
                if entry not in Globals.frame.sidePanel.selectedDeviceApps:
                    Globals.frame.sidePanel.selectedDeviceApps.append(entry)
                if entry not in Globals.frame.sidePanel.enterpriseApps:
                    Globals.frame.sidePanel.enterpriseApps.append(entry)
                version = (
                    app["application"]["version"]["version_code"][
                        1 : len(app["application"]["version"]["version_code"])
                    ]
                    if app["application"]["version"]["version_code"].startswith("v")
                    else app["application"]["version"]["version_code"]
                )
                applist.append(
                    app["application"]["application_name"]
                    + (
                        " (%s) v" % app["application"]["package_name"]
                        if Globals.SHOW_PKG_NAME
                        else " v"
                    )
                    + version
                )
            else:
                appName = app["app_name"]
                appPkgName = appName + (" (%s)" % app["package_name"])
                entry = {
                    "app_name": app["app_name"],
                    appName: app["package_name"],
                    appPkgName: app["package_name"],
                    "app_state": app["state"],
                }
                version = (
                    app["version_code"][1 : len(app["version_code"])]
                    if app["version_code"].startswith("v")
                    else app["version_code"]
                )
                applist.append(
                    app["app_name"]
                    + (
                        " (%s) v" % app["package_name"]
                        if Globals.SHOW_PKG_NAME
                        else " v"
                    )
                    + version
                )
            if entry and entry not in Globals.frame.sidePanel.knownApps:
                Globals.frame.sidePanel.knownApps.append(entry)
    return applist, json_resp


def getkioskmodeapp(deviceid):
    """Retrieves The Kiosk Mode Application ID"""
    json_resp = getInfo(Globals.DEVICE_STATUS_REQUEST_EXTENSION, deviceid)
    respData = None
    if json_resp["results"]:
        respData = json_resp["results"][0]["data"]
    appName = ""
    if respData and "kioskAppName" in respData:
        appName = respData["kioskAppName"]
    return appName


def getNetworkInfo(deviceid):
    """Retrieves The Kiosk Mode Application ID"""
    json_resp = getInfo(Globals.DEVICE_STATUS_REQUEST_EXTENSION, deviceid)
    respData = None
    if json_resp["results"]:
        respData = json_resp["results"][0]["data"]
    network_event = ""
    if respData and "networkEvent" in respData:
        network_event = respData["networkEvent"]
    return network_event


def getLocationInfo(deviceid):
    """Retrieves The Kiosk Mode Application ID"""
    json_resp = getInfo(Globals.DEVICE_STATUS_REQUEST_EXTENSION, deviceid)
    respData = None
    if json_resp["results"]:
        respData = json_resp["results"][0]["data"]
    location_event = ""
    if respData and "locationEvent" in respData:
        location_event = respData["locationEvent"]
    return location_event, respData


def setdevicetags(deviceid, tags):
    """Pushes New Tag To Device"""
    json_resp = patchInfo(Globals.BASE_REQUEST_EXTENSION, deviceid, tags)
    if json_resp and "tags" in json_resp:
        tags = json_resp["tags"]
    return tags


def setdevicename(
    frame, deviceid, devicename, ignoreQueue, timeout=Globals.COMMAND_TIMEOUT
):
    """Pushes New Name To Name"""
    api_instance = getCommandsApiInstance()
    args = esperclient.V0CommandArgs(device_alias_name=devicename)
    command = esperclient.V0CommandRequest(
        command_type="DEVICE",
        devices=[deviceid],
        command="UPDATE_DEVICE_CONFIG",
        command_args=args,
        device_type="all",
    )
    api_response = api_instance.create_command(Globals.enterprise_id, command)
    response = api_instance.get_command_request_status(
        Globals.enterprise_id, api_response.id
    )
    status = response.results[0].state
    status = waitForCommandToFinish(frame, api_response.id, ignoreQueue, timeout)
    return status


def getAllGroups():
    """ Make a API call to get all Groups belonging to the Enterprise """
    try:
        api_instance = esperclient.DeviceGroupApi(
            esperclient.ApiClient(Globals.configuration)
        )
        api_response = api_instance.get_all_groups(
            Globals.enterprise_id, limit=Globals.limit, offset=Globals.offset
        )
        postEventToFrame(wxThread.myEVT_LOG, "---> Group API Request Finished")
        return api_response
    except ApiException as e:
        raise Exception(
            "Exception when calling DeviceGroupApi->get_all_groups: %s\n" % e
        )


def uploadApplicationForHost(config, enterprise_id, file):
    try:
        api_instance = esperclient.ApplicationApi(esperclient.ApiClient(config))
        api_response = api_instance.upload(enterprise_id, file)
        return api_response
    except ApiException as e:
        raise Exception("Exception when calling ApplicationApi->upload: %s\n" % e)


def getDeviceGroupsForHost(config, enterprise_id):
    try:
        api_instance = esperclient.DeviceGroupApi(esperclient.ApiClient(config))
        api_response = api_instance.get_all_groups(
            enterprise_id, limit=Globals.limit, offset=Globals.offset
        )
        return api_response
    except Exception as e:
        raise e


def createDeviceGroupForHost(config, enterprise_id, group):
    try:
        api_instance = esperclient.DeviceGroupApi(esperclient.ApiClient(config))
        api_response = api_instance.create_group(enterprise_id, data={"name": group})
        return api_response
    except Exception as e:
        raise e


def getDeviceGroupForHost(config, enterprise_id, group_id):
    try:
        api_instance = esperclient.DeviceGroupApi(esperclient.ApiClient(config))
        api_response = api_instance.get_group_by_id(
            group_id=group_id, enterprise_id=enterprise_id
        )
        return api_response
    except Exception as e:
        raise e


def getAllDevices(groupToUse):
    """ Make a API call to get all Devices belonging to the Enterprise """
    if not groupToUse:
        return None
    try:
        api_instance = esperclient.DeviceApi(
            esperclient.ApiClient(Globals.configuration)
        )
        api_response = None
        if type(groupToUse) == list:
            for group in groupToUse:
                response = api_instance.get_all_devices(
                    Globals.enterprise_id,
                    group=group,
                    limit=Globals.limit,
                    offset=Globals.offset,
                )
                if not api_response:
                    api_response = response
                else:
                    api_response.results = api_response.results + response.results
        else:
            api_response = api_instance.get_all_devices(
                Globals.enterprise_id,
                group=groupToUse,
                limit=Globals.limit,
                offset=Globals.offset,
            )
        postEventToFrame(wxThread.myEVT_LOG, "---> Device API Request Finished")
        return api_response
    except ApiException as e:
        raise Exception("Exception when calling DeviceApi->get_all_devices: %s\n" % e)


def getAllApplications():
    """ Make a API call to get all Applications belonging to the Enterprise """
    try:
        api_instance = esperclient.ApplicationApi(
            esperclient.ApiClient(Globals.configuration)
        )
        api_response = api_instance.get_all_applications(
            Globals.enterprise_id,
            limit=Globals.limit,
            offset=Globals.offset,
            is_hidden=False,
        )
        postEventToFrame(wxThread.myEVT_LOG, "---> App API Request Finished")
        return api_response
    except ApiException as e:
        raise Exception(
            "Exception when calling ApplicationApi->get_all_applications: %s\n" % e
        )


def getAllApplicationsForHost(config, enterprise_id):
    """ Make a API call to get all Applications belonging to the Enterprise """
    try:
        api_instance = esperclient.ApplicationApi(esperclient.ApiClient(config))
        api_response = api_instance.get_all_applications(
            enterprise_id,
            limit=Globals.limit,
            offset=0,
            is_hidden=False,
        )
        return api_response
    except Exception as e:
        raise Exception(
            "Exception when calling ApplicationApi->get_all_applications: %s\n" % e
        )


def getDeviceById(deviceToUse):
    """ Make a API call to get a Device belonging to the Enterprise by its Id """
    try:
        api_instance = esperclient.DeviceApi(
            esperclient.ApiClient(Globals.configuration)
        )
        api_response_list = []
        api_response = None
        if type(deviceToUse) == list:
            for device in deviceToUse:
                api_response = api_instance.get_device_by_id(
                    Globals.enterprise_id, device_id=device
                )
                api_response_list.append(api_response)
        else:
            api_response = api_instance.get_device_by_id(
                Globals.enterprise_id, device_id=deviceToUse
            )
        if api_response and api_response_list:
            api_response.results = api_response_list
        elif api_response:
            api_response.results = [api_response]
        postEventToFrame(wxThread.myEVT_LOG, "---> Device API Request Finished")
        return api_response
    except ApiException as e:
        print("Exception when calling DeviceApi->get_device_by_id: %s\n" % e)
        ApiToolLog().LogError(e)


def getTokenInfo():
    api_instance = esperclient.TokenApi(esperclient.ApiClient(Globals.configuration))
    try:
        api_response = api_instance.get_token_info()
        return api_response
    except ApiException as e:
        print("Exception when calling TokenApi->get_token_info: %s\n" % e)
        ApiToolLog().LogError(e)


####End Esper API Requests####


def iterateThroughGridRows(frame, action):
    """Iterates Through Each Device in the Displayed Grid And Performs A Specified Action"""
    if action == Globals.MODIFY_ALIAS_AND_TAGS:
        modifyDevice(frame)


def iterateThroughDeviceList(
    frame, action, api_response, entId, isDevice=False, isUpdate=False
):
    """Iterates Through Each Device And Performs A Specified Action"""
    if len(api_response.results):
        number_of_devices = 0
        if not isDevice and not isUpdate:
            n = int(len(api_response.results) / Globals.MAX_THREAD_COUNT)
            if n == 0:
                n = len(api_response.results)
            splitResults = [
                api_response.results[i * n : (i + 1) * n]
                for i in range((len(api_response.results) + n - 1) // n)
            ]

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
            (Globals.SHOW_ALL_AND_GENERATE_REPORT, Globals.enterprise_id, deviceList),
        )


def processCollectionDevices(collectionList):
    n = int(len(collectionList["results"]) / Globals.MAX_THREAD_COUNT)
    if n == 0:
        n = len(collectionList["results"])
    splitResults = [
        collectionList["results"][i * n : (i + 1) * n]
        for i in range((len(collectionList["results"]) + n - 1) // n)
    ]
    if collectionList["results"]:
        # for device in collectionList["results"]:
        #     try:
        #         deviceInfo = {}
        #         deviceInfo = populateDeviceInfoDictionary(device, deviceInfo)

        #         deviceList[num] = [device, deviceInfo]
        #         num += 1
        #     except Exception as e:
        #         print(e)
        #         ApiToolLog().LogError(e)
        threads = []
        number_of_devices = 0
        for chunk in splitResults:
            t = wxThread.GUIThread(
                Globals.frame,
                fillInDeviceInfoDict,
                args=(chunk, number_of_devices),
            )
            threads.append(t)
            t.start()
            number_of_devices += len(chunk)

        t = wxThread.GUIThread(
            Globals.frame,
            waitTillThreadsFinish,
            args=(
                tuple(threads),
                Globals.SHOW_ALL_AND_GENERATE_REPORT,
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
    # return (Globals.SHOW_ALL_AND_GENERATE_REPORT, Globals.enterprise_id, deviceList)


def fillInDeviceInfoDict(chunk, number_of_devices):
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
    kioskMode = iskioskmode(deviceId)
    deviceInfo.update({"EsperName": deviceName})

    detailInfo = getDeviceDetail(deviceId)
    unpackageDict(deviceInfo, detailInfo)

    if deviceGroups:
        groupNames = []
        if type(deviceGroups) == list:
            for groupURL in deviceGroups:
                groupName = fetchGroupName(groupURL)
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

    apps, _ = getdeviceapps(deviceId, True, Globals.USE_ENTERPRISE_APP)
    deviceInfo.update({"Apps": str(apps)})

    if kioskMode == 1 and deviceStatus == 1:
        deviceInfo.update({"KioskApp": str(getkioskmodeapp(deviceId))})
    else:
        deviceInfo.update({"KioskApp": ""})

    location_info, resp_json = getLocationInfo(deviceId)
    network_info = getNetworkInfo(deviceId)
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


def logActionExecution(frame, action, selection=None):
    actionName = ""
    if frame.sidePanel.actionChoice.GetValue() in Globals.GRID_ACTIONS:
        actionName = '"%s"' % str(Globals.GRID_ACTIONS[action])
    elif frame.sidePanel.actionChoice.GetValue() in Globals.GENERAL_ACTIONS:
        actionName = '"%s"' % str(Globals.GENERAL_ACTIONS[action])
    if selection:
        frame.Logging("---> Starting Execution " + actionName + " on " + str(selection))
    else:
        frame.Logging("---> Starting Execution " + actionName)


####Perform Actions. Set Kiosk Mode, Multi App Mode, Tags, or Alias####
def TakeAction(frame, group, action, label, isDevice=False, isUpdate=False):
    """Calls API To Perform Action And Logs Result To UI"""
    if not Globals.enterprise_id:
        frame.loadConfigPrompt()

    if frame:
        frame.menubar.disableConfigMenu()

    # api_instance = esperclient.DeviceApi(esperclient.ApiClient(Globals.configuration))
    logActionExecution(frame, action, group)
    if (action == Globals.SHOW_ALL_AND_GENERATE_REPORT) and not isUpdate:
        frame.gridPanel.emptyDeviceGrid()
        frame.gridPanel.emptyNetworkGrid()
        frame.CSVUploaded = False

    deviceList = None
    if isDevice:
        deviceToUse = group
        frame.Logging("---> Making API Request")
        # device = getDeviceById(deviceToUse)
        # if device:
        # deviceList = iterateThroughDeviceList(
        #     frame, action, device, isDevice=True, isUpdate=isUpdate
        # )
        wxThread.doAPICallInThread(
            frame,
            getDeviceById,
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
                api_response = getAllDevices(groupToUse)
                deviceList = iterateThroughDeviceList(
                    frame, action, api_response, Globals.enterprise_id, isUpdate=True
                )
            else:
                wxThread.doAPICallInThread(
                    frame,
                    getAllDevices,
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
                if action == Globals.SHOW_ALL_AND_GENERATE_REPORT:
                    frame.gridPanel.addDeviceToDeviceGrid(deviceInfo)
                    frame.gridPanel.addDeviceToNetworkGrid(device, deviceInfo)
                elif action == Globals.SET_KIOSK:
                    setKiosk(frame, device, deviceInfo)
                elif action == Globals.SET_MULTI:
                    setMulti(frame, device, deviceInfo)
                elif action == Globals.CLEAR_APP_DATA:
                    clearAppData(frame, device)
                # elif action == Globals.POWER_OFF:
                #    powerOffDevice(frame, device, deviceInfo)
            postEventToFrame(wxThread.myEVT_COMPLETE, None)


def iterateThroughAllGroups(frame, action, api_instance, group=None):
    # for index, value in enumerate(frame.groups):
    # groupToUse = frame.groupChoice.GetClientData(index)  # Get Device Group ID
    groupToUse = None
    if group:
        groupToUse = group[0]
    # if value != "All devices":
    #     continue
    try:
        frame.Logging("---> Making API Request")
        wxThread.doAPICallInThread(
            frame,
            getAllDevices,
            args=(groupToUse),
            eventType=wxThread.myEVT_RESPONSE,
            callback=iterateThroughDeviceList,
            callbackArgs=(frame, action, Globals.enterprise_id),
            optCallbackArgs=(Globals.enterprise_id),
            waitForJoin=False,
            name="iterateThroughDeviceListForAllDeviceGroup",
        )
    except ApiException as e:
        print("Exception when calling DeviceApi->get_all_devices: %s\n" % e)
        ApiToolLog().LogError(e)


def setKiosk(frame, device, deviceInfo):
    """Toggles Kiosk Mode With Specified App"""
    logString = ""
    failed = False
    warning = False
    appToUse = frame.sidePanel.appChoice.GetClientData(
        frame.sidePanel.appChoice.GetSelection()
    )
    logString = (
        str("--->" + str(device.device_name) + " " + str(device.alias_name))
        + " -> Kiosk ->"
        + str(appToUse)
    )
    stateStatus = setAppState(device.id, appToUse, "SHOW")
    timeout = Globals.COMMAND_TIMEOUT if "Command Success" in str(stateStatus) else 0
    status = toggleKioskMode(frame, device.id, appToUse, True, timeout)
    if "Success" in str(status):
        logString = logString + " <success>"
    elif "Queued" in str(status):
        logString = (
            logString + " <warning, check back on the device (%s)>" % device.device_name
        )
        warning = True
    else:
        logString = logString + " <failed>"
        failed = True
    if deviceInfo["Status"] != "Online":
        logString = logString + " (Device offline)"
    postEventToFrame(wxThread.myEVT_LOG, logString)
    if failed:
        postEventToFrame(wxThread.myEVT_ON_FAILED, deviceInfo)
    if warning:
        postEventToFrame(wxThread.myEVT_ON_FAILED, (device, "Queued"))


def setMulti(frame, device, deviceInfo):
    """Toggles Multi App Mode"""
    logString = (
        str("--->" + str(device.device_name) + " " + str(device.alias_name))
        + " -> Multi ->"
    )
    failed = False
    warning = False
    if deviceInfo["Mode"] == "Kiosk":
        status = toggleKioskMode(frame, device.id, {}, False)
        if "Success" in str(status):
            logString = logString + " <success>"
        elif "Queued" in str(status):
            logString = (
                logString
                + " <warning, check back on the device (%s)>" % device.device_name
            )
            warning = True
        else:
            logString = logString + " <failed>"
            failed = True
    else:
        logString = logString + " (Already Multi mode, skipping)"
    if deviceInfo["Status"] != "Online":
        logString = logString + " (Device offline)"
    postEventToFrame(wxThread.myEVT_LOG, logString)
    if failed:
        postEventToFrame(wxThread.myEVT_ON_FAILED, deviceInfo)
    if warning:
        postEventToFrame(wxThread.myEVT_ON_FAILED, (device, "Queued"))


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
        n = int(len(api_response.results) / Globals.MAX_THREAD_COUNT)
        if n == 0:
            n = len(api_response.results)
        splitResults = [
            api_response.results[i * n : (i + 1) * n]
            for i in range((len(api_response.results) + n - 1) // n)
        ]

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


def processDeviceModificationForList(
    frame, chunk, tagsFromGrid, aliasDic, maxGaugeAction
):
    changeSucceeded = 0
    succeeded = 0
    numNewName = 0
    for device in chunk:
        # changeSucceeded += changeTagsForDevice(device, tagsFromGrid, frame, maxGaugeAction)
        # numNewName, succeeded += changeAliasForDevice(device, aliasDic, frame, maxGaugeAction)
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
                status = setdevicename(frame, device.id, newName, ignoreQueued)
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
        tags = setdevicetags(device.id, tagsFromCell)
        if tags == tagsFromGrid[key]:
            changeSucceeded += 1
        postEventToFrame(wxThread.myEVT_UPDATE_TAG_CELL, (device.device_name, tags))
        postEventToFrame(
            wxThread.myEVT_UPDATE_GAUGE,
            int(frame.gauge.GetValue() + 1 / maxGaugeAction * 100),
        )
    return changeSucceeded


####End Perform Actions####


def getCommandsApiInstance():
    """ Returns an instace of the Commands API """
    return esperclient.CommandsV2Api(esperclient.ApiClient(Globals.configuration))


@api_tool_decorator
def executeCommandOnGroup(
    frame, command_args, schedule=None, command_type="UPDATE_DEVICE_CONFIG"
):
    """ Execute a Command on a Group of Devices """
    # groupToUse = frame.groupChoice.GetClientData(
    #     frame.groupChoice.GetSelection()
    # )  # Get Device Group ID
    statusList = []
    for groupToUse in frame.sidePanel.selectedGroupsList:
        request = esperclient.V0CommandRequest(
            enterprise=Globals.enterprise_id,
            command_type="GROUP",
            device_type="all",
            groups=[groupToUse],
            command=command_type,
            command_args=command_args,
            schedule="IMMEDIATE" if command_type != "UPDATE_LATEST_DPC" else "WINDOW",
            schedule_args=schedule,
        )
        api_instance = getCommandsApiInstance()
        api_response = api_instance.create_command(Globals.enterprise_id, request)
        ignoreQueued = False if Globals.REACH_QUEUED_ONLY else True
        last_status = waitForCommandToFinish(
            frame, api_response.id, ignoreQueue=ignoreQueued
        )
        if hasattr(last_status, "state"):
            statusList.append({"group": groupToUse, "status": last_status.state})
        else:
            statusList.append({"group": groupToUse, "status": last_status})
    return statusList


@api_tool_decorator
def executeCommandOnDevice(
    frame, command_args, schedule=None, command_type="UPDATE_DEVICE_CONFIG"
):
    """ Execute a Command on a Device """
    # deviceToUse = frame.deviceChoice.GetClientData(
    #     frame.deviceChoice.GetSelection()
    # )  # Get Device Group ID
    statusList = []
    for deviceToUse in frame.sidePanel.selectedDevicesList:
        request = esperclient.V0CommandRequest(
            enterprise=Globals.enterprise_id,
            command_type="DEVICE",
            device_type="all",
            devices=[deviceToUse],
            command=command_type,
            command_args=command_args,
            schedule="IMMEDIATE" if command_type != "UPDATE_LATEST_DPC" else "WINDOW",
            schedule_args=schedule,
        )
        api_instance = getCommandsApiInstance()
        api_response = api_instance.create_command(Globals.enterprise_id, request)
        ignoreQueued = False if Globals.REACH_QUEUED_ONLY else True
        last_status = waitForCommandToFinish(
            frame, api_response.id, ignoreQueue=ignoreQueued
        )
        if hasattr(last_status, "state"):
            statusList.append({"group": deviceToUse, "status": last_status.state})
        else:
            statusList.append({"group": deviceToUse, "status": last_status})
    return statusList


@api_tool_decorator
def waitForCommandToFinish(
    frame, request_id, ignoreQueue=False, timeout=Globals.COMMAND_TIMEOUT
):
    """ Wait until a Command is done or it times out """
    api_instance = getCommandsApiInstance()
    response = api_instance.get_command_request_status(
        Globals.enterprise_id, request_id
    )
    if response.results:
        status = response.results[0]
        postEventToFrame(
            wxThread.myEVT_LOG, "---> Command state: %s" % str(status.state)
        )

        stateList = [
            "Command Success",
            "Command Failure",
            "Command TimeOut",
            "Command Cancelled",
            "Command Queued",
            "Command Scheduled",
        ]
        if ignoreQueue:
            stateList.remove("Command Queued")

        start = time.perf_counter()
        while status.state not in stateList:
            end = time.perf_counter()
            duration = end - start
            if duration >= timeout:
                postEventToFrame(
                    wxThread.myEVT_LOG,
                    "---> Skipping wait for Command, last logged Command state: %s (Device may be offline)"
                    % str(status.state),
                )
                break
            response = api_instance.get_command_request_status(
                Globals.enterprise_id, request_id
            )
            if response and response.results:
                status = response.results[0]
            postEventToFrame(
                wxThread.myEVT_LOG, "---> Command state: %s" % str(status.state)
            )
            time.sleep(3)
        return status
    else:
        return response.results


def ApplyDeviceConfig(frame, config, commandType):
    """ Attempt to apply a Command given user specifications """
    otherConfig = {}
    cmdConfig = config[0]
    scheduleConfig = config[1]
    for key in cmdConfig.keys():
        if key not in Globals.COMMAND_ARGS:
            otherConfig[key] = cmdConfig[key]

    command_args = V0CommandArgs(
        app_state=cmdConfig["app_state"] if "app_state" in cmdConfig else None,
        app_version=cmdConfig["app_version"] if "app_version" in cmdConfig else None,
        device_alias_name=cmdConfig["device_alias_name"]
        if "device_alias_name" in cmdConfig
        else None,
        custom_settings_config=otherConfig,
        package_name=cmdConfig["package_name"] if "package_name" in cmdConfig else None,
        policy_url=cmdConfig["policy_url"] if "policy_url" in cmdConfig else None,
        state=cmdConfig["state"] if "state" in cmdConfig else None,
        message=cmdConfig["message"] if "message" in cmdConfig else None,
        wifi_access_points=cmdConfig["wifi_access_points"]
        if "wifi_access_points" in cmdConfig
        else None,
    )
    result, isGroup = frame.confirmCommand(command_args, commandType)
    schedule = V0CommandScheduleArgs(
        name=scheduleConfig["name"] if "name" in scheduleConfig else None,
        start_datetime=scheduleConfig["start_datetime"]
        if "start_datetime" in scheduleConfig
        else None,
        end_datetime=scheduleConfig["end_datetime"]
        if "end_datetime" in scheduleConfig
        else None,
        time_type=scheduleConfig["time_type"]
        if "time_type" in scheduleConfig
        else None,
        window_start_time=scheduleConfig["window_start_time"]
        if "window_start_time" in scheduleConfig
        else None,
        window_end_time=scheduleConfig["window_end_time"]
        if "window_end_time" in scheduleConfig
        else None,
        days=scheduleConfig["days"] if "days" in scheduleConfig else None,
    )
    t = None
    if result and isGroup:
        t = wxThread.GUIThread(
            frame,
            executeCommandOnGroup,
            args=(frame, command_args, schedule, commandType),
            eventType=wxThread.myEVT_COMMAND,
        )
    elif result and not isGroup:
        t = wxThread.GUIThread(
            frame,
            executeCommandOnDevice,
            args=(frame, command_args, schedule, commandType),
            eventType=wxThread.myEVT_COMMAND,
        )
    if t:
        frame.menubar.disableConfigMenu()
        frame.gauge.Pulse()
        t.start()


@api_tool_decorator
def validateConfiguration(host, entId, key, prefix="Bearer"):
    configuration = esperclient.Configuration()
    configuration.host = host
    configuration.api_key["Authorization"] = key
    configuration.api_key_prefix["Authorization"] = prefix

    api_instance = esperclient.EnterpriseApi(esperclient.ApiClient(configuration))
    enterprise_id = entId

    try:
        # Fetch all devices in an enterprise
        api_response = api_instance.get_enterprise(enterprise_id)
        if hasattr(api_response, "id"):
            return True
    except ApiException as e:
        print("Exception when calling EnterpriseApi->get_enterprise: %s\n" % e)
        ApiToolLog().LogError(e)
    return False


def powerOffDevice(frame, device, device_info):
    # out, err = runSubprocessPOpen()
    pass


def postEsperCommand(command_data, useV0=True):
    json_resp = None
    resp = None
    try:
        headers = getHeader()
        url = ""
        if useV0:
            url = "https://%s-api.esper.cloud/api/v0/enterprise/%s/command/" % (
                Globals.configuration.host.split("-api")[0].replace("https://", ""),
                Globals.enterprise_id,
            )
        else:
            url = "https://%s-api.esper.cloud/api/enterprise/%s/command/" % (
                Globals.configuration.host.split("-api")[0].replace("https://", ""),
                Globals.enterprise_id,
            )
        resp = requests.post(url, headers=headers, json=command_data)
        json_resp = resp.json()
        logBadResponse(url, resp, json_resp)
    except Exception as e:
        ApiToolLog().LogError(e)
    return resp, json_resp


def clearAppData(frame, device):
    json_resp = None
    try:
        appToUse = frame.sidePanel.appChoice.GetClientData(
            frame.sidePanel.appChoice.GetSelection()
        )
        _, apps = getdeviceapps(device.id, createAppList=False, useEnterprise=True)
        cmdArgs = {}
        for app in apps["results"]:
            if app["package_name"] == appToUse:
                cmdArgs["package_name"] = app["package_name"]
                cmdArgs["application_name"] = app["app_name"]
                cmdArgs["version_code"] = app["version_code"]
                cmdArgs["version_name"] = app["version_name"]
                if app["app_type"] == "GOOGLE":
                    cmdArgs["is_g_play"] = True
                else:
                    cmdArgs["is_g_play"] = False
                break

        if cmdArgs:
            reqData = {
                "command_type": "DEVICE",
                "command_args": cmdArgs,
                "devices": [device.id],
                "groups": [],
                "device_type": "all",
                "command": "CLEAR_APP_DATA",
            }
            resp, json_resp = postEsperCommand(reqData)
            logBadResponse(resp.request.url, resp, json_resp)
            if resp.status_code > 300:
                postEventToFrame(wxThread.myEVT_ON_FAILED, device)
            if resp.status_code < 300:
                frame.Logging(
                    "---> Clear %s App Data Command has been sent to %s"
                    % (cmdArgs["application_name"], device.device_name)
                )
        else:
            frame.Logging(
                "ERROR: Failed to send Clear %s App Data Command to %s"
                % (frame.sidePanel.appChoice.GetValue(), device.device_name)
            )
    except Exception as e:
        ApiToolLog().LogError(e)
        frame.Logging(
            "ERROR: Failed to send Clear App Data Command to %s" % (device.device_name)
        )
        postEventToFrame(wxThread.myEVT_ON_FAILED, device)
    return json_resp


def getDeviceApplicationById(device_id, application_id):
    try:
        headers = getHeader()
        url = "https://%s-api.esper.cloud/api/enterprise/%s/device/%s/app/%s" % (
            Globals.configuration.host.split("-api")[0].replace("https://", ""),
            Globals.enterprise_id,
            device_id,
            application_id,
        )
        resp = requests.get(url, headers=headers)
        json_resp = resp.json()
        logBadResponse(url, resp, json_resp)
    except Exception as e:
        ApiToolLog().LogError(e)
    return resp, json_resp


def setAppState(device_id, pkg_name, state="HIDE"):
    pkgName = pkg_name
    appVer = None
    _, app = getdeviceapps(device_id, createAppList=False, useEnterprise=True)
    app = list(
        filter(
            lambda x: x["package_name"] == pkg_name,
            app["results"],
        )
    )
    if app:
        app = app[0]
    if "application" in app:
        appVer = app["application"]["version"]["version_code"]
    else:
        appVer = app["version_code"]
    if pkgName and appVer:
        args = V0CommandArgs(
            app_state=state,
            app_version=appVer,
            package_name=pkgName,
        )
        args.version_code = appVer
        request = esperclient.V0CommandRequest(
            enterprise=Globals.enterprise_id,
            command_type="DEVICE",
            device_type="all",
            devices=[device_id],
            command="SET_APP_STATE",
            command_args=args,
        )
        api_instance = getCommandsApiInstance()
        api_response = api_instance.create_command(Globals.enterprise_id, request)
        ignoreQueued = False if Globals.REACH_QUEUED_ONLY else True
        return waitForCommandToFinish(
            Globals.frame, api_response.id, ignoreQueue=ignoreQueued
        )
