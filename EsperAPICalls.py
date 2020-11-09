import requests
import esperclient
import time
import json
import os.path
import Globals
import string
import platform
import ctypes

from tkinter import Tk
from tkinter.filedialog import askopenfilename

from deviceInfo import getSecurityPatch, getWifiStatus, getCellularStatus, getDeviceName

from esperclient import EnterpriseApi, ApiClient
from esperclient.rest import ApiException
from esperclient.models.command_args import CommandArgs
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
        command_args = esperclient.CommandArgs(package_name=appToUse)
    else:
        command_args = {}
    command = esperclient.CommandRequest(
        command="SET_KIOSK_APP", command_args=command_args
    )
    api_response = api_instance.create_command(Globals.enterprise_id, command)
    response = api_instance.get_command_request_status(
        Globals.enterprise_id, api_response.id
    )

    status = response.state
    frame.Logging("---> " + str(status))

    waitForCommandToFinish(frame, api_response.id)
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
    frame.Logging("---> " + str(status))
    status = waitForCommandToFinish(frame, api_response.id)
    return status


####End Esper API Requests####


def iterateThroughGridRows(frame, action):
    if action == Globals.SET_ALIAS:
        modifyAlias(frame)
    elif action == Globals.MODIFY_TAGS:
        modifyTags(frame)


def iterateThroughDeviceList(frame, action, api_response):
    """Iterates Through Each Device And Performs A Specified Action"""
    number_of_devices = 0
    deviceInfo = {}
    for device in api_response.results:
        frame.buttonYieldEvent()
        number_of_devices = number_of_devices + 1
        deviceInfo.clear()
        deviceInfo.update({"num": number_of_devices})
        deviceInfo = populateDeviceInfoDictionary(device, deviceInfo)
        if action == Globals.SHOW_ALL_AND_GENERATE_REPORT:
            logstring = frame.createLogString(deviceInfo, action)
            frame.addDeviceToDeviceGrid(deviceInfo)
            frame.Logging(logstring)

            output = generateReport(frame, device, deviceInfo)
            frame.addDeviceToNetworkGrid(device, deviceInfo)
            frame.Logging(output)
        elif action == Globals.SET_KIOSK:
            setKiosk(frame, device, deviceInfo)
        elif action == Globals.SET_MULTI:
            setMulti(frame, device, deviceInfo)


