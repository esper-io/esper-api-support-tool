#!/usr/bin/env python

import os
import platform
import threading

import esperclient

from Common.enum import GeneralActions, GridActions
from Utility.Threading.ThreadPoolQueue import Pool

configuration = esperclient.Configuration()
enterprise_id = ""

IS_DEBUG = False

API_LOGGER = None

""" Constants """
VERSION = "v0.19522"
TITLE = "Esper API Support Tool"
RECORD_PLACE = False
MIN_LIMIT = 50
MAX_LIMIT = 250
MIN_SIZE = (900, 700)
MAX_TAGS = 5
error_tracker = {}
IS_TOKEN_VALID = False
TOKEN_USER = None

MAX_DEVICE_COUNT = 5000

MAX_ERROR_TIME_DIFF = 2
MAX_THREAD_COUNT = 20
MAX_RETRY = 5
RETRY_SLEEP = 3
MAX_STATUS_CHAR = 80
PRINT_RESPONSES = False
PRINT_FUNC_DURATION = False
PRINT_API_LOGS = False

MAX_NUMBER_OF_SHEETS_PER_FILE = 255
SHEET_CHUNK_SIZE = 500000
MIN_SHEET_CHUNK_SIZE = 50000
MAX_SHEET_CHUNK_SIZE = 1000000

THREAD_POOL = Pool(MAX_THREAD_COUNT)
if THREAD_POOL:
    THREAD_POOL.run()

DESCRIPTION = """Esper API Support Tool makes use of Esper's APIs to programmatically control and monitor
your enterprise's Android-based Dedicated Devices providing features that are not currently
available on the Esper Console Dashboard."""

TERMS_AND_CONDITIONS = """
<html><body><p>This Beta Services Addendum (“<strong>Beta Terms</strong>”) describes your rights and responsibilities when accessing the Beta Services. By using a Beta Service, you:</p>
<ul><li><p>agree to the following terms on behalf of the Esper customer with which you are employed, affiliated or associated (“<strong>Customer</strong>”),</p></li>
<li><p>represent that you have the authority to bind Customer to these Beta Terms, and</p></li>
<li><p>represent that you are an Authorized User under the Terms of Service found at https://www.esper.io/terms-of-service or other written agreement between Esper and Customer governing provision and use of the Solution, Services, or other similar operative term for Esper service (as referenced herein, the “<strong>Services</strong>”) (the “<strong>Agreement</strong>”).</p></li></ul>
<p>If you do not have such authority or do not agree to these Beta Terms, you may not use the Beta Services. These Beta Terms are an addendum to and form a part of the Agreement. To the extent of any conflict or inconsistency between the provisions in these Beta Terms and the Agreement, these Beta Terms shall control. Capitalized terms used but not defined herein shall have the meaning ascribed in the Agreement.</p>
<ol><li><p><strong>Beta Services.</strong> From time to time, Esper may make certain Services, features or functionality available to Customer, at no charge, which may be designated by Esper as a beta, pilot, limited release, developer preview, non-production, evaluation, or by a similar description, to be used in conjunction with or separate from the Services, as applicable (each, a “<strong>Beta Service</strong>” and collectively, the “<strong>Beta Services</strong>”). Pursuant to the terms hereof, Esper agrees to allow Customer to use the Beta Services and Customer may choose to use such Beta Services or not in its sole discretion. Beta Services are not generally available, may contain bugs and errors, and may be subject to additional terms as set forth in any associated documentation.</p></li>
<li><p><strong>No Performance or Uptime Warranties.</strong> NOTWITHSTANDING ANYTHING TO THE CONTRARY IN THE AGREEMENT, CUSTOMER ACKNOWLEDGES AND AGREES THAT THE BETA SERVICES ARE PROVIDED “AS-IS” WITH RESPECT TO THEIR PERFORMANCE, SPEED, FUNCTIONALITY, SUPPORT, AND AVAILABILITY AND ESPER WILL HAVE NO LIABILITY OR OBLIGATION FOR ANY HARM OR DAMAGE ARISING FROM DEFICIENCIES THEREWITH OR RESULTING FROM ANY USE OF BETA SERVICES.</p></li>
<li><p><strong>Confidentiality.</strong> Customer agrees that any associated functionality or product information; any features or functions that are disclosed by Esper to Customer and are not publicly available including, without limitation, non-public or pre-release tools, products, environments or APIs and any associated documentation, and any and all data or information contained therein (“<strong>Esper Proprietary Elements</strong>”); and Customer’s participation in the Beta Services program constitute Esper’s Confidential Information, as defined in the Agreement. This “Confidentiality” section shall survive termination of these Beta Terms and shall continue to apply to the Esper Proprietary Elements unless and until the Esper Proprietary Elements become generally available to the public without restriction and through no fault of Customer or any of its Affiliates, agents, consultants or employees.</p></li>
<li><p><strong>Term and Termination.</strong> Notwithstanding anything to the contrary in the Agreement, these Beta Terms commence on the date you indicate your acceptance to the Beta Terms, or enable or use a Beta Service, whichever is earliest. Customer acknowledges and agrees that Esper may discontinue making any particular Beta Service available to Customer at any time in its sole discretion, and may never make the Beta Service generally available as part of, or an add-on to, the Services, and that its decision to purchase the Services was not and is not contingent on the delivery of any future functionality or features within the Beta Services.</p></li></ol></body></html>
"""

