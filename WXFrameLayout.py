import wx
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


class FrameLayout(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent)

        self.WINDOWS = True
        if platform.system() == "Windows":
            self.WINDOWS = True
        else:
            self.WINDOWS = False

        # Panel
        self.panel = wx.Panel(self)
        self.title = wx.StaticText(
            self.panel, label="Esper Device Actions at the Group Level"
        )

        if self.WINDOWS:
            font = wx.Font(
                10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_LIGHT
            )
        else:
            font = wx.Font(
                14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_LIGHT
            )
        self.panel.SetFont(font)

        topSizer = wx.BoxSizer(wx.VERTICAL)
        titleSizer = wx.BoxSizer(wx.HORIZONTAL)
        titleSizer.Add(self.title, 0, wx.ALL, 5)

        # Configuration UI
        self.configLabel = wx.StaticText(self.panel, label="Loaded Configurations")

        self.configChoice = wx.ComboBox(self.panel, wx.CB_READONLY, size=(200, -1))
        self.configChoice.Bind(wx.EVT_COMBOBOX, self.onConfigChoice, self.configChoice)
        self.configList = wx.TextCtrl(
            self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(400, 80)
        )

        configSizer = wx.BoxSizer(wx.HORIZONTAL)
        configSizer.Add((20, -1), proportion=1)  # this is a spacer
        configSizer.Add(self.configLabel, 0, wx.CENTER, 5)
        configSizer.Add(self.configChoice, 0, wx.CENTER | wx.EXPAND)
        configListSizer = wx.BoxSizer(wx.HORIZONTAL)
        configListSizer.Add(self.configList, 0, wx.ALIGN_CENTER)

        # Actions UI
        self.groupLabel = wx.StaticText(
            self.panel, label="Choose the Group to take Action on"
        )
        self.groupChoice = wx.ComboBox(self.panel, wx.CB_READONLY, size=(100, -1))
        self.actionLabel = wx.StaticText(
            self.panel, label="Action to apply to Devices in Group"
        )
        self.actionChoice = wx.Choice(
            self.panel, wx.CB_SORT, size=(100, -1), choices=Globals.ACTIONS
        )
        self.appLabel = wx.StaticText(self.panel, label="Application for Kiosk Mode")
        self.appChoice = wx.ComboBox(self.panel, wx.CB_READONLY, size=(100, -1))
        self.goButton = wx.Button(self.panel, label=" Go ")
        self.goButton.Bind(wx.EVT_BUTTON, self.onGoButton, self.goButton)
        groupSizer = wx.BoxSizer(wx.HORIZONTAL)
        groupSizer.Add((20, -1), proportion=1)  # this is a spacer
        groupSizer.Add(self.groupLabel, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        actionSizer = wx.BoxSizer(wx.HORIZONTAL)
        actionSizer.Add((20, -1), proportion=1)  # this is a spacer
        actionSizer.Add(self.actionLabel, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        appSizer = wx.BoxSizer(wx.HORIZONTAL)
        appSizer.Add((20, -1), proportion=1)  # this is a spacer
        appSizer.Add(self.appLabel, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        goButtonSizer = wx.BoxSizer(wx.HORIZONTAL)
        goButtonSizer.Add(self.goButton, 0, wx.ALL, 5)

        gridSizer = wx.GridSizer(rows=3, cols=2, hgap=5, vgap=5)
        gridSizer.Add(groupSizer, 0, wx.ALIGN_RIGHT)
        gridSizer.Add(self.groupChoice, 0, wx.EXPAND)
        gridSizer.Add(actionSizer, 0, wx.ALIGN_RIGHT)
        gridSizer.Add(self.actionChoice, 0, wx.EXPAND)
        gridSizer.Add(appSizer, 0, wx.ALIGN_RIGHT)
        gridSizer.Add(self.appChoice, 0, wx.EXPAND)

        # Logging UI
        if self.WINDOWS:
            self.loggingList = wx.ListBox(
                self.panel, size=(700, 300), style=wx.LB_NEEDED_SB | wx.LB_HSCROLL
            )
            myfont = wx.Font(
                8,
                wx.FONTFAMILY_MODERN,
                wx.FONTSTYLE_ITALIC,
                wx.FONTWEIGHT_NORMAL,
                False,
            )
        else:
            self.loggingList = wx.ListBox(
                self.panel, size=(700, 400), style=wx.LB_NEEDED_SB | wx.LB_HSCROLL
            )
            myfont = wx.Font(
                10,
                wx.FONTFAMILY_MODERN,
                wx.FONTSTYLE_ITALIC,
                wx.FONTWEIGHT_NORMAL,
                False,
            )

        self.loggingList.SetFont(myfont)
        self.saveButton = wx.Button(self.panel, label=" Create CSV ")
        self.saveButton.Bind(wx.EVT_BUTTON, self.onSaveButton, self.saveButton)
        self.uploadCSV = wx.Button(self.panel, label=" Upload Device CSV ")
        self.uploadCSV.Bind(wx.EVT_BUTTON, self.onUploadCSV, self.uploadCSV)
        self.clearButton = wx.Button(self.panel, label=" Clear ")
        self.clearButton.Bind(wx.EVT_BUTTON, self.onClearButton, self.clearButton)
        self.reloadButton = wx.Button(self.panel, label=" Reload Names/Tags ")
        self.reloadButton.Bind(wx.EVT_BUTTON, self.onReloadButton, self.reloadButton)
        # self.get_bt_csv = wx.Button(self.panel, label=' Create Bluetooth CSV ')
        # self.get_bt_csv.Bind(wx.EVT_BUTTON, self.get_bt_csv, self.get_bt_csv)
        loggingSizer = wx.BoxSizer(wx.HORIZONTAL)
        clearButtonSizer = wx.BoxSizer(wx.HORIZONTAL)
        saveButtonSizer = wx.BoxSizer(wx.HORIZONTAL)
        relaodButtonSizer = wx.BoxSizer(wx.HORIZONTAL)
        loggingSizer.Add(self.loggingList, 0, wx.EXPAND)
        clearButtonSizer.Add(self.clearButton, 0, wx.ALL, 5)
        clearButtonSizer.Add(self.saveButton, 0, wx.ALL, 5)
        clearButtonSizer.Add(self.reloadButton, 0, wx.ALL, 5)
        clearButtonSizer.Add(self.uploadCSV, 0, wx.ALL, 5)

        # Bring sections together
        topSizer.Add(titleSizer, 0, wx.CENTER)
        topSizer.Add(wx.StaticLine(self.panel), 0, wx.ALL | wx.EXPAND, 5)

        topSizer.Add(configSizer, 0, wx.CENTER, 5)
        topSizer.Add(configListSizer, 0, wx.CENTER, 5)
        topSizer.Add(wx.StaticLine(self.panel), 0, wx.ALL | wx.EXPAND, 5)

        topSizer.Add(gridSizer, 0, wx.ALL | wx.EXPAND, 5)
        topSizer.Add(wx.StaticLine(self.panel), 0, wx.ALL | wx.EXPAND, 5)
        topSizer.Add(goButtonSizer, 0, wx.ALL | wx.CENTER, 5)
        topSizer.Add(wx.StaticLine(self.panel), 0, wx.ALL | wx.EXPAND, 5)

        topSizer.Add(loggingSizer, 0, wx.ALL | wx.EXPAND, 5)
        topSizer.Add(clearButtonSizer, 0, wx.ALL | wx.CENTER, 5)
        topSizer.Add(clearButtonSizer, 0, wx.ALL | wx.CENTER, 5)

        # SetSizeHints(minW, minH, maxW, maxH)
        self.SetSizeHints(250, 300, 800, 800)

        self.panel.SetSizer(topSizer)
        topSizer.Fit(self)

    def onGoButton(self, event):
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

    def onUploadCSV(self, event):
        self.askForNameTagCSV()

    def onSaveButton(self, event):
        self.SaveLogging()

    def onReloadButton(self, event):
        self.LoadTagsAndAliases()

    def onClearButton(self, event):
        self.loggingList.Clear()

    def onConfigChoice(self, event):
        self.SetConfigValues()

    def onCancel(self, event):
        self.closeProgram()

    def closeProgram(self):
        self.Close()

    def buttonYieldEvent(self):
        """Allows Button Press Action to Yield For Result"""
        if Globals.frame.WINDOWS:
            wx.Yield()
        else:
            Globals.app.SafeYield(None, True)

    # Frame Population
    def SetConfigValues(self):
        """Populate Frame Layout With Device Configuration"""
        choice = self.configChoice.GetSelection()
        selectedConfig = self.configChoice.GetClientData(choice)

        self.configList.Clear()
        self.configList.AppendText("API Host = " + selectedConfig["apiHost"] + "\n")
        self.configList.AppendText("API key = " + selectedConfig["apiKey"] + "\n")
        self.configList.AppendText("API Prefix = " + selectedConfig["apiPrefix"] + "\n")
        self.configList.AppendText("Enterprise = " + selectedConfig["enterprise"])

        if "https" in str(selectedConfig["apiHost"]):
            Globals.configuration.host = selectedConfig["apiHost"]
            Globals.configuration.api_key["Authorization"] = selectedConfig["apiKey"]
            Globals.configuration.api_key_prefix["Authorization"] = selectedConfig[
                "apiPrefix"
            ]
            Globals.enterprise_id = selectedConfig["enterprise"]
            self.PopulateGroups()
            self.PopulateApps()
        else:
            self.Logging(self, "--->**** Please Select an Endpoint")

    def PopulateGroups(self):
        """create an instance of the API class"""
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
        except ApiException as e:
            print("Exception when calling DeviceGroupApi->get_all_groups: %s\n" % e)

    def PopulateApps(self):
        """create an instance of the API class"""
        api_instance = esperclient.ApplicationApi(
            esperclient.ApiClient(Globals.configuration)
        )
        limit = 5000  # int | Number of results to return per page. (optional) (default to 20)
        offset = 0  # int | The initial index from which to return the results. (optional) (default to 0)
        self.appChoice.Clear()
        try:
            api_response = api_instance.get_all_applications(
                Globals.enterprise_id, limit=limit, offset=offset, is_hidden=False
            )
            if len(api_response.results):
                for app in api_response.results:
                    self.appChoice.Append(app.application_name, app.package_name)
        except ApiException as e:
            print(
                "Exception when calling ApplicationApi->get_all_applications: %s\n" % e
            )

    def LoadTagsAndAliases(self):
        """Loads Configuration From CSV"""
        self.Logging("--->Loading Names/Tags by serial# from Tag/Name CSV")

        Globals.TAGSandALIASES.clear()
        # currentpath = os.path.realpath(__file__)
        # namestagsfile = os.path.dirname(currentpath) + os.path.sep + Globals.NAMESTAGSFILE
        namestagsfile = Globals.csv_tag_path

        if os.path.isfile(namestagsfile):
            with open(namestagsfile, newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    Globals.TAGSandALIASES[row["Serial"]] = [row["Alias"], row["Tags"]]
        else:
            self.Logging(
                "--->****"
                + " Tag/Name CSV "
                + " not found - Set Names/Tags Action will not work"
            )

    def PopulateConfig(self):
        """Populates Configuration From CSV"""
        self.Logging("--->Loading Configurations from ./EsperGroupActionsConfig.csv")
        # currentpath = os.path.realpath(__file__)
        # configfile = os.path.dirname(currentpath) + os.path.sep + Globals.CONFIGFILE
        configfile = Globals.csv_auth_path

        if os.path.isfile(configfile):
            with open(configfile, newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # print(row['name'], row['enterprise'])
                    self.configChoice.Append(row["name"], row)
        else:
            self.Logging(
                "--->****"
                + Globals.CONFIGFILE
                + " not found - PLEASE Quit and create configuration file"
            )

    # Frame UI Logging
    def Logging(self, entry):
        """Logs Infromation To Frame UI"""
        self.loggingList.Append(entry)
        if self.WINDOWS:
            self.loggingList.EnsureVisible(self.loggingList.GetCount() - 1)
        if "--->" not in entry:
            Globals.LOGLIST.append(entry)

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
                + ","
                + str(deviceInfo["bluetoothState"])
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
                + ","
                + str(appString)
                + ","
                + str(deviceInfo["KioskApp"])
                + ","
                + str(deviceInfo["bluetoothState"])
            )
        elif action == Globals.SHOW_APP_VERSION:
            logString = logString + ",,," + "{:32.32}".format(appString)
            if "KioskApp" in deviceInfo:
                logString = logString + "," + "{:16.16}".format(deviceInfo["KioskApp"])
        return logString

    def askForNameTagCSV(self):
        # Windows, Standalone executable will allow user to select CSV
        if "Windows" in platform.system():
            answer = ctypes.windll.user32.MessageBoxW(
                0, "Please Select The Device List CSV", "Esper Tool", 1
            )
            if answer != 2:
                root = Tk()
                filename = askopenfilename()
                Globals.csv_tag_path = filename
                self.LoadTagsAndAliases()
                print(filename)
                root.destroy()
            else:
                root.destroy()
        # Mac, Debug mode, find csv file using system path
        else:
            currentpath = os.path.realpath(__file__)
            filename = (
                os.path.dirname(currentpath) + os.path.sep + Globals.NAMESTAGSFILE
            )
            Globals.csv_tag_path = filename

    def GenerateReport(self):
        TakeAction(self, self.groupChoice.GetSelection(), Globals.GENERATE_REPORT)

    def OnQuit(self, e):
        self.Close()

    def showUrlBlacklistDialog(self):
        dlg = wx.TextEntryDialog(
            self.Parent, "Enter URL BlackList (comma seperated)", "URL BlackList"
        )
        dlg.SetValue("Default")
        if dlg.ShowModal() == wx.ID_OK:
            Globals.url_blacklist = dlg.GetValue()
            print(dlg.GetValue())
        dlg.Destroy()

    def get_bt_csv(self):
        return
