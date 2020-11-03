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
    return location_event


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
        if (
            action == Globals.SHOW_DEVICES
            or action == Globals.SHOW_APP_VERSION
            or action == Globals.SHOW_ALL
        ):
            Globals.header_format = Globals.CSV_TAG_HEADER
            logstring = frame.createLogString(deviceInfo, action)
            frame.Logging(logstring)
            Globals.new_output_to_save = Globals.new_output_to_save + "\n" + logstring
        elif action == Globals.SET_KIOSK:
            setKiosk(frame, device, deviceInfo)
        elif action == Globals.SET_MULTI:
            setMulti(frame, device, deviceInfo)
        elif action == Globals.SET_ALIAS and bool(Globals.TAGSandALIASES):
            setAlias(frame, device, deviceInfo)
        elif action == Globals.SET_TAGS and bool(Globals.TAGSandALIASES):
            editTags(frame, device, deviceInfo, removeTag=False)
        elif action == Globals.REMOVE_TAGS and bool(Globals.TAGSandALIASES):
            editTags(frame, device, deviceInfo, removeTag=True)
        elif action == Globals.GENERATE_REPORT:
            Globals.header_format = Globals.CSV_SECURITY_WIFI_HEADER
            output = generateReport(frame, device, deviceInfo)
            Globals.new_output_to_save += "\n" + output
        elif action == Globals.URL_BLACKLIST:
            urlBlacklist(frame)


def populateDeviceInfoDictionary(device, deviceInfo):
    """Populates Device Info Dictionary"""
    kioskMode = iskioskmode(device.id)
    deviceInfo.update({"EsperName": device.device_name})

    if bool(device.alias_name):
        deviceInfo.update({"Alias": device.alias_name})
    else:
        deviceInfo.update({"Alias": ""})

    if device.status == 1:
        deviceInfo.update({"Status": "On-Line"})
    else:
        deviceInfo.update({"Status": "Off-Line"})

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

    location_info = getLocationInfo(device.id)
    network_info = getNetworkInfo(device.id)

    deviceInfo.update({"location_info": location_info})
    deviceInfo.update({"network_event": network_info})

    return deviceInfo


####Perform Actions. Set Kiosk Mode, Multi App Mode, Tags, or Alias####
def TakeAction(frame, group, action, label):
    """Calls API To Perform Action And Logs Result To UI"""
    Globals.new_output_to_save = ""
    api_instance = esperclient.DeviceApi(esperclient.ApiClient(Globals.configuration))
    groupToUse = frame.groupChoice.GetClientData(group)  # Get Device Group ID
    frame.Logging(
        "---> Starting Execution - "
        + str(Globals.ACTIONS[action])
        + " on "
        + frame.groupChoice.GetString(group)
    )
    if action == Globals.SHOW_NamesAndTags:
        # Iterate Through Each Device in Group VIA CSV
        for serial, names in Globals.TAGSandALIASES.items():
            tag = names[1]
            frame.Logging(
                ", , "
                + "{:18.16}".format(names[0])
                + ", , , "
                + "{:18.16}".format(serial)
                + ", "
                + tag
            )
    else:
        if label == "All devices":
            iterateThroughAllGroups(frame, action, api_instance)
        else:
            # Iterate Through Each Device in Group VIA Api Request
            try:
                api_response = api_instance.get_all_devices(
                    Globals.enterprise_id,
                    group=groupToUse,
                    limit=Globals.limit,
                    offset=Globals.offset,
                )
                if len(api_response.results):
                    iterateThroughDeviceList(frame, action, api_response)
                    frame.Logging("--- Completed ---")
            except ApiException as e:
                print("Exception when calling DeviceApi->get_all_devices: %s\n" % e)


def iterateThroughAllGroups(frame, action, api_instance):
    for index, value in enumerate(frame.groupChoice.Strings):
        groupToUse = frame.groupChoice.GetClientData(index)  # Get Device Group ID
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


