#!/usr/bin/env python

import sys
import threading
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

from Common.enum import Color, GeneralActions, GridActions

from datetime import datetime

from GUI.sidePanel import SidePanel
from GUI.gridPanel import GridPanel
from GUI.toolBar import ToolsToolBar
from GUI.menuBar import ToolMenuBar
from GUI.consoleWindow import Console
from GUI.Dialogs.CheckboxMessageBox import CheckboxMessageBox
from GUI.Dialogs.TemplateDialog import TemplateDialog
from GUI.Dialogs.CommandDialog import CommandDialog
from GUI.Dialogs.PreferencesDialog import PreferencesDialog
from GUI.Dialogs.ConfirmTextDialog import ConfirmTextDialog
from GUI.Dialogs.InstalledDevicesDlg import InstalledDevicesDlg

from GUI.Dialogs.NewEndpointDialog import NewEndpointDialog

from Common.decorator import api_tool_decorator

from pathlib import Path

from Utility.ApiToolLogging import ApiToolLog
from Utility.crypto import crypto
from Utility.EsperAPICalls import (
    getInstallDevices,
    setAppState,
    setKiosk,
    setMulti,
    getdeviceapps,
    getAllDevices,
    getAllGroups,
    getAllApplications,
    validateConfiguration,
    getTokenInfo,
    clearAppData,
)
from Utility.EastUtility import (
    TakeAction,
    createCommand,
    iterateThroughGridRows,
    processInstallDevices,
)
from Utility.Resource import (
    checkForInternetAccess,
    limitActiveThreads,
    postEventToFrame,
    resourcePath,
    createNewFile,
    joinThreadList,
    displayMessageBox,
    updateErrorTracker,
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
        self.isSavingPrefs = False
        self.isRunningUpdate = False
        self.isForceUpdate = False
        self.kill = False
        self.CSVUploaded = False
        self.defaultDir = os.getcwd()

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
            self.keyPath = "%s\\EsperApiTool\\east.key" % tempfile.gettempdir().replace(
                "Local", "Roaming"
            ).replace("Temp", "")
        else:
            self.WINDOWS = False
            self.prefPath = "%s/EsperApiTool/prefs.json" % os.path.expanduser(
                "~/Desktop/"
            )
            self.authPath = "%s/EsperApiTool/auth.csv" % os.path.expanduser(
                "~/Desktop/"
            )
            self.keyPath = "%s/EsperApiTool/east.key" % os.path.expanduser("~/Desktop/")

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
        self.Bind(wx.EVT_QUERY_END_SESSION, self.OnQuit)
        self.Bind(wx.EVT_END_SESSION, self.OnQuit)
        self.Bind(wx.EVT_END_PROCESS, self.OnQuit)
        self.Bind(wx.EVT_BUTTON, self.onRun, self.sidePanel.runBtn)

        # Menu Bar
        self.menubar = ToolMenuBar(self)
        self.SetMenuBar(self.menubar)
        # Menu Bar end

        # Tool Bar
        self.frame_toolbar = ToolsToolBar(self, -1)
        self.SetToolBar(self.frame_toolbar)
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
        self.Bind(wxThread.EVT_APPS, self.addAppsToAppChoice)
        self.Bind(wxThread.EVT_RESPONSE, self.performAPIResponse)
        self.Bind(wxThread.EVT_COMPLETE, self.onComplete)
        self.Bind(wxThread.EVT_LOG, self.onLog)
        self.Bind(wxThread.EVT_COMMAND, self.onCommandDone)
        self.Bind(wxThread.EVT_UPDATE_GAUGE, self.setGaugeValue)
        self.Bind(wxThread.EVT_UPDATE_TAG_CELL, self.gridPanel.updateTagCell)
        self.Bind(wxThread.EVT_UPDATE_GRID_CONTENT, self.gridPanel.updateGridContent)
        self.Bind(wxThread.EVT_UNCHECK_CONSOLE, self.menubar.uncheckConsole)
        self.Bind(wxThread.EVT_ON_FAILED, self.onFail)
        self.Bind(wxThread.EVT_CONFIRM_CLONE, self.confirmClone)
        self.Bind(wxThread.EVT_CONFIRM_CLONE_UPDATE, self.confirmCloneUpdate)
        self.Bind(wxThread.EVT_MESSAGE_BOX, displayMessageBox)
        self.Bind(wxThread.EVT_THREAD_WAIT, self.waitForThreadsThenSetCursorDefault)
        self.Bind(wx.EVT_ACTIVATE_APP, self.MacReopenApp)
        self.Bind(wx.EVT_ACTIVATE, self.onActivate)

        if self.kill:
            return

        self.loadPref()
        self.__set_properties()
        self.Layout()
        self.Centre()
        self.Raise()
        self.Iconize(False)
        self.SetFocus()

        if self.kill:
            return

        self.menubar.checkCollectionEnabled()
        internetCheck = wxThread.GUIThread(
            self, checkForInternetAccess, (self), name="InternetCheck"
        )
        internetCheck.start()
        errorTracker = wxThread.GUIThread(
            self, updateErrorTracker, None, name="updateErrorTracker"
        )
        errorTracker.start()

    @api_tool_decorator
    def __set_properties(self):
        self.SetTitle(Globals.TITLE)
        self.SetBackgroundColour(Color.grey.value)
        self.SetThemeEnabled(False)

        if self.kill:
            return

        maxInt = sys.maxsize

        while True:
            try:
                csv.field_size_limit(maxInt)
                break
            except OverflowError:
                maxInt = int(maxInt / 10)

        self.frame_toolbar.Realize()

    @api_tool_decorator
    def onLog(self, event):
        """ Event trying to log data """
        evtValue = event.GetValue()
        self.Logging(evtValue)

    @api_tool_decorator
    def Logging(self, entry, isError=False):
        """ Frame UI Logging """
        try:
            entry = entry.replace("\n", " ")
            shortMsg = entry
            Globals.LOGLIST.append(entry)
            while len(Globals.LOGLIST) > Globals.MAX_LOG_LIST_SIZE:
                Globals.LOGLIST.pop(0)
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
                            displayMessageBox(
                                ("Endpoint has been added", wx.ICON_INFORMATION)
                            )
                        else:
                            displayMessageBox(
                                (
                                    "ERROR: Invalid input in Configuration. Check inputs!",
                                    wx.ICON_ERROR,
                                )
                            )
                    except:
                        displayMessageBox(
                            (
                                "ERROR: An error occured when attempting to add the endpoint. Check inputs values and your internet connection.",
                                wx.ICON_ERROR,
                            )
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
        if os.path.exists(self.authPath):
            if self.key and crypto().isFileDecrypt(self.authPath, self.key):
                crypto().encryptFile(self.authPath, self.key)
        if self.consoleWin:
            self.consoleWin.Close()
            self.consoleWin.DestroyLater()
            self.consoleWin = None
        if self.prefDialog:
            self.prefDialog.Close()
            self.prefDialog.DestroyLater()
        if e:
            if e.EventType != wx.EVT_CLOSE.typeId:
                self.Close()
        self.savePrefs(self.prefDialog)
        self.DestroyLater()

    @api_tool_decorator
    def onSaveBoth(self, event):
        if self.gridPanel.grid_1.GetNumberRows() > 0:
            dlg = wx.FileDialog(
                self,
                message="Save Device and Network Info CSV as...",
                defaultFile="",
                wildcard="*.csv",
                defaultDir=str(self.defaultDir),
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            )
            result = dlg.ShowModal()
            inFile = dlg.GetPath()
            dlg.DestroyLater()

            if result == wx.ID_OK:  # Save button was pressed
                self.defaultDir = Path(inFile).parent
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
                headersNoDup = []
                [headersNoDup.append(x) for x in headers if x not in headersNoDup]
                headers = headersNoDup

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
            displayMessageBox(
                ("Please load a configuration first!", wx.OK | wx.ICON_ERROR)
            )
            return

        if self.isRunning:
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
            defaultDir=str(self.defaultDir),
        ) as fileDialog:
            result = fileDialog.ShowModal()
            if result == wx.ID_OK:
                # Proceed loading the file chosen by the user
                csv_auth_path = fileDialog.GetPath()
                self.defaultDir = Path(fileDialog.GetPath()).parent
                self.Logging(
                    "--->Attempting to load device data from %s" % csv_auth_path
                )
                try:
                    with open(csv_auth_path, "r", encoding="utf-8-sig") as csvFile:
                        reader = csv.reader(
                            csvFile, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True
                        )
                        data = list(reader)
                        self.processDeviceCSVUpload(data)
                        self.gridPanel.grid_1.AutoSizeColumns()
                except UnicodeDecodeError as e:
                    with open(csv_auth_path, "r") as csvFile:
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
        self.toggleEnabledState(False)
        self.sidePanel.groupChoice.Enable(False)
        self.sidePanel.deviceChoice.Enable(False)
        self.gridPanel.disableGridProperties()
        self.gridPanel.grid_1.Freeze()
        self.gridPanel.grid_2.Freeze()
        self.processCsvDataByGrid(
            self.gridPanel.grid_1,
            data,
            Globals.CSV_TAG_ATTR_NAME,
            Globals.grid1_lock,
        )
        self.processCsvDataByGrid(
            self.gridPanel.grid_2,
            data,
            Globals.CSV_NETWORK_ATTR_NAME,
            Globals.grid2_lock,
        )
        indx = self.sidePanel.actionChoice.GetItems().index(
            list(Globals.GRID_ACTIONS.keys())[1]
        )
        self.sidePanel.actionChoice.SetSelection(indx)
        if self.gridPanel.grid_1.IsFrozen():
            self.gridPanel.grid_1.Thaw()
        if self.gridPanel.grid_2.IsFrozen():
            self.gridPanel.grid_2.Thaw()
        self.gridPanel.enableGridProperties()
        self.gridPanel.autoSizeGridsColumns()
        self.sidePanel.groupChoice.Enable(True)
        self.sidePanel.deviceChoice.Enable(True)
        self.toggleEnabledState(True)

    @api_tool_decorator
    def processCsvDataByGrid(self, grid, data, headers, lock=None):
        if lock:
            lock.acquire()
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
        if lock:
            lock.release()

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
                    self.Logging("--->ERROR: Empty Auth File, please add an Endpoint!")
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

    @api_tool_decorator
    def setCursorDefault(self):
        """ Set cursor icon to default state """
        try:
            self.isBusy = False
            myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
            self.SetCursor(myCursor)
        except:
            pass

    @api_tool_decorator
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
        Globals.LAST_DEVICE_ID = []
        Globals.LAST_GROUP_ID = []
        self.sidePanel.groups = {}
        self.sidePanel.devices = {}
        self.sidePanel.clearGroupAndDeviceSelections()
        self.sidePanel.destroyMultiChoiceDialogs()
        self.sidePanel.deviceChoice.Enable(False)
        self.sidePanel.removeEndpointBtn.Enable(False)
        self.sidePanel.appChoice.Clear()
        self.toggleEnabledState(False)
        self.setCursorBusy()

        for thread in threading.enumerate():
            if thread.name == "fetchUpdateDataActionThread":
                if hasattr(thread, "stop"):
                    thread.stop()

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
            self.sidePanel.configList.ShowPosition(0)

            if "https" in str(host):
                Globals.configuration.host = host.strip()
                Globals.configuration.api_key["Authorization"] = key.strip()
                Globals.configuration.api_key_prefix["Authorization"] = prefix.strip()
                Globals.enterprise_id = entId.strip()

                res = getTokenInfo()
                if res and hasattr(res, "expires_on"):
                    if res.expires_on <= datetime.now(res.expires_on.tzinfo) or not res:
                        raise Exception(
                            "API Token has expired! Please replace Configuration entry by adding endpoint with a new API Key."
                        )
                # else:
                #     raise Exception(
                #         "Failed to fetch API Token Info! Please replace Configuration entry by adding endpoint with a new API Key."
                #     )

                groupThread = self.PopulateGroups()
                appThread = self.PopulateApps()
                threads = [groupThread, appThread]
                wxThread.GUIThread(
                    self,
                    self.waitForThreadsThenSetCursorDefault,
                    (threads, 0),
                    name="waitForThreadsThenSetCursorDefault_0",
                ).start()
                return True
        else:
            displayMessageBox(("Invalid Configuration", wx.ICON_ERROR))
            return False

    @api_tool_decorator
    def waitForThreadsThenSetCursorDefault(self, threads, source=None, action=None):
        if hasattr(threads, "GetValue"):
            evtVal = threads.GetValue()
            threads = evtVal[0]
            if len(evtVal) > 1:
                source = evtVal[1]
            if len(evtVal) > 2:
                action = evtVal[2]
        joinThreadList(threads)
        if source == 0:
            self.sidePanel.sortAndPopulateAppChoice()
            self.sidePanel.groupChoice.Enable(True)
            self.sidePanel.actionChoice.Enable(True)
            self.sidePanel.removeEndpointBtn.Enable(True)
        if source == 1:
            if not self.sidePanel.devices:
                self.sidePanel.selectedDevices.Append("No Devices Found", "")
                self.sidePanel.deviceChoice.Enable(False)
                self.Logging("---> No Devices found")
            else:
                if (
                    self.preferences
                    and "getAppsForEachDevice" in self.preferences
                    and self.preferences["getAppsForEachDevice"]
                ):
                    newThreads = []
                    self.Logging("---> Attempting to populate Application list")
                    self.gauge.Pulse()
                    for deviceId in self.sidePanel.devices.values():
                        thread = wxThread.doAPICallInThread(
                            self,
                            getdeviceapps,
                            args=(deviceId, True, Globals.USE_ENTERPRISE_APP),
                            eventType=wxThread.myEVT_APPS,
                            waitForJoin=False,
                            name="GetDeviceAppsToPopulateApps",
                        )
                        newThreads.append(thread)
                        limitActiveThreads(newThreads)
                    num = 0
                    for thread in newThreads:
                        thread.join()
                        num += 1
                        if (
                            not self.preferences
                            or self.preferences["enableDevice"] == True
                        ):
                            self.setGaugeValue(
                                int(float(num / len(newThreads) / 2) * 100)
                            )
                self.sidePanel.sortAndPopulateAppChoice()
                self.Logging("---> Application list populated")
                if not self.isRunning:
                    self.menubar.enableConfigMenu()
            if not self.preferences or self.preferences["enableDevice"] == True:
                self.sidePanel.deviceChoice.Enable(True)
            else:
                self.sidePanel.deviceChoice.Enable(False)
        if source == 2:
            indx = self.sidePanel.actionChoice.GetItems().index(
                list(Globals.GRID_ACTIONS.keys())[1]
            )
            self.sidePanel.actionChoice.SetSelection(indx)
            if self.gridPanel.grid_1.IsFrozen():
                self.gridPanel.grid_1.Thaw()
            if self.gridPanel.grid_2.IsFrozen():
                self.gridPanel.grid_2.Thaw()
            self.gridPanel.enableGridProperties()
            self.gridPanel.autoSizeGridsColumns()
            self.sidePanel.groupChoice.Enable(True)
            self.sidePanel.deviceChoice.Enable(True)
        if source == 3:
            cmdResults = []
            if (
                action == GeneralActions.SET_KIOSK.value
                or action == GeneralActions.SET_MULTI.value
                or action == GeneralActions.SET_APP_STATE_DISABLE.value
                or action == GeneralActions.SET_APP_STATE_HIDE.value
                or action == GeneralActions.SET_APP_STATE_SHOW.value
                or action == GridActions.SET_APP_STATE_DISABLE.value
                or action == GridActions.SET_APP_STATE_HIDE.value
                or action == GridActions.SET_APP_STATE_SHOW.value
            ):
                for t in threads:
                    if t.result:
                        if type(t.result) == list:
                            cmdResults = cmdResults + t.result
                        else:
                            cmdResults.append(t.result)
            postEventToFrame(wxThread.myEVT_COMPLETE, (True, action, cmdResults))
        self.toggleEnabledState(not self.isRunning and not self.isSavingPrefs)
        self.setCursorDefault()
        self.setGaugeValue(100)

    @api_tool_decorator
    def PopulateGroups(self):
        """ Populate Group Choice """
        self.sidePanel.groupChoice.Enable(False)
        self.Logging("--->Attempting to populate groups...")
        self.setCursorBusy()
        self.setGaugeValue(0)
        self.gauge.Pulse()
        thread = wxThread.doAPICallInThread(
            self,
            getAllGroups,
            eventType=wxThread.myEVT_GROUP,
            waitForJoin=False,
            name="PopulateGroupsGetAll",
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
        self.sidePanel.groupChoice.Enable(True)
        self.sidePanel.actionChoice.Enable(True)

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
            if not self.isRunning or not self.isBusy:
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
                name="AddDevicesToDeviceChoice",
            )
            threads.append(thread)
        wxThread.GUIThread(
            self,
            self.waitForThreadsThenSetCursorDefault,
            (threads, 1),
            name="waitForThreadsThenSetCursorDefault_1",
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
            self,
            self.fetchAllApps,
            eventType=None,
            waitForJoin=False,
            name="PopulateApps",
        )
        return thread

    def fetchAllApps(self):
        resp = getAllApplications()
        self.addAppsToAppChoice(resp)

    @api_tool_decorator
    def addAppsToAppChoice(self, event):
        """ Populate App Choice """
        api_response = None
        if hasattr(event, "GetValue"):
            api_response = event.GetValue()
        else:
            api_response = event
        results = None

        if hasattr(api_response, "results"):
            results = api_response.results
        else:
            results = api_response[1]["results"]

        if results and type(results[0]) == dict and "application" in results[0]:
            results = sorted(
                results,
                key=lambda i: i["application"]["application_name"].lower(),
            )
        elif results and hasattr(results[0], "application_name"):
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
            for app in results:
                self.addAppToAppList(app)

    @api_tool_decorator
    def addAppToAppList(self, app):
        entry = None
        if type(app) == dict and "application" in app:
            appName = app["application"]["application_name"]
            appPkgName = appName + (" (%s)" % app["application"]["package_name"])
            entry = {
                "app_name": app["application"]["application_name"],
                appName: app["application"]["package_name"],
                appPkgName: app["application"]["package_name"],
                "id": app["id"],
                "app_state": None,
            }
        elif hasattr(app, "application_name"):
            appName = app.application_name
            appPkgName = appName + (" (%s)" % app.package_name)
            entry = {
                "app_name": app.application_name,
                appName: app.package_name,
                appPkgName: app.package_name,
                "versions": app.versions,
                "id": app.id,
            }
        else:
            appName = app["app_name"]
            appPkgName = appName + (" (%s)" % app["package_name"])
            entry = {
                "app_name": app["app_name"],
                appName: app["package_name"],
                appPkgName: app["package_name"],
                "app_state": app["state"],
                "id": app["id"],
            }
        if entry and entry not in self.sidePanel.enterpriseApps:
            self.sidePanel.enterpriseApps.append(entry)
        if (
            entry
            and self.sidePanel.selectedDevicesList
            and entry not in self.sidePanel.selectedDeviceApps
        ):
            self.sidePanel.selectedDeviceApps.append(entry)
        if (
            entry
            and self.sidePanel.selectedGroupsList
            and entry not in self.sidePanel.knownApps
        ):
            self.sidePanel.knownApps.append(entry)

    @api_tool_decorator
    def onRun(self, event):
        """ Try to run the specifed Action on a group or device """
        if self.isBusy or not self.sidePanel.runBtn.IsEnabled():
            return
        self.setCursorBusy()
        self.isRunning = True
        self.setGaugeValue(0)
        self.toggleEnabledState(False)

        self.gridPanel.grid_1.UnsetSortingColumn()
        self.gridPanel.grid_2.UnsetSortingColumn()

        appSelection = self.sidePanel.appChoice.GetSelection()
        actionSelection = self.sidePanel.actionChoice.GetSelection()
        actionClientData = self.sidePanel.actionChoice.GetClientData(actionSelection)

        appLabel = (
            self.sidePanel.appChoice.Items[appSelection]
            if len(self.sidePanel.appChoice.Items) > 0
            and self.sidePanel.appChoice.Items[appSelection]
            else ""
        )
        actionLabel = (
            self.sidePanel.actionChoice.Items[actionSelection]
            if len(self.sidePanel.actionChoice.Items) > 0
            and self.sidePanel.actionChoice.Items[actionSelection]
            else ""
        )
        if (
            self.sidePanel.selectedGroupsList
            and not self.sidePanel.selectedDevicesList
            and actionSelection > 0
            and actionClientData > 0
            and actionClientData < GridActions.MODIFY_ALIAS_AND_TAGS.value
        ):
            # run action on group
            if (
                actionClientData == GeneralActions.SET_KIOSK.value
                or actionClientData == GeneralActions.CLEAR_APP_DATA.value
            ) and (
                appSelection < 0 or appLabel == "No available app(s) on this device"
            ):
                displayMessageBox(
                    ("Please select a valid application", wx.OK | wx.ICON_ERROR)
                )
                self.isRunning = False
                self.setCursorDefault()
                self.toggleEnabledState(True)
                return
            self.gridPanel.grid_1_contents = []
            self.gridPanel.grid_2_contents = []
            self.gridPanel.userEdited = []
            self.gridPanel.disableGridProperties()
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
            self.gauge.Pulse()
            wxThread.GUIThread(
                self,
                TakeAction,
                (
                    self,
                    self.sidePanel.selectedGroupsList,
                    actionClientData,
                    groupLabel,
                ),
                name="TakeActionOnGroups",
            ).start()
        elif (
            self.sidePanel.selectedDevicesList
            and actionSelection > 0
            and actionClientData > 0
            and actionClientData < GridActions.MODIFY_ALIAS_AND_TAGS.value
        ):
            # run action on device
            if (
                actionClientData == GeneralActions.SET_KIOSK.value
                or actionClientData == GeneralActions.CLEAR_APP_DATA.value
            ) and (
                appSelection < 0 or appLabel == "No available app(s) on this device"
            ):
                displayMessageBox(
                    ("Please select a valid application", wx.OK | wx.ICON_ERROR)
                )
                self.isRunning = False
                self.setCursorDefault()
                self.toggleEnabledState(True)
                return
            self.gridPanel.grid_1_contents = []
            self.gridPanel.grid_2_contents = []
            self.gridPanel.userEdited = []
            self.gridPanel.disableGridProperties()
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
            self.gauge.Pulse()
            wxThread.GUIThread(
                self,
                TakeAction,
                (
                    self,
                    self.sidePanel.selectedDevicesList,
                    actionClientData,
                    None,
                    True,
                ),
                name="TakeActionOnDevices",
            ).start()
        elif actionClientData >= GridActions.MODIFY_ALIAS_AND_TAGS.value:
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
                    self.preferences["gridDialog"] = Globals.SHOW_GRID_DIALOG
                if runAction:
                    self.Logging(
                        '---> Attempting to run grid action, "%s".'
                        % GridActions.MODIFY_ALIAS_AND_TAGS.name
                    )
                    self.gridPanel.applyTextColorToDevice(
                        None,
                        Color.black.value,
                        bgColor=Color.white.value,
                        applyAll=True,
                    )
                    self.gridPanel.disableGridProperties()
                    self.frame_toolbar.search.SetValue("")
                    self.gauge.Pulse()
                    wxThread.GUIThread(
                        self,
                        iterateThroughGridRows,
                        (self, actionClientData),
                        name="iterateThroughGridRows",
                    ).start()
            else:
                displayMessageBox(
                    (
                        "Make sure the grid has data to perform the action on",
                        wx.OK | wx.ICON_ERROR,
                    )
                )
                self.isRunning = False
                self.setCursorDefault()
                self.toggleEnabledState(True)
        else:
            displayMessageBox(
                (
                    "Please select an valid action to perform on the selected group(s) or device(s)!",
                    wx.OK | wx.ICON_ERROR,
                )
            )
            self.isRunning = False
            self.setCursorDefault()
            self.toggleEnabledState(True)

    @api_tool_decorator
    def showConsole(self, event):
        """ Toggle Console Display """
        if not self.consoleWin:
            self.consoleWin = Console(parent=self)
            self.menubar.clearConsole.Enable(True)
            self.Bind(wx.EVT_MENU, self.onClear, self.menubar.clearConsole)
        else:
            self.consoleWin.DestroyLater()
            self.menubar.clearConsole.Enable(False)

    @api_tool_decorator
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
                        cmdArgs = None
                        commandType = None
                        schArgs = None
                        schType = None
                        try:
                            (
                                cmdArgs,
                                commandType,
                                schArgs,
                                schType,
                            ) = cmdDialog.GetValue()
                        except Exception as e:
                            displayMessageBox(
                                (
                                    "An error occurred while process the inputted JSON object, please make sure it is formatted correctly",
                                    wx.OK | wx.ICON_ERROR,
                                )
                            )
                            ApiToolLog().LogError(e)
                        if cmdArgs != None:
                            createCommand(self, cmdArgs, commandType, schArgs, schType)
            else:
                displayMessageBox(
                    ("Please select an group and or device", wx.OK | wx.ICON_ERROR)
                )

            self.setCursorDefault()

    @api_tool_decorator
    def onCommandDone(self, event):
        """ Tell user to check the Esper Console for detailed results """
        cmdResult = None
        if hasattr(event, "GetValue"):
            cmdResult = event.GetValue()
        else:
            cmdResult = event
        self.menubar.enableConfigMenu()
        self.setGaugeValue(100)
        if cmdResult:
            result = ""
            for res in cmdResult:
                formattedRes = ""
                try:
                    formattedRes = json.dumps(res, indent=2).replace("\\n", "\n")
                except:
                    formattedRes = json.dumps(str(res), indent=2).replace("\\n", "\n")
                if formattedRes:
                    result += formattedRes
                    result += "\n\n"
            with ConfirmTextDialog(
                "Command(s) have been fired.",
                "Check the Esper Console for details. Last command status listed below.",
                "Command(s) have been fired.",
                result,
            ) as dialog:
                res = dialog.ShowModal()
        wx.CallLater(3000, self.setGaugeValue, 0)

    @api_tool_decorator
    def setStatus(self, status, orgingalMsg, isError=False):
        """ Set status bar text """
        self.sbText.SetLabel(status)
        if orgingalMsg:
            self.sbText.SetToolTip(orgingalMsg.replace("--->", ""))
        if isError:
            self.sbText.SetForegroundColour(Color.red.value)
        else:
            self.sbText.SetForegroundColour(Color.black.value)

    @api_tool_decorator
    def onFetch(self, event):
        self.gauge.Pulse()
        evtValue = event.GetValue()
        if evtValue:
            action = evtValue[0]
            entId = evtValue[1]
            deviceList = evtValue[2]

            wxThread.GUIThread(
                self,
                self.processFetch,
                (action, entId, deviceList, True, len(deviceList) * 2),
                name="ProcessFetch",
            ).start()

    @api_tool_decorator
    def processFetch(self, action, entId, deviceList, updateGauge=False, maxGauge=None):
        """ Given device data perform the specified action """
        threads = []
        appToUse = None
        appSelection = self.sidePanel.appChoice.GetSelection()
        if appSelection > 0:
            appToUse = self.sidePanel.appChoice.GetClientData(appSelection)
        if action == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value:
            self.gridPanel.disableGridProperties()
        num = len(deviceList)
        for entry in deviceList.values():
            if entId != Globals.enterprise_id:
                self.onClearGrids(None)
                break
            if hasattr(threading.current_thread(), "isStopped"):
                if threading.current_thread().isStopped():
                    self.onClearGrids(None)
                    break
            device = entry[0]
            deviceInfo = entry[1]
            if action == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value:
                self.gridPanel.addDeviceToDeviceGrid(deviceInfo)
                self.gridPanel.addDeviceToNetworkGrid(device, deviceInfo)
            elif action == GeneralActions.SET_KIOSK.value:
                thread = wxThread.GUIThread(
                    self, setKiosk, (self, device, deviceInfo), name="SetKiosk"
                )
                thread.start()
                threads.append(thread)
            elif action == GeneralActions.SET_MULTI.value:
                thread = wxThread.GUIThread(
                    self, setMulti, (self, device, deviceInfo), name="SetMulti"
                )
                thread.start()
                threads.append(thread)
            elif action == GeneralActions.CLEAR_APP_DATA.value:
                clearAppData(self, device)
            elif action == GeneralActions.SET_APP_STATE_DISABLE.value:
                thread = wxThread.GUIThread(
                    self,
                    setAppState,
                    (device.id, appToUse, None, "DISABLE"),
                    name="SetAppDisable",
                )
                thread.start()
                threads.append(thread)
            elif action == GeneralActions.SET_APP_STATE_HIDE.value:
                thread = wxThread.GUIThread(
                    self,
                    setAppState,
                    (device.id, appToUse, None, "HIDE"),
                    name="SetAppHide",
                )
                thread.start()
                threads.append(thread)
            elif action == GeneralActions.SET_APP_STATE_SHOW.value:
                thread = wxThread.GUIThread(
                    self,
                    setAppState,
                    (device.id, appToUse, None, "SHOW"),
                    name="SetAppShow",
                )
                thread.start()
                threads.append(thread)
            limitActiveThreads(threads)

            value = int(num / maxGauge * 100)
            if updateGauge and value <= 50:
                num += 1
                self.setGaugeValue(value)
        wxThread.GUIThread(
            self,
            self.waitForThreadsThenSetCursorDefault,
            (threads, 3, action),
            name="waitForThreadsThenSetCursorDefault_3",
        ).start()

    @api_tool_decorator
    def onUpdateComplete(self, event):
        """ Alert user to chcek the Esper Console for detailed results for some actions """
        action = None
        if hasattr(event, "GetValue"):
            action = event.GetValue()
        else:
            action = event
        if action and action == GeneralActions.CLEAR_APP_DATA.value:
            displayMessageBox(
                (
                    "Clear App Data Command has been sent to the device(s). Please check devices' event feeds for command status.",
                    wx.ICON_INFORMATION,
                )
            )

    @api_tool_decorator
    def onDeviceSelections(self, event):
        """ When the user selects a device showcase apps related to that device """
        self.SetFocus()
        self.gauge.Pulse()
        self.setCursorBusy()
        if len(self.sidePanel.selectedDevicesList) > 0:
            self.sidePanel.runBtn.Enable(False)
            wxThread.GUIThread(
                self,
                self.addDevicesApps,
                args=None,
                eventType=wxThread.myEVT_COMPLETE,
                eventArg=(not self.isRunning and not self.isSavingPrefs),
                sendEventArgInsteadOfResult=True,
                name="addDeviceApps",
            ).start()
        else:
            evt = wxThread.CustomEvent(wxThread.myEVT_COMPLETE, -1, True)
            wx.PostEvent(self, evt)

    @api_tool_decorator
    def addDevicesApps(self):
        num = 1
        appAdded = False
        self.sidePanel.deviceApps = []
        self.sidePanel.apps = self.sidePanel.knownApps + self.sidePanel.enterpriseApps
        for deviceId in self.sidePanel.selectedDevicesList:
            appList, _ = getdeviceapps(
                deviceId, createAppList=True, useEnterprise=Globals.USE_ENTERPRISE_APP
            )

            for app in appList:
                appAdded = True
                app_name = app.split(" v")[0]
                entry = [app for app in self.sidePanel.apps if app_name in app]
                if entry:
                    entry = entry[0]
                if entry and entry not in self.sidePanel.selectedDeviceApps:
                    self.sidePanel.selectedDeviceApps.append(entry)
            self.setGaugeValue(
                int(float(num / len(self.sidePanel.selectedDevicesList)) * 100)
            )
            num += 1
        if not appAdded:
            self.sidePanel.appChoice.Append("No available app(s) on this device")
            self.sidePanel.appChoice.SetSelection(0)

    @api_tool_decorator
    def MacReopenApp(self, event):
        """Called when the doc icon is clicked, and ???"""
        self.onActivate(self, event, skip=False)
        if event.GetActive():
            try:
                self.GetTopWindow().Raise()
            except:
                pass
        event.Skip()

    @api_tool_decorator
    def MacNewFile(self):
        pass

    @api_tool_decorator
    def MacPrintFile(self, file_path):
        pass

    @api_tool_decorator
    def setGaugeValue(self, value):
        """ Attempt to set Gauge to the specififed value """
        if Globals.gauge_lock.locked():
            return
        Globals.gauge_lock.acquire()
        if hasattr(value, "GetValue"):
            value = value.GetValue()
        maxValue = self.gauge.GetRange()
        if value > maxValue:
            value = maxValue
        if value < 0:
            value = 0
        if value >= 0 and value <= maxValue:
            self.gauge.SetValue(value)
        Globals.gauge_lock.release()

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
                if type(cbArgs) == tuple and type(optCbArgs) == tuple:
                    wxThread.GUIThread(
                        self, callback, (*cbArgs, response, *optCbArgs)
                    ).start()
                elif type(cbArgs) == tuple and type(optCbArgs) != tuple:
                    wxThread.GUIThread(
                        self, callback, (*cbArgs, response, optCbArgs)
                    ).start()
                elif type(cbArgs) != tuple and type(optCbArgs) == tuple:
                    wxThread.GUIThread(
                        self, callback, (cbArgs, response, *optCbArgs)
                    ).start()
                elif type(cbArgs) != tuple and type(optCbArgs) != tuple:
                    wxThread.GUIThread(
                        self, callback, (cbArgs, response, optCbArgs)
                    ).start()
            else:
                if type(cbArgs) == tuple:
                    wxThread.GUIThread(self, callback, (*cbArgs, response)).start()
                else:
                    wxThread.GUIThread(self, callback, (cbArgs, response)).start()

    @api_tool_decorator
    def onComplete(self, event):
        """ Things that should be done once an Action is completed """
        enable = False
        action = None
        cmdResults = None
        if event:
            eventVal = event.GetValue()
            if type(eventVal) == tuple:
                enable = eventVal[0]
                if len(eventVal) > 1:
                    action = eventVal[1]
                if len(eventVal) > 2:
                    cmdResults = eventVal[2]
            else:
                enable = eventVal
        self.setCursorDefault()
        self.setGaugeValue(100)
        if self.IsFrozen():
            self.Thaw()
        if self.gridPanel.grid_1.IsFrozen():
            self.gridPanel.grid_1.Thaw()
        if self.gridPanel.grid_2.IsFrozen():
            self.gridPanel.grid_2.Thaw()
        if self.gridPanel.disableProperties:
            self.gridPanel.enableGridProperties()
        self.gridPanel.autoSizeGridsColumns()
        if self.isRunning or enable:
            self.toggleEnabledState(True)
        self.isRunning = False
        self.sidePanel.sortAndPopulateAppChoice()
        if not self.IsIconized() and self.IsActive():
            wx.CallLater(3000, self.setGaugeValue, 0)
        if action:
            self.onUpdateComplete(action)
        if cmdResults:
            self.onCommandDone(cmdResults)
        self.menubar.enableConfigMenu()
        self.Logging("---> Completed Action")

    @api_tool_decorator
    def onActivate(self, event, skip=True):
        if not self.isRunning:
            wx.CallLater(3000, self.setGaugeValue, 0)
        if skip:
            event.Skip()

    @api_tool_decorator
    def onClearGrids(self, event):
        """ Empty Grids """
        thread = wxThread.GUIThread(
            self,
            self.gridPanel.emptyDeviceGrid,
            None,
            eventType=None,
            name="emptyDeviceGrid",
        )
        thread.start()
        netThread = wxThread.GUIThread(
            self,
            self.gridPanel.emptyNetworkGrid,
            None,
            eventType=None,
            name="emptyNetworkGrid",
        )
        netThread.start()

    @api_tool_decorator
    def readAuthCSV(self):
        if os.path.exists(Globals.csv_auth_path):
            if self.key and crypto().isFileEncrypt(Globals.csv_auth_path, self.key):
                crypto().decrypt(Globals.csv_auth_path, self.key, True)
            with open(Globals.csv_auth_path, "r") as csvFile:
                reader = csv.reader(
                    csvFile, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True
                )
                self.auth_data = list(reader)

    @api_tool_decorator
    def loadPref(self):
        """ Attempt to load preferences from file system """
        if not os.path.exists(self.keyPath):
            self.key = crypto().create_key(self.keyPath)
        else:
            self.key = crypto().load_key(self.keyPath)
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
            if os.path.getsize(self.prefPath) > 2:
                with open(self.prefPath) as jsonFile:
                    if jsonFile:
                        try:
                            self.preferences = json.load(jsonFile)
                        except Exception as e:
                            ApiToolLog().LogError(e)
                            self.Logging(
                                "Preference file possibly has been corrupted and is malformed!",
                                isError=True,
                            )
                self.prefDialog.SetPrefs(self.preferences)
            else:
                self.Logging("Missing or empty preference file!", isError=True)
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

    @api_tool_decorator
    def onPref(self, event):
        """ Update Preferences when they are changed """
        if self.isRunning:
            return
        self.prefDialog.SetPrefs(self.preferences, onBoot=False)
        if self.prefDialog.ShowModal() == wx.ID_APPLY:
            self.isSavingPrefs = True
            save = wxThread.GUIThread(
                self,
                self.savePrefs,
                (self.prefDialog),
                eventType=None,
                name="SavePrefs",
            )
            save.start()
            if self.sidePanel.selectedGroupsList:
                self.sidePanel.knownApps = []
                self.PopulateDevices(None)
            if self.sidePanel.selectedDevicesList:
                self.sidePanel.selectedDeviceApps = []
                self.onDeviceSelections(None)
        if self.preferences["enableDevice"]:
            self.sidePanel.deviceChoice.Enable(True)
        else:
            self.sidePanel.deviceChoice.Enable(False)
        self.isSavingPrefs = False

    @api_tool_decorator
    def onFail(self, event):
        """ Try to showcase rows in the grid on which an action failed on """
        failed = event.GetValue()
        if self.gridPanel.grid_1_contents and self.gridPanel.grid_2_contents:
            if type(failed) == list:
                for device in failed:
                    if "Queued" in device:
                        self.gridPanel.applyTextColorToDevice(
                            device[0], Color.orange.value, bgColor=Color.warnBg.value
                        )
                    else:
                        self.gridPanel.applyTextColorToDevice(
                            device, Color.red.value, bgColor=Color.errorBg.value
                        )
            elif type(failed) == tuple:
                if "Queued" in failed:
                    self.gridPanel.applyTextColorToDevice(
                        failed[0], Color.orange.value, bgColor=Color.warnBg.value
                    )
                else:
                    self.gridPanel.applyTextColorToDevice(
                        failed, Color.red.value, bgColor=Color.errorBg.value
                    )
            elif failed:
                self.gridPanel.applyTextColorToDevice(
                    failed, Color.red.value, bgColor=Color.errorBg.value
                )

    @api_tool_decorator
    def onFileDrop(self, event):
        if self.isRunning:
            return

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
                        self.PopulateConfig(auth=file)
                    else:
                        if not Globals.enterprise_id:
                            displayMessageBox(
                                (
                                    "Please load a configuration first!",
                                    wx.OK | wx.ICON_ERROR,
                                )
                            )
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
                self.toggleEnabledState(True)
                if self.isForceUpdate:
                    self.isForceUpdate = False
                    self.setGaugeValue(100)
                    wx.CallLater(3000, self.setGaugeValue, 0)

    @api_tool_decorator
    def startUpdateThread(self):
        if not self.refresh:
            self.refresh = wxThread.GUIThread(
                self,
                self.updateGrids,
                None,
                eventType=wxThread.myEVT_UPDATE,
                name="fetchUpdateData",
            )
            self.refresh.start()

    @api_tool_decorator
    def updateGrids(self, event=None):
        if event:
            self.Logging("---> Updating Grids' Data")
            self.toggleEnabledState(False)
            self.gauge.Pulse()
            thread = wxThread.GUIThread(
                self,
                self.fetchUpdateData,
                (True),
                eventType=None,
                name="fetchUpdateData",
            )
            thread.start()
        else:
            while Globals.ENABLE_GRID_UPDATE:
                time.sleep(Globals.GRID_UPDATE_RATE)
                if self.kill:
                    break
                if hasattr(threading.current_thread(), "isStopped"):
                    if threading.current_thread().isStopped():
                        break
                if self.IsActive() and not self.IsIconized():
                    self.fetchUpdateData()
            self.refresh = None

    @api_tool_decorator
    def fetchUpdateData(self, forceUpdate=False):
        if not self.gridPanel.grid_1_contents and not self.gridPanel.grid_2_contents:
            return
        threads = []
        if self.isForceUpdate:
            self.isForceUpdate = forceUpdate
        if (
            not self.isRunning
            and not self.isRunningUpdate
            and self.IsActive()
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
                    thread = wxThread.GUIThread(
                        self,
                        TakeAction,
                        (self, groupId, 1, None, False, True),
                        eventType=None,
                        name="fetchUpdateDataActionThread",
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
                        name="fetchUpdateDataActionThread",
                    )
                    thread.start()
                    threads.append(thread)
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
            name="PrepTemplate",
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
                name="createTemplateClone",
            )
            clone.start()
        else:
            self.isRunning = False
            self.setGaugeValue(0)
            self.setCursorDefault()
        if result and result.getCheckBoxValue():
            Globals.SHOW_TEMPLATE_DIALOG = False
            self.preferences["templateDialog"] = Globals.SHOW_TEMPLATE_DIALOG

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
                name="updateTemplate",
            )
            clone.start()
        else:
            self.isRunning = False
            self.setGaugeValue(0)
            self.setCursorDefault()
        if result and result.getCheckBoxValue():
            Globals.SHOW_TEMPLATE_UPDATE = False
            self.preferences["templateUpdate"] = Globals.SHOW_TEMPLATE_UPDATE

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
            displayMessageBox(
                ("Template sucessfully %s." % action, wx.OK | wx.ICON_INFORMATION)
            )
        else:
            action = "recreate" if not update else "update"
            self.Logging("ERROR: Failed to %s Template.%s" % (action, res))
            displayMessageBox(
                (
                    "ERROR: Failed to %s Template. Please try again." % action,
                    wx.OK | wx.ICON_ERROR,
                )
            )
        self.isRunning = False
        evt = wxThread.CustomEvent(wxThread.myEVT_COMPLETE, -1, None)
        wx.PostEvent(self, evt)

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
            self.gridPanel.applyTextColorMatchingGridRow(
                self.gridPanel.grid_1, queryString, Color.white.value, True
            )
            self.gridPanel.applyTextColorMatchingGridRow(
                self.gridPanel.grid_2, queryString, Color.white.value, True
            )
        if queryString:
            self.gridPanel.applyTextColorMatchingGridRow(
                self.gridPanel.grid_1, queryString, Color.lightYellow.value
            )
            self.gridPanel.applyTextColorMatchingGridRow(
                self.gridPanel.grid_2, queryString, Color.lightYellow.value
            )
            self.Logging("--> Search for %s completed" % queryString)
        else:
            self.frame_toolbar.search.SetValue("")

    @api_tool_decorator
    def toggleEnabledState(self, state):
        self.sidePanel.runBtn.Enable(state)
        self.sidePanel.actionChoice.Enable(state)
        self.sidePanel.removeEndpointBtn.Enable(state)

        self.frame_toolbar.EnableTool(self.frame_toolbar.otool.Id, state)
        self.frame_toolbar.EnableTool(self.frame_toolbar.rtool.Id, state)
        self.frame_toolbar.EnableTool(self.frame_toolbar.rftool.Id, state)
        self.frame_toolbar.EnableTool(self.frame_toolbar.cmdtool.Id, state)

        self.menubar.fileOpenConfig.Enable(state)
        self.menubar.pref.Enable(state)
        self.menubar.collection.Enable(state)
        self.menubar.eqlQuery.Enable(state)
        self.menubar.run.Enable(state)
        # self.menubar.installedDevices.Enable(state)
        self.menubar.clone.Enable(state)
        self.menubar.command.Enable(state)

    def onInstalledDevices(self, event):
        with InstalledDevicesDlg(self.sidePanel.apps) as dlg:
            res = dlg.ShowModal()
            if res == wx.ID_OK:
                app, version = dlg.getAppValues()
                if app and version:
                    self.onClearGrids(None)
                    self.gauge.Pulse()
                    resp = getInstallDevices(version, app)
                    res = []
                    for r in resp.results:
                        if r:
                            res.append(r.to_dict())
                    if res:
                        wxThread.doAPICallInThread(
                            self,
                            processInstallDevices,
                            args=(res),
                            eventType=None,
                            waitForJoin=False,
                            name="iterateThroughDeviceList",
                        )
                    else:
                        displayMessageBox(
                            (
                                "No device with that app version found",
                                wx.ICON_INFORMATION,
                            )
                        )
