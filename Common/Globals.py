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

""" Constants """
VERSION = "v0.19484"
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

SHEET_CHUNK_SIZE = 500000
MIN_SHEET_CHUNK_SIZE = 50000
MAX_SHEET_CHUNK_SIZE = 500000

IS_GENERATEING_EXE = False

THREAD_POOL = Pool(MAX_THREAD_COUNT) if not IS_GENERATEING_EXE else None
if THREAD_POOL:
    THREAD_POOL.run()

DESCRIPTION = """Esper API Support Tool makes use of Esper's APIs to programmatically control and monitor
your enterprise's Android-based Dedicated Devices providing features that are not currently
available on the Esper Console Dashboard."""

TERMS_AND_CONDITIONS = """
<html><body>
<h1>Terms and Conditions</h1>
<p>Last updated: March 27, 2023</p>
<p>Please read these terms and conditions carefully before using Our Service.</p>
<h1>Interpretation and Definitions</h1>
<h2>Interpretation</h2>
<p>The words of which the initial letter is capitalized have meanings defined under the following conditions. The following definitions shall have the same meaning regardless of whether they appear in singular or in plural.</p>
<h2>Definitions</h2>
<p>For the purposes of these Terms and Conditions:</p>
<ul>
<li>
<p><strong>Application</strong> means the software program provided by the Company downloaded by You on any electronic device, named Esper Api Support Tool</p>
</li>
<li>
<p><strong>Affiliate</strong> means an entity that controls, is controlled by or is under common control with a party, where &quot;control&quot; means ownership of 50% or more of the shares, equity interest or other securities entitled to vote for election of directors or other managing authority.</p>
</li>
<li>
<p><strong>Country</strong> refers to: Washington,  United States</p>
</li>
<li>
<p><strong>Company</strong> (referred to as either &quot;the Company&quot;, &quot;We&quot;, &quot;Us&quot; or &quot;Our&quot; in this Agreement) refers to Esper, 3600 136th Pl SE # 210, Bellevue, WA 98006.</p>
</li>
<li>
<p><strong>Device</strong> means any device that can access the Service such as a computer, a cellphone or a digital tablet.</p>
</li>
<li>
<p><strong>Service</strong> refers to the Application.</p>
</li>
<li>
<p><strong>Terms and Conditions</strong> (also referred as &quot;Terms&quot;) mean these Terms and Conditions that form the entire agreement between You and the Company regarding the use of the Service. This Terms and Conditions agreement has been created with the help of the <a href="https://www.termsfeed.com/terms-conditions-generator/" target="_blank">TermsFeed Terms and Conditions Generator</a>.</p>
</li>
<li>
<p><strong>You</strong> means the individual accessing or using the Service, or the company, or other legal entity on behalf of which such individual is accessing or using the Service, as applicable.</p>
</li>
</ul>
<h1>Acknowledgment</h1>
<p>These are the Terms and Conditions governing the use of this Service and the agreement that operates between You and the Company. These Terms and Conditions set out the rights and obligations of all users regarding the use of the Service.</p>
<p>Your access to and use of the Service is conditioned on Your acceptance of and compliance with these Terms and Conditions. These Terms and Conditions apply to all visitors, users and others who access or use the Service.</p>
<p>By accessing or using the Service You agree to be bound by these Terms and Conditions. If You disagree with any part of these Terms and Conditions then You may not access the Service.</p>
<p>Your access to and use of the Service is also conditioned on Your acceptance of and compliance with the Privacy Policy of the Company. Our Privacy Policy describes Our policies and procedures on the collection, use and disclosure of Your personal information when You use the Application or the Website and tells You about Your privacy rights and how the law protects You. Please read Our Privacy Policy carefully before using Our Service.</p>
<h1>Termination</h1>
<p>We may terminate or suspend Your access immediately, without prior notice or liability, for any reason whatsoever, including without limitation if You breach these Terms and Conditions.</p>
<p>Upon termination, Your right to use the Service will cease immediately.</p>
<h1>Limitation of Liability</h1>
<p>To the maximum extent permitted by applicable law, in no event shall the Company or its suppliers be liable for any special, incidental, indirect, or consequential damages whatsoever (including, but not limited to, damages for loss of profits, loss of data or other information, for business interruption, for personal injury, loss of privacy arising out of or in any way related to the use of or inability to use the Service, third-party software and/or third-party hardware used with the Service, or otherwise in connection with any provision of this Terms), even if the Company or any supplier has been advised of the possibility of such damages and even if the remedy fails of its essential purpose.</p>
<p>Some states do not allow the exclusion of implied warranties or limitation of liability for incidental or consequential damages, which means that some of the above limitations may not apply. In these states, each party's liability will be limited to the greatest extent permitted by law.</p>
<h1>&quot;AS IS&quot; and &quot;AS AVAILABLE&quot; Disclaimer</h1>
<p>The Service is provided to You &quot;AS IS&quot; and &quot;AS AVAILABLE&quot; and with all faults and defects without warranty of any kind. To the maximum extent permitted under applicable law, the Company, on its own behalf and on behalf of its Affiliates and its and their respective licensors and service providers, expressly disclaims all warranties, whether express, implied, statutory or otherwise, with respect to the Service, including all implied warranties of merchantability, fitness for a particular purpose, title and non-infringement, and warranties that may arise out of course of dealing, course of performance, usage or trade practice. Without limitation to the foregoing, the Company provides no warranty or undertaking, and makes no representation of any kind that the Service will meet Your requirements, achieve any intended results, be compatible or work with any other software, applications, systems or services, operate without interruption, meet any performance or reliability standards or be error free or that any errors or defects can or will be corrected.</p>
<p>Without limiting the foregoing, neither the Company nor any of the company's provider makes any representation or warranty of any kind, express or implied: (i) as to the operation or availability of the Service, or the information, content, and materials or products included thereon; (ii) that the Service will be uninterrupted or error-free; (iii) as to the accuracy, reliability, or currency of any information or content provided through the Service; or (iv) that the Service, its servers, the content, or e-mails sent from or on behalf of the Company are free of viruses, scripts, trojan horses, worms, malware, timebombs or other harmful components.</p>
<p>Some jurisdictions do not allow the exclusion of certain types of warranties or limitations on applicable statutory rights of a consumer, so some or all of the above exclusions and limitations may not apply to You. But in such a case the exclusions and limitations set forth in this section shall be applied to the greatest extent enforceable under applicable law.</p>
<h1>Governing Law</h1>
<p>The laws of the Country, excluding its conflicts of law rules, shall govern this Terms and Your use of the Service. Your use of the Application may also be subject to other local, state, national, or international laws.</p>
<h1>Disputes Resolution</h1>
<p>If You have any concern or dispute about the Service, You agree to first try to resolve the dispute informally by contacting the Company.</p>
<h1>For European Union (EU) Users</h1>
<p>If You are a European Union consumer, you will benefit from any mandatory provisions of the law of the country in which you are resident in.</p>
<h1>United States Legal Compliance</h1>
<p>You represent and warrant that (i) You are not located in a country that is subject to the United States government embargo, or that has been designated by the United States government as a &quot;terrorist supporting&quot; country, and (ii) You are not listed on any United States government list of prohibited or restricted parties.</p>
<h1>Severability and Waiver</h1>
<h2>Severability</h2>
<p>If any provision of these Terms is held to be unenforceable or invalid, such provision will be changed and interpreted to accomplish the objectives of such provision to the greatest extent possible under applicable law and the remaining provisions will continue in full force and effect.</p>
<h2>Waiver</h2>
<p>Except as provided herein, the failure to exercise a right or to require performance of an obligation under these Terms shall not effect a party's ability to exercise such right or require such performance at any time thereafter nor shall the waiver of a breach constitute a waiver of any subsequent breach.</p>
<h1>Translation Interpretation</h1>
<p>These Terms and Conditions may have been translated if We have made them available to You on our Service.
You agree that the original English text shall prevail in the case of a dispute.</p>
<h1>Changes to These Terms and Conditions</h1>
<p>We reserve the right, at Our sole discretion, to modify or replace these Terms at any time. If a revision is material We will make reasonable efforts to provide at least 30 days' notice prior to any new terms taking effect. What constitutes a material change will be determined at Our sole discretion.</p>
<p>By continuing to access or use Our Service after those revisions become effective, You agree to be bound by the revised terms. If You do not agree to the new terms, in whole or in part, please stop using the website and the Service.</p>
<h1>Contact Us</h1>
<p>If you have any questions about these Terms and Conditions, You can contact us:</p>
<ul>
<li>
<p>By email: support@esper.io</p>
</li>
<li>
<p>By visiting this page on our website: <a href="esper.io" rel="external nofollow noopener" target="_blank">esper.io</a></p>
</li>
<li>
<p>By mail: 3600 136th Pl SE # 210, Bellevue, WA 98006</p>
</li>
</ul>
</body></html>
"""