HAS_INTERNET = None

""" Locks """
lock = threading.Lock()
error_lock = threading.Lock()
msg_lock = threading.Lock()
api_log_lock = threading.Lock()
gauge_lock = threading.Lock()
grid1_lock = threading.Lock()
grid2_lock = threading.Lock()
grid3_lock = threading.Lock()
token_lock = threading.Lock()
join_lock = threading.Lock()

# Known Group Var
knownGroups = {}

# Known Blueprints
knownBlueprints = {}

OPEN_DIALOGS = []

""" Actions """
NUM_STARS = 8 if platform.system() == "Windows" else 3
GENERAL_ACTIONS = {
    ("\t" if platform.system() == "Windows" else "")
    + "* " * NUM_STARS
    + "Generate Report "
    + "* " * NUM_STARS: -1,
    "Generate All Reports": GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value,
    "Generate Device Report": GeneralActions.GENERATE_DEVICE_REPORT.value,
    "Generate Device & Network Report": GeneralActions.GENERATE_INFO_REPORT.value,
    "Generate App Report": GeneralActions.GENERATE_APP_REPORT.value,
    ("\t" if platform.system() == "Windows" else "")
    + "* " * NUM_STARS
    + "General Actions "
    + "* " * NUM_STARS: -1,
    "Action -> Set Device Mode": 1.5,
    "Action -> Clear App Data": GeneralActions.CLEAR_APP_DATA.value,
    "Action -> Set App's State to ...": GeneralActions.SET_APP_STATE.value,
    "Action -> Remove Non-Whitelisted Wifi Access Point": GeneralActions.REMOVE_NON_WHITELIST_AP.value,
    "Action -> Move Selected Device(s) to new Group": GeneralActions.MOVE_GROUP.value,
    "Action -> Install App": GeneralActions.INSTALL_APP.value,
    "Action -> Uninstall App": GeneralActions.UNINSTALL_APP.value,
}

GRID_ACTIONS = {
    ("\t" if platform.system() == "Windows" else "")
    + "* " * NUM_STARS
    + "Grid Actions "
    + "* " * NUM_STARS: -1,
    "Action -> Modify Device Alias": GridActions.MODIFY_ALIAS.value,
    "Action -> Modify Device Tags": GridActions.MODIFY_TAGS.value,
    "Action -> Set All Apps' State to ...": GridActions.SET_APP_STATE.value,
    "Action -> Move Device(s) to new Group": GridActions.MOVE_GROUP.value,
    "Action -> Install Selected App": GridActions.INSTALL_APP.value,
    "Action -> Uninstall Selected App": GridActions.UNINSTALL_APP.value,
    # "Action -> Remove Selected Devices From Dashboard": GridActions.SET_DEVICE_DISABLED.value,
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
    # "SET_KIOSK_APP",
    # "SET_DEVICE_LOCKDOWN_STATE",
    # "SET_APP_STATE",
    # "WIPE",
    # "UPDATE_LATEST_DPC",
]

JSON_COMMAND_TYPES = [
    "REBOOT",
    "UPDATE_HEARTBEAT",
    "UPDATE_DEVICE_CONFIG",
    # "SET_NEW_POLICY",
    # "ADD_WIFI_AP",
    # "REMOVE_WIFI_AP",
    # "SET_KIOSK_APP",
    # "SET_DEVICE_LOCKDOWN_STATE",
    # "SET_APP_STATE",
    # "WIPE",
    # "UPDATE_LATEST_DPC",
]

