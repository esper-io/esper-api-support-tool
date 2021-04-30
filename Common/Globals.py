#!/usr/bin/env python

import esperclient
import threading

from Common.enum import GridActions, GeneralActions

configuration = esperclient.Configuration()
enterprise_id = ""

""" Constants """
VERSION = "v0.182"
TITLE = "Esper API Support Tool"
RECORD_PLACE = False
MIN_LIMIT = 50
MAX_LIMIT = 500000
MAX_UPDATE_COUNT = 500
MIN_SIZE = (900, 700)
error_tracker = {}

MAX_ERROR_TIME_DIFF = 2
MAX_THREAD_COUNT = 20
MAX_RETRY = 5
RETRY_SLEEP = 1.5
MAX_STATUS_CHAR = 80
PRINT_RESPONSES = False
PRINT_FUNC_DURATION = False

DESCRIPTION = """Esper API Support Tool makes use of Esper's APIs to programmatically control and monitor 
your enterprise's Android-based Dedicated Devices providing features that are not currently
available on the Esper Console Dashboard."""

""" Locks """
lock = threading.Lock()
error_lock = threading.Lock()
msg_lock = threading.Lock()
gauge_lock = threading.Lock()
grid1_lock = threading.Lock()
grid1_status_lock = threading.Lock()
grid2_lock = threading.Lock()
grid_color_lock = threading.Lock()

""" Actions """
GENERAL_ACTIONS = {
    "\t" + "* " * 8 + "General Actions " + "* " * 8: -1,
    "Show - Device Info & Network And Security Report": GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value,
    "Action -> Set Kiosk Mode": GeneralActions.SET_KIOSK.value,
    "Action -> Set Multi-App Mode": GeneralActions.SET_MULTI.value,
    "Action -> Clear App Data": GeneralActions.CLEAR_APP_DATA.value,
    "Action -> Set App's State to Disable": GeneralActions.SET_APP_STATE_DISABLE.value,
    "Action -> Set App's State to Hide": GeneralActions.SET_APP_STATE_HIDE.value,
    "Action -> Set App's State to Show": GeneralActions.SET_APP_STATE_SHOW.value,
}

GRID_ACTIONS = {
    "\t" + "* " * 8 + "Grid Actions " + "* " * 8: -1,
    "Action -> Modify Device Alias & Tags": GridActions.MODIFY_ALIAS_AND_TAGS.value,
    "Action -> Set All Apps' State to Disable": GridActions.SET_APP_STATE_DISABLE.value,
    "Action -> Set All Apps' State to Hide": GridActions.SET_APP_STATE_HIDE.value,
    "Action -> Set All Apps' State to Show": GridActions.SET_APP_STATE_SHOW.value,
    # "Action -> Set Specific Apps' State to Hide": 50,
}

LOGLIST = []
MAX_LOG_LIST_SIZE = 75

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
    "SET_KIOSK_APP",
    "SET_DEVICE_LOCKDOWN_STATE",
    "SET_APP_STATE",
    "WIPE",
    "UPDATE_LATEST_DPC",
]

JSON_COMMAND_TYPES = [
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
    "Custom Serial Number": "Custom Serial",
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
BLACKLIST_PACKAGE_NAME = ["io.shoonya.shoonyadpc"]

CMD_DEVICE_TYPES = ["All", "Active", "Inactive"]

""" WxPython Frame """
frame = None
app = None

""" CSV Save File """
csv_auth_path = ""
# GRID_DEVICE_INFO_LIST = []

LAST_DEVICE_ID = None
LAST_GROUP_ID = None

""" Preferences """
SET_APP_STATE_AS_SHOW = False
COMMAND_TIMEOUT = 30
COMMAND_JSON_INPUT = True
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
CMD_DEVICE_TYPE = "all"
MATCH_SCROLL_POS = True
limit = (
    MAX_LIMIT  # int | Number of results to return per page. (optional) (default to 20)
)
offset = 0  # int | The initial index from which to return the results. (optional) (default to 0)
