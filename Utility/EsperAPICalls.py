import requests
import esperclient
import time
import json
import os.path
import Common.Globals as Globals
import string
import platform
import ctypes
import Utility.wxThread as wxThread
import wx

from Utility.deviceInfo import (
    getSecurityPatch,
    getWifiStatus,
    getCellularStatus,
    getDeviceName,
)

from Common.decorator import api_tool_decorator

from esperclient import ApiClient
from esperclient.rest import ApiException
from esperclient.models.v0_command_args import V0CommandArgs

####Esper API Requests####
def getInfo(request_extension, deviceid):
    """Sends Request For Device Info JSON"""
    headers = {
        "Authorization": f"Bearer {Globals.configuration.api_key['Authorization']}",
        "Content-Type": "application/json",
    }
    url = (
        Globals.BASE_REQUEST_URL.format(
            configuration_host=Globals.configuration.host,
            enterprise_id=Globals.enterprise_id,
            device_id=deviceid,
        )
        + request_extension
    )
    resp = requests.get(url, headers=headers)
    json_resp = resp.json()
    if Globals.PRINT_RESPONSES or resp.status_code > 300:
        print(
            "Response {result}".format(
                result=json.dumps(json_resp, indent=4, sort_keys=True)
            )
        )
    return json_resp


def patchInfo(request_extension, deviceid, tags):
    """Pushes Data To Device Info JSON"""
    headers = {
        "Authorization": f"Bearer {Globals.configuration.api_key['Authorization']}",
        "Content-Type": "application/json",
    }
    url = (
        Globals.BASE_REQUEST_URL.format(
            configuration_host=Globals.configuration.host,
            enterprise_id=Globals.enterprise_id,
            device_id=deviceid,
        )
        + request_extension
    )
    resp = requests.patch(url, headers=headers, data=json.dumps({"tags": tags}))
    json_resp = resp.json()
    if Globals.PRINT_RESPONSES or resp.status_code > 300:
        print(
            "Response {result}".format(
                result=json.dumps(json_resp, indent=4, sort_keys=True)
            )
        )
    return json_resp


def iskioskmode(deviceid):
    """Checks If Device Is In Kiosk Mode"""
    kioskmode = False
    json_resp = getInfo(Globals.BASE_REQUEST_EXTENSION, deviceid)
    if json_resp["current_app_mode"] == 0:
        kioskmode = True
    return kioskmode


def toggleKioskMode(frame, deviceid, appToUse, isKiosk):
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
    status = waitForCommandToFinish(frame, api_response.id)
    return status


def getdevicetags(deviceid):
    """Retrieves Device Tags"""
    tags = ""
    json_resp = getInfo(Globals.BASE_REQUEST_EXTENSION, deviceid)
    if "tags" in json_resp:
        tags = json_resp["tags"]
    return tags


def getdeviceapps(deviceid):
    """Retrieves List Of Installed Apps"""
    applist = []
    json_resp = getInfo(Globals.DEVICE_APP_LIST_REQUEST_EXTENSION, deviceid)
    if len(json_resp["results"]):
        for app in json_resp["results"]:
            applist.append(
                app["application"]["application_name"]
                + " v"
                + app["application"]["version"]["version_code"]
            )
    return applist


def getkioskmodeapp(deviceid):
    """Retrieves The Kiosk Mode Application ID"""
    json_resp = getInfo(Globals.DEVICE_STATUS_REQUEST_EXTENSION, deviceid)
    respData = json_resp["results"][0]["data"]
    appName = ""
    if "kioskAppName" in respData:
        appName = respData["kioskAppName"]
    return appName


def getNetworkInfo(deviceid):
    """Retrieves The Kiosk Mode Application ID"""
    json_resp = getInfo(Globals.DEVICE_STATUS_REQUEST_EXTENSION, deviceid)
    respData = json_resp["results"][0]["data"]
    network_event = ""
    if "networkEvent" in respData:
        network_event = respData["networkEvent"]
    return network_event


def getLocationInfo(deviceid):
    """Retrieves The Kiosk Mode Application ID"""
    json_resp = getInfo(Globals.DEVICE_STATUS_REQUEST_EXTENSION, deviceid)
    respData = json_resp["results"][0]["data"]
    location_event = ""
    if "locationEvent" in respData:
        location_event = respData["locationEvent"]
    return location_event, respData