""" URL Requests and Extensions """
ESPER_LINK = "https://esper.io/"
HELP_LINK = "https://github.com/esper-io/esper-api-support-tool/wiki"
LATEST_UPDATE_LINK = (
    "https://api.github.com/repos/esper-io/esper-api-support-tool/releases/latest"
)
UPDATE_LINK = "https://api.github.com/repos/esper-io/esper-api-support-tool/releases"
BASE_REQUEST_URL = "{configuration_host}/enterprise/{enterprise_id}/"
BASE_DEVICE_URL = BASE_REQUEST_URL + "device/{device_id}/"
BASE_REQUEST_EXTENSION = "/?&format=json"
DEVICE_STATUS_REQUEST_EXTENSION = "status/?&format=json&latest_event=0"
DEVICE_ENTERPRISE_APP_LIST_REQUEST_EXTENSION = "app/?limit={limit}&app_type=ENTERPRISE"
DEVICE_APP_LIST_REQUEST_EXTENSION = "app/?limit={limit}&format=json"

""" CSV Headers """

CSV_TAG_ATTR_NAME = {
    "Esper Name": ["EsperName", "name"],
    "Alias": ["Alias", "alias"],
    "Group": "groups",
    "Brand": "brand",
    "Manufacturer": "manufacturer",
    "Model": "model",
    "Hardware Chip Set": "hardware",
    "OS": "os",
    "OS Version": ["androidVersion", "os_version"],
    "Build Number": ["androidBuildNumber", "os_build_number"],
    "Registered On": ["provisioned_on", "onboarded_on"],
    "Updated On": ["updated_on", "updated_at"],
    "Created On": ["created_on", "created_at"],
    "Last Seen": "last_seen",
    # "State": "Status",
    "Esper Version": "esper_client",
    "Foundation Version": "eeaVersion",
    "Is EMM": "is_emm",
    "Managed By": "managed_by",
    "Template": "template_name",
    "Template Device Language": "templateDeviceLocale",
    "Assigned Blueprint": "assigned_blueprint_id",
    "Current Blueprint": "current_blueprint_id",
    "Current Blueprint Version": "current_blueprint_version_id",
    "Policy": "policy_name",
    "Mode": "Mode",
    "Lockdown State": "lockdown_state",
    "Serial Number": ["Serial", "serial"],
    "Custom Serial Number": "Custom Serial",
    "IMEI 1": "imei1",
    "IMEI 2": "imei2",
    "Phone Number 1": "phoneNumber1",
    "Phone Number 2": "phoneNumber2",
    "ICCID 1": "iccid1",
    "ICCID 2": "iccid2",
    "Is Knox Active": "isKnoxActive",
    "Is CSDK Active": "isCSDKActive",
    "Is Supervisor Plugin Active": "isSupervisorPluginActive",
    "Tags": "Tags",
    "Applications": "Apps",
    "Pinned App": "KioskApp",
    "Is GMS": "is_gms",
    "Device Type": ["device_type", "device_source"],
    "Available RAM (MB)": "AVAILABLE_RAM_MEASURED",
    "Total RAM (MB)": "totalRam",
    "Storage Occupied by OS (MB)": "OS_OCCUPIED_STORAGE_MEASURED",
    "Available Internal Storage (MB)": "AVAILABLE_INTERNAL_STORAGE_MEASURED",
    "Total Internal Storage (MB)": "totalInternalStorage",
    # "Audio Contraints": "audio_constraints",
    "Timezone": "timezone_string",
    "GPS State": "gpsState",
    "Location Coordinates (Alt, Lat., Long.)": "location_info",
    "Rotation": "rotationState",
    "Brightness": "brightnessScale",
    "Screen Timeout (ms)": "screenOffTimeout",
    "Music Volume": "STREAM_MUSIC",
    "Ring Volume": "STREAM_RING",
    "Alarm Volume": "STREAM_ALARM",
    "Notification Volume": "STREAM_NOTIFICATION",
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
    "Esper Id": "id",
    "Group Id": "groupId",
}
CSV_NETWORK_ATTR_NAME = {
    "Esper Name": "EsperName",
    "Group": "groups",
    "Security Patch": ["securityPatchLevel", "security_patch_level"],
    "[WIFI ACCESS POINTS]": "wifiAP",
    "[Current WIFI Connection]": "currentWifi",
    "Ethernet Connection": "ethernetState",
    "[Cellular Access Point]": "cellAP",
    "Active Connection": "activeConnection",
    "IPv4 Address(es)": "ipv4Address",
    "IPv6 Address(es)": "ipv6Address",
    "Bluetooth State": "bluetoothState",
    "Paired Devices": "pairedDevices",
    "Connected Devices": "connectedDevices",
    "Wifi Mac Id": "wifiMacAddress",
    "IPv6 Mac Address(es)": "macAddress",
    # "Signal Strength": "signalStrength",
    "DNS": "dns",
    "Frequency": "frequency",
    "linkSpeed": "linkSpeed",
    "Data Speed Down": "dataSpeedDown",
    "Data Speed Up": "dataSpeedUp",
}
CSV_APP_ATTR_NAME = [
    "Esper Name",
    "Group",
    "Application Name",
    "Application Type",
    "Application Version Code",
    "Application Version Name",
    "Package Name",
    "State",
    "Whitelisted",
    "Can Clear Data",
    "Can Uninstall",
]

