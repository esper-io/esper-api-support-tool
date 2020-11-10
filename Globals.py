import esperclient

configuration = esperclient.Configuration()
enterprise_id = ""

""" Constants """
TITLE = "Esper API Tool"
CONFIGFILE = "EsperGroupActionsConfig.csv"
# LOGFILE = "EsperGroupActionLog"
NAMESTAGSFILE = "EsperGroupActionsNamesTags.csv"
limit = 500000  # int | Number of results to return per page. (optional) (default to 20)
offset = 0  # int | The initial index from which to return the results. (optional) (default to 0)
SHOW_GRID_DIALOG = True

""" Actions """
GENERAL_ACTIONS = [
    "Show - Device Info & Network And Secruity Report",
    "Action -> Set Kiosk Mode",
    "Action -> Set Multi-App Mode",
]
SHOW_ALL_AND_GENERATE_REPORT = 0
SET_KIOSK = 1
SET_MULTI = 2

GRID_ACTIONS = [
    "Action -> Set Device Names",
    "Action -> Modify Tags",
]
SET_ALIAS = 0
MODIFY_TAGS = 1

LOGLIST = []
TAGSandALIASES = {}  # Unused?

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
    "Status": "Status",
    "Mode": "Mode",
    "Serial": "Serial",
    "Tags": "Tags",
    "Applications": "Apps",
    "Pinned App": "KioskApp",
    "Bluetooth State": "bluetoothState",
}
CSV_NETWORK_ATTR_NAME = [
    "Device Name",
    "Security Patch",
    "[WIFI ACCESS POINTS]",
    "[Current WIFI Connection]",
    "[Cellular Access Point]",
    "Active Connection",
    "Bluetooth State",
]

""" WxPython Frame """
frame = None
app = None

""" CSV Save File """
csv_tag_path = ""
csv_tag_path_clone = ""
csv_auth_path = ""
