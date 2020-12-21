#!/usr/bin/env python

import esperclient

configuration = esperclient.Configuration()
enterprise_id = ""

""" Constants """
VERSION = "0.1"
TITLE = "Esper API Support Tool"
MIN_LIMIT = 1000
MAX_LIMIT = 500000
limit = (
    MAX_LIMIT  # int | Number of results to return per page. (optional) (default to 20)
)
offset = 0  # int | The initial index from which to return the results. (optional) (default to 0)
SHOW_GRID_DIALOG = True
SHOW_TEMPLATE_DIALOG = True
COMMAND_TIMEOUT = 15
MAX_THREAD_COUNT = 8
MAX_RETRY = 5
MAX_RECENT_ITEMS = 5
PRINT_RESPONSES = False
PRINT_FUNC_DURATION = False

DESCRIPTION = """Esper API Support Tool makes use of Esper's APIs to programmatically control and monitor 
your enterprise's Android-based Dedicated Devices providing features that are not currently
available on the Esper Console Dashboard."""

DEVS = ["Jonathan Featherston", "James Schaefer", "Chris Stirrat"]

""" Actions """
GENERAL_ACTIONS = [
    "",
    "Show - Device Info & Network And Secruity Report",
    "Action -> Set Kiosk Mode",
    "Action -> Set Multi-App Mode",
]
SHOW_ALL_AND_GENERATE_REPORT = 1
SET_KIOSK = 2
SET_MULTI = 3

GRID_ACTIONS = [
    "",
    "Action -> Modify Device Alias & Tags",
]
MODIFY_ALIAS_AND_TAGS = 1

LOGLIST = []

COMMAND_ARGS = [
    "app_state",
    "app_version",
    "device_alias_name",
    "message",
    "package_name",
    "policy_url",
    "state",
    "wifi_access_points",
]

COMMAND_TYPES = [
    "REBOOT",
    "UPDATE_HEARTBEAT",
    "UPDATE_DEVICE_CONFIG",
    # "INSTALL",
    # "UNINSTALL",
    "SET_NEW_POLICY",
    "ADD_WIFI_AP",
    "REMOVE_WIFI_AP",
    "SET_KIOSK_APP",
    "SET_DEVICE_LOCKDOWN_STATE",
    "SET_APP_STATE",
    "WIPE",
    "UPDATE_LATEST_DPC",
]

""" URL Requests and Extensions """
BASE_REQUEST_URL = "{configuration_host}/enterprise/{enterprise_id}/device/{device_id}"
BASE_REQUEST_EXTENSION = "/?&format=json"
DEVICE_STATUS_REQUEST_EXTENSION = "/status?&format=json&latest_event=0"
DEVICE_APP_LIST_REQUEST_EXTENSION = "/install?&format=json"

""" CSV Headers """
CSV_DEPRECATED_HEADER_LABEL = ["Number"]
CSV_EDITABLE_COL = ["Alias", "Tags"]
CSV_TAG_ATTR_NAME = {
    "Esper Name": "EsperName",
    "Alias": "Alias",
    "Brand": "brand",
    "Model": "model",
    "Android Version": "androidVersion",
    "Status": "Status",
    "Mode": "Mode",
    "Serial": "Serial",
    "IMEI 1": "imei1",
    "IMEI 2": "imei2",
    "Tags": "Tags",
    "Applications": "Apps",
    "Pinned App": "KioskApp",
    "Is GMS": "is_gms",
}
CSV_NETWORK_ATTR_NAME = {
    "Device Name": "EsperName",
    "Security Patch": "securityPatchLevel",
    "[WIFI ACCESS POINTS]": "",
    "[Current WIFI Connection]": "",
    "[Cellular Access Point]": "",
    "Active Connection": "",
    "IP Address": "ipAddress",
    "Bluetooth State": "bluetoothState",
    "Paired Devices": "pairedDevices",
    "Connected Devices": "connectedDevices",
}

""" WxPython Frame """
frame = None
app = None

""" CSV Save File """
csv_auth_path = ""
# GRID_DEVICE_INFO_LIST = []

LAST_DEVICE_ID = None
LAST_GROUP_ID = None
GRID_UPDATE_RATE = 60
MAX_GRID_UPDATE_RATE = 3600
ENABLE_GRID_UPDATE = True
MAX_UPDATE_COUNT = 500
