import esperclient

configuration = esperclient.Configuration()
enterprise_id = ""

limit = 500000  # int | Number of results to return per page. (optional) (default to 20)
offset = 0  # int | The initial index from which to return the results. (optional) (default to 0)

ACTIONS = [
    "Show - Device information",
    "Show - Applications on Device",
    "Show - Names/Tags loaded from file",
    "Show - All Device Info",
    "Action -> Set Kiosk Mode",
    "Action -> Set Multi-App Mode",
    "Action -> Set Device Names <from loaded file>",
    "Action -> Add Device Tags <from loaded file>",
    "Action -> Remove Device Tags <from loaded file>",
    "Show -> Network And Secruity Report",
    "Action -> Apply URL Blacklist",
]

CONFIGFILE = "EsperGroupActionsConfig.csv"
SHOW_DEVICES = 0
SHOW_APP_VERSION = 1
SHOW_NamesAndTags = 2
SHOW_ALL = 3
SET_KIOSK = 4
SET_MULTI = 5
SET_ALIAS = 6
SET_TAGS = 7
REMOVE_TAGS = 8
GENERATE_REPORT = 9
URL_BLACKLIST = 10

LOGLIST = []
TAGSandALIASES = {}

LOGFILE = "EsperGroupActionLog"
NAMESTAGSFILE = "EsperGroupActionsNamesTags.csv"

BASE_REQUEST_URL = "{configuration_host}/enterprise/{enterprise_id}/device/{device_id}"
BASE_REQUEST_EXTENSION = "/?&format=json"
DEVICE_STATUS_REQUEST_EXTENSION = "/status?&format=json&latest_event=0"
DEVICE_APP_LIST_REQUEST_EXTENSION = "/install?&format=json"

CSV_TAG_HEADER = (
    "Number,EsperName,Alias,OnLine,Mode,Serial,Tags,Applications,Pinned App, Bluetooth State" + "\n"
)
CSV_SECURITY_WIFI_HEADER = (
    "Device Name,Security Patch,[WIFI ACCESS POINTS],[Current WIFI Connection],[Cellular Access Point],Active Connection"
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