def setdevicetags(deviceid, tags):
    """Pushes New Tag To Device"""
    json_resp = patchInfo(Globals.BASE_REQUEST_EXTENSION, deviceid, tags)
    if "tags" in json_resp:
        tags = json_resp["tags"]
    return tags


def setdevicename(frame, deviceid, devicename):
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
    status = waitForCommandToFinish(frame, api_response.id)
    return status


def getAllGroups(*args, **kwds):
    try:
        api_instance = esperclient.DeviceGroupApi(
            esperclient.ApiClient(Globals.configuration)
        )
        api_response = api_instance.get_all_groups(
            Globals.enterprise_id, limit=Globals.limit, offset=Globals.offset
        )
        evt = wxThread.CustomEvent(wxThread.myEVT_LOG, -1, "---> Group API Request Finished")
        wx.PostEvent(Globals.frame, evt)
        return api_response
    except ApiException as e:
        raise Exception(
            "Exception when calling DeviceGroupApi->get_all_groups: %s\n" % e
        )


def getAllDevices(groupToUse, *args, **kwds):
    try:
        api_instance = esperclient.DeviceApi(
            esperclient.ApiClient(Globals.configuration)
        )
        api_response = api_instance.get_all_devices(
            Globals.enterprise_id,
            group=groupToUse,
            limit=Globals.limit,
            offset=Globals.offset,
        )
        evt = wxThread.CustomEvent(wxThread.myEVT_LOG, -1, "---> Device API Request Finished")
        wx.PostEvent(Globals.frame, evt)
        return api_response
    except ApiException as e:
        raise Exception("Exception when calling DeviceApi->get_all_devices: %s\n" % e)


def getAllApplications(*args, **kwds):
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
        evt = wxThread.CustomEvent(wxThread.myEVT_LOG, -1, "---> App API Request Finished")
        wx.PostEvent(Globals.frame, evt)
        return api_response
    except ApiException as e:
        raise Exception(
            "Exception when calling ApplicationApi->get_all_applications: %s\n" % e
        )


def getDeviceById(deviceToUse, *args, **kwds):
    try:
        api_instance = esperclient.DeviceApi(
            esperclient.ApiClient(Globals.configuration)
        )
        api_response = api_instance.get_device_by_id(
            Globals.enterprise_id, device_id=deviceToUse
        )
        if api_response:
            api_response.results = [api_response]
        evt = wxThread.CustomEvent(wxThread.myEVT_LOG, -1, "---> Device API Request Finished")
        wx.PostEvent(Globals.frame, evt)
        return api_response
    except ApiException as e:
        print("Exception when calling DeviceApi->get_device_by_id: %s\n" % e)


####End Esper API Requests####


def iterateThroughGridRows(frame, action):
    if action == Globals.SET_ALIAS:
        modifyAlias(frame)
    elif action == Globals.MODIFY_TAGS:
        modifyTags(frame)


def iterateThroughDeviceList(frame, action, api_response):
    """Iterates Through Each Device And Performs A Specified Action"""
    if len(api_response.results):
        number_of_devices = 0
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
                eventType=wxThread.myEVT_UPDATE,
            )
            threads.append(t)
            t.start()
            number_of_devices += len(chunk)

        t = wxThread.GUIThread(
            frame,
            waitTillThreadsFinish,
            args=(tuple(threads), action),
            eventType=wxThread.myEVT_COMPLETE,
        )
        t.start()
    else:
        frame.Logging("---> No devices found for group")


@api_tool_decorator
def waitTillThreadsFinish(threads, action):
    for t in threads:
        t.join()
    evt = wxThread.CustomEvent(wxThread.myEVT_UPDATE_DONE, -1, action)
    wx.PostEvent(Globals.frame, evt)


def processDevices(chunk, number_of_devices, action):
    deviceList = {}
    for device in chunk:
        try:
            number_of_devices = number_of_devices + 1
            deviceInfo = {}
            deviceInfo.update({"num": number_of_devices})
            deviceInfo = populateDeviceInfoDictionary(device, deviceInfo)

            deviceList[number_of_devices] = [device, deviceInfo]
            if deviceInfo not in Globals.GRID_DEVICE_INFO_LIST:
                Globals.GRID_DEVICE_INFO_LIST.append(deviceInfo)
        except Exception as e:
            print(e)
    return (action, deviceList)


