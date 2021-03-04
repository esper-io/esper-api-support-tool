#!/usr/bin/env python

import esperclient
import threading

configuration = esperclient.Configuration()
enterprise_id = ""

""" Constants """
VERSION = "v0.176"
TITLE = "Esper API Support Tool"
MIN_LIMIT = 1000
MAX_LIMIT = 500000
MAX_UPDATE_COUNT = 500
MIN_SIZE = (900, 700)
lock = threading.Lock()
gauge_lock = threading.Lock()
grid1_lock = threading.Lock()
grid2_lock = threading.Lock()

MAX_THREAD_COUNT = 8
MAX_RETRY = 5
MAX_STATUS_CHAR = 80
PRINT_RESPONSES = False
PRINT_FUNC_DURATION = False

DESCRIPTION = """Esper API Support Tool makes use of Esper's APIs to programmatically control and monitor 
your enterprise's Android-based Dedicated Devices providing features that are not currently
available on the Esper Console Dashboard."""

""" Actions """
GENERAL_ACTIONS = [
    "",
    "Show - Device Info & Network And Secruity Report",
    "Action -> Set Kiosk Mode",
    "Action -> Set Multi-App Mode",
    "Action -> Clear App Data"
    # "Action -> Power off Device",
]
SHOW_ALL_AND_GENERATE_REPORT = 1
SET_KIOSK = 2
SET_MULTI = 3
CLEAR_APP_DATA = 4
# POWER_OFF = 4

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
    # "SET_NEW_POLICY",
    # "ADD_WIFI_AP",
    # "REMOVE_WIFI_AP",
    "SET_KIOSK_APP",
    "SET_DEVICE_LOCKDOWN_STATE",
    "SET_APP_STATE",
    "WIPE",
    "UPDATE_LATEST_DPC",
]

""" URL Requests and Extensions """
ESPER_LINK = "https://esper.io/"
HELP_LINK = "https://docs.google.com/document/d/1WwDIQ-7CzQscVNFhiErbYtIwMyE34hGxE_MQWBqc9_k/edit#heading=h.50j8ygvoempc"
UPDATE_LINK = (
    "https://api.github.com/repos/esper-io/esper-api-support-tool/releases/latest"
)
BASE_REQUEST_URL = "{configuration_host}/enterprise/{enterprise_id}/"
BASE_DEVICE_URL = BASE_REQUEST_URL + "device/{device_id}/"
BASE_REQUEST_EXTENSION = "/?&format=json"
DEVICE_STATUS_REQUEST_EXTENSION = "/status?&format=json&latest_event=0"
DEVICE_ENTERPRISE_APP_LIST_REQUEST_EXTENSION = "/install?&format=json"
DEVICE_APP_LIST_REQUEST_EXTENSION = "/app?&format=json"

""" CSV Headers """
CSV_DEPRECATED_HEADER_LABEL = ["Number"]
CSV_EDITABLE_COL = ["Alias", "Tags"]
CSV_TAG_ATTR_NAME = {
    "Esper Name": "EsperName",
    "Alias": "Alias",
    "Group": "groups",
    "Brand": "brand",
    "Model": "model",
    "Android Version": "androidVersion",
    "Status": "Status",
    "Esper Version": "esper_client",
    "Mode": "Mode",
    "Serial Number": "Serial",
    "IMEI 1": "imei1",
    "IMEI 2": "imei2",
    "Tags": "Tags",
    "Applications": "Apps",
    "Pinned App": "KioskApp",
    "Is GMS": "is_gms",
}
CSV_NETWORK_ATTR_NAME = {
    "Device Name": "EsperName",
    "Group": "groups",
    "Security Patch": "securityPatchLevel",
    "[WIFI ACCESS POINTS]": "",
    "[Current WIFI Connection]": "",
    "[Cellular Access Point]": "",
    "Active Connection": "",
    "IP Address": "ipAddress",
    "Bluetooth State": "bluetoothState",
    "Paired Devices": "pairedDevices",
    "Connected Devices": "connectedDevices",
    "Wifi Mac Id": "wifiMacAddress",
    "IPv6 Mac Address(es)": "macAddress",
}

""" WxPython Frame """
frame = None
app = None

""" CSV Save File """
csv_auth_path = ""
# GRID_DEVICE_INFO_LIST = []

LAST_DEVICE_ID = None
LAST_GROUP_ID = None

""" Preferences """
COMMAND_TIMEOUT = 30
GRID_UPDATE_RATE = 60
MAX_GRID_UPDATE_RATE = 3600
ENABLE_GRID_UPDATE = False
USE_ENTERPRISE_APP = True
SHOW_PKG_NAME = False
REACH_QUEUED_ONLY = True
GET_APP_EACH_DEVICE = False
SHOW_GRID_DIALOG = True
SHOW_TEMPLATE_DIALOG = True
SHOW_TEMPLATE_UPDATE = True
limit = (
    MAX_LIMIT  # int | Number of results to return per page. (optional) (default to 20)
)
offset = 0  # int | The initial index from which to return the results. (optional) (default to 0)