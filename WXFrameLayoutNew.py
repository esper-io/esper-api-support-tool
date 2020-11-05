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
        self.actionChoice = wx.Choice(self.panel_1, wx.ID_ANY, choices=Globals.ACTIONS)
        self.appChoice = wx.ComboBox(
            self.panel_1, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN
        )
        self.button_1 = wx.Button(self.panel_1, wx.ID_ANY, "Run on Group")
        self.button_2 = wx.Button(self.panel_1, wx.ID_ANY, "Run on Device")
        self.panel_2 = wx.Panel(self, wx.ID_ANY)
        self.loggingList = wx.ListBox(
            self.panel_2, wx.ID_ANY, choices=[""], style=wx.LB_NEEDED_SB | wx.LB_HSCROLL
        )
        self.grid_1 = wx.grid.Grid(
            self.panel_2, wx.ID_ANY, size=(1, 1), style=wx.LB_NEEDED_SB | wx.LB_HSCROLL
        )

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
        foa = wx.MenuItem(fileMenu, wx.ID_OPEN, "&Open Auth CSV\tCtrl+O")
        fileOpenAuth = fileMenu.Append(foa)

        foc = wx.MenuItem(fileMenu, wx.ID_APPLY, "&Open Device CSV\tCtrl+D")
        fileOpenConfig = fileMenu.Append(foc)

        fileMenu.Append(wx.ID_SEPARATOR)
        fs = wx.MenuItem(fileMenu, wx.ID_SAVE, "&Save As\tCtrl+S")
        fileSave = fileMenu.Append(fs)

        fileMenu.Append(wx.ID_SEPARATOR)
        fi = wx.MenuItem(fileMenu, wx.ID_EXIT, "&Quit\tCtrl+Q")
        fileItem = fileMenu.Append(fi)

        consoleMenu = wx.Menu()
        clearConsole = consoleMenu.Append(wx.ID_RESET, "Clear", "Clear Console")

        self.configMenu = wx.Menu()
        defaultConfigVal = self.configMenu.Append(
            wx.ID_NONE, "No Loaded Configurations", "No Loaded Configurations"
        )
        self.configMenuOptions.append(defaultConfigVal)

        runMenu = wx.Menu()
        self.runGroup = runMenu.Append(wx.ID_RETRY, "Run on Group", "Run on Group")
        self.runDevice = runMenu.Append(wx.ID_RETRY, "Run on Device", "Run on Device")

        viewMenu = wx.Menu()
        self.viewMenuOptions = {}
        colNum = 0
        for header in Globals.CSV_TAG_HEADER.split(","):
            if header == "Esper Name":
                continue
            item = viewMenu.Append(
                wx.ID_ANY, "Show  %s" % header, "Show  %s" % header, kind=wx.ITEM_CHECK
            )
            item.Check(True)
            self.Bind(wx.EVT_MENU, self.toggleColVisibility, item)
            self.viewMenuOptions[item.Id] = colNum
            colNum += 1
        # viewMenu.Append(wx.ID_SEPARATOR)

        self.menubar.Append(fileMenu, "&File")
        self.menubar.Append(viewMenu, "&View")
        self.menubar.Append(self.configMenu, "&Configurations")
        self.menubar.Append(consoleMenu, "&Console")
        self.menubar.Append(runMenu, "&Run")
        self.SetMenuBar(self.menubar)

        self.Bind(wx.EVT_MENU, self.OnOpen, defaultConfigVal)
        self.Bind(wx.EVT_MENU, self.OnOpen, fileOpenAuth)
        self.Bind(wx.EVT_MENU, self.onUploadCSV, fileOpenConfig)
        self.Bind(wx.EVT_MENU, self.OnQuit, fileItem)
        self.Bind(wx.EVT_MENU, self.onSave, fileSave)
        self.Bind(wx.EVT_MENU, self.onClear, clearConsole)
        self.Bind(wx.EVT_MENU, self.runActionOnGroup, self.runGroup)
        self.Bind(wx.EVT_MENU, self.runActionOnDevice, self.runDevice)
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

        self.actionChoice.SetSelection(1)
        self.actionChoice.Enable(False)
        self.deviceChoice.Enable(False)
        self.groupChoice.Enable(False)
        self.appChoice.Enable(False)
        self.runGroup.Enable(False)
        self.button_1.Enable(False)
        self.button_2.Enable(False)
        self.runDevice.Enable(False)

        self.grid_1.CreateGrid(0, len(Globals.CSV_TAG_HEADER.split(",")))
        self.fillGridHeaders()

        # self.frame_toolbar.Realize()
        self.panel_1.SetMinSize((400, 900))
        self.panel_2.SetMinSize((2000, 800))
        self.Maximize(True)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MyFrame.__do_layout
        sizer_1 = wx.FlexGridSizer(1, 2, 0, 0)
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
        # label_1.Wrap(200)
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
            "Action to apply:",
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
        sizer_3.Add(self.actionChoice, 0, wx.EXPAND, 0)
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
        """Sends Device Info To Frame For Logging"""
        if self.grid_1.GetNumberRows() > 0:
            dlg = wx.FileDialog(
                self,
                "Save CSV as...",
                os.getcwd(),
                "",
                "*.csv",
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            )
            result = dlg.ShowModal()
            inFile = dlg.GetPath()
            dlg.Destroy()

            if result == wx.ID_OK:  # Save button was pressed
                self.save(inFile)
                return True
            elif (
                result == wx.ID_CANCEL
            ):  # Either the cancel button was pressed or the window was closed
                return False

    def save(self, inFile):
        numRows = self.grid_1.GetNumberRows()
        numCols = self.grid_1.GetNumberCols()
        gridData = []
        gridData.append(Globals.CSV_TAG_HEADER.replace("\n", "").split(","))

        self.createNewFile(inFile)

        for row in range(numRows):
            rowValues = []
            for col in range(numCols):
                value = self.grid_1.GetCellValue(row, col)
                rowValues.append(value)
            gridData.append(rowValues)

        with open(Globals.csv_tag_path_clone, "w", newline="") as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerows(gridData)

        self.Logging(
            "---> Logging info saved to csv file - " + Globals.csv_tag_path_clone
        )

    def createNewFile(self, filePath):
        Globals.csv_tag_path_clone = filePath
        if not os.path.exists(Globals.csv_tag_path_clone):
            with open(Globals.csv_tag_path_clone, "w"):
                pass

    def onClear(self, event=None):
        self.loggingList.Clear()

    def onUploadCSV(self, event=None):
        self.emptyGrid()
        with wx.FileDialog(
            self,
            "Open Device CSV File",
            wildcard="CSV files (*.csv)|*.csv",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as fileDialog:
            result = fileDialog.ShowModal()
            if result == wx.ID_OK:
                # Proceed loading the file chosen by the user
                Globals.csv_auth_path = fileDialog.GetPath()
                self.Logging(
                    "--->Attempting to load device data from %s" % Globals.csv_auth_path
                )
                num = 0
                with open(Globals.csv_auth_path, "r") as csvFile:
                    reader = csv.reader(
                        csvFile, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True
                    )
                    header = None
                    grid_headers = Globals.CSV_TAG_HEADER.replace("\n", "").split(",")
                    for row in reader:
                        if not all("" == val or val.isspace() for val in row):
                            if num == 0:
                                header = row
                                num += 1
                                continue
                            self.grid_1.AppendRows(1)
                            fileCol = 0
                            toolCol = 0
                            for colValue in row:
                                colName = (
                                    header[fileCol].replace(" ", "").lower()
                                    if len(header) > fileCol
                                    else ""
                                )
                                if (
                                    header[fileCol]
                                    in Globals.CSV_DEPRECATED_HEADER_LABEL
                                ):
                                    fileCol += 1
                                    continue
                                gridColName = (
                                    grid_headers[toolCol].replace(" ", "").lower()
                                )
                                val = str(colValue) if colName == gridColName else ""
                                self.grid_1.SetCellValue(
                                    self.grid_1.GetNumberRows() - 1,
                                    toolCol,
                                    str(colValue),
                                )
                                toolCol += 1
                                fileCol += 1
                    self.grid_1.AutoSizeColumns()
            elif result == wx.ID_CANCEL:
                return  # the user changed their mind

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
                    if "name" in row:
                        self.configChoice[row["name"]] = row
                        item = self.configMenu.Append(
                            wx.ID_ANY, row["name"], row["name"], kind=wx.ITEM_CHECK
                        )
                        self.Bind(wx.EVT_MENU, self.loadConfiguartion, item)
                        self.configMenuOptions.append(item)
                    else:
                        self.Logging(
                            "--->ERROR: Please check that the Auth CSV is set up correctly!"
                        )
                        defaultConfigVal = self.configMenu.Append(
                            wx.ID_NONE,
                            "No Loaded Configurations",
                            "No Loaded Configurations",
                        )
                        self.configMenuOptions.append(defaultConfigVal)
                        self.Bind(wx.EVT_MENU, self.OnOpen, defaultConfigVal)
                        return
            self.Logging(
                "--->**** Please Select an Endpoint From the Configuartion Menu (defaulting to first Config)"
            )
            defaultConfigItem = self.configMenuOptions[0]
            defaultConfigItem.Check(True)
            self.loadConfiguartion(defaultConfigItem)
        else:
            self.Logging(
                "--->****"
                + Globals.CONFIGFILE
                + " not found - PLEASE Quit and create configuration file"
            )
            defaultConfigVal = self.configMenu.Append(
                wx.ID_NONE, "No Loaded Configurations", "No Loaded Configurations"
            )
            self.configMenuOptions.append(defaultConfigVal)
            self.Bind(wx.EVT_MENU, self.OnOpen, defaultConfigVal)

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

            self.deviceChoice.Enable(True)
            self.groupChoice.Enable(True)
            self.appChoice.Enable(True)
            self.actionChoice.Enable(True)
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
            self.runGroup.Enable(True)
            self.button_1.Enable(True)
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
        # self.grid_1.ClearGrid()
        # self.fillGridHeaders()
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

            if len(api_response.results):
                self.deviceChoice.Enable(True)
                for device in api_response.results:
                    name = "%s %s %s %s" % (
                        device.hardware_info["manufacturer"],
                        device.hardware_info["model"],
                        device.device_name,
                        device.software_info["androidVersion"],
                    )
                    self.deviceChoice.Append(name, device.id)
                self.deviceChoice.SetValue("<Select Device>")
                self.runDevice.Enable(False)
                self.button_2.Enable(True)
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
                # "{:>4}".format(str(deviceInfo["num"]))
                # + ","
                deviceInfo["EsperName"]
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
            # "{:>4}".format(str(deviceInfo["num"]))
            # + ","
            +"{:13.13}".format(deviceInfo["EsperName"])
            + ","
            + "{:16.16}".format(str(deviceInfo["Alias"]))
            + ","
            + "{:10.10}".format(deviceInfo["Status"])
            + ","
            + "{:8.8}".format(deviceInfo["Mode"])
        )
        return logString

    def runActionOnGroup(self, event=None):
        self.Logging("Running Action on Group")
        if self.groupChoice.GetSelection() < 0:
            wx.MessageBox("Please select a Group", style=wx.OK)
        elif self.actionChoice.GetSelection() < 0:
            wx.MessageBox("Please select an Action", style=wx.OK)
        elif (
            self.actionChoice.GetSelection() == Globals.SET_KIOSK
            and self.appChoice.GetSelection() < 0
        ):
            wx.MessageBox("Please select an Application", style=wx.OK)
        else:
            groupLabel = self.groupChoice.Items[self.groupChoice.GetSelection()]
            TakeAction(
                self,
                self.groupChoice.GetSelection(),
                self.actionChoice.GetSelection(),
                groupLabel,
            )

    def runActionOnDevice(self, event=None):
        self.Logging("Running Action on Device")
        if self.deviceChoice.GetSelection() < 0:
            wx.MessageBox("Please select a Device", style=wx.OK)
        elif self.actionChoice.GetSelection() < 0:
            wx.MessageBox("Please select an Action", style=wx.OK)
        elif (
            self.actionChoice.GetSelection() == Globals.SET_KIOSK
            and self.appChoice.GetSelection() < 0
        ):
            wx.MessageBox("Please select an Application", style=wx.OK)
        else:
            deviceLabel = self.deviceChoice.Items[self.deviceChoice.GetSelection()]
            TakeAction(
                self,
                self.deviceChoice.GetSelection(),
                self.actionChoice.GetSelection(),
                deviceLabel,
                isDevice=True,
            )

    def buttonYieldEvent(self):
        """Allows Button Press Action to Yield For Result"""
        if Globals.frame.WINDOWS:
            wx.Yield()
        else:
            Globals.app.SafeYield(None, True)

    def fillGridHeaders(self):
        num = 0
        headerLabels = Globals.CSV_TAG_HEADER.split(",")
        for head in headerLabels:
            if head:
                if self.grid_1.GetNumberCols() < len(headerLabels):
                    self.grid_1.AppendCols(1)
                self.grid_1.SetColLabelValue(num, head)
                num += 1
        self.grid_1.AutoSizeColumns()

    def emptyGrid(self):
        self.grid_1.ClearGrid()
        if self.grid_1.GetNumberRows() > 0:
            self.grid_1.DeleteRows(0, self.grid_1.GetNumberRows())
        self.grid_1.SetScrollLineX(15)
        self.grid_1.SetScrollLineY(15)
        self.fillGridHeaders()

    def addDeviceToGrid(self, device_info):
        num = 0
        self.grid_1.AppendRows(1)

        # self.grid_1.SetCellValue(self.grid_1.GetNumberRows() - 1, 0, str(num))
        for attribute in Globals.CSV_TAG_ATTR_NAME:
            value = (
                device_info[Globals.CSV_TAG_ATTR_NAME[attribute]]
                if Globals.CSV_TAG_ATTR_NAME[attribute] in device_info
                else ""
            )
            self.grid_1.SetCellValue(self.grid_1.GetNumberRows() - 1, num, str(value))
            num += 1

        self.grid_1.AutoSizeColumns()

    def toggleColVisibility(self, event):
        index = (
            self.viewMenuOptions[event.Id] if event.Id in self.viewMenuOptions else None
        )
        isShown = self.grid_1.IsColShown(index)
        if isShown:
            self.grid_1.HideCol(index)
        else:
            self.grid_1.ShowCol(index)