def unpackageDict(deviceInfo, deviceDict):
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
    kioskMode = iskioskmode(device.id)
    deviceInfo.update({"EsperName": device.device_name})
    deviceDict = device.__dict__
    unpackageDict(deviceInfo, deviceDict)

    if bool(device.alias_name):
        deviceInfo.update({"Alias": device.alias_name})
    else:
        deviceInfo.update({"Alias": ""})

    if device.status == 1:
        deviceInfo.update({"Status": "Online"})
    else:
        deviceInfo.update({"Status": "Offline"})

    if kioskMode == 1:
        deviceInfo.update({"Mode": "Kiosk"})
    else:
        deviceInfo.update({"Mode": "Multi"})

    if bool(device.hardware_info["serialNumber"]):
        deviceInfo.update({"Serial": str(device.hardware_info["serialNumber"])})
    else:
        deviceInfo.update({"Serial": ""})

    if bool(device.tags):
        # Add Functionality For Modifying Multiple Tags
        deviceInfo.update({"Tags": device.tags})
    else:
        deviceInfo.update({"Tags": ""})

        if device.tags is None:
            device.tags = []

    deviceInfo.update({"Apps": str(getdeviceapps(device.id))})

    if kioskMode == 1 and device.status == 1:
        deviceInfo.update({"KioskApp": str(getkioskmodeapp(device.id))})
    else:
        deviceInfo.update({"KioskApp": ""})

    location_info, resp_json = getLocationInfo(device.id)
    network_info = getNetworkInfo(device.id)
    unpackageDict(deviceInfo, resp_json)

    deviceInfo.update({"location_info": location_info})
    deviceInfo.update({"network_event": network_info})

    return deviceInfo


####Perform Actions. Set Kiosk Mode, Multi App Mode, Tags, or Alias####
def TakeAction(frame, group, action, label, isDevice=False):
    """Calls API To Perform Action And Logs Result To UI"""
    if not Globals.enterprise_id:
        frame.loadConfigPrompt()

    api_instance = esperclient.DeviceApi(esperclient.ApiClient(Globals.configuration))
    actionName = ""
    if frame.actionChoice.GetValue() in Globals.GRID_ACTIONS:
        actionName = '"%s"' % str(Globals.GRID_ACTIONS[action])
    elif frame.actionChoice.GetValue() in Globals.GENERAL_ACTIONS:
        actionName = '"%s"' % str(Globals.GENERAL_ACTIONS[action])
    frame.Logging(
        "---> Starting Execution "
        + actionName
        + " on "
        + frame.groupChoice.GetString(group)
    )
    if (
        action == Globals.SHOW_ALL_AND_GENERATE_REPORT
        or action == Globals.SET_KIOSK
        or action == Globals.SET_MULTI
    ):
        frame.emptyDeviceGrid()
        frame.emptyNetworkGrid()

    frame.runBtn.Enable(False)
    if isDevice:
        deviceToUse = (
            frame.deviceChoice.GetClientData(group)
            if frame.deviceChoice.GetClientData(group)
            else ""
        )
        frame.Logging("---> Making API Request")
        wxThread.doAPICallInThread(
            frame,
            getDeviceById,
            args=(deviceToUse),
            eventType=wxThread.myEVT_RESPONSE,
            callback=iterateThroughDeviceList,
            callbackArgs=(frame, action),
            waitForJoin=False,
        )
    elif action in Globals.GRID_ACTIONS:
        iterateThroughGridRows(frame, action)
    else:
        if label == "All devices":
            iterateThroughAllGroups(frame, action, api_instance)
        else:
            # Iterate Through Each Device in Group VIA Api Request
            try:
                groupToUse = (
                    frame.groupChoice.GetClientData(group)
                    if frame.groupChoice.GetClientData(group)
                    else ""
                )  # Get Device Group ID
                frame.Logging("---> Making API Request")
                wxThread.doAPICallInThread(
                    frame,
                    getAllDevices,
                    args=(groupToUse),
                    eventType=wxThread.myEVT_RESPONSE,
                    callback=iterateThroughDeviceList,
                    callbackArgs=(frame, action),
                    waitForJoin=False,
                )
            except ApiException as e:
                print("Exception when calling DeviceApi->get_all_devices: %s\n" % e)
    frame.runBtn.Enable(True)