def populateDeviceInfoDictionary(device, deviceInfo):
    """Populates Device Info Dictionary"""
    kioskMode = iskioskmode(device.id)
    deviceInfo.update({"EsperName": device.device_name})

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

    if resp_json and "bluetoothStats" in resp_json:
        deviceInfo.update({"bluetoothStats": resp_json["bluetoothStats"]})
    if (
        resp_json
        and "deviceSettings" in resp_json
        and "bluetoothState" in resp_json["deviceSettings"]
    ):
        deviceInfo.update(
            {"bluetoothState": resp_json["deviceSettings"]["bluetoothState"]}
        )

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
    if action in Globals.GRID_ACTIONS:
        actionName = str(Globals.GRID_ACTIONS[action])
    elif action in Globals.GENERAL_ACTIONS:
        actionName = actionName = str(Globals.GENERAL_ACTIONS[action])
    frame.Logging(
        "---> Starting Execution - "
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
        # if action == Globals.GENERATE_REPORT:
        frame.emptyNetworkGrid()

    if isDevice:
        deviceToUse = (
            frame.deviceChoice.GetClientData(group)
            if frame.deviceChoice.GetClientData(group)
            else ""
        )
        try:
            api_response = api_instance.get_device_by_id(
                Globals.enterprise_id, device_id=deviceToUse
            )
            if api_response:
                api_response.results = [api_response]
                iterateThroughDeviceList(frame, action, api_response)
                frame.Logging("--- Completed ---")
        except ApiException as e:
            print("Exception when calling DeviceApi->get_device_by_id: %s\n" % e)
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
                api_response = api_instance.get_all_devices(
                    Globals.enterprise_id,
                    group=groupToUse,
                    limit=Globals.limit,
                    offset=Globals.offset,
                )
                if len(api_response.results):
                    iterateThroughDeviceList(frame, action, api_response)
                    frame.Logging("--- Completed ---")
                else:
                    frame.Logging("No devices found for group")
                    frame.Logging("--- Completed ---")
            except ApiException as e:
                print("Exception when calling DeviceApi->get_all_devices: %s\n" % e)


def iterateThroughAllGroups(frame, action, api_instance):
    for index, value in enumerate(frame.groupChoice.Strings):
        groupToUse = frame.groupChoice.GetClientData(index)  # Get Device Group ID
        if value != "All devices":
            continue
        try:
            api_response = api_instance.get_all_devices(
                Globals.enterprise_id,
                group=groupToUse,
                limit=Globals.limit,
                offset=Globals.offset,
            )
            if len(api_response.results):
                frame.Logging("Group Name:" + value)
                iterateThroughDeviceList(frame, action, api_response)
        except ApiException as e:
            print("Exception when calling DeviceApi->get_all_devices: %s\n" % e)
    frame.Logging("---Completed Request---")


def setKiosk(frame, device, deviceInfo):
    """Toggles Kiosk Mode With Specified App"""
    logString = frame.createLogString(deviceInfo, Globals.SET_KIOSK)
    if deviceInfo["Mode"] == "Multi":
        if deviceInfo["Status"] == "On-Line":
            appToUse = frame.appChoice.GetClientData(frame.appChoice.GetSelection())
            logString = logString + ",->Kiosk->" + appToUse
            frame.Logging(
                str("--->" + str(device.device_name) + " " + str(device.alias_name))
                + " "
                + ",->Kiosk->"
                + str(appToUse)
            )
            status = toggleKioskMode(frame, device.id, appToUse, True)
            if "Success" in str(status):
                logString = logString + " <success>"
            else:
                logString = logString + " <failed>"
        else:
            logString = logString + ",(Device off-line)"
    else:
        logString = logString + ",(Already Kiosk mode)"
    frame.Logging(logString)


def setMulti(frame, device, deviceInfo):
    """Toggles Multi App Mode"""
    logString = frame.createLogString(deviceInfo, Globals.SET_MULTI)
    if deviceInfo["Mode"] == "Kiosk":
        if deviceInfo["Status"] == "On-Line":
            logString = logString + ",->Multi->"
            frame.Logging(
                str("--->" + str(device.device_name) + " " + str(device.alias_name))
                + " "
                + ",->Multi->"
            )
            status = toggleKioskMode(frame, device.id, {}, False)
            if "Success" in str(status):
                logString = logString + " <success>"
            else:
                logString = logString + " <failed>"
        else:
            logString = logString + ",(Device off-line)"
    else:
        logString = logString + ",(Already Multi mode)"
    frame.Logging(logString)


# def setAlias(frame, device, deviceInfo):
#     """Sets Device Alias"""
#     logString = frame.createLogString(deviceInfo, Globals.SET_ALIAS)
#     serialNum = device.hardware_info["serialNumber"]
#     if serialNum in Globals.TAGSandALIASES.keys():
#         newName = Globals.TAGSandALIASES[serialNum][0]
#         if not (newName in str(device.alias_name)):
#             if deviceInfo["Status"] == "On-Line":
#                 logString = logString + ",->Name->"
#                 frame.Logging(
#                     str("--->" + str(device.device_name) + " " + str(device.alias_name))
#                     + " "
#                     + ",->Name->"
#                     + newName
#                 )
#                 status = setdevicename(frame, device.id, newName)
#                 if "Success" in str(status):
#                     logString = logString + " <success>"
#                 else:
#                     logString = logString + " <failed>"
#             else:
#                 logString = logString + ",(Device off-line)"
#         else:
#             logString = logString + ",(Name already set)"
#     else:
#         logString = logString + ",(no Name found in file)"
#     frame.Logging(logString)  # log results


# def editTags(frame, device, deviceInfo, removeTag):
#     """Sends Request To Edit Tags"""
#     serialNum = device.hardware_info["serialNumber"]
#     if serialNum in Globals.TAGSandALIASES.keys():
#         if removeTag:
#             removeTags(frame, device, deviceInfo, serialNum)
#         else:
#             addTags(frame, device, deviceInfo, serialNum)
#     else:
#         logString = str(device) + ",(no Tag found in file)"
#         frame.Logging(logString)


# def addTags(frame, device, deviceInfo, serialNum):
#     """Sets Device Tags"""
#     logString = frame.createLogString(
#         deviceInfo, Globals.MODIFY_TAGS
#     )  # Globals.SET_TAGS)
#     newTags = Globals.TAGSandALIASES[serialNum][1]
#     if newTags != "":
#         newTagsList = newTags.split(",")
#         tagList = device.tags
#         for tag in tagList:
#             if tag not in newTagsList:
#                 newTagsList.append(tag)
#         setdevicetags(device.id, newTagsList)
#         logString = logString + ",Tags Added, New Tag List -> " + str(newTagsList)
#         frame.Logging(logString)
#     else:
#         frame.Logging("No Tags To Add")


# def removeTags(frame, device, deviceInfo, serialNum):
#     """Removes Device Tags"""
#     logString = frame.createLogString(
#         deviceInfo, Globals.MODIFY_TAGS
#     )  # Globals.REMOVE_TAGS)
#     newTags = Globals.TAGSandALIASES[serialNum][1]
#     newTagsList = newTags.split(",")
#     tagList = device.tags
#     if tagList is not None:
#         for tag in newTagsList:
#             if tag in tagList:
#                 tagList.remove(tag)
#         setdevicetags(device.id, tagList)
#         logString = logString + ",Tags Removed, New Tag List -> " + str(tagList)
#         frame.Logging(logString)
#     else:
#         frame.Logging("No Tags To Remove, Device Has No Tags")


def modifyTags(frame):
    api_instance = esperclient.DeviceApi(esperclient.ApiClient(Globals.configuration))
    try:
        api_response = api_instance.get_all_devices(
            Globals.enterprise_id,
            limit=Globals.limit,
            offset=Globals.offset,
        )
    except Exception as e:
        frame.Logging("Failed to get devices ids to modify tags")
        print(e)

    tagsFromGrid = frame.getDeviceTagsFromGrid()
    for device in api_response.results:
        for esperName in tagsFromGrid.keys():
            if device.device_name == esperName:
                tags = setdevicetags(device.id, tagsFromGrid[esperName])
                frame.updateTagCell(esperName, tags)


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
        frame.Logging("Failed to get devices ids to modify tags")
        print(e)

    aliasDic = frame.getDeviceAliasFromGrid()
    logString = ""
    for device in api_response.results:
        for esperName in aliasDic.keys():
            if device.device_name == esperName:
                newName = aliasDic[esperName]
                if not (newName in str(device.alias_name)):
                    if device.status == 1:
                        logString = logString + ",->Name->"
                        frame.Logging(
                            str(
                                "--->"
                                + str(device.device_name)
                                + " "
                                + str(device.alias_name)
                            )
                            + " "
                            + ",->Name->"
                            + newName
                        )
                        status = setdevicename(frame, device.id, newName)
                        if "Success" in str(status):
                            logString = logString + " <success>"
                        else:
                            logString = logString + " <failed>"
                    else:
                        logString = logString + ",(Device off-line)"
                else:
                    logString = logString + ",(Name already set)"
    frame.Logging(logString)


####End Perform Actions####


def generateReport(frame, device, deviceInfo):
    patchVersion = getSecurityPatch(device)
    wifiStatus = getWifiStatus(deviceInfo)
    networkStatus = getCellularStatus(deviceInfo)
    device_name = getDeviceName(device)
    bluetooth_state = deviceInfo["bluetoothState"]

    deviceCSV = (
        device_name
        + ","
        + patchVersion
        + ","
        + wifiStatus
        + ","
        + networkStatus
        + ","
        + str(bluetooth_state)
    )
    frame.Logging(deviceCSV)
    return deviceCSV


def getCommandsApiInstance():
    return esperclient.CommandsV2Api(esperclient.ApiClient(Globals.configuration))


def executeUpdateDeviceConfigCommandOnGroup(frame, command_args):
    groupToUse = frame.groupChoice.GetClientData(
        frame.groupChoice.GetSelection()
    )  # Get Device Group ID
    request = esperclient.V0CommandRequest(
        enterprise=Globals.enterprise_id,
        command_type="GROUP",
        device_type="all",
        groups=[groupToUse],
        command="UPDATE_DEVICE_CONFIG",
        command_args=command_args,
    )
    api_instance = getCommandsApiInstance()
    api_response = api_instance.create_command(Globals.enterprise_id, request)
    return waitForCommandToFinish(frame, api_response.id)


def executeUpdateDeviceConfigCommandOnDevice(frame, command_args):
    deviceToUse = frame.deviceChoice.GetClientData(
        frame.deviceChoice.GetSelection()
    )  # Get Device Group ID
    request = esperclient.V0CommandRequest(
        enterprise=Globals.enterprise_id,
        command_type="DEVICE",
        device_type="all",
        devices=[deviceToUse],
        command="UPDATE_DEVICE_CONFIG",
        command_args=command_args,
    )
    api_instance = getCommandsApiInstance()
    api_response = api_instance.create_command(Globals.enterprise_id, request)
    return waitForCommandToFinish(frame, api_response.id)


def waitForCommandToFinish(frame, request_id):
    api_instance = getCommandsApiInstance()
    response = api_instance.get_command_request_status(
        Globals.enterprise_id, request_id
    )
    status = response.results[0]

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
        frame.Logging("---> " + str(status))
        frame.buttonYieldEvent()
        time.sleep(1)
    return status


def ApplyDeviceConfig(frame, config):
    command_args = V0CommandArgs(custom_settings_config=config)
    result, isGroup = frame.confirmCommand(command_args)

    if result and isGroup:
        return executeUpdateDeviceConfigCommandOnGroup(frame, command_args)
    elif result and not isGroup:
        return executeUpdateDeviceConfigCommandOnDevice(frame, command_args)