def setAlias(frame, device, deviceInfo):
    """Sets Device Alias"""
    logString = frame.createLogString(deviceInfo, Globals.SET_ALIAS)
    serialNum = device.hardware_info["serialNumber"]
    if serialNum in Globals.TAGSandALIASES.keys():
        newName = Globals.TAGSandALIASES[serialNum][0]
        if not (newName in str(device.alias_name)):
            if deviceInfo["Status"] == "On-Line":
                logString = logString + ",->Name->"
                frame.Logging(
                    str("--->" + str(device.device_name) + " " + str(device.alias_name))
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
    else:
        logString = logString + ",(no Name found in file)"
    frame.Logging(logString)  # log results


def editTags(frame, device, deviceInfo, removeTag):
    """Sends Request To Edit Tags"""
    serialNum = device.hardware_info["serialNumber"]
    if serialNum in Globals.TAGSandALIASES.keys():
        if removeTag:
            removeTags(frame, device, deviceInfo, serialNum)
        else:
            addTags(frame, device, deviceInfo, serialNum)
    else:
        logString = str(device) + ",(no Tag found in file)"
        frame.Logging(logString)


def addTags(frame, device, deviceInfo, serialNum):
    """Sets Device Tags"""
    logString = frame.createLogString(deviceInfo, Globals.SET_TAGS)
    newTags = Globals.TAGSandALIASES[serialNum][1]
    if newTags != "":
        newTagsList = newTags.split(",")
        tagList = device.tags
        for tag in tagList:
            if tag not in newTagsList:
                newTagsList.append(tag)
        setdevicetags(device.id, newTagsList)
        logString = logString + ",Tags Added, New Tag List -> " + str(newTagsList)
        frame.Logging(logString)
    else:
        frame.Logging("No Tags To Add")


def removeTags(frame, device, deviceInfo, serialNum):
    """Removes Device Tags"""
    logString = frame.createLogString(deviceInfo, Globals.REMOVE_TAGS)
    newTags = Globals.TAGSandALIASES[serialNum][1]
    newTagsList = newTags.split(",")
    tagList = device.tags
    if tagList is not None:
        for tag in newTagsList:
            if tag in tagList:
                tagList.remove(tag)
        setdevicetags(device.id, tagList)
        logString = logString + ",Tags Removed, New Tag List -> " + str(tagList)
        frame.Logging(logString)
    else:
        frame.Logging("No Tags To Remove, Device Has No Tags")


####End Perform Actions####


def generateReport(frame, device, deviceInfo):
    patchVersion = getSecurityPatch(device)
    wifiStatus = getWifiStatus(deviceInfo)
    networkStatus = getCellularStatus(deviceInfo)
    device_name = getDeviceName(device)

    deviceCSV = (
        device_name + "," + patchVersion + "," + wifiStatus + "," + networkStatus
    )
    frame.Logging(deviceCSV)
    return deviceCSV


def getSecurityPatch(device):
    patch_ver = " "
    if "securityPatchLevel" in device.software_info:
        if device.software_info["securityPatchLevel"] is not None:
            patch_ver = device.software_info["securityPatchLevel"]
    return patch_ver


def getAliasName(device):
    alias_name = " "
    if hasattr(device, "alias_name"):
        if device.alias_name is not None:
            alias_name = device.alias_name
    return alias_name


def getDeviceName(device):
    device_name = " "
    if hasattr(device, "device_name"):
        if device.device_name is not None:
            device_name = device.device_name
    return device_name


def getWifiStatus(deviceInfo):
    wifi_event = deviceInfo["network_event"]
    wifi_string = ""
    current_wifi_connection = "Wifi Disconnected"
    current_wifi_configurations = ""

    # Configured Networks
    if "configuredWifiNetworks" in wifi_event:
        for access_point in wifi_event["configuredWifiNetworks"]:
            current_wifi_configurations += access_point + " "

    # Connected Network
    if "wifiNetworkInfo" in wifi_event:
        if "<unknown ssid>" not in wifi_event["wifiNetworkInfo"]["wifiSSID"]:
            ssid = wifi_event["wifiNetworkInfo"]["wifiSSID"] + ": Connected"
            current_wifi_connection = ssid

    wifi_string = (
        "[" + current_wifi_configurations + "],[" + current_wifi_connection + "]"
    )
    return wifi_string


def getIMEIAddress(device):
    imei = ""
    if hasattr(device, "network_info"):
        if device.network_info is not None:
            if "imei1" in device.network_info:
                imei = device.network_info["imei1"]
    return str(imei)


def getCellularStatus(deviceInfo):
    network_event = deviceInfo["network_event"]
    cellular_connections = "[NOT CONNECTED]"
    current_active_connection = ""

    if "currentActiveConnection" in network_event:
        current_active_connection = network_event["currentActiveConnection"]

    simoperator = ""
    if "cellularNetworkInfo" in network_event:
        cellularNetworkInfo = network_event["cellularNetworkInfo"]
        connection_status = cellularNetworkInfo["mobileNetworkStatus"]
        if len(cellularNetworkInfo["simOperator"]) > 0:
            simoperator = cellularNetworkInfo["simOperator"][0] + ":"
        cellular_connections = (
            "["
            + simoperator
            + connection_status
            + "]"
            + ","
            + current_active_connection
        )
    cellular_connections = "Cellular:" + cellular_connections
    return cellular_connections + "," + current_active_connection


def getMACAddress(device):
    mac_address = ""
    if hasattr(device, "network_info"):
        if device.network_info is not None:
            if "wifiMacAddress" in device.network_info:
                mac_address = device.network_info["wifiMacAddress"]
    return mac_address


def getSerial(device):
    serial_num = ""
    if hasattr(device, "hardware_info"):
        if device.hardware_info is not None:
            if "serialNumber" in device.hardware_info:
                serial_num = device.hardware_info["serialNumber"]
    return serial_num


def getID(device, deviceInfo):
    id = ""
    id = device.id
    return id


def findVersion(device):
    pass


def getBuildNumber(device):
    build_num = ""
    if hasattr(device, "software_info"):
        if device.software_info is not None:
            if "androidVersion" in device.software_info:
                build_num = device.hardware_info["androidVersion"]
    return build_num


def getLocation(device):
    latitude = ""
    longitude = ""
    if "location_info" in device:
        if "locationLats" in device["location_info"]:
            latitude = device["location_info"]["locationLats"]
        if "locationLongs" in device["location_info"]:
            longitude = device["location_info"]["locationLongs"]
    return latitude, longitude


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


def urlBlacklist(frame):
    # Create new window and ask user for blacklist data
    frame.showUrlBlacklistDialog()
    command_args = V0CommandArgs(
        custom_settings_config={
            "managedAppConfigurations": {
                "com.android.chrome": {"URLBlacklist": [Globals.url_blacklist]}
            }
        }
    )
    return executeUpdateDeviceConfigCommandOnGroup(frame, command_args)


def urlWhiteList(frame, urlWhiteList):
    command_args = V0CommandArgs(
        custom_settings_config={
            "managedAppConfigurations": {
                "com.android.chrome": {"URLWhitelist": urlWhiteList}
            }
        }
    )
    return executeUpdateDeviceConfigCommandOnGroup(frame, command_args)


def setIncognitoMode(frame, mode):
    command_args = V0CommandArgs(
        custom_settings_config={
            "managedAppConfigurations": {
                "com.android.chrome": {
                    "IncognitoModeAvailability": mode,  # 1 disable incognito mode
                }
            }
        }
    )
    return executeUpdateDeviceConfigCommandOnGroup(frame, command_args)


def setGoogleSafeSearch(frame, mode):
    command_args = V0CommandArgs(
        custom_settings_config={
            "managedAppConfigurations": {
                "com.android.chrome": {
                    "ForceGoogleSafeSearch": mode,  # enable safe search to work
                }
            }
        }
    )
    return executeUpdateDeviceConfigCommandOnGroup(frame, command_args)


def setHomepageLocation(frame, homeURL):
    command_args = V0CommandArgs(
        custom_settings_config={
            "managedAppConfigurations": {
                "com.android.chrome": {
                    "HomepageLocation": homeURL  # set chrome home page
                }
            }
        }
    )
    return executeUpdateDeviceConfigCommandOnGroup(frame, command_args)