def iterateThroughAllGroups(frame, action, api_instance):
    for index, value in enumerate(frame.groupChoice.Strings):
        groupToUse = frame.groupChoice.GetClientData(index)  # Get Device Group ID
        if value != "All devices":
            continue
        try:
            frame.Logging("---> Making API Request")
            wxThread.doAPICallInThread(
                frame,
                getAllDevices,
                args=(groupToUse),
                eventType=wxThread.myEVT_RESPONSE,
                callback=iterateThroughDeviceList,
                callbackArgs=(frame, action),
                waitForJoin=False,
            )
        except ApiException as e:
            print("Exception when calling DeviceApi->get_all_devices: %s\n" % e)


def setKiosk(frame, device, deviceInfo):
    """Toggles Kiosk Mode With Specified App"""
    logString = ""
    if deviceInfo["Mode"] == "Multi":
        if deviceInfo["Status"] == "Online":
            appToUse = frame.appChoice.GetClientData(frame.appChoice.GetSelection())
            logString = (
                str("--->" + str(device.device_name) + " " + str(device.alias_name))
                + " ->Kiosk->"
                + str(appToUse)
            )
            status = toggleKioskMode(frame, device.id, appToUse, True)
            if "Success" in str(status):
                logString = logString + " <success>"
            else:
                logString = logString + " <failed>"
        else:
            logString = logString + "(Device offline, skipping)"
    else:
        logString = logString + "(Already Kiosk mode, skipping)"
    evt = wxThread.CustomEvent(wxThread.myEVT_LOG, -1, logString)
    wx.PostEvent(Globals.frame, evt)


def setMulti(frame, device, deviceInfo):
    """Toggles Multi App Mode"""
    logString = (
        str("--->" + str(device.device_name) + " " + str(device.alias_name))
        + " ,->Multi->"
    )
    if deviceInfo["Mode"] == "Kiosk":
        if deviceInfo["Status"] == "Online":
            status = toggleKioskMode(frame, device.id, {}, False)
            if "Success" in str(status):
                logString = logString + " <success>"
            else:
                logString = logString + " <failed>"
        else:
            logString = logString + "(Device offline, skipping)"
    else:
        logString = logString + "(Already Multi mode, skipping)"
    evt = wxThread.CustomEvent(wxThread.myEVT_LOG, -1, logString)
    wx.PostEvent(Globals.frame, evt)


def modifyTags(frame):
    api_instance = esperclient.DeviceApi(esperclient.ApiClient(Globals.configuration))
    try:
        api_response = api_instance.get_all_devices(
            Globals.enterprise_id,
            limit=Globals.limit,
            offset=Globals.offset,
        )
    except Exception as e:
        frame.Logging("---> ERROR: Failed to get devices ids to modify tags")
        print(e)

    tagsFromGrid = frame.getDeviceTagsFromGrid()
    num = 1

    for device in api_response.results:
        if device.device_name in tagsFromGrid.keys():
            tags = setdevicetags(device.id, tagsFromGrid[device.device_name])
            frame.updateTagCell(device.device_name, tags)
            frame.setGaugeValue(int(num / len(tagsFromGrid.keys()) * 100))
            num += 1


def modifyAlias(frame):
    """Sets Device Alias"""
    api_instance = esperclient.DeviceApi(esperclient.ApiClient(Globals.configuration))
    try:
        api_response = api_instance.get_all_devices(
            Globals.enterprise_id,
            limit=Globals.limit,
            offset=Globals.offset,
        )
    except Exception as e:
        frame.Logging("---> ERROR: Failed to get devices ids to modify tags")
        print(e)

    aliasDic = frame.getDeviceAliasFromGrid()
    logString = ""
    num = 1
    for device in api_response.results:
        if device.device_name in aliasDic.keys():
            newName = aliasDic[device.device_name]
            logString = str(
                "--->" + str(device.device_name) + " : " + str(newName) + "--->"
            )
            if not (newName in str(device.alias_name)):
                if device.status == 1:
                    status = setdevicename(frame, device.id, newName)
                    if "Success" in str(status):
                        logString = logString + " <success>"
                    else:
                        logString = logString + " <failed>"
                else:
                    logString = logString + "(Device offline)"
            else:
                logString = logString + "(Name already set)"
            frame.setGaugeValue(int(num / len(aliasDic.keys()) * 100))
            num += 1
        frame.Logging(logString)


