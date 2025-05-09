#!/usr/bin/env python

import Common.Globals as Globals
from Utility.Resource import getHeader
from Utility.Web.WebRequests import performGetRequestWithRetry


def getSecurityPatch(device, deviceInfo=None):
    patch_ver = ""
    if type(device) == dict:
        if "software" in device and device["software"]:
            if "security_patch_level" in device["software"]:
                if device["software"]["security_patch_level"] is not None:
                    patch_ver = device["software"]["security_patch_level"]
        else:
            if "securityPatchLevel" in device and device["securityPatchLevel"] is not None:
                patch_ver = device["securityPatchLevel"]
    else:
        if hasattr(device, "software_info") and device.software_info:
            if "securityPatchLevel" in device.software_info:
                if device.software_info["securityPatchLevel"] is not None:
                    patch_ver = device.software_info["securityPatchLevel"]
        else:
            if "securityPatchLevel" in device and device["securityPatchLevel"] is not None:
                patch_ver = device["securityPatchLevel"]
    return patch_ver


def getWifiStatus(deviceInfo):
    wifi_event = None
    if "network_event" in deviceInfo:
        wifi_event = deviceInfo["network_event"]
    if "network" in deviceInfo:
        wifi_event = deviceInfo["network"]
    wifi_string = ""
    current_wifi_connection = ""
    current_wifi_configurations = ""

    if wifi_event:
        # Configured Networks
        if "configuredWifiNetworks" in wifi_event and wifi_event["configuredWifiNetworks"]:
            for access_point in wifi_event["configuredWifiNetworks"]:
                current_wifi_configurations += access_point + " "
        if "wifi_access_points" in wifi_event and wifi_event["wifi_access_points"]:
            for access_point in wifi_event["wifi_access_points"]:
                current_wifi_configurations += access_point + " "

        # Connected Network
        if "wifiNetworkInfo" in wifi_event and wifi_event["wifiNetworkInfo"]:
            if "<unknown ssid>" not in wifi_event["wifiNetworkInfo"]["wifiSSID"]:
                ssid = wifi_event["wifiNetworkInfo"]["wifiSSID"] + ": Connected"
                current_wifi_connection = ssid
        if "ssid" in wifi_event:
            ssid = wifi_event["ssid"] + ": Connected"
            current_wifi_connection = ssid

    wifi_string = "[" + current_wifi_configurations + "],[" + current_wifi_connection + "]"
    return wifi_string


def getCellularStatus(deviceInfo):
    network_event = deviceInfo["network_event"]
    cellular_connections = ""
    current_active_connection = ""

    if network_event and "currentActiveConnection" in network_event:
        current_active_connection = network_event["currentActiveConnection"]
    if network_event and "active_connection" in network_event:
        current_active_connection = network_event["active_connection"]

    simoperator = ""
    connection_status = ""
    if network_event and "cellularNetworkInfo" in network_event:
        cellular_connections = "[NOT CONNECTED]"
        cellularNetworkInfo = network_event["cellularNetworkInfo"]
        if cellularNetworkInfo:
            if "mobileNetworkStatus" in cellularNetworkInfo:
                connection_status = cellularNetworkInfo["mobileNetworkStatus"]
            if len(cellularNetworkInfo["simOperator"]) > 0:
                simoperator = cellularNetworkInfo["simOperator"][0] + ":"
        cellular_connections = "[" + simoperator + connection_status + "]" + "," + current_active_connection
    elif network_event and "cellular" in network_event:
        cellularNetworkInfo = network_event["cellular"]
        connection_status = cellularNetworkInfo["status"]
        if "sim_operator" in cellularNetworkInfo and len(cellularNetworkInfo["sim_operator"]) > 0:
            simoperator = cellularNetworkInfo["sim_operator"][0] + ":"
        cellular_connections = "[" + simoperator + connection_status + "]" + "," + current_active_connection

    cellular_connections = "Cellular:" + cellular_connections
    return cellular_connections + "," + current_active_connection


def constructNetworkInfo(device, deviceInfo):
    networkInfo = {}
    networkInfo["Security Patch"] = getSecurityPatch(device, deviceInfo)
    wifiStatus = getWifiStatus(deviceInfo).split(",")
    networkInfo["[WIFI ACCESS POINTS]"] = wifiStatus[0]
    networkInfo["[Current WIFI Connection]"] = wifiStatus[1]
    cellStatus = getCellularStatus(deviceInfo).split(",")
    networkInfo["[Cellular Access Point]"] = cellStatus[0]
    networkInfo["Active Connection"] = cellStatus[1]
    networkInfo["Device Name"] = getDeviceName(device)

    deviceInfo["wifiAP"] = wifiStatus[0]
    deviceInfo["currentWifi"] = wifiStatus[1]
    deviceInfo["cellAP"] = cellStatus[0]
    deviceInfo["activeConnection"] = cellStatus[1]

    deviceInfo["networkSignalStrength"] = "N/A"
    deviceInfo["cellularSignalStrength"] = "N/A"

    cellularKey = ""
    if deviceInfo["network_event"] and "cellularNetworkInfo" in deviceInfo["network_event"]:
        cellularKey = "cellularNetworkInfo"
    elif deviceInfo["network_event"] and "cellular" in deviceInfo["network_event"]:
        cellularKey = "cellular"
    if (
        cellularKey
        and deviceInfo
        and "network_event" in deviceInfo
        and deviceInfo["network_event"]
        and cellularKey in deviceInfo["network_event"]
        and deviceInfo["network_event"][cellularKey]
        and "signalStrength" in deviceInfo["network_event"][cellularKey]
    ):
        deviceInfo["cellularSignalStrength"] = deviceInfo["network_event"][cellularKey]["signalStrength"]

    if (
        deviceInfo
        and deviceInfo["network_event"]
        and "wifiNetworkInfo" in deviceInfo["network_event"]
        and deviceInfo["network_event"]["wifiNetworkInfo"]
        and "signalStrength" in deviceInfo["network_event"]["wifiNetworkInfo"]
    ):
        deviceInfo["networkSignalStrength"] = deviceInfo["network_event"]["wifiNetworkInfo"]["signalStrength"]

    for key, value in Globals.CSV_NETWORK_ATTR_NAME.items():
        if value:
            if type(value) is str and value in deviceInfo:
                networkInfo[key] = str(deviceInfo[value])
            elif type(value) is list:
                for v in value:
                    if v in deviceInfo:
                        networkInfo[key] = str(deviceInfo[v])
            else:
                networkInfo[key] = ""

    return networkInfo


def getDeviceName(device):
    device_name = " "
    if hasattr(device, "device_name"):
        if device.device_name is not None:
            device_name = device.device_name
    elif type(device) is dict and "device_name" in device:
        device_name = device["device_name"]
    return device_name


def getDeviceInitialTemplate(deviceId):
    url = "{tenant}/enterprise/{enterprise_id}/device/{device_id}/initialtemplate/".format(
        tenant=Globals.configuration.host,
        enterprise_id=Globals.enterprise_id,
        device_id=deviceId,
    )
    resp = performGetRequestWithRetry(url, headers=getHeader())
    return resp.json()
