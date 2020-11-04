import wx
import wx.grid
import esperclient
import time
import csv
import os.path
import platform
import logging
import Globals
import platform
import ctypes
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from esperclient import EnterpriseApi, ApiClient
from esperclient.rest import ApiException
from EsperAPICalls import TakeAction


class NewFrameLayout(wx.Frame):
    def __init__(self, *args, **kwds):
        self.configMenuOptions = []
        self.WINDOWS = True
        if platform.system() == "Windows":
            self.WINDOWS = True
        else:
            self.WINDOWS = False
        self.auth_csv_reader = None
        self.configChoice = {}

        self.csvHeaders = [
            "Number",
            "EsperName",
            "Alias",
            "Online",
            "Mode",
            "Serial",
            "Tags",
            "Applications",
            "Pinned App",
        ]

        # begin wxGlade: MyFrame.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((1552, 840))
        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.panel_3 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.configList = wx.TextCtrl(
            self.panel_3, wx.ID_ANY, style=wx.TE_MULTILINE | wx.TE_READONLY
        )
        self.groupChoice = wx.ComboBox(
            self.panel_1, wx.ID_ANY, choices=[], style=wx.CB_READONLY
        )
        self.deviceChoice = wx.ComboBox(
            self.panel_1, wx.ID_ANY, choices=[], style=wx.CB_READONLY
        )
        self.choice_1 = wx.Choice(self.panel_1, wx.ID_ANY, choices=[""])
        self.appChoice = wx.ComboBox(
            self.panel_1, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN
        )
        self.button_1 = wx.Button(self.panel_1, wx.ID_ANY, "Run on Group")
        self.button_2 = wx.Button(self.panel_1, wx.ID_ANY, "Run on Device")
        self.panel_2 = wx.Panel(self, wx.ID_ANY)
        self.loggingList = wx.ListBox(
            self.panel_2, wx.ID_ANY, choices=[""], style=wx.LB_NEEDED_SB
        )
        self.grid_1 = wx.grid.Grid(self.panel_2, wx.ID_ANY, size=(1, 1))

        self.Bind(wx.EVT_BUTTON, self.runActionOnGroup, self.button_1)
        self.Bind(wx.EVT_BUTTON, self.runActionOnDevice, self.button_2)

        self.configList.SetFont(
            wx.Font(
                11,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "",
            )
        )
        self.loggingList.SetFont(
            wx.Font(
                11,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "",
            )
        )

        # Menu Bar
        self.menubar = wx.MenuBar()

        fileMenu = wx.Menu()
        fileOpenAuth = fileMenu.Append(wx.ID_OPEN, "Open Auth CSV", "Open Auth CSV")
        fileOpenConfig = fileMenu.Append(
            wx.ID_APPLY, "Open Device CSV", "Open Device CSV"
        )
        fileMenu.Append(wx.ID_SEPARATOR)
        fileSave = fileMenu.Append(wx.ID_SAVE, "Save As", "Save As")
        fileMenu.Append(wx.ID_SEPARATOR)
        fileItem = fileMenu.Append(wx.ID_EXIT, "Quit", "Quit application")

        consoleMenu = wx.Menu()
        clearConsole = consoleMenu.Append(wx.ID_RESET, "Clear", "Clear Console")

        self.configMenu = wx.Menu()
        self.configMenuOptions.append(
            self.configMenu.Append(
                wx.ID_NONE, "No Loaded Configurations", "No Loaded Configurations"
            )
        )

        runMenu = wx.Menu()
        run = runMenu.Append(wx.ID_RETRY, "Run", "Run")

        self.menubar.Append(fileMenu, "&File")
        self.menubar.Append(self.configMenu, "&Configurations")
        self.menubar.Append(consoleMenu, "&Console")
        self.menubar.Append(runMenu, "&Run")
        self.SetMenuBar(self.menubar)

        self.Bind(wx.EVT_MENU, self.OnOpen, fileOpenAuth)
        self.Bind(wx.EVT_MENU, self.onUploadCSV, fileOpenConfig)
        self.Bind(wx.EVT_MENU, self.OnQuit, fileItem)
        self.Bind(wx.EVT_MENU, self.onSave, fileSave)
        self.Bind(wx.EVT_MENU, self.onClear, clearConsole)
        self.Bind(wx.EVT_MENU, self.onRun, run)
        # Menu Bar end

        # Tool Bar
        # self.frame_toolbar = wx.ToolBar(self, -1)
        # self.SetToolBar(self.frame_toolbar)

        # qtool = self.frame_toolbar.AddTool(wx.ID_ANY, 'Quit', png)
        # otool = self.frame_toolbar.AddTool(wx.ID_ANY, 'Open Auth CSV',  wx.Bitmap('Images/openFile.png', wx.BITMAP_TYPE_ANY))
        # stool = self.frame_toolbar.AddTool(wx.ID_ANY, 'Save As',  wx.Bitmap('Images/save.png', wx.BITMAP_TYPE_ANY))
        # ctool = self.frame_toolbar.AddTool(wx.ID_ANY, 'Clear',  wx.Bitmap('Images/clear.png', wx.BITMAP_TYPE_ANY))

        # self.Bind(wx.EVT_TOOL, self.OnQuit, qtool)
        # self.Bind(wx.EVT_TOOL, self.OnOpen, otool)
        # self.Bind(wx.EVT_TOOL, self.onSave, stool)
        # self.Bind(wx.EVT_TOOL, self.onClear, ctool)
        # Tool Bar end

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MyFrame.__set_properties
        self.SetTitle("frame")
        self.SetBackgroundColour(wx.Colour(192, 192, 192))
        self.choice_1.SetSelection(0)
        self.grid_1.CreateGrid(0, len(self.csvHeaders))
        # self.frame_toolbar.Realize()
        self.Maximize(True)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MyFrame.__do_layout
        sizer_1 = wx.GridSizer(1, 2, 0, 0)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_2 = wx.GridSizer(2, 1, 0, 0)
        grid_sizer_1 = wx.GridSizer(3, 1, 0, 0)
        grid_sizer_3 = wx.GridSizer(1, 1, 0, 0)
        grid_sizer_4 = wx.GridSizer(1, 2, 0, 0)
        label_1 = wx.StaticText(
            self.panel_1,
            wx.ID_ANY,
            "Loaded Configuration:",
            style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END,
        )
        label_1.SetFont(
            wx.Font(
                11,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        label_1.Wrap(200)
        sizer_2.Add(label_1, 0, wx.EXPAND, 0)
        grid_sizer_3.Add(self.configList, 0, wx.EXPAND, 0)
        self.panel_3.SetSizer(grid_sizer_3)
        sizer_2.Add(self.panel_3, 1, wx.EXPAND, 0)
        grid_sizer_1.Add(sizer_2, 0, wx.EXPAND, 0)
        label_2 = wx.StaticText(
            self.panel_1,
            wx.ID_ANY,
            "Choose a Group to take Action on:",
            style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END,
        )
        label_2.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        sizer_3.Add(label_2, 0, wx.EXPAND, 0)
        sizer_3.Add(self.groupChoice, 0, wx.ALL | wx.EXPAND, 0)
        sizer_3.Add((20, 20), 0, wx.EXPAND, 0)
        label_device = wx.StaticText(
            self.panel_1,
            wx.ID_ANY,
            "Choose a Device to take Action on:",
            style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END,
        )
        label_device.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        sizer_3.Add(label_device, 0, wx.EXPAND, 0)
        sizer_3.Add(self.deviceChoice, 0, wx.ALL | wx.EXPAND, 0)
        sizer_3.Add((20, 20), 0, wx.EXPAND, 0)
        label_3 = wx.StaticText(
            self.panel_1,
            wx.ID_ANY,
            "Action to apply to Devices in Group:",
            style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END,
        )
        label_3.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        sizer_3.Add(label_3, 0, wx.EXPAND, 0)
        sizer_3.Add(self.choice_1, 0, wx.EXPAND, 0)
        sizer_3.Add((20, 20), 0, wx.EXPAND, 0)
        label_4 = wx.StaticText(
            self.panel_1,
            wx.ID_ANY,
            "Application for Kiosk Mode:",
            style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END,
        )
        label_4.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        sizer_3.Add(label_4, 0, wx.EXPAND, 0)
        sizer_3.Add(self.appChoice, 0, wx.EXPAND, 0)
        grid_sizer_1.Add(sizer_3, 1, wx.EXPAND, 0)
        grid_sizer_4.Add(self.button_1, 0, wx.ALIGN_BOTTOM | wx.ALL | wx.EXPAND, 5)
        grid_sizer_4.Add(self.button_2, 0, wx.ALIGN_BOTTOM | wx.ALL | wx.EXPAND, 5)
        grid_sizer_1.Add(grid_sizer_4, 1, wx.EXPAND, 0)
        self.panel_1.SetSizer(grid_sizer_1)
        sizer_1.Add(self.panel_1, 1, wx.ALL | wx.EXPAND, 5)
        grid_sizer_2.Add(self.loggingList, 0, wx.EXPAND, 0)
        grid_sizer_2.Add(self.grid_1, 1, wx.EXPAND, 1)
        self.panel_2.SetSizer(grid_sizer_2)
        sizer_1.Add(self.panel_2, 0, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(sizer_1)
        self.Layout()
        # end wxGlade

    def scaleBitmapImage(self, width, height, path):
        image = wx.Bitmap(path).ConvertToImage()
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        result = wx.Bitmap(image)
        return result

    # Frame UI Logging
    def Logging(self, entry):
        """Logs Infromation To Frame UI"""
        self.loggingList.Append(entry)
        if self.WINDOWS:
            self.loggingList.EnsureVisible(self.loggingList.GetCount() - 1)
        if "--->" not in entry:
            Globals.LOGLIST.append(entry)
        return

    def OnOpen(self, event):
        # otherwise ask the user what new file to open
        with wx.FileDialog(
            self,
            "Open Auth CSV File",
            wildcard="CSV files (*.csv)|*.csv",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # Proceed loading the file chosen by the user
            Globals.csv_auth_path = fileDialog.GetPath()
            print(Globals.csv_auth_path)
            self.PopulateConfig()

    def OnQuit(self, e):
        self.Close()

    def askForAuthCSV():
        # Windows, Standalone executable will allow user to select CSV
        if "Windows" in platform.system():
            answer = ctypes.windll.user32.MessageBoxW(
                0, "Please Select The Config CSV", "Esper Tool", 1
            )
            print(answer)
            if answer == 2:
                sys.exit("No CSV Selected")
            root = Tk()
            filename = askopenfilename()
            Globals.csv_auth_path = filename
            print(filename)
            root.destroy()
        # Mac, Debug mode, find csv file using system path
        else:
            currentpath = os.path.realpath(__file__)
            filename = os.path.dirname(currentpath) + os.path.sep + Globals.CONFIGFILE
            Globals.csv_auth_path = filename

    def onSave(self, event=None):
        self.SaveLogging()

    def SaveLogging(self):
        """Sends Device Info To Frame For Logging"""
        secs = time.time()
        timestamp = "{}".format(time.strftime("%Y%m%d-%H%M", time.localtime(secs)))
        self.CreateNewFile()
        loggingfile = Globals.csv_tag_path_clone
        header = Globals.header_format
        with open(loggingfile, "w") as csvfile:
            csvfile.write(header)
            # for rows in Globals.new_output_to_save:
            csvfile.write(Globals.new_output_to_save)
        self.Logging(
            "---> Logging info saved to csv file - " + Globals.csv_tag_path_clone
        )

    def CreateNewFile(self):
        newFile = "output.csv"
        Globals.csv_tag_path_clone = newFile
        if not os.path.exists(Globals.csv_tag_path_clone):
            with open(Globals.csv_tag_path_clone, "w"):
                pass

    def onClear(self, event=None):
        self.loggingList.Clear()

    def onUploadCSV(self):
        return

    def onRun(self, event=None):
        return

    def PopulateConfig(self):
        """Populates Configuration From CSV"""
        self.Logging("--->Loading Configurations from %s" % Globals.csv_auth_path)
        configfile = Globals.csv_auth_path

        for item in self.configMenuOptions:
            try:
                self.configMenu.Delete(item)
            except:
                pass
        self.configMenuOptions = []

        if os.path.isfile(configfile):
            with open(configfile, newline="") as csvfile:
                self.auth_csv_reader = csv.DictReader(csvfile)
                num = 0
                for row in self.auth_csv_reader:
                    self.configChoice[row["name"]] = row
                    item = self.configMenu.Append(
                        wx.ID_ANY, row["name"], row["name"], kind=wx.ITEM_CHECK
                    )
                    self.Bind(wx.EVT_MENU, self.loadConfiguartion, item)
                    self.configMenuOptions.append(item)
            self.Logging("--->**** Please Select an Endpoint")
        else:
            self.Logging(
                "--->****"
                + Globals.CONFIGFILE
                + " not found - PLEASE Quit and create configuration file"
            )
            self.configMenuOptions.append(
                self.configMenu.Append(
                    wx.ID_NONE, "No Loaded Configurations", "No Loaded Configurations"
                )
            )

    def LoadTagsAndAliases(self):
        return

    def loadConfiguartion(self, event, *args, **kwargs):
        """Populate Frame Layout With Device Configuration"""
        menuItem = self.configMenu.FindItemById(event.Id)
        try:
            self.Logging(
                "--->Attempting to load configuration: %s."
                % menuItem.GetItemLabelText()
            )
            selectedConfig = self.configChoice[menuItem.GetItemLabelText()]

            for item in menuItem.Menu.MenuItems:
                if item != menuItem:
                    item.Check(False)

            self.configList.Clear()
            self.configList.AppendText("API Host = " + selectedConfig["apiHost"] + "\n")
            self.configList.AppendText("API key = " + selectedConfig["apiKey"] + "\n")
            self.configList.AppendText(
                "API Prefix = " + selectedConfig["apiPrefix"] + "\n"
            )
            self.configList.AppendText("Enterprise = " + selectedConfig["enterprise"])

            if "https" in str(selectedConfig["apiHost"]):
                Globals.configuration.host = selectedConfig["apiHost"]
                Globals.configuration.api_key["Authorization"] = selectedConfig[
                    "apiKey"
                ]
                Globals.configuration.api_key_prefix["Authorization"] = selectedConfig[
                    "apiPrefix"
                ]
                Globals.enterprise_id = selectedConfig["enterprise"]

                self.PopulateGroups()
                self.PopulateApps()

        except:
            self.Logging(
                "--->****An Error has occured while loading the configuration, please try again."
            )
            menuItem.Check(False)

    def PopulateGroups(self):
        """create an instance of the API class"""
        self.Logging("--->Attemptting to populate groups...")
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)
        api_instance = esperclient.DeviceGroupApi(
            esperclient.ApiClient(Globals.configuration)
        )
        limit = 5000  # int | Number of results to return per page. (optional) (default to 20)
        offset = 0  # int | T    he initial index from which to return the results. (optional) (default to 0)
        self.groupChoice.Clear()
        try:
            api_response = api_instance.get_all_groups(
                Globals.enterprise_id, limit=limit, offset=offset
            )
            if len(api_response.results):
                for group in api_response.results:
                    self.groupChoice.Append(group.name, group.id)
                self.groupChoice.SetValue("<Select Group>")
                self.Bind(wx.EVT_COMBOBOX, self.PopulateDevices, self.groupChoice)
        except ApiException as e:
            self.Logging(
                "Exception when calling DeviceGroupApi->get_all_groups: %s\n" % e
            )
            print("Exception when calling DeviceGroupApi->get_all_groups: %s\n" % e)
        myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
        self.SetCursor(myCursor)

    def PopulateDevices(self, event=None):
        self.Logging(
            "--->Attemptting to populate devices of selected group (%s)..."
            % event.String
        )
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)
        self.deviceChoice.Clear()
        self.grid_1.ClearGrid()
        try:
            api_instance = esperclient.DeviceApi(
                esperclient.ApiClient(Globals.configuration)
            )
            api_response = api_instance.get_all_devices(
                Globals.enterprise_id,
                group=event.ClientData,
                limit=Globals.limit,
                offset=Globals.offset,
            )
            self.grid_1.AppendRows(1)
            num = 0
            for head in self.csvHeaders:
                self.grid_1.SetCellValue(0, num, head)
                num += 1

            if len(api_response.results):
                self.deviceChoice.Enable(True)
                for device in api_response.results:
                    name = "%s %s %s %s" % (
                        device.hardware_info["manufacturer"],
                        device.hardware_info["model"],
                        device.device_name,
                        device.software_info["androidVersion"],
                    )
                    self.deviceChoice.Append(name, device)
                self.deviceChoice.SetValue("<Select Device>")
            else:
                self.deviceChoice.Append("No Devices Found", "")
                self.groupChoice.SetValue("No Devices Found")
                self.deviceChoice.Enable(False)
                self.Logging("No Devices found in group")
        except ApiException as e:
            self.Logging("Exception when calling DeviceApi->get_all_devices: %s\n" % e)
            print(print("Exception when calling DeviceApi->get_all_devices: %s\n" % e))
        myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
        self.SetCursor(myCursor)

    def PopulateApps(self):
        """create an instance of the API class"""
        self.Logging("--->Attemptting to populate apps...")
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)
        api_instance = esperclient.ApplicationApi(
            esperclient.ApiClient(Globals.configuration)
        )
        limit = 5000  # int | Number of results to return per page. (optional) (default to 20)
        offset = 0  # int | The initial index from which to return the results. (optional) (default to 0)
        self.appChoice.Clear()
        try:
            api_response = api_instance.get_all_applications(
                Globals.enterprise_id,
                limit=Globals.limit,
                offset=Globals.offset,
                is_hidden=False,
            )
            if len(api_response.results):
                for app in api_response.results:
                    self.appChoice.Append(app.application_name, app.package_name)
                self.appChoice.SetValue("<Select App>")
        except ApiException as e:
            self.Logging(
                "Exception when calling ApplicationApi->get_all_applications: %s\n" % e
            )
            print(
                "Exception when calling ApplicationApi->get_all_applications: %s\n" % e
            )
        myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
        self.SetCursor(myCursor)

    def createLogString(self, deviceInfo, action):
        """Prepares Raw Data For UI"""
        logString = ""
        tagString = str(deviceInfo["Tags"])
        tagString = tagString.replace("'", "")
        tagString = tagString.replace("[", "")
        tagString = tagString.replace("]", "")
        tagString = tagString.replace(", ", ",")
        appString = str(deviceInfo["Apps"]).replace(",", "")
        if action == Globals.SHOW_ALL:
            logString = (
                "{:>4}".format(str(deviceInfo["num"]))
                + ","
                + deviceInfo["EsperName"]
                + ","
                + deviceInfo["Alias"]
                + ","
                + deviceInfo["Status"]
                + ","
                + deviceInfo["Mode"]
                + ","
                + deviceInfo["Serial"]
                + ","
                + '"'
                + str(tagString)
                + '"'
                + ","
                + str(appString)
                + ","
                + str(deviceInfo["KioskApp"])
            )
            return logString
        logString = (
            "{:>4}".format(str(deviceInfo["num"]))
            + ","
            + "{:13.13}".format(deviceInfo["EsperName"])
            + ","
            + "{:16.16}".format(str(deviceInfo["Alias"]))
            + ","
            + "{:10.10}".format(deviceInfo["Status"])
            + ","
            + "{:8.8}".format(deviceInfo["Mode"])
        )
        if action == Globals.SHOW_DEVICES:
            logString = (
                logString
                + ","
                + "{:20.20}".format(deviceInfo["Serial"])
                + ","
                + "{:20.20}".format(tagString)
            )
        elif action == Globals.SHOW_APP_VERSION:
            logString = logString + ",,," + "{:32.32}".format(appString)
            if "KioskApp" in deviceInfo:
                logString = logString + "," + "{:16.16}".format(deviceInfo["KioskApp"])
        return logString

    def runActionOnGroup(self, event=None):
        self.Logging("Running Action on Group")
        return

    def runActionOnDevice(self, event=None):
        self.Logging("Running Action on Device")
        return

    def OnGridRightDown(self):
        return
