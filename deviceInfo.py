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
