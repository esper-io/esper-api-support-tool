#!/usr/bin/env python

import wx
import time
import csv
import os.path
import platform
import json
import tempfile
import ast

import Common.Globals as Globals
import GUI.EnhancedStatusBar as ESB

import Utility.wxThread as wxThread
import Utility.EsperTemplateUtil as templateUtil

from functools import partial

from datetime import datetime

from GUI.sidePanel import SidePanel
from GUI.gridPanel import GridPanel
from GUI.toolBar import ToolsToolBar
from GUI.menuBar import ToolMenuBar
from GUI.consoleWindow import Console
from GUI.Dialogs.CheckboxMessageBox import CheckboxMessageBox
from GUI.Dialogs.TemplateDialog import TemplateDialog
from GUI.Dialogs.CommandDialog import CommandDialog
from GUI.Dialogs.ProgressCheckDialog import ProgressCheckDialog
from GUI.Dialogs.PreferencesDialog import PreferencesDialog
from GUI.Dialogs.CmdConfirmDialog import CmdConfirmDialog

from GUI.Dialogs.NewEndpointDialog import NewEndpointDialog

from Common.decorator import api_tool_decorator

from Utility.ApiToolLogging import ApiToolLog
from Utility.EsperAPICalls import (
    TakeAction,
    iterateThroughGridRows,
    ApplyDeviceConfig,
    setKiosk,
    setMulti,
    getdeviceapps,
    getAllDevices,
    getAllGroups,
    getAllApplications,
    validateConfiguration,
    # powerOffDevice,
    getTokenInfo,
    clearAppData,
)

from Utility.Resource import (
    limitActiveThreads,
    resourcePath,
    createNewFile,
    checkEsperInternetConnection,
    joinThreadList,
)