SEMANTIC_VERSION_COL = [
    "Android Version",
    "Application Version Code",
    "Application Version Name"
]

DATE_COL = {
    "Security Patch": "%Y/%m/%d",
    "Registered On": "%Y/%m/%d %H:%M:%S.%f",
    "Updated On": "%Y/%m/%d %H:%M:%S.%f",
    "Created On": "%Y/%m/%d %H:%M:%S.%f",
    "Last Seen": "%Y/%m/%d %H:%M:%S.%f",
}

WHITELIST_AP = []

""" Static Lists """
CSV_DEPRECATED_HEADER_LABEL = ["Number"]
CSV_EDITABLE_COL = ["Alias", "Tags", "Group"]

BLACKLIST_PACKAGE_NAME = [
    "io.shoonya.shoonyadpc",
    "io.esper.remoteviewer",
    "io.shoonya.helper",
]

CMD_DEVICE_TYPES = ["All", "Active", "Inactive"]

APP_FILTER_TYPES = ["ALL", "SHOW", "HIDE", "DISABLE"]

EXCEPTION_MSGS = ["Not Able to Process CSV File! Missing HEADERS!"]

""" WxPython Frame """
frame = None
app = None

""" CSV Save File """
csv_auth_path = ""

""" Preferences """
# General Prefs
LAST_OPENED_ENDPOINT = -1
FONT_SIZE = 11
HEADER_FONT_SIZE = FONT_SIZE + 7
CHECK_PRERELEASES = False
AUTO_REPORT_ISSUES = False
SHOW_DISCLAIMER = True

# Save Prefs
SAVE_VISIBILITY = False
COMBINE_DEVICE_AND_NETWORK_SHEETS = False

# Report Prefs
SHOW_DISABLED_DEVICES = False
INHIBIT_SLEEP = False
GET_DEVICE_LANGUAGE = False
APPS_IN_DEVICE_GRID = True

# Grid Prefs
REPLACE_SERIAL = True
LAST_SEEN_AS_DATE = True
VERSON_NAME_INSTEAD_OF_CODE = False
SHOW_GROUP_PATH = False

# App Prefs
SET_APP_STATE_AS_SHOW = False
USE_ENTERPRISE_APP = True
SHOW_PKG_NAME = False
COMMAND_TIMEOUT = 30
COMMAND_JSON_INPUT = True
REACH_QUEUED_ONLY = True
CMD_DEVICE_TYPE = "all"
APP_FILTER = "all"
ALIAS_DAY_DELTA = 14
ALIAS_MAX_DAY_DELTA = 356
APP_COL_FILTER = []

# Dialog Prefs
SHOW_GRID_DIALOG = True
SHOW_TEMPLATE_DIALOG = True
SHOW_TEMPLATE_UPDATE = True
SHOW_APP_FILTER_DIALOG = True

# Schedule Report
SCHEDULE_INTERVAL = 12
MIN_SCHEDULE_INTERVAL = 4
MAX_SCHEDULE_INTERVAL = 23
SCHEDULE_TYPE = "Device & Network"
SCHEDULE_ENABLED = False
SCHEDULE_LOCATION = os.getcwd()
SCHEDULE_SAVE = "xlsx"

limit = MAX_LIMIT  # Number of results to return per page
offset = 0  # The initial index from which to return the results