####End Perform Actions####


def getCommandsApiInstance():
    return esperclient.CommandsV2Api(esperclient.ApiClient(Globals.configuration))


@api_tool_decorator
def executeUpdateDeviceConfigCommandOnGroup(
    frame, command_args, command_type="UPDATE_DEVICE_CONFIG"
):
    groupToUse = frame.groupChoice.GetClientData(
        frame.groupChoice.GetSelection()
    )  # Get Device Group ID
    request = esperclient.V0CommandRequest(
        enterprise=Globals.enterprise_id,
        command_type="GROUP",
        device_type="all",
        groups=[groupToUse],
        command=command_type,
        command_args=command_args,
    )
    api_instance = getCommandsApiInstance()
    api_response = api_instance.create_command(Globals.enterprise_id, request)
    return waitForCommandToFinish(frame, api_response.id)


@api_tool_decorator
def executeUpdateDeviceConfigCommandOnDevice(
    frame, command_args, command_type="UPDATE_DEVICE_CONFIG"
):
    deviceToUse = frame.deviceChoice.GetClientData(
        frame.deviceChoice.GetSelection()
    )  # Get Device Group ID
    request = esperclient.V0CommandRequest(
        enterprise=Globals.enterprise_id,
        command_type="DEVICE",
        device_type="all",
        devices=[deviceToUse],
        command=command_type,
        command_args=command_args,
    )
    api_instance = getCommandsApiInstance()
    api_response = api_instance.create_command(Globals.enterprise_id, request)
    return waitForCommandToFinish(frame, api_response.id)


@api_tool_decorator
def waitForCommandToFinish(frame, request_id):
    api_instance = getCommandsApiInstance()
    response = api_instance.get_command_request_status(
        Globals.enterprise_id, request_id
    )
    status = response.results[0]
    evt = wxThread.CustomEvent(
        wxThread.myEVT_LOG, -1, "---> Command state: %s" % str(status.state)
    )
    wx.PostEvent(Globals.frame, evt)

    while status.state not in [
        "Command Success",
        "Command Failure",
        "Command TimeOut",
        "Command Cancelled",
        "Command Queued",
    ]:
        response = api_instance.get_command_request_status(
            Globals.enterprise_id, request_id
        )
        status = response.results[0]
        evt = wxThread.CustomEvent(
            wxThread.myEVT_LOG, -1, "---> Command state: %s" % str(status.state)
        )
        wx.PostEvent(Globals.frame, evt)
        time.sleep(1)
    return status


def ApplyDeviceConfig(frame, config, commandType):
    otherConfig = {}
    for key in config.keys():
        if key not in Globals.COMMAND_ARGS:
            otherConfig[key] = config[key]

    command_args = V0CommandArgs(
        app_state=config["app_state"] if "app_state" in config else None,
        app_version=config["app_version"] if "app_version" in config else None,
        device_alias_name=config["device_alias_name"]
        if "device_alias_name" in config
        else None,
        custom_settings_config=otherConfig,
        package_name=config["package_name"] if "package_name" in config else None,
        policy_url=config["policy_url"] if "policy_url" in config else None,
        state=config["state"] if "state" in config else None,
        message=config["message"] if "message" in config else None,
        wifi_access_points=config["wifi_access_points"]
        if "wifi_access_points" in config
        else None,
    )
    result, isGroup = frame.confirmCommand(command_args, commandType)

    t = None
    if result and isGroup:
        t = wxThread.GUIThread(
            frame,
            executeUpdateDeviceConfigCommandOnGroup,
            args=(frame, command_args, commandType),
            eventType=wxThread.myEVT_COMMAND,
        )
    elif result and not isGroup:
        t = wxThread.GUIThread(
            frame,
            executeUpdateDeviceConfigCommandOnDevice,
            args=(frame, command_args, commandType),
            eventType=wxThread.myEVT_COMMAND,
        )
    if t:
        t.start()