HAS_INTERNET = None

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
grid3_lock = threading.Lock()
token_lock = threading.Lock()

# Known Group Var
knownGroups = {}

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
    "Action -> Modify Device Alias & Tags": GridActions.MODIFY_ALIAS_AND_TAGS.value,
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
    "Esper Name": "EsperName",
    "Alias": "Alias",
    "Group": "groups",
    "Brand": "brand",
    "Model": "model",
    "Android Version": "androidVersion",
    "Android Build Number": "androidBuildNumber",
    "Status": "Status",
    "Esper Version": "esper_client",
    "Foundation Version": "eeaVersion",
    "Is EMM": "is_emm",
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
    "Registered On": "provisioned_on",
    "Updated On": "updated_on",
    "Created On": "created_on",
    "Last Seen": "last_seen",
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
    "Ringer Mode": "ringerMode",
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
    "Security Patch": "securityPatchLevel",
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

# Save Prefs
SAVE_VISIBILITY = False
COMBINE_DEVICE_AND_NETWORK_SHEETS = False

# Report Prefs
GROUP_FETCH_ALL = True
SHOW_DISABLED_DEVICES = False
INHIBIT_SLEEP = False

# Grid Prefs
MAX_GRID_LOAD = 100
REPLACE_SERIAL = True
LAST_SEEN_AS_DATE = True
APPS_IN_DEVICE_GRID = True
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
MATCH_SCROLL_POS = True
ALIAS_DAY_DELTA = 14
ALIAS_MAX_DAY_DELTA = 356
APP_COL_FILTER = []

# Dialog Prefs
SHOW_GRID_DIALOG = True
SHOW_TEMPLATE_DIALOG = True
SHOW_TEMPLATE_UPDATE = True

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
