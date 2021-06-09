#!/usr/bin/env python

import esperclient
import threading

from Common.enum import GridActions, GeneralActions

configuration = esperclient.Configuration()
enterprise_id = ""

""" Constants """
VERSION = "v0.185"
TITLE = "Esper API Support Tool"
RECORD_PLACE = False
MIN_LIMIT = 50
MAX_LIMIT = 500000
MAX_UPDATE_COUNT = 500
MIN_SIZE = (900, 700)
error_tracker = {}

API_REQUEST_SESSION_TRACKER = 0

MAX_ERROR_TIME_DIFF = 2
MAX_THREAD_COUNT = 16
MAX_RETRY = 5
RETRY_SLEEP = 1.5
MAX_STATUS_CHAR = 80
PRINT_RESPONSES = False
PRINT_FUNC_DURATION = False
PRINT_API_LOGS = False

DESCRIPTION = """Esper API Support Tool makes use of Esper's APIs to programmatically control and monitor 
your enterprise's Android-based Dedicated Devices providing features that are not currently
available on the Esper Console Dashboard."""

""" Locks """
lock = threading.Lock()
error_lock = threading.Lock()
msg_lock = threading.Lock()
api_log_lock = threading.Lock()
gauge_lock = threading.Lock()
grid1_lock = threading.Lock()
grid1_status_lock = threading.Lock()
grid2_lock = threading.Lock()
grid_color_lock = threading.Lock()