class NewFrameLayout(wx.Frame):
    def __init__(self):
        self.prefPath = ""
        self.authPath = ""

        self.consoleWin = None
        self.refresh = None
        self.checkConsole = None
        self.preferences = None
        self.auth_data = None

        self.WINDOWS = True
        self.isBusy = False
        self.isRunning = False
        self.isRunningUpdate = False
        self.isForceUpdate = False
        self.kill = False
        self.CSVUploaded = False

        self.prefDialog = PreferencesDialog(self.preferences, parent=self)

        if platform.system() == "Windows":
            self.WINDOWS = True
            self.prefPath = (
                "%s\\EsperApiTool\\prefs.json"
                % tempfile.gettempdir().replace("Local", "Roaming").replace("Temp", "")
            )
            self.authPath = (
                "%s\\EsperApiTool\\auth.csv"
                % tempfile.gettempdir().replace("Local", "Roaming").replace("Temp", "")
            )
        else:
            self.WINDOWS = False
            self.prefPath = "%s/EsperApiTool/prefs.json" % os.path.expanduser(
                "~/Desktop/"
            )
            self.authPath = "%s/EsperApiTool/auth.csv" % os.path.expanduser(
                "~/Desktop/"
            )

        wx.Frame.__init__(self, None, title=Globals.TITLE, style=wx.DEFAULT_FRAME_STYLE)
        self.SetSize(Globals.MIN_SIZE)
        self.SetMinSize(Globals.MIN_SIZE)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)

        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        self.sidePanel = SidePanel(self, self.panel_1, sizer_4)

        self.gridPanel = GridPanel(self, self.panel_1, wx.ID_ANY)
        sizer_4.Add(self.gridPanel, 1, wx.EXPAND, 0)

        self.panel_1.SetSizer(sizer_4)

        self.Bind(wx.EVT_CLOSE, self.OnQuit)
        self.Bind(wx.EVT_BUTTON, self.onRun, self.sidePanel.runBtn)

        # Menu Bar
        self.menubar = ToolMenuBar()
        self.SetMenuBar(self.menubar)

        self.Bind(wx.EVT_MENU, self.showConsole, self.menubar.consoleView)
        self.Bind(wx.EVT_MENU, self.updateGrids, self.menubar.refreshGrids)
        self.Bind(wx.EVT_MENU, self.onClearGrids, self.menubar.clearGrids)
        self.Bind(wx.EVT_MENU, self.AddEndpoint, self.menubar.defaultConfigVal)
        self.Bind(wx.EVT_MENU, self.AddEndpoint, self.menubar.fileOpenAuth)
        self.Bind(wx.EVT_MENU, self.onUploadCSV, self.menubar.fileOpenConfig)
        self.Bind(wx.EVT_MENU, self.OnQuit, self.menubar.fileItem)
        self.Bind(wx.EVT_MENU, self.onSaveBoth, self.menubar.fileSave)
        self.Bind(wx.EVT_MENU, self.onRun, self.menubar.run)
        self.Bind(wx.EVT_MENU, self.onCommand, self.menubar.command)
        self.Bind(wx.EVT_MENU, self.onClone, self.menubar.clone)
        self.Bind(wx.EVT_MENU, self.onPref, self.menubar.pref)
        self.Bind(
            wx.EVT_MENU, self.gridPanel.onDeviceColumn, self.menubar.deviceColumns
        )
        self.Bind(
            wx.EVT_MENU, self.gridPanel.onNetworkColumn, self.menubar.networkColumns
        )
        # Menu Bar end

        # Tool Bar
        self.frame_toolbar = ToolsToolBar(self, -1)  # wx.ToolBar(self, -1)
        self.SetToolBar(self.frame_toolbar)

        self.Bind(wx.EVT_TOOL, self.OnQuit, self.frame_toolbar.qtool)
        self.Bind(wx.EVT_TOOL, self.AddEndpoint, self.frame_toolbar.atool)
        self.Bind(wx.EVT_TOOL, self.onUploadCSV, self.frame_toolbar.otool)
        self.Bind(wx.EVT_TOOL, self.onSaveBoth, self.frame_toolbar.stool)
        self.Bind(wx.EVT_TOOL, self.onRun, self.frame_toolbar.rtool)
        self.Bind(wx.EVT_TOOL, self.updateGrids, self.frame_toolbar.rftool)
        self.Bind(wx.EVT_TOOL, self.onCommand, self.frame_toolbar.cmdtool)
        self.frame_toolbar.search.Bind(wx.EVT_SEARCH, self.onSearch)
        self.frame_toolbar.search.Bind(wx.EVT_CHAR, self.onChar)
        self.frame_toolbar.search.Bind(wx.EVT_SEARCH_CANCEL, self.onSearch)
        # Tool Bar end

        # Status Bar
        self.statusBar = ESB.EnhancedStatusBar(self, wx.ID_ANY)
        self.statusBar.SetFieldsCount(2)
        self.SetStatusBar(self.statusBar)
        self.statusBar.SetStatusText("")

        self.sbText = wx.StaticText(self.statusBar, wx.ID_ANY, "")
        self.statusBar.AddWidget(
            self.sbText, pos=0, horizontalalignment=ESB.ESB_EXACT_FIT
        )

        self.gauge = wx.Gauge(
            self.statusBar,
            wx.ID_ANY,
            100,
            style=wx.GA_HORIZONTAL | wx.GA_PROGRESS | wx.GA_SMOOTH,
        )
        self.statusBar.AddWidget(
            self.gauge, pos=1, horizontalalignment=ESB.ESB_EXACT_FIT
        )
        # End Status Bar

        # Set Icon
        icon = wx.Icon()
        icon.CopyFromBitmap(
            wx.Bitmap(resourcePath("Images/icon.png"), wx.BITMAP_TYPE_PNG)
        )
        self.SetIcon(icon)

        # Bound Events
        self.DragAcceptFiles(True)
        self.Bind(wx.EVT_DROP_FILES, self.onFileDrop)
        self.Bind(wxThread.EVT_FETCH, self.onFetch)
        self.Bind(wxThread.EVT_UPDATE, self.onUpdate)
        self.Bind(wxThread.EVT_UPDATE_DONE, self.onUpdateComplete)
        self.Bind(wxThread.EVT_GROUP, self.addGroupsToGroupChoice)
        # self.Bind(wxThread.EVT_DEVICE, self.addDevicesToDeviceChoice)
        self.Bind(wxThread.EVT_APPS, self.addAppsToAppChoice)
        self.Bind(wxThread.EVT_RESPONSE, self.performAPIResponse)
        self.Bind(wxThread.EVT_COMPLETE, self.onComplete)
        self.Bind(wxThread.EVT_LOG, self.onLog)
        self.Bind(wxThread.EVT_COMMAND, self.onCommandDone)
        self.Bind(wxThread.EVT_UPDATE_GAUGE, self.setGaugeValue)
        self.Bind(wxThread.EVT_UPDATE_TAG_CELL, self.gridPanel.updateTagCell)
        self.Bind(wxThread.EVT_UNCHECK_CONSOLE, self.menubar.uncheckConsole)
        self.Bind(wxThread.EVT_ON_FAILED, self.onFail)
        self.Bind(wxThread.EVT_CONFIRM_CLONE, self.confirmClone)
        self.Bind(wxThread.EVT_CONFIRM_CLONE_UPDATE, self.confirmCloneUpdate)
        self.Bind(wx.EVT_ACTIVATE_APP, self.MacReopenApp)
        self.Bind(wx.EVT_ACTIVATE, self.onActivate)

        self.loadPref()
        self.__set_properties()
        self.Layout()
        self.Centre()
        self.Raise()
        self.Iconize(False)
        self.SetFocus()

        internetCheck = wxThread.GUIThread(self, self.checkForInternetAccess, None)
        internetCheck.start()

    def __set_properties(self):
        self.SetTitle(Globals.TITLE)
        self.SetBackgroundColour(wx.Colour(192, 192, 192))
        self.SetThemeEnabled(False)

        self.sidePanel.actionChoice.SetSelection(1)
        self.sidePanel.gridActions.SetSelection(0)

        self.sidePanel.actionChoice.Enable(False)
        self.sidePanel.deviceChoice.Enable(False)
        self.sidePanel.groupChoice.Enable(False)
        self.sidePanel.appChoice.Enable(False)
        self.sidePanel.runBtn.Enable(False)
        self.frame_toolbar.EnableTool(self.frame_toolbar.rtool.Id, False)
        self.frame_toolbar.EnableTool(self.frame_toolbar.cmdtool.Id, False)
        self.frame_toolbar.EnableTool(self.frame_toolbar.rftool.Id, False)
        self.menubar.run.Enable(False)
        self.menubar.clone.Enable(False)
        self.menubar.command.Enable(False)
        self.menubar.clearConsole.Enable(False)

        if self.kill:
            return

        self.frame_toolbar.Realize()
        # self.Maximize(True)

    def setColorTheme(self, parent=None):
        """ Set theme color to bypass System Theme (Mac) """
        white = wx.Colour(255, 255, 255)
        black = wx.Colour(0, 0, 0)
        if not parent:
            parent = self
        for child in parent.GetChildren():
            if (
                type(child) != wx.Panel
                and type(child) != wx.Button
                and type(child) != wx.ComboBox
            ):
                if type(child) != wx.StaticText:
                    child.SetBackgroundColour(white)
                child.SetForegroundColour(black)
            if child.GetChildren():
                self.setColorTheme(child)

    def onLog(self, event):
        """ Event trying to log data """
        evtValue = event.GetValue()
        self.Logging(evtValue)

    def Logging(self, entry, isError=False):
        """ Frame UI Logging """
        try:
            entry = entry.replace("\n", " ")
            shortMsg = entry
            Globals.LOGLIST.append(entry)
            if self.consoleWin:
                self.consoleWin.Logging(entry)
            if "error" in entry.lower():
                isError = True
            if len(entry) >= Globals.MAX_STATUS_CHAR:
                longEntryMsg = "....(See console for details)"
                shortMsg = entry[0 : Globals.MAX_STATUS_CHAR - len(longEntryMsg)]
                shortMsg += longEntryMsg
            self.setStatus(shortMsg, entry, isError)
        except:
            pass

    @api_tool_decorator
    def AddEndpoint(self, event):
        """ Try to open and load an Auth CSV """
        isValid = False
        errorMsg = None
        name = host = entId = key = None
        while not isValid:
            with NewEndpointDialog(
                errorMsg=errorMsg, name=name, host=host, entId=entId, key=key
            ) as dialog:
                res = dialog.ShowModal()
                if res == wx.ID_ADD:
                    try:
                        name, host, entId, key, prefix = dialog.getInputValues()
                        csvRow = dialog.getCSVRowEntry()
                        isValid = validateConfiguration(host, entId, key, prefix=prefix)
                        if isValid:
                            matchingConfig = []
                            if self.auth_data:
                                matchingConfig = list(
                                    filter(
                                        lambda x: x[2] == entId or x[0] == name,
                                        self.auth_data,
                                    )
                                )
                            if (
                                not self.auth_data or not csvRow in self.auth_data
                            ) and not matchingConfig:
                                with open(self.authPath, "a", newline="") as csvfile:
                                    writer = csv.writer(
                                        csvfile, quoting=csv.QUOTE_NONNUMERIC
                                    )
                                    writer.writerow(csvRow)
                            elif csvRow in self.auth_data or matchingConfig:
                                self.auth_data = [
                                    csvRow if x == matchingConfig[0] else x
                                    for x in self.auth_data
                                ]
                                with open(self.authPath, "w", newline="") as csvfile:
                                    writer = csv.writer(
                                        csvfile, quoting=csv.QUOTE_NONNUMERIC
                                    )
                                    res = []
                                    [
                                        res.append(x)
                                        for x in self.auth_data
                                        if x not in res
                                    ]
                                    self.auth_data = res
                                    writer.writerows(self.auth_data)

                            self.readAuthCSV()
                            self.PopulateConfig(auth=self.authPath)
                            wx.MessageBox(
                                "Endpoint has been added",
                                style=wx.ICON_INFORMATION,
                            )
                        else:
                            wx.MessageBox(
                                "ERROR: Invalid input in Configuration. Check inputs!",
                                style=wx.ICON_ERROR,
                            )
                    except:
                        wx.MessageBox(
                            "ERROR: An error occured when attempting to add the endpoint. Check inputs values and your internet connection.",
                            style=wx.ICON_ERROR,
                        )
                else:
                    self.readAuthCSV()
                    if self.auth_data:
                        isValid = True
                    if not self.IsShown():
                        isValid = True
                        self.OnQuit(None)

    @api_tool_decorator
    def OnQuit(self, e):
        """ Actions to take when frame is closed """
        self.kill = True
        if self.consoleWin:
            self.consoleWin.Close()
            self.consoleWin.Destroy()
            self.consoleWin = None
        if self.prefDialog:
            self.prefDialog.Close()
            self.prefDialog.Destroy()
        if e:
            if e.EventType != wx.EVT_CLOSE.typeId:
                self.Close()
        self.savePrefs(self.prefDialog)
        self.Destroy()

    @api_tool_decorator
    def onSaveBoth(self, event):
        if self.gridPanel.grid_1.GetNumberRows() > 0:
            dlg = wx.FileDialog(
                self,
                "Save Device and Network Info CSV as...",
                os.getcwd(),
                "",
                "*.csv",
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            )
            result = dlg.ShowModal()
            inFile = dlg.GetPath()
            dlg.Destroy()

            if result == wx.ID_OK:  # Save button was pressed
                gridDeviceData = []
                for device in self.gridPanel.grid_1_contents:
                    tempDict = {}
                    tempDict.update(device)
                    deviceListing = list(
                        filter(
                            lambda x: (
                                x["Device Name"]
                                == device[Globals.CSV_TAG_ATTR_NAME["Esper Name"]]
                            ),
                            self.gridPanel.grid_2_contents,
                        )
                    )
                    if deviceListing:
                        tempDict.update(deviceListing[0])
                    gridDeviceData.append(tempDict)
                headers = []
                headers.extend(Globals.CSV_TAG_ATTR_NAME.keys())
                headers.extend(Globals.CSV_NETWORK_ATTR_NAME.keys())
                headers.remove("Device Name")

                gridData = []
                gridData.append(headers)

                createNewFile(inFile)

                for deviceData in gridDeviceData:
                    rowValues = []
                    for header in headers:
                        value = ""
                        if header in deviceData:
                            value = deviceData[header]
                        else:
                            if header in Globals.CSV_TAG_ATTR_NAME.keys():
                                if Globals.CSV_TAG_ATTR_NAME[header] in deviceData:
                                    value = deviceData[
                                        Globals.CSV_TAG_ATTR_NAME[header]
                                    ]
                            if header in Globals.CSV_NETWORK_ATTR_NAME.keys():
                                if Globals.CSV_NETWORK_ATTR_NAME[header] in deviceData:
                                    value = deviceData[
                                        Globals.CSV_NETWORK_ATTR_NAME[header]
                                    ]
                        rowValues.append(value)
                    gridData.append(rowValues)

                with open(inFile, "w", newline="") as csvfile:
                    writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
                    writer.writerows(gridData)

                self.Logging("---> Info saved to csv file - " + inFile)

                return True
            elif (
                result == wx.ID_CANCEL
            ):  # Either the cancel button was pressed or the window was closed
                return False

    @api_tool_decorator
    def onUploadCSV(self, event):
        """ Upload device CSV to the device Grid """
        if not Globals.enterprise_id:
            self.loadConfigPrompt()
            return

        self.setCursorBusy()
        self.gridPanel.emptyDeviceGrid()
        self.gridPanel.emptyNetworkGrid()
        self.setGaugeValue(0)
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
                try:
                    with open(
                        Globals.csv_auth_path, "r", encoding="utf-8-sig"
                    ) as csvFile:
                        reader = csv.reader(
                            csvFile, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True
                        )
                        data = list(reader)
                        self.processDeviceCSVUpload(data)
                        self.gridPanel.grid_1.AutoSizeColumns()
                except UnicodeDecodeError as e:
                    with open(Globals.csv_auth_path, "r") as csvFile:
                        reader = csv.reader(
                            csvFile, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True
                        )
                        data = list(reader)
                        self.processDeviceCSVUpload(data)
                        self.gridPanel.grid_1.AutoSizeColumns()
            elif result == wx.ID_CANCEL:
                return  # the user changed their mind
        wx.CallLater(3000, self.setGaugeValue, 0)
        self.setCursorDefault()

    def processDeviceCSVUpload(self, data):
        self.CSVUploaded = True
        deviceThread = wxThread.GUIThread(
            self,
            self.processCsvDataByGrid,
            args=(self.gridPanel.grid_1, data, Globals.CSV_TAG_ATTR_NAME),
            eventType=None,
        )
        netThread = wxThread.GUIThread(
            self,
            self.processCsvDataByGrid,
            args=(self.gridPanel.grid_2, data, Globals.CSV_NETWORK_ATTR_NAME),
            eventType=None,
        )
        deviceThread.start()
        netThread.start()
        wxThread.GUIThread(
            self,
            self.waitForThreadsThenSetCursorDefault,
            ([deviceThread, netThread], 2),
        ).start()

    def processCsvDataByGrid(self, grid, data, headers):
        grid_headers = list(headers.keys())
        len_reader = len(data)
        rowCount = 1
        num = 0
        for row in data:
            self.setGaugeValue(int(float((rowCount) / len_reader) * 100))
            rowCount += 1
            if not all("" == val or val.isspace() for val in row):
                if num == 0:
                    header = row
                    num += 1
                    continue
                grid.AppendRows(1)
                toolCol = 0
                for expectedCol in headers.keys():
                    fileCol = 0
                    for colValue in row:
                        colName = (
                            header[fileCol].replace(" ", "").lower()
                            if len(header) > fileCol
                            else ""
                        )
                        if colName == "storenumber":
                            colName = "Alias"
                            header[fileCol] = "Alias"
                        if colName == "tag":
                            colName = "Tags"
                            header[fileCol] = "Tags"
                        if (
                            expectedCol == "Device Name"
                            and colName == "espername"
                            and grid == self.gridPanel.grid_2
                        ):
                            colName = "devicename"
                        if (
                            fileCol > len(header)
                            or header[fileCol].strip()
                            in Globals.CSV_DEPRECATED_HEADER_LABEL
                            or (
                                header[fileCol].strip() not in headers.keys()
                                and colName != "devicename"
                            )
                        ):
                            fileCol += 1
                            continue
                        if colName == expectedCol.replace(" ", "").lower():
                            if expectedCol == "Tags":
                                try:
                                    ast.literal_eval(colValue)
                                except:
                                    if (
                                        expectedCol == "Tags"
                                        and "," in colValue
                                        and (
                                            (
                                                colValue.count('"') % 2 != 0
                                                or colValue.count("'") % 2 != 0
                                            )
                                            or (
                                                '"' not in colValue
                                                or "'" not in colValue
                                            )
                                        )
                                    ):
                                        colValue = '"' + colValue + '"'
                            grid.SetCellValue(
                                grid.GetNumberRows() - 1,
                                toolCol,
                                str(colValue),
                            )
                            isEditable = True
                            if grid_headers[toolCol] in Globals.CSV_EDITABLE_COL:
                                isEditable = False
                            grid.SetReadOnly(
                                grid.GetNumberRows() - 1,
                                toolCol,
                                isEditable,
                            )
                        fileCol += 1
                    toolCol += 1

    @api_tool_decorator
    def PopulateConfig(self, auth=None, event=None):
        """Populates Configuration From CSV"""
        self.Logging("--->Loading Configurations from %s" % Globals.csv_auth_path)
        if auth:
            if Globals.csv_auth_path != auth:
                Globals.csv_auth_path = auth
        configfile = Globals.csv_auth_path

        for item in self.menubar.configMenuOptions:
            try:
                self.menubar.configMenu.Delete(item)
            except:
                pass
        self.menubar.configMenuOptions = []

        self.setGaugeValue(0)
        if os.path.isfile(configfile):
            with open(configfile, newline="") as csvfile:
                auth_csv_reader = csv.DictReader(csvfile)
                auth_csv_reader = list(auth_csv_reader)
                maxRow = len(auth_csv_reader)
                num = 1

                # Handle empty File
                if maxRow == 0:
                    self.Logging(
                        "--->ERROR: Empty Auth File, please select a proper Auth CSV file!"
                    )
                    self.AddEndpoint(None)
                    return

                for row in auth_csv_reader:
                    self.setGaugeValue(int(float(num / maxRow) * 100))
                    num += 1
                    if "name" in row:
                        self.sidePanel.configChoice[row["name"]] = row
                        item = self.menubar.configMenu.Append(
                            wx.ID_ANY, row["name"], row["name"], kind=wx.ITEM_CHECK
                        )
                        self.Bind(wx.EVT_MENU, self.loadConfiguartion, item)
                        self.menubar.configMenuOptions.append(item)
                    else:
                        self.Logging(
                            "--->ERROR: Please check that the Auth CSV is set up correctly!"
                        )
                        defaultConfigVal = self.menubar.configMenu.Append(
                            wx.ID_NONE,
                            "No Loaded Configurations",
                            "No Loaded Configurations",
                        )
                        self.menubar.configMenuOptions.append(defaultConfigVal)
                        self.Bind(wx.EVT_MENU, self.AddEndpoint, defaultConfigVal)
                        return
            self.Logging(
                "--->**** Please Select an Endpoint From the Configuartion Menu (defaulting to first Config)"
            )
            defaultConfigItem = self.menubar.configMenuOptions[0]
            defaultConfigItem.Check(True)
            self.loadConfiguartion(defaultConfigItem)
        else:
            self.Logging(
                "--->****"
                + configfile
                + " not found - PLEASE Quit and create configuration file"
            )
            defaultConfigVal = self.menubar.configMenu.Append(
                wx.ID_NONE, "No Loaded Configurations", "No Loaded Configurations"
            )
            self.menubar.configMenuOptions.append(defaultConfigVal)
            self.Bind(wx.EVT_MENU, self.AddEndpoint, defaultConfigVal)
        wx.CallLater(3000, self.setGaugeValue, 0)

    def setCursorDefault(self):
        """ Set cursor icon to default state """
        try:
            self.isBusy = False
            myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
            self.SetCursor(myCursor)
        except:
            pass

    def setCursorBusy(self):
        """ Set cursor icon to busy state """
        self.isBusy = True
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)

    @api_tool_decorator
    def loadConfiguartion(self, event, *args, **kwargs):
        """Populate Frame Layout With Device Configuration"""
        menuItem = self.menubar.configMenu.FindItemById(event.Id)
        self.onClearGrids(None)
        self.sidePanel.removeEndpointBtn.Enable(False)
        self.sidePanel.appChoice.Clear()
        self.setCursorBusy()
        try:
            self.Logging(
                "--->Attempting to load configuration: %s."
                % menuItem.GetItemLabelText()
            )
            selectedConfig = self.sidePanel.configChoice[menuItem.GetItemLabelText()]

            for item in menuItem.Menu.MenuItems:
                if item != menuItem:
                    item.Check(False)
                else:
                    item.Check(True)

            filledIn = False
            for _ in range(Globals.MAX_RETRY):
                if not filledIn:
                    filledIn = self.fillInConfigListing(selectedConfig)
                else:
                    break

            if not filledIn:
                raise Exception("Failed to load configuration")

            self.sidePanel.groupChoice.Enable(True)
            self.sidePanel.actionChoice.Enable(True)
            self.sidePanel.removeEndpointBtn.Enable(True)
        except Exception as e:
            self.Logging(
                "--->****An Error has occured while loading the configuration, please try again."
            )
            print(e)
            ApiToolLog().LogError(e)
            menuItem.Check(False)

    @api_tool_decorator
    def fillInConfigListing(self, config):
        self.sidePanel.configList.Clear()
        host = key = entId = prefix = ""
        if type(config) is dict or isinstance(config, dict):
            host = config["apiHost"]
            key = config["apiKey"]
            prefix = config["apiPrefix"]
            entId = config["enterprise"]
        elif type(config) is tuple or isinstance(config, tuple):
            host = config[0]
            key = config[1]
            prefix = config[2]
            entId = config[3]

        if host and key and prefix and entId:
            self.sidePanel.configList.AppendText("API Host = " + host + "\n")
            self.sidePanel.configList.AppendText("API key = " + key + "\n")
            self.sidePanel.configList.AppendText("API Prefix = " + prefix + "\n")
            self.sidePanel.configList.AppendText("Enterprise = " + entId)

            if "https" in str(host):
                Globals.configuration.host = host.strip()
                Globals.configuration.api_key["Authorization"] = key.strip()
                Globals.configuration.api_key_prefix["Authorization"] = prefix.strip()
                Globals.enterprise_id = entId.strip()

                res = getTokenInfo()
                if res.expires_on <= datetime.now(res.expires_on.tzinfo) or not res:
                    raise Exception(
                        "API Token has expired! Please replace Configuration entry by adding endpoint with a new API Key."
                    )

                groupThread = self.PopulateGroups()
                appThread = None  # self.PopulateApps()
                threads = [groupThread, appThread]
                wxThread.GUIThread(
                    self,
                    self.waitForThreadsThenSetCursorDefault,
                    (threads, 0),
                ).start()
                return True
        else:
            wx.MessageBox("Invalid Configuration", style=wx.ICON_ERROR)
            return False

    def waitForThreadsThenSetCursorDefault(self, threads, source=None):
        joinThreadList(threads)
        if source == 1:
            if not self.sidePanel.devices:
                self.sidePanel.selectedDevices.Append("No Devices Found", "")
                self.sidePanel.deviceChoice.Enable(False)
                self.Logging("---> No Devices found")
            else:
                newThreads = []
                self.Logging("---> Attempting to populate Application list")
                self.gauge.Pulse()
                for deviceId in self.sidePanel.devices.values():
                    thread = wxThread.doAPICallInThread(
                        self,
                        getdeviceapps,
                        args=(deviceId),
                        eventType=wxThread.myEVT_APPS,
                        waitForJoin=False,
                    )
                    newThreads.append(thread)
                    limitActiveThreads(newThreads)
                num = 0
                for thread in newThreads:
                    thread.join()
                    num += 1
                    if not self.preferences or self.preferences["enableDevice"] == True:
                        self.setGaugeValue(int(float(num / len(newThreads) / 2) * 100))
                self.sidePanel.sortAndPopulateAppChoice()
                self.Logging("---> Application list populated")
            if not self.preferences or self.preferences["enableDevice"] == True:
                self.sidePanel.deviceChoice.Enable(True)
            else:
                self.sidePanel.deviceChoice.Enable(False)
        if source == 2:
            self.gridPanel.autoSizeGridsColumns()
        self.sidePanel.runBtn.Enable(True)
        self.frame_toolbar.EnableTool(self.frame_toolbar.rtool.Id, True)
        self.frame_toolbar.EnableTool(self.frame_toolbar.cmdtool.Id, True)
        self.frame_toolbar.EnableTool(self.frame_toolbar.rftool.Id, True)
        self.menubar.run.Enable(True)
        self.menubar.clone.Enable(True)
        self.menubar.command.Enable(True)
        self.setCursorDefault()
        self.setGaugeValue(100)

    @api_tool_decorator
    def PopulateGroups(self):
        """ Populate Group Choice """
        self.Logging("--->Attempting to populate groups...")
        self.setCursorBusy()
        self.setGaugeValue(0)
        self.gauge.Pulse()
        thread = wxThread.doAPICallInThread(
            self, getAllGroups, eventType=wxThread.myEVT_GROUP, waitForJoin=False
        )
        return thread

    @api_tool_decorator
    def addGroupsToGroupChoice(self, event):
        """ Populate Group Choice """
        results = event.GetValue().results
        num = 1
        results = sorted(
            results,
            key=lambda i: i.name.lower(),
        )
        if len(results):
            for group in results:
                self.sidePanel.groups[group.name] = group.id
                self.setGaugeValue(int(float(num / len(results)) * 100))
                num += 1
            # self.Bind(wx.EVT_COMBOBOX, self.PopulateDevices, self.sidePanel.groupChoice)
        # self.sidePanel.runBtn.Enable(True)
        # self.frame_toolbar.EnableTool(self.frame_toolbar.rtool.Id, True)
        # self.frame_toolbar.EnableTool(self.frame_toolbar.cmdtool.Id, True)
        # self.frame_toolbar.EnableTool(self.frame_toolbar.rftool.Id, True)
        # self.menubar.run.Enable(True)
        # self.menubar.clone.Enable(True)
        # self.menubar.command.Enable(True)
        self.sidePanel.groupChoice.Enable(True)
        self.sidePanel.actionChoice.Enable(True)
        # wx.CallLater(3000, self.setGaugeValue, 0)

    @api_tool_decorator
    def PopulateDevices(self, event):
        """ Populate Device Choice """
        self.SetFocus()
        self.Logging("--->Attempting to populate devices of selected group(s)")
        self.setCursorBusy()
        if not self.preferences or self.preferences["enableDevice"] == True:
            self.sidePanel.runBtn.Enable(False)
            self.frame_toolbar.EnableTool(self.frame_toolbar.rtool.Id, False)
            self.frame_toolbar.EnableTool(self.frame_toolbar.rftool.Id, False)
            self.frame_toolbar.EnableTool(self.frame_toolbar.cmdtool.Id, False)
            self.setGaugeValue(0)
            self.gauge.Pulse()
        else:
            self.sidePanel.runBtn.Enable(True)
            self.frame_toolbar.EnableTool(self.frame_toolbar.rtool.Id, True)
            self.frame_toolbar.EnableTool(self.frame_toolbar.rftool.Id, True)
        self.frame_toolbar.EnableTool(self.frame_toolbar.cmdtool.Id, True)
        threads = []
        for clientData in self.sidePanel.selectedGroupsList:
            thread = wxThread.doAPICallInThread(
                self,
                self.addDevicesToDeviceChoice,
                args=(clientData),
                eventType=None,
                waitForJoin=False,
            )
            threads.append(thread)
        wxThread.GUIThread(
            self,
            self.waitForThreadsThenSetCursorDefault,
            (threads, 1),
        ).start()

    @api_tool_decorator
    def addDevicesToDeviceChoice(self, groupId):
        """ Populate Device Choice """
        api_response = getAllDevices(groupId)
        if len(api_response.results):
            api_response.results = sorted(
                api_response.results,
                key=lambda i: i.device_name.lower(),
            )
            for device in api_response.results:
                name = "%s %s %s" % (
                    device.hardware_info["manufacturer"],
                    device.hardware_info["model"],
                    device.device_name,
                )
                if name and not name in self.sidePanel.devices:
                    self.sidePanel.devices[name] = device.id

    @api_tool_decorator
    def PopulateApps(self):
        """ Populate App Choice """
        self.Logging("--->Attempting to populate apps...")
        self.setCursorBusy()
        self.sidePanel.appChoice.Clear()
        thread = wxThread.doAPICallInThread(
            self, getAllApplications, eventType=wxThread.myEVT_APPS, waitForJoin=False
        )
        return thread

    @api_tool_decorator
    def addAppsToAppChoice(self, event):
        """ Populate App Choice """
        api_response = event.GetValue()
        results = None
        if hasattr(api_response, "results"):
            results = api_response.results
        else:
            results = api_response[1]["results"]
        if hasattr(results[0], "application_name"):
            results = sorted(
                results,
                key=lambda i: i.application_name.lower(),
            )
        else:
            results = sorted(
                results,
                key=lambda i: i["app_name"].lower(),
            )
        if len(results):
            num = 1
            for app in results:
                entry = None
                if hasattr(app, "application_name"):
                    appName = app.application_name
                    appPkgName = appName + (" (%s)" % app.package_name)
                    entry = {
                        "app_name": app.application_name,
                        appName: app.package_name,
                        appPkgName: app.package_name,
                        "app_state": app.state,
                    }
                    if entry not in self.sidePanel.enterpriseApps:
                        self.sidePanel.enterpriseApps.append(entry)
                else:
                    appName = app["app_name"]
                    appPkgName = appName + (" (%s)" % app["package_name"])
                    entry = {
                        "app_name": app["app_name"],
                        appName: app["package_name"],
                        appPkgName: app["package_name"],
                        "app_state": app["state"],
                    }
                    if entry not in self.sidePanel.deviceApps:
                        self.sidePanel.deviceApps.append(entry)
                num += 1
        # self.sidePanel.runBtn.Enable(True)
        # self.frame_toolbar.EnableTool(self.frame_toolbar.rtool.Id, True)
        # self.frame_toolbar.EnableTool(self.frame_toolbar.rftool.Id, True)
        # self.frame_toolbar.EnableTool(self.frame_toolbar.cmdtool.Id, True)

    @api_tool_decorator
    def onRun(self, event):
        """ Try to run the specifed Action on a group or device """
        if self.isBusy or not self.sidePanel.runBtn.IsEnabled():
            return
        self.setCursorBusy()
        self.isRunning = True
        self.gauge.Pulse()
        self.sidePanel.runBtn.Enable(False)
        self.frame_toolbar.EnableTool(self.frame_toolbar.rtool.Id, False)
        self.frame_toolbar.EnableTool(self.frame_toolbar.rftool.Id, False)
        self.frame_toolbar.EnableTool(self.frame_toolbar.cmdtool.Id, False)

        self.gridPanel.grid_1.UnsetSortingColumn()
        self.gridPanel.grid_2.UnsetSortingColumn()

        gridSelection = self.sidePanel.gridActions.GetSelection()
        appSelection = self.sidePanel.appChoice.GetSelection()
        actionSelection = self.sidePanel.actionChoice.GetSelection()

        appLabel = (
            self.sidePanel.appChoice.Items[appSelection]
            if len(self.sidePanel.appChoice.Items) > 0
            and self.sidePanel.appChoice.Items[appSelection]
            else ""
        )
        gridLabel = (
            self.sidePanel.gridActions.Items[gridSelection]
            if len(self.sidePanel.gridActions.Items) > 0
            and self.sidePanel.gridActions.Items[gridSelection]
            else ""
        )
        actionLabel = (
            self.sidePanel.actionChoice.Items[actionSelection]
            if len(self.sidePanel.actionChoice.Items) > 0
            and self.sidePanel.actionChoice.Items[actionSelection]
            else ""
        )
        self.setGaugeValue(0)
        if (
            self.sidePanel.selectedGroupsList
            and not self.sidePanel.selectedDevicesList
            and gridSelection <= 0
            and actionSelection > 0
        ):
            # run action on group
            if (
                actionSelection == Globals.SET_KIOSK
                or actionSelection == Globals.CLEAR_APP_DATA
            ) and (
                appSelection < 0 or appLabel == "No available app(s) on this device"
            ):
                wx.MessageBox(
                    "Please select a valid application", style=wx.OK | wx.ICON_ERROR
                )
                self.setCursorDefault()
                self.sidePanel.runBtn.Enable(True)
                return
            self.gridPanel.grid_1_contents = []
            self.gridPanel.grid_2_contents = []
            self.gridPanel.userEdited = []
            Globals.LAST_DEVICE_ID = None
            Globals.LAST_GROUP_ID = self.sidePanel.selectedGroupsList

            groupLabel = ""
            for groupId in self.sidePanel.selectedGroupsList:
                groupLabel = list(self.sidePanel.groups.keys())[
                    list(self.sidePanel.groups.values()).index(groupId)
                ]
                self.Logging(
                    '---> Attempting to run action, "%s", on group, %s.'
                    % (actionLabel, groupLabel)
                )
            TakeAction(
                self,
                self.sidePanel.selectedGroupsList,
                actionSelection,
                groupLabel,
            )
        elif (
            self.sidePanel.selectedDevicesList
            and gridSelection <= 0
            and actionSelection > 0
        ):
            # run action on device
            if (
                actionSelection == Globals.SET_KIOSK
                or actionSelection == Globals.CLEAR_APP_DATA
            ) and (
                appSelection < 0 or appLabel == "No available app(s) on this device"
            ):
                wx.MessageBox(
                    "Please select a valid application", style=wx.OK | wx.ICON_ERROR
                )
                self.setCursorDefault()
                self.sidePanel.runBtn.Enable(True)
                return
            self.gridPanel.grid_1_contents = []
            self.gridPanel.grid_2_contents = []
            self.gridPanel.userEdited = []
            Globals.LAST_DEVICE_ID = self.sidePanel.selectedDevicesList
            Globals.LAST_GROUP_ID = None
            for deviceId in self.sidePanel.selectedDevicesList:
                deviceLabel = list(self.sidePanel.devices.keys())[
                    list(self.sidePanel.devices.values()).index(deviceId)
                ]
                self.Logging(
                    '---> Attempting to run action, "%s", on device, %s.'
                    % (actionLabel, deviceLabel)
                )
            TakeAction(
                self,
                self.sidePanel.selectedDevicesList,
                actionSelection,
                None,
                isDevice=True,
            )
        elif gridSelection > 0:
            # run grid action
            if self.gridPanel.grid_1.GetNumberRows() > 0:
                runAction = True
                result = None
                if Globals.SHOW_GRID_DIALOG:
                    result = CheckboxMessageBox(
                        "Confirmation",
                        "The %s will attempt to process the action on all devices in the Device Info grid. \n\nContinue?"
                        % Globals.TITLE,
                    )

                    if result.ShowModal() != wx.ID_OK:
                        runAction = False
                if result and result.getCheckBoxValue():
                    Globals.SHOW_GRID_DIALOG = False
                if runAction:
                    self.Logging(
                        '---> Attempting to run grid action, "%s".' % gridLabel
                    )
                    self.gridPanel.applyTextColorToDevice(
                        None,
                        wx.Colour(0, 0, 0),
                        bgColor=wx.Colour(255, 255, 255),
                        applyAll=True,
                    )
                    self.frame_toolbar.search.SetValue("")
                    iterateThroughGridRows(self, gridSelection)
            else:
                wx.MessageBox(
                    "Make sure the grid has data to perform an action on",
                    style=wx.OK | wx.ICON_ERROR,
                )
                self.setCursorDefault()
                self.sidePanel.runBtn.Enable(True)
        else:
            wx.MessageBox(
                "Please select an action to perform on a group or device!",
                style=wx.OK | wx.ICON_ERROR,
            )
            self.setCursorDefault()
            self.sidePanel.runBtn.Enable(True)

    def loadConfigPrompt(self):
        """ Display message to user to load config """
        wx.MessageBox("Please load a configuration first!", style=wx.OK | wx.ICON_ERROR)

    def showConsole(self, event):
        """ Toggle Console Display """
        if not self.consoleWin:
            self.consoleWin = Console(parent=self)
            self.menubar.clearConsole.Enable(True)
            self.Bind(wx.EVT_MENU, self.onClear, self.menubar.clearConsole)
        else:
            self.consoleWin.Destroy()
            self.menubar.clearConsole.Enable(False)

    def onClear(self, event):
        """ Clear Console """
        if self.consoleWin:
            self.consoleWin.onClear()

    @api_tool_decorator
    def onCommand(self, event, value="{\n\n}", level=0):
        """ When the user wants to run a command show the command dialog """
        if level < Globals.MAX_RETRY:
            self.setCursorBusy()
            self.setGaugeValue(0)

            if self.sidePanel.selectedGroupsList:
                with CommandDialog("Enter JSON Command", value=value) as cmdDialog:
                    result = cmdDialog.ShowModal()
                    if result == wx.ID_OK:
                        cmd = None
                        commandType = None
                        config = None
                        try:
                            config, commandType = cmdDialog.GetValue()
                            configParts = config.split("_-_")
                            cmd = [
                                json.loads(configParts[0]),
                                json.loads(configParts[1]),
                            ]
                        except:
                            wx.MessageBox(
                                "An error occurred while process the inputted JSON object, please make sure it is formatted correctly",
                                style=wx.OK | wx.ICON_ERROR,
                            )
                            self.onCommand(event, config, level + 1)
                        if cmd != None:
                            ApplyDeviceConfig(self, cmd, commandType)
            else:
                wx.MessageBox(
                    "Please select an group and or device", style=wx.OK | wx.ICON_ERROR
                )
            self.setCursorDefault()

    def onCommandDone(self, event):
        """ Tell user to check the Esper Console for detailed results """
        cmdResult = event.GetValue()
        self.setGaugeValue(100)
        if cmdResult:
            dlg = wx.RichMessageDialog(
                self, "Command has been fired. Check the Esper Console for details."
            )
            result = ""
            for res in cmdResult:
                result += json.dumps(str(res), indent=2)
                result += "\n\n"
            dlg.ShowDetailedText(str(cmdResult).replace("[", "").replace("]", ""))
            dlg.ShowModal()
        wx.CallLater(3000, self.setGaugeValue, 0)

    def confirmCommand(self, cmd, commandType):
        """ Ask user to confirm the command they want to run """
        modal = None
        isGroup = False
        cmd_dict = ast.literal_eval(str(cmd).replace("\n", ""))
        cmdFormatted = json.dumps(cmd_dict, indent=2)
        label = ""
        applyTo = ""
        commaSeperated = ", "
        if len(self.sidePanel.selectedDevicesList) > 0:
            selections = self.sidePanel.deviceMultiDialog.GetSelections()
            choices = list(self.sidePanel.devices.keys())
            label = ""
            for device in selections:
                label += choices[device] + commaSeperated
            if label.endswith(", "):
                label = label[0 : len(label) - len(commaSeperated)]
            applyTo = "device"
        elif len(self.sidePanel.selectedGroupsList) >= 0:
            selections = self.sidePanel.groupMultiDialog.GetSelections()
            choices = list(self.sidePanel.groups.keys())
            label = ""
            for group in selections:
                label += choices[group] + commaSeperated
            if label.endswith(", "):
                label = label[0 : len(label) - len(commaSeperated)]
            applyTo = "group"
            isGroup = True
        modal = wx.NO
        with CmdConfirmDialog(commandType, cmdFormatted, applyTo, label) as dialog:
            res = dialog.ShowModal()
            if res == wx.ID_OK:
                modal = wx.YES

        if modal == wx.YES:
            return True, isGroup
        else:
            return False, isGroup

    def setStatus(self, status, orgingalMsg, isError=False):
        """ Set status bar text """
        self.sbText.SetLabel(status)
        if orgingalMsg:
            self.sbText.SetToolTip(orgingalMsg.replace("--->", ""))
        if isError:
            self.sbText.SetForegroundColour(wx.Colour(255, 0, 0))
        else:
            self.sbText.SetForegroundColour(wx.Colour(0, 0, 0))

    @api_tool_decorator
    def onFetch(self, event):
        """ Given device data perform the specified action """
        self.gauge.Pulse()
        evtValue = event.GetValue()
        action = evtValue[0]
        deviceList = evtValue[1]
        threads = []
        for entry in deviceList.values():
            device = entry[0]
            deviceInfo = entry[1]
            if action == Globals.SHOW_ALL_AND_GENERATE_REPORT:
                self.gridPanel.addDeviceToDeviceGrid(deviceInfo)
                self.gridPanel.addDeviceToNetworkGrid(device, deviceInfo)
            elif action == Globals.SET_KIOSK:
                # setKiosk(self, device, deviceInfo)
                thread = wxThread.GUIThread(
                    self,
                    setKiosk,
                    (self, device, deviceInfo),
                )
                thread.start()
                threads.append(thread)
            elif action == Globals.SET_MULTI:
                # setMulti(self, device, deviceInfo)
                thread = wxThread.GUIThread(
                    self,
                    setMulti,
                    (self, device, deviceInfo),
                )
                thread.start()
                threads.append(thread)
            elif action == Globals.CLEAR_APP_DATA:
                clearAppData(self, device)
            # elif action == Globals.POWER_OFF:
            #     powerOffDevice(self, device, deviceInfo)
            limitActiveThreads(threads)
        joinThreadList(threads)

    def onUpdateComplete(self, event):
        """ Alert user to chcek the Esper Console for detailed results for some actions """
        action = event.GetValue()
        if action == Globals.SET_KIOSK or action == Globals.SET_MULTI:
            self.Logging("---> Please refer to the Esper Console for detailed results.")
            if not self.checkConsole:
                try:
                    self.checkConsole = ProgressCheckDialog()
                    self.checkConsole.ShowModal()
                    self.checkConsole = None
                except Exception as e:
                    print(e)
                    ApiToolLog().LogError(e)
        if action == Globals.CLEAR_APP_DATA:
            wx.MessageBox(
                "Clear App Data Command has been sent to the device(s). Please check devices' event feeds for command status.",
                style=wx.ICON_INFORMATION,
            )

    @api_tool_decorator
    def onDeviceSelections(self, event):
        """ When the user selects a device showcase apps related to that device """
        self.SetFocus()
        self.gauge.Pulse()
        self.setCursorBusy()
        num = 1
        if len(self.sidePanel.selectedDevicesList) > 0:
            self.sidePanel.runBtn.Enable(False)
            wxThread.GUIThread(
                self,
                self.addDevicesApps,
                self.sidePanel.selectedDevicesList,
                eventType=wxThread.myEVT_COMPLETE,
                passArgAsTuple=True,
            ).start()
        # else:
        #    self.sidePanel.sortAndPopulateAppChoice()
        evt = wxThread.CustomEvent(wxThread.myEVT_COMPLETE, -1, True)
        wx.PostEvent(self, evt)

    def addDevicesApps(self, deviceId):
        num = 1
        appAdded = False
        for deviceId in self.sidePanel.selectedDevicesList:
            self.Logging("---> Fetching Apps on Device Through API")
            appList, _ = getdeviceapps(
                deviceId, createAppList=True, useEnterprise=Globals.USE_ENTERPRISE_APP
            )
            self.Logging("---> Finished Fetching Apps on Device Through API")
            for app in appList:
                appAdded = True
                app_name = app.split(" v")[0]
                d = [k for k in self.sidePanel.apps if app_name in k]
                if d:
                    d = d[0]
                    self.sidePanel.appChoice.Append(app_name, d[app_name])
                self.setGaugeValue(int(float(num / len(appList)) * 100))
                num += 1
        if not appAdded:
            self.sidePanel.appChoice.Append("No available app(s) on this device")
            self.sidePanel.appChoice.SetSelection(0)
        evt = wxThread.CustomEvent(wxThread.myEVT_COMPLETE, -1, True)
        wx.PostEvent(self, evt)

    def MacReopenApp(self, event):
        """Called when the doc icon is clicked, and ???"""
        self.onActivate(self, event, skip=False)
        if event.GetActive():
            try:
                self.GetTopWindow().Raise()
            except:
                pass
        event.Skip()

    def MacNewFile(self):
        pass

    def MacPrintFile(self, file_path):
        pass

    def setGaugeValue(self, value):
        """ Attempt to set Gauge to the specififed value """
        if hasattr(value, "GetValue"):
            value = value.GetValue()
        maxValue = self.gauge.GetRange()
        if value > maxValue:
            value = maxValue
        if value < 0:
            value = 0
        if value >= 0 and value <= maxValue:
            self.gauge.SetValue(value)

    @api_tool_decorator
    def performAPIResponse(self, event):
        """ Once an API has given its response attempt to run the specififed callback """
        self.Logging("---> API Response Returned")
        self.gauge.Pulse()
        evtValue = event.GetValue()
        response = evtValue[0]
        callback = evtValue[1]
        cbArgs = evtValue[2]
        optCbArgs = evtValue[3]

        if callback:
            self.Logging("---> Attempting to Process API Response")
            if optCbArgs:
                callback(*(*cbArgs, response, *optCbArgs))
            else:
                callback(*(*cbArgs, response))

    def onComplete(self, event):
        """ Things that should be done once an Action is completed """
        enable = False
        if event:
            enable = event.GetValue()
        self.setCursorDefault()
        self.setGaugeValue(100)
        if self.isRunning or enable:
            self.sidePanel.runBtn.Enable(True)
            self.frame_toolbar.EnableTool(self.frame_toolbar.rtool.Id, True)
            self.frame_toolbar.EnableTool(self.frame_toolbar.rftool.Id, True)
            self.frame_toolbar.EnableTool(self.frame_toolbar.cmdtool.Id, True)
        self.isRunning = False
        self.sidePanel.sortAndPopulateAppChoice()
        if not self.IsIconized() and self.IsActive():
            wx.CallLater(3000, self.setGaugeValue, 0)
        self.Logging("---> Completed Action")

    def onActivate(self, event, skip=True):
        if not self.isRunning:
            wx.CallLater(3000, self.gauge.SetValue, 0)
        if skip:
            event.Skip()

    def onClearGrids(self, event):
        """ Empty Grids """
        thread = wxThread.GUIThread(
            self, self.gridPanel.emptyDeviceGrid, None, eventType=None
        )
        thread.start()
        netThread = wxThread.GUIThread(
            self, self.gridPanel.emptyNetworkGrid, None, eventType=None
        )
        netThread.start()
        # self.gridPanel.emptyDeviceGrid()
        # self.gridPanel.emptyNetworkGrid()

    @api_tool_decorator
    def readAuthCSV(self):
        if os.path.exists(Globals.csv_auth_path):
            with open(Globals.csv_auth_path, "r") as csvFile:
                reader = csv.reader(
                    csvFile, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True
                )
                self.auth_data = list(reader)

    @api_tool_decorator
    def loadPref(self):
        """ Attempt to load preferences from file system """
        if os.path.exists(self.authPath):
            Globals.csv_auth_path = self.authPath
            self.readAuthCSV()
        else:
            if self.kill:
                return
            createNewFile(self.authPath)
            with open(self.authPath, "w", newline="") as csvfile:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
                writer.writerow(
                    ["name", "apiHost", "enterprise", "apiKey", "apiPrefix"]
                )
            self.AddEndpoint(None)
        self.PopulateConfig()

        if self.kill:
            return

        if (
            os.path.isfile(self.prefPath)
            and os.path.exists(self.prefPath)
            and os.access(self.prefPath, os.R_OK)
        ):
            with open(self.prefPath) as jsonFile:
                self.preferences = json.load(jsonFile)
            self.prefDialog.SetPrefs(self.preferences)
        else:
            createNewFile(self.prefPath)
            self.savePrefs(self.prefDialog)

    @api_tool_decorator
    def savePrefs(self, dialog):
        """ Save Preferences """
        self.preferences = dialog.GetPrefs()
        with open(self.prefPath, "w") as outfile:
            json.dump(self.preferences, outfile)
        evt = wxThread.CustomEvent(wxThread.myEVT_LOG, -1, "---> Preferences' Saved")
        wx.PostEvent(self, evt)

    def onPref(self, event):
        """ Update Preferences when they are changed """
        if self.prefDialog.ShowModal() == wx.ID_APPLY:
            save = wxThread.GUIThread(
                self,
                self.savePrefs,
                (self.prefDialog),
                passArgAsTuple=True,
                eventType=None,
            )
            save.start()
            # self.savePrefs(self.prefDialog)
            self.sidePanel.sortAndPopulateAppChoice()
        if self.preferences["enableDevice"]:
            self.sidePanel.deviceChoice.Enable(True)
        else:
            self.sidePanel.deviceChoice.Enable(False)

    @api_tool_decorator
    def onFail(self, event):
        """ Try to showcase rows in the grid on which an action failed on """
        failed = event.GetValue()
        red = wx.Colour(255, 0, 0)
        errorBg = wx.Colour(255, 235, 234)
        orange = wx.Colour(255, 165, 0)
        warnBg = wx.Colour(255, 241, 216)
        if type(failed) == list:
            for device in failed:
                if "Queued" in device:
                    self.gridPanel.applyTextColorToDevice(
                        device[0], orange, bgColor=warnBg
                    )
                else:
                    self.gridPanel.applyTextColorToDevice(device, red, bgColor=errorBg)
        elif type(failed) == tuple:
            if "Queued" in failed:
                self.gridPanel.applyTextColorToDevice(failed[0], orange, bgColor=warnBg)
            else:
                self.gridPanel.applyTextColorToDevice(failed, red, bgColor=errorBg)
        elif failed:
            self.gridPanel.applyTextColorToDevice(failed, red, bgColor=errorBg)

    @api_tool_decorator
    def onFileDrop(self, event):
        for file in event.Files:
            if file.endswith(".csv"):
                with open(file, "r") as csvFile:
                    reader = csv.reader(
                        csvFile, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True
                    )
                    data = list(reader)
                    if (
                        "apiHost" in data[0]
                        and "apiKey" in data[0]
                        and "apiPrefix" in data[0]
                        and "enterprise" in data[0]
                    ):
                        Globals.csv_auth_path = file
                        self.PopulateConfig(auth=file)
                    else:
                        if not Globals.enterprise_id:
                            self.loadConfigPrompt()
                            return
                        self.processDeviceCSVUpload(data)
                        self.gridPanel.grid_1.AutoSizeColumns()

    @api_tool_decorator
    def onUpdate(self, event):
        if event:
            deviceList = event.GetValue()
            if deviceList:
                for entry in deviceList.values():
                    device = entry[0]
                    deviceInfo = entry[1]
                    self.gridPanel.addDeviceToDeviceGrid(deviceInfo, isUpdate=True)
                    self.gridPanel.addDeviceToNetworkGrid(
                        device, deviceInfo, isUpdate=True
                    )
                if self.gridPanel.grid_1.GetSortingColumn() != wx.NOT_FOUND:
                    self.gridPanel.onDeviceGridSort(
                        self.gridPanel.grid_1.GetSortingColumn()
                    )
                if self.gridPanel.grid_2.GetSortingColumn() != wx.NOT_FOUND:
                    self.gridPanel.onNetworkGridSort(
                        self.gridPanel.grid_2.GetSortingColumn()
                    )
                self.frame_toolbar.EnableTool(self.frame_toolbar.rtool.Id, True)
                self.frame_toolbar.EnableTool(self.frame_toolbar.rftool.Id, True)
                self.frame_toolbar.EnableTool(self.frame_toolbar.cmdtool.Id, True)
                self.sidePanel.runBtn.Enable(True)
                if self.isForceUpdate:
                    self.isForceUpdate = False
                    self.setGaugeValue(100)
                    wx.CallLater(3000, self.setGaugeValue, 0)

    @api_tool_decorator
    def startUpdateThread(self):
        if not self.refresh:
            self.refresh = wxThread.GUIThread(
                self, self.updateGrids, None, eventType=wxThread.myEVT_UPDATE
            )
            self.refresh.start()

    @api_tool_decorator
    def updateGrids(self, event=None):
        if event:
            self.Logging("---> Updating Grids' Data")
            self.frame_toolbar.EnableTool(self.frame_toolbar.rtool.Id, False)
            self.frame_toolbar.EnableTool(self.frame_toolbar.rftool.Id, False)
            self.frame_toolbar.EnableTool(self.frame_toolbar.cmdtool.Id, False)
            self.sidePanel.runBtn.Enable(False)
            self.gauge.Pulse()
            # self.fetchUpdateData(forceUpdate=True)
            thread = wxThread.GUIThread(
                self,
                self.fetchUpdateData,
                (True),
                passArgAsTuple=True,
                eventType=None,
            )
            thread.start()
        else:
            while Globals.ENABLE_GRID_UPDATE:
                time.sleep(Globals.GRID_UPDATE_RATE)
                if self.kill:
                    break
                self.fetchUpdateData()
            self.refresh = None

    @api_tool_decorator
    def fetchUpdateData(self, forceUpdate=False):
        threads = []
        if self.isForceUpdate:
            self.isForceUpdate = forceUpdate
        if (
            not self.isRunning
            and not self.isRunningUpdate
            and (
                (
                    self.gridPanel.grid_1_contents
                    and self.gridPanel.grid_2_contents
                    and len(self.gridPanel.grid_1_contents) <= Globals.MAX_UPDATE_COUNT
                    and len(self.gridPanel.grid_2_contents) <= Globals.MAX_UPDATE_COUNT
                )
                or forceUpdate
            )
        ):
            if Globals.LAST_GROUP_ID and not Globals.LAST_DEVICE_ID:
                self.isRunningUpdate = True
                for groupId in Globals.LAST_GROUP_ID:
                    # TakeAction(self, groupId, 1, None, isUpdate=True)
                    thread = wxThread.GUIThread(
                        self,
                        TakeAction,
                        (self, groupId, 1, None, False, True),
                        eventType=None,
                    )
                    thread.start()
                    threads.append(thread)
            elif Globals.LAST_DEVICE_ID:
                self.isRunningUpdate = True
                for deviceId in Globals.LAST_DEVICE_ID:
                    thread = wxThread.GUIThread(
                        self,
                        TakeAction,
                        (self, deviceId, 1, None, True, True),
                        eventType=None,
                    )
                    thread.start()
                    threads.append(thread)
                    # TakeAction(self, deviceId, 1, None, isDevice=True, isUpdate=True)
            self.isRunningUpdate = False
        joinThreadList(threads)
        evt = wxThread.CustomEvent(wxThread.myEVT_COMPLETE, -1, True)
        wx.PostEvent(self, evt)

    @api_tool_decorator
    def onClone(self, event):
        with TemplateDialog(self.sidePanel.configChoice, parent=self) as self.tmpDialog:
            result = self.tmpDialog.ShowModal()
            if result == wx.ID_OK:
                self.prepareClone(self.tmpDialog)

    @api_tool_decorator
    def prepareClone(self, tmpDialog):
        self.setCursorBusy()
        self.isRunning = True
        self.gauge.Pulse()
        util = templateUtil.EsperTemplateUtil(*tmpDialog.getInputSelections())
        clone = wxThread.GUIThread(
            self,
            util.prepareTemplate,
            (tmpDialog.destTemplate, tmpDialog.chosenTemplate),
            eventType=None,
        )
        clone.start()

    @api_tool_decorator
    def confirmClone(self, event):
        result = None
        res = None
        (util, toApi, toKey, toEntId, templateFound, missingApps) = event.GetValue()
        if Globals.SHOW_TEMPLATE_DIALOG:
            result = CheckboxMessageBox(
                "Confirmation",
                "The %s will attempt to clone to template.\nThe following apps are missing: %s\n\nContinue?"
                % (Globals.TITLE, missingApps if missingApps else None),
            )
            res = result.ShowModal()
        else:
            res = wx.ID_OK
        if res == wx.ID_OK:
            clone = wxThread.GUIThread(
                self,
                self.createClone,
                (util, templateFound, toApi, toKey, toEntId, False),
                eventType=None,
            )
            clone.start()
        else:
            self.isRunning = False
            self.setGaugeValue(0)
            self.setCursorDefault()
        if result and result.getCheckBoxValue():
            Globals.SHOW_TEMPLATE_DIALOG = False

    @api_tool_decorator
    def confirmCloneUpdate(self, event):
        result = None
        res = None
        (util, toApi, toKey, toEntId, templateFound, missingApps) = event.GetValue()
        if Globals.SHOW_TEMPLATE_UPDATE:
            result = CheckboxMessageBox(
                "Confirmation",
                "The Template already exists on the destination endpoint.\nThe following apps are missing: %s\n\nWould you like to update th template?"
                % (missingApps if missingApps else None),
            )
            res = result.ShowModal()
        else:
            res = wx.ID_OK
        if res == wx.ID_OK:
            clone = wxThread.GUIThread(
                self,
                self.createClone,
                (util, templateFound, toApi, toKey, toEntId, True),
                eventType=None,
            )
            clone.start()
        else:
            self.isRunning = False
            self.setGaugeValue(0)
            self.setCursorDefault()
        if result and result.getCheckBoxValue():
            Globals.SHOW_TEMPLATE_UPDATE = False

    @api_tool_decorator
    def createClone(self, util, templateFound, toApi, toKey, toEntId, update=False):
        templateFound = util.processDeviceGroup(templateFound)
        templateFound = util.processWallpapers(templateFound)
        self.Logging("Attempting to copy template...")
        res = None
        if update:
            res = util.updateTemplate(toApi, toKey, toEntId, templateFound)
        else:
            res = util.createTemplate(toApi, toKey, toEntId, templateFound)
        if "errors" not in res:
            action = "created" if not update else "updated."
            self.Logging("Template sucessfully %s." % action)
            wx.MessageBox(
                "Template sucessfully %s." % action, style=wx.OK | wx.ICON_INFORMATION
            )
        else:
            action = "recreate" if not update else "update"
            self.Logging("ERROR: Failed to %s Template.%s" % (action, res))
            wx.MessageBox(
                "ERROR: Failed to %s Template. Please try again." % action,
                style=wx.OK | wx.ICON_ERROR,
            )
        self.isRunning = False
        evt = wxThread.CustomEvent(wxThread.myEVT_COMPLETE, -1, None)
        wx.PostEvent(self, evt)

    def checkForInternetAccess(self):
        while not self.kill:
            if not checkEsperInternetConnection():
                wx.MessageBox(
                    "ERROR: An internet connection is required when using the tool!",
                    style=wx.OK | wx.ICON_ERROR,
                )
            time.sleep(15)

    def onChar(self, event):
        event.Skip()
        wx.CallAfter(self.onSearch, wx.EVT_CHAR.typeId)

    @api_tool_decorator
    def onSearch(self, event=None):
        queryString = ""
        if hasattr(event, "GetString"):
            queryString = event.GetString()
        elif isinstance(event, str):
            queryString = event
        else:
            queryString = self.frame_toolbar.search.GetValue()
        if (
            hasattr(event, "EventType")
            and (
                (wx.EVT_TEXT.typeId == event.EventType and not queryString)
                or (wx.EVT_SEARCH.typeId == event.EventType and not queryString)
                or wx.EVT_SEARCH_CANCEL.typeId == event.EventType
            )
            or wx.EVT_CHAR.typeId == event
        ):
            white = wx.Colour(255, 255, 255)
            self.gridPanel.applyTextColorMatchingGridRow(
                self.gridPanel.grid_1, queryString, white, True
            )
            self.gridPanel.applyTextColorMatchingGridRow(
                self.gridPanel.grid_2, queryString, white, True
            )
        if queryString:
            light_yellow = wx.Colour(255, 255, 224)
            self.gridPanel.applyTextColorMatchingGridRow(
                self.gridPanel.grid_1, queryString, light_yellow
            )
            self.gridPanel.applyTextColorMatchingGridRow(
                self.gridPanel.grid_2, queryString, light_yellow
            )
            self.Logging("--> Search for %s completed" % queryString)
        else:
            self.frame_toolbar.search.SetValue("")
