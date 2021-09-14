#!/usr/bin/env python

import esperclient
import threading

from Common.enum import GridActions, GeneralActions

configuration = esperclient.Configuration()
enterprise_id = ""

""" Constants """
VERSION = "v0.189"
TITLE = "Esper API Support Tool"
RECORD_PLACE = False
MIN_LIMIT = 50
MAX_LIMIT = 500000
MAX_UPDATE_COUNT = 500
MIN_SIZE = (900, 700)
MAX_TAGS = 5
error_tracker = {}

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
    "Action -> Set App's State to ...": GeneralActions.SET_APP_STATE.value,
    "Action -> Remove Non-Whitelisted Wifi Acess Point": GeneralActions.REMOVE_NON_WHITELIST_AP.value,
    "Action -> Move Selected Device(s) to new Group": GeneralActions.MOVE_GROUP.value,
    "Action -> Install App": GeneralActions.INSTALL_APP.value,
    "Action -> Uninstall App": GeneralActions.UNINSTALL_APP.value,
}

GRID_ACTIONS = {
    "\t" + "* " * 8 + "Grid Actions " + "* " * 8: -1,
    "Action -> Modify Device Alias & Tags": GridActions.MODIFY_ALIAS_AND_TAGS.value,
    "Action -> Set All Apps' State to ...": GridActions.SET_APP_STATE.value,
    "Action -> Move Device(s) to new Group": GridActions.MOVE_GROUP.value,
    "Action -> Install Selected App": GridActions.INSTALL_APP.value,
    "Action -> Uninstall Selected App": GridActions.UNINSTALL_APP.value,
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
CSV_EDITABLE_COL = ["Alias", "Tags", "Group"]
CSV_TAG_ATTR_NAME = {
    # "Esper Id": "id",
    "Esper Name": "EsperName",
    "Alias": "Alias",
    "Group": "groups",
    "Subgroups": "subgroups",
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
    "Available RAM (MB)": "AVAILABLE_RAM_MEASURED",
    "Total RAM (MB)": "totalRam",
    "Storage Occupied by OS (MB)": "OS_OCCUPIED_STORAGE_MEASURED",
    "Available Internal Storage (MB)" : "AVAILABLE_INTERNAL_STORAGE_MEASURED",
    "Total Internal Storage (MB)": "totalInternalStorage",
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
    "Registered On": "provisioned_on",
    "Power Source": "powerSource",
    "Power Status": "powerStatus",
    "Battery Present": "batteryPresent",
    "Battery State": "batteryState",
    "Battery Health": "batteryHealth",
    "Battery Level (%)": "batteryLevel",
    "Battery Scale": "batteryScale",
    "Battery Current (μA)": "batteryCurrent",
    "Battery Current Avg. (μA)": "batteryCurrentAvg",
    "Battery Voltage (Volt)": "batteryVoltage",
    "Battery Energy Count": "batteryEnergyCount",
    "Battery Temperature (Celsius)": "batteryTemperature",
    "Battery Low Indicator": "batteryLowIndicator",
    "Battery Technology": "batteryTechnology",
    "Battery Capacity Count (%)": "batteryCapacityCount",
    "Battery Capacity Total (Ah)": "batteryCapacityTotal",
    "Battery Level Absolute": "batteryLevelAbsolute",
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
ALIAS_MAX_DAY_DELTA = 356
FONT_SIZE = 11
HEADER_FONT_SIZE = FONT_SIZE + 7
GET_IMMEDIATE_SUBGROUPS = False
SAVE_VISIBILITY = False
limit = MAX_LIMIT  # Number of results to return per page
offset = 0  # The initial index from which to return the results