""" Actions """
GENERAL_ACTIONS = {
    "\t" + "* " * 8 + "General Actions " + "* " * 8: -1,
    "Show Device Info & Network And Security Report": GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value,
    "Action -> Set Kiosk Mode": GeneralActions.SET_KIOSK.value,
    "Action -> Set Multi-App Mode": GeneralActions.SET_MULTI.value,
    "Action -> Clear App Data": GeneralActions.CLEAR_APP_DATA.value,
    "Action -> Set App's State to Disable": GeneralActions.SET_APP_STATE_DISABLE.value,
    "Action -> Set App's State to Hide": GeneralActions.SET_APP_STATE_HIDE.value,
    "Action -> Set App's State to Show": GeneralActions.SET_APP_STATE_SHOW.value,
    "Action -> Remove Non-Whitelisted Wifi Acess Point": GeneralActions.REMOVE_NON_WHITELIST_AP.value,
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

API_REQUEST_TRACKER = {
    "/application": 0,
    "/collection": 0,
    "/command": 0,
    "/content": 0,
    "/device/": 0,
    "/devicegroup": 0,
    "/v1/enterprise": 0,
    "/policy": 0,
    "/geofence": 0,
    "/GroupCommandsApi": 0,
    "/subscription": 0,
    "/token": 0,
    "/user": 0,
    "OtherAPI": 0,
    "/devicetemplate": 0,
}

API_FUNCTIONS = {
    "delete_app_version": "/application",
    "delete_application": "/application",
    "get_all_applications": "/application",
    "get_app_version": "/application",
    "get_app_versions": "/application",
    "get_application": "/application",
    "get_install_devices": "/application",
    "upload": "/application",
    "get_command": "/command",
    "run_command": "/command",
    "create_command": "/command",
    "get_command_request_status": "/command",
    "get_device_command_history": "/command",
    "list_command_request": "/command",
    "delete_content": "/content",
    "get_all_content": "/content",
    "get_content": "/content",
    "patch_content": "/content",
    "post_content": "/content",
    "get_all_devices": "/device/",
    "get_app_installs": "/device/",
    "get_device_app_by_id": "/device/",
    "get_device_apps": "/device/",
    "get_device_by_id": "/device/",
    "get_device_event": "/device/",
    "create_group": "/devicegroup",
    "delete_group": "/devicegroup",
    "get_all_groups": "/devicegroup",
    "get_group_by_id": "/devicegroup",
    "partial_update_group": "/devicegroup",
    "update_group": "/devicegroup",
    "get_enterprise": "/v1/enterprise",
    "partial_update_enterprise": "/v1/enterprise",
    "create_policy": "/policy",
    "delete_enterprise_policy": "/policy",
    "get_policy_by_id": "/policy",
    "list_policies": "/policy",
    "partialupdate_policy": "/policy",
    "update_policy": "/policy",
    "create_geofence": "/geofence",
    "delete_geofence": "/geofence",
    "get_all_geofences": "/geofence",
    "get_geofence": "/geofence",
    "partial_update_geofence": "/geofence",
    "update_geofence": "/geofence",
    "get_group_command": "/GroupCommandsApi",
    "run_group_command": "/GroupCommandsApi",
    "create_subscription": "/subscription",
    "delete_subscription": "/subscription",
    "get_all_subscriptions": "/subscription",
    "get_subscription": "/subscription",
    "get_token_info": "/token",
    "renew_token": "/token",
}

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
    # "Esper Id": "id",
    "Esper Name": "EsperName",
    "Alias": "Alias",
    "Group": "groups",
    "Brand": "brand",
    "Model": "model",
    "Android Version": "androidVersion",
    "Android Build Number": "androidBuildNumber",
    "Status": "Status",
    "Esper Version": "esper_client",
    "Template": "template_name",
    "Policy": "policy_name",
    "Mode": "Mode",
    "Lockdown State": "lockdown_state",
    "Serial Number": "Serial",
    "Custom Serial Number": "Custom Serial",
    "IMEI 1": "imei1",
    "IMEI 2": "imei2",
    "Tags": "Tags",
    "Applications": "Apps",
    "Pinned App": "KioskApp",
    "Is GMS": "is_gms",
    "Device Type": "device_type",
    "Total RAM": "totalRam",
    "Total Internal Storage": "totalInternalStorage",
    # "Audio Contraints": "audio_constraints",
    "Timezone": "timezone_string",
    "Location": "location_info",
    "Rotation": "rotationState",
    "Brightness": "brightnessScale",
    "Screen Timeout (ms)": "screenOffTimeout",
    "Ringer Mode": "ringerMode",
    "Music Volume": "STREAM_MUSIC",
    "Ring Volume": "STREAM_RING",
    "Alarm Volume": "STREAM_ALARM",
    "Notification Volume": "STREAM_NOTIFICATION",
}
CSV_NETWORK_ATTR_NAME = {
    "Device Name": "EsperName",
    "Group": "groups",
    "Security Patch": "securityPatchLevel",
    "[WIFI ACCESS POINTS]": "",
    "[Current WIFI Connection]": "",
    "Ethernet Connection": "ethernetState",
    "[Cellular Access Point]": "",
    "Active Connection": "",
    "IPv4 Address(es)": "ipv4Address",
    "IPv6 Address(es)": "ipv6Address",
    "Bluetooth State": "bluetoothState",
    "Paired Devices": "pairedDevices",
    "Connected Devices": "connectedDevices",
    "Wifi Mac Id": "wifiMacAddress",
    "IPv6 Mac Address(es)": "macAddress",
    # "Signal Strength": "signalStrength",
    "Frequency": "frequency",
    "linkSpeed": "linkSpeed",
    "Data Speed Down": "dataSpeedDown",
    "Data Speed Up": "dataSpeedUp",
}
BLACKLIST_PACKAGE_NAME = ["io.shoonya.shoonyadpc"]
WHITELIST_AP = []

CMD_DEVICE_TYPES = ["All", "Active", "Inactive"]

""" WxPython Frame """
frame = None
app = None

""" CSV Save File """
csv_auth_path = ""

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
ALIAS_DAY_DELTA = 14
ALIAS_MAX_DAY_DELTA = 56
FONT_SIZE = 11
HEADER_FONT_SIZE = FONT_SIZE + 7
limit = (
    MAX_LIMIT  # int | Number of results to return per page. (optional) (default to 20)
)
offset = 0  # int | The initial index from which to return the results. (optional) (default to 0)
