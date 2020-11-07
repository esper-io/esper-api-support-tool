import esperclient

configuration = esperclient.Configuration()
enterprise_id = ""

limit = 500000  # int | Number of results to return per page. (optional) (default to 20)
offset = 0  # int | The initial index from which to return the results. (optional) (default to 0)

GENERAL_ACTIONS = [
    # "Show - Device information",
    # "Show - Applications on Device",
    # "Show - Names/Tags loaded from file",
    "Show - Device Info",
    "Show -> Network And Secruity Report",
    "Action -> Set Kiosk Mode",
    "Action -> Set Multi-App Mode"
    # "Action -> Add Device Tags <from loaded file>",
    # "Action -> Remove Device Tags <from loaded file>",
]

GRID_ACTIONS = [
    "Action -> Set Device Names",
    "Action -> Modify Tags",
]

CONFIGFILE = "EsperGroupActionsConfig.csv"
# SHOW_DEVICES = 0
# SHOW_APP_VERSION = 1
# SHOW_NamesAndTags = 0
SHOW_ALL = 0
GENERATE_REPORT = 1
SET_KIOSK = 2
SET_MULTI = 3

SET_ALIAS = 0
MODIFY_TAGS = 1
# SET_TAGS = 5
# REMOVE_TAGS = 6

LOGLIST = []
TAGSandALIASES = {}

LOGFILE = "EsperGroupActionLog"
NAMESTAGSFILE = "EsperGroupActionsNamesTags.csv"

BASE_REQUEST_URL = "{configuration_host}/enterprise/{enterprise_id}/device/{device_id}"
BASE_REQUEST_EXTENSION = "/?&format=json"
DEVICE_STATUS_REQUEST_EXTENSION = "/status?&format=json&latest_event=0"
DEVICE_APP_LIST_REQUEST_EXTENSION = "/install?&format=json"

CSV_TAG_HEADER = (
    "Esper Name,Alias,Online,Mode,Serial,Tags,Applications,Pinned App,Bluetooth State"
    + "\n"
)
CSV_DEPRECATED_HEADER_LABEL = ["Number"]
CSV_TAG_ATTR_NAME = {
    "Esper Name": "EsperName",
    "Alias": "Alias",
    "Online": "Status",
    "Mode": "Mode",
    "Serial": "Serial",
    "Tags": "Tags",
    "Applications": "Apps",
    "Pinned App": "KioskApp",
    "Bluetooth State": "bluetoothState",
}
CSV_EDITABLE_COL = [
    "Alias",
    "Tags"
]
CSV_NETWORK_ATTR_NAME = [
    "Device Name","Security Patch","[WIFI ACCESS POINTS]","[Current WIFI Connection]","[Cellular Access Point]","Active Connection","Bluetooth State"
]
CSV_SECURITY_WIFI_HEADER = (
    "Device Name,Security Patch,[WIFI ACCESS POINTS],[Current WIFI Connection],[Cellular Access Point],Active Connection,Bluetooth State"
    + "\n"
)

header_format = ""

frame = None
app = None

new_output_to_save = ""

csv_tag_path = ""
csv_tag_path_clone = ""
csv_auth_path = ""

url_blacklist = ""
