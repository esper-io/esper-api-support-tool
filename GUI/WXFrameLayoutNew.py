#!/usr/bin/env python

from Common.SleepInhibitor import SleepInhibitor
from GUI.Dialogs.BulkFactoryReset import BulkFactoryReset
from GUI.Dialogs.GeofenceDialog import GeofenceDialog
from Utility.API.DeviceUtility import getAllDevices
from Utility.GridActionUtility import bulkFactoryReset, iterateThroughGridRows
from GUI.Dialogs.groupManagement import GroupManagement
from GUI.Dialogs.MultiSelectSearchDlg import MultiSelectSearchDlg
from wx.core import TextEntryDialog
from GUI.Dialogs.LargeTextEntryDialog import LargeTextEntryDialog

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

import pandas as pd

# import gc
import wx.adv as wxadv
import Utility.EventUtility as eventUtil

import Common.Globals as Globals
import Common.ApiTracker as ApiTracker
import GUI.EnhancedStatusBar as ESB

import Utility.wxThread as wxThread
import Utility.API.EsperTemplateUtil as templateUtil

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

from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.crypto import crypto
from Utility.API.EsperAPICalls import (
    clearAppData,
    getdeviceapps,
    setAppState,
    setKiosk,
    setMulti,
    validateConfiguration,
    getTokenInfo,
)
from Utility.EastUtility import (
    TakeAction,
    clearKnownGroups,
    filterDeviceList,
    getAllDeviceInfo,
    processInstallDevices,
    removeNonWhitelisted,
    uploadAppToEndpoint,
)
from Utility.Resource import (
    checkEsperInternetConnection,
    checkForInternetAccess,
    limitActiveThreads,
    postEventToFrame,
    resourcePath,
    createNewFile,
    joinThreadList,
    displayMessageBox,
    splitListIntoChunks,
    updateErrorTracker,
)
from Utility.API.CommandUtility import createCommand
from Utility.API.AppUtilities import (
    getAllInstallableApps,
    getAppDictEntry,
    getInstallDevices,
    installAppOnDevices,
    uninstallAppOnDevice,
    installAppOnGroups,
    uninstallAppOnGroup,
)
from Utility.API.GroupUtility import getAllGroups, moveGroup


class NewFrameLayout(wx.Frame):
    def __init__(self):
        self.prefPath = ""
        self.authPath = ""

        pd.options.display.max_rows = 9999

        self.consoleWin = None
        self.refresh = None
        self.preferences = None
        self.auth_data = None
        self.sleepInhibitor = SleepInhibitor()

        self.WINDOWS = True
        self.isBusy = False
        self.isRunning = False
        self.isSavingPrefs = False
        self.isRunningUpdate = False
        self.isUploading = False
        self.kill = False
        self.CSVUploaded = False
        self.defaultDir = os.getcwd()
        self.gridArrowState = {"next": False, "prev": False}
        self.groups = None
        self.groupManage = None
        self.AppState = None
        self.searchThreads = []

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

        sizer_4 = wx.FlexGridSizer(1, 2, 0, 0)
        self.sidePanel = SidePanel(self, self.panel_1)
        sizer_4.Add(self.sidePanel, 1, wx.EXPAND, 0)

        self.gridPanel = GridPanel(self, self.panel_1, wx.ID_ANY)
        sizer_4.Add(self.gridPanel, 1, wx.TOP | wx.BOTTOM | wx.RIGHT | wx.EXPAND, 4)

        sizer_4.AddGrowableRow(0)
        sizer_4.AddGrowableCol(1)

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
        self.sbText.Bind(wx.EVT_LEFT_UP, self.showConsole)

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

        self.notification = None

        # Bound Events
        self.DragAcceptFiles(True)
        self.Bind(wx.EVT_DROP_FILES, self.onFileDrop)
        self.Bind(eventUtil.EVT_FETCH, self.onFetch)
        self.Bind(eventUtil.EVT_GROUP, self.addGroupsToGroupChoice)
        self.Bind(eventUtil.EVT_APPS, self.addAppstoAppChoiceThread)
        self.Bind(eventUtil.EVT_COMPLETE, self.onComplete)
        self.Bind(eventUtil.EVT_LOG, self.onLog)
        self.Bind(eventUtil.EVT_COMMAND, self.onCommandDone)
        self.Bind(eventUtil.EVT_UPDATE_GAUGE, self.setGaugeValue)
        self.Bind(eventUtil.EVT_UPDATE_TAG_CELL, self.gridPanel.updateTagCell)
        self.Bind(eventUtil.EVT_UPDATE_GRID_CONTENT, self.gridPanel.updateGridContent)
        self.Bind(eventUtil.EVT_UNCHECK_CONSOLE, self.menubar.uncheckConsole)
        self.Bind(eventUtil.EVT_ON_FAILED, self.onFail)
        self.Bind(eventUtil.EVT_CONFIRM_CLONE, self.confirmClone)
        self.Bind(eventUtil.EVT_CONFIRM_CLONE_UPDATE, self.confirmCloneUpdate)
        self.Bind(eventUtil.EVT_MESSAGE_BOX, displayMessageBox)
        self.Bind(eventUtil.EVT_THREAD_WAIT, self.waitForThreadsThenSetCursorDefault)
        self.Bind(eventUtil.EVT_PROCESS_FUNCTION, self.processFunc)
        self.Bind(wx.EVT_ACTIVATE_APP, self.MacReopenApp)
        self.Bind(wx.EVT_ACTIVATE, self.onActivate)
        self.Bind(eventUtil.EVT_UPDATE_GAUGE_LATER, self.callSetGaugeLater)
        self.Bind(eventUtil.EVT_DISPLAY_NOTIFICATION, self.displayNotificationEvent)
        self.Bind(wx.EVT_POWER_SUSPENDING, self.onSuspend)

        if self.kill:
            return

        self.prefDialog = PreferencesDialog(self.preferences, parent=self)

        self.loadPref()
        self.__set_properties()
        self.Layout()
        self.Centre()
        self.tryToMakeActive()

        if self.kill:
            return

        self.menubar.checkCollectionEnabled()
        self.internetCheck = wxThread.GUIThread(
            self, checkForInternetAccess, (self), name="InternetCheck"
        )
        self.internetCheck.startWithRetry()
        self.errorTracker = wxThread.GUIThread(
            self, updateErrorTracker, None, name="updateErrorTracker"
        )
        self.errorTracker.startWithRetry()
        self.menubar.onUpdateCheck(showDlg=False)

    @api_tool_decorator()
    def tryToMakeActive(self):
        self.Raise()
        self.Iconize(False)
        style = self.GetWindowStyle()
        self.SetWindowStyle(style | wx.STAY_ON_TOP)
        self.SetFocus()
        self.SetWindowStyle(style)

    @api_tool_decorator()
    def __set_properties(self):
        self.SetTitle(Globals.TITLE)
        self.SetBackgroundColour(Color.lightGrey.value)
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

    @api_tool_decorator()
    def setFontSizeForLabels(self, parent=None):
        children = None
        if not parent:
            children = self.GetChildren()
        else:
            children = parent.GetChildren()
        for child in children:
            if type(child) == wx.StaticText:
                currentFont = child.GetFont()
                if (
                    currentFont.GetWeight() >= wx.FONTWEIGHT_BOLD
                    and child.Id == wx.ID_BOLD
                ):
                    boldNormalFontSize = ["GridNotebook", "NormalBold"]
                    if child.GetFaceName() in boldNormalFontSize:
                        child.SetFont(
                            wx.Font(
                                Globals.FONT_SIZE,
                                currentFont.GetFamily(),
                                currentFont.GetStyle(),
                                currentFont.GetWeight(),
                                0,
                                "GridNotebook",
                            )
                        )
                    else:
                        child.SetFont(
                            wx.Font(
                                Globals.HEADER_FONT_SIZE,
                                currentFont.GetFamily(),
                                currentFont.GetStyle(),
                                currentFont.GetWeight(),
                                0,
                                "Header",
                            )
                        )
                else:
                    child.SetFont(
                        wx.Font(
                            Globals.FONT_SIZE,
                            currentFont.GetFamily(),
                            currentFont.GetStyle(),
                            currentFont.GetWeight(),
                            0,
                            "Normal",
                        )
                    )
            if child.GetChildren():
                self.setFontSizeForLabels(parent=child)
        self.Refresh()

    @api_tool_decorator()
    def onLog(self, event):
        """ Event trying to log data """
        evtValue = event.GetValue()
        self.Logging(evtValue)

    @api_tool_decorator()
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

    @api_tool_decorator()
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
                        isValid = self.addEndpointEntry(
                            name, host, entId, key, prefix, csvRow
                        )
                        if isValid and type(isValid) == wx.MenuItem:
                            self.loadConfiguartion(isValid)
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
                dialog.DestroyLater()

    def addEndpointEntry(self, name, host, entId, key, prefix, csvRow):
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
                not self.auth_data or csvRow not in self.auth_data
            ) and not matchingConfig:
                with open(self.authPath, "a", newline="") as csvfile:
                    writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
                    writer.writerow(csvRow)
                self.readAuthCSV()
                isValid = self.PopulateConfig(auth=self.authPath, getItemForName=name)
                displayMessageBox(("Endpoint has been added", wx.ICON_INFORMATION))
            elif csvRow in self.auth_data or matchingConfig:
                self.auth_data = [
                    csvRow if x == matchingConfig[0] else x for x in self.auth_data
                ]
                tmp = []
                for auth in self.auth_data:
                    if auth not in tmp:
                        tmp.append(auth)
                self.auth_data = tmp
                with open(self.authPath, "w", newline="") as csvfile:
                    writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
                    writer.writerows(self.auth_data)
                self.readAuthCSV()
                isValid = self.PopulateConfig(auth=self.authPath, getItemForName=name)
                displayMessageBox(("Endpoint has been added", wx.ICON_INFORMATION))
            else:
                displayMessageBox(
                    (
                        "ERROR: Invalid input in Configuration. Check inputs!",
                        wx.ICON_ERROR,
                    )
                )
        return isValid

    @api_tool_decorator()
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
        if self.notification:
            self.notification.Close()
        if self.menubar.uc:
            self.menubar.uc.Close()
            self.menubar.uc.DestroyLater()
        if e:
            if e.EventType != wx.EVT_CLOSE.typeId:
                self.Close()
        if self.groupManage:
            self.groupManage.Close()
            self.groupManage.DestroyLater()
        thread = ApiToolLog().LogApiRequestOccurrence(
            None, ApiTracker.API_REQUEST_TRACKER, True
        )
        self.savePrefs(self.prefDialog)
        if thread:
            thread.join()
        if hasattr(self, "internetCheck") and self.internetCheck:
            self.internetCheck.stop()
        if hasattr(self, "errorTracker") and self.errorTracker:
            self.errorTracker.stop()
        self.Destroy()
        for item in list(wx.GetTopLevelWindows()):
            if not isinstance(item, NewFrameLayout):
                if item and isinstance(item, wx.Dialog):
                    item.Destroy()
                item.Close()
        wx.Exit()

    @api_tool_decorator()
    def onSaveBoth(self, event):
        dlg = wx.FileDialog(
            self,
            message="Save Reports as...",
            defaultFile="",
            wildcard="Microsoft Excel Open XML Spreadsheet (*.xlsx)|*.xlsx|CSV files (*.csv)|*.csv",
            defaultDir=str(self.defaultDir),
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )
        result = dlg.ShowModal()
        inFile = dlg.GetPath()

        if result == wx.ID_OK:  # Save button was pressed
            self.setCursorBusy()
            self.toggleEnabledState(False)
            self.gridPanel.disableGridProperties()
            thread = wxThread.GUIThread(
                self, self.saveFile, (inFile), name="saveFile"
            )
            thread.startWithRetry()
            if inFile.endswith(".csv") and self.gridPanel.grid_3_contents:
                newFileName = dlg.GetFilename().replace(".csv", "_app-report.csv")
                inFile = dlg.GetPath().replace(dlg.GetFilename(), newFileName)
                thread = wxThread.GUIThread(
                    self, self.saveAppInfo, (inFile), name="saveAppFile"
                )
                thread.startWithRetry()
            dlg.DestroyLater()
            return True
        elif (
            result == wx.ID_CANCEL
        ):  # Either the cancel button was pressed or the window was closed
            dlg.DestroyLater()
            return False

    @api_tool_decorator()
    def onSaveBothAll(self, event):
        if self.sidePanel.selectedDevicesList or self.sidePanel.selectedGroupsList:
            dlg = wx.FileDialog(
                self,
                message="Save Reports as...",
                defaultFile="",
                wildcard="Microsoft Excel Open XML Spreadsheet (*.xlsx)|*.xlsx|CSV files (*.csv)|*.csv",
                defaultDir=str(self.defaultDir),
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            )
            result = dlg.ShowModal()
            inFile = dlg.GetPath()
            dlg.DestroyLater()

            if result == wx.ID_OK:  # Save button was pressed
                self.setCursorBusy()
                self.toggleEnabledState(False)
                self.gridPanel.disableGridProperties()
                self.Logging("Attempting to save CSV at %s" % inFile)
                self.gauge.Pulse()
                thread = wxThread.GUIThread(
                    self, self.saveAllFile, (inFile), name="saveAllFile"
                )
                thread.startWithRetry()
                return True
            elif (
                result == wx.ID_CANCEL
            ):  # Either the cancel button was pressed or the window was closed
                return False
        else:
            displayMessageBox(
                ("Please select a group and or device(s) first!", wx.OK | wx.ICON_ERROR)
            )

    @api_tool_decorator()
    def getCSVHeaders(self, visibleOnly=False):
        headers = []
        deviceHeaders = Globals.CSV_TAG_ATTR_NAME.keys()
        networkHeaders = Globals.CSV_NETWORK_ATTR_NAME.keys()
        headers.extend(deviceHeaders)
        headers.extend(networkHeaders)
        headersNoDup = []
        [headersNoDup.append(x) for x in headers if x not in headersNoDup]
        headers = headersNoDup

        headersNoDup = []
        for header in headers:
            if visibleOnly:
                if (
                    header in deviceHeaders
                    and self.gridPanel.grid_1.GetColSize(
                        list(deviceHeaders).index(header)
                    )
                    > 0
                    and header not in headersNoDup
                ):
                    headersNoDup.append(header)
                if (
                    header in networkHeaders
                    and self.gridPanel.grid_2.GetColSize(
                        list(networkHeaders).index(header)
                    )
                    > 0
                    and header not in headersNoDup
                ):
                    headersNoDup.append(header)
            else:
                if header in deviceHeaders and header not in headersNoDup:
                    headersNoDup.append(header)
                if header in networkHeaders and header not in headersNoDup:
                    headersNoDup.append(header)
        headers = headersNoDup
        return headers, deviceHeaders, networkHeaders

    @api_tool_decorator()
    def saveAllFile(self, inFile):
        self.sleepInhibitor.inhibit()
        self.start_time = time.time()
        headers, deviceHeaders, networkHeaders = self.getCSVHeaders(
            visibleOnly=Globals.SAVE_VISIBILITY
        )
        deviceList = getAllDeviceInfo(self)
        self.Logging("Finished fetching device and network information for CSV")
        postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 50)
        gridDeviceData = []

        splitResults = splitListIntoChunks(list(deviceList.values()))
        threads = []
        for chunk in splitResults:
            t = wxThread.GUIThread(
                self,
                self.fetchAllGridData,
                args=(chunk, gridDeviceData),
                name="fetchAllGridData",
            )
            threads.append(t)
            t.startWithRetry()
        joinThreadList(threads)

        self.Logging("Finished compiling device and network information for CSV")
        postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 75)

        self.saveGridData(
            inFile, headers, deviceHeaders, networkHeaders, gridDeviceData
        )
        self.sleepInhibitor.uninhibit()
        postEventToFrame(eventUtil.myEVT_COMPLETE, (True, -1))
        print("Execution time: %s" % (time.time() - self.start_time))

    @api_tool_decorator()
    def fetchAllGridData(self, chunk, gridDeviceData):
        for entry in chunk:
            gridDeviceData.append(self.gridPanel.getDeviceNetworkInfoListing(*entry))

    @api_tool_decorator()
    def saveFile(self, inFile):
        self.defaultDir = Path(inFile).parent
        gridDeviceData = []
        headers, deviceHeaders, networkHeaders = self.getCSVHeaders(
            visibleOnly=Globals.SAVE_VISIBILITY
        )
        self.saveGridData(
            inFile, headers, deviceHeaders, networkHeaders, gridDeviceData
        )
        postEventToFrame(eventUtil.myEVT_COMPLETE, (True, -1))

    def mergeDeviceAndNetworkInfo(self, device, gridDeviceData):
        tempDict = {}
        tempDict.update(device)
        for entry in self.gridPanel.grid_2_contents:
            if entry["Device Name"] == device[Globals.CSV_TAG_ATTR_NAME["Esper Name"]]:
                # if deviceListing:
                tempDict.update(entry)
                break
        gridDeviceData.append(tempDict)

    @api_tool_decorator()
    def saveGridData(
        self, inFile, headers, deviceHeaders, networkHeaders, gridDeviceData
    ):
        if inFile.endswith(".csv"):
            threads = []
            num = 1
            for device in self.gridPanel.grid_1_contents:
                self.mergeDeviceAndNetworkInfo(device, gridDeviceData)
                val = (num / (len(gridDeviceData) * 2)) * 100
                if val <= 50:
                    self.setGaugeValue(int(val))
                num += 1
            joinThreadList(threads)

            gridData = []
            gridData.append(headers)

            createNewFile(inFile)

            num = len(gridDeviceData)
            for deviceData in gridDeviceData:
                rowValues = []
                for header in headers:
                    value = ""
                    if header in deviceData:
                        value = deviceData[header]
                    else:
                        if header in deviceHeaders:
                            if Globals.CSV_TAG_ATTR_NAME[header] in deviceData:
                                value = deviceData[Globals.CSV_TAG_ATTR_NAME[header]]
                        if header in networkHeaders:
                            if Globals.CSV_NETWORK_ATTR_NAME[header] in deviceData:
                                value = deviceData[
                                    Globals.CSV_NETWORK_ATTR_NAME[header]
                                ]
                    rowValues.append(value)
                gridData.append(rowValues)
                val = (num / (len(gridDeviceData) * 2)) * 100
                if val <= 95:
                    self.setGaugeValue(int(val))
                num += 1

            with open(inFile, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
                writer.writerows(gridData)
        elif inFile.endswith(".xlsx"):
            deviceGridData = []
            networkGridData = []
            appGridData = []
            threads = []

            deviceThread = wxThread.GUIThread(
                None,
                self.getGridDataToSave,
                (
                    gridDeviceData
                    if gridDeviceData
                    else self.gridPanel.grid_1_contents,
                    deviceHeaders,
                    Globals.CSV_TAG_ATTR_NAME,
                    deviceGridData,
                ),
            )
            deviceThread.startWithRetry()
            threads.append(deviceThread)

            networkThread = wxThread.GUIThread(
                None,
                self.getGridDataToSave,
                (
                    gridDeviceData
                    if gridDeviceData
                    else self.gridPanel.grid_2_contents,
                    networkHeaders,
                    Globals.CSV_NETWORK_ATTR_NAME,
                    networkGridData,
                ),
            )
            networkThread.startWithRetry()
            threads.append(networkThread)

            for entry in self.gridPanel.grid_3_contents:
                appGridData.append(list(entry.values()))

            joinThreadList(threads)
            networkGridData = networkThread.result
            deviceGridData = deviceThread.result

            df_1 = None
            if Globals.COMBINE_DEVICE_AND_NETWORK_SHEETS:
                df_devices = pd.DataFrame(
                    deviceGridData, columns=Globals.CSV_TAG_ATTR_NAME.keys()
                )
                df_network = pd.DataFrame(
                    networkGridData, columns=Globals.CSV_NETWORK_ATTR_NAME.keys()
                )
                columns = list(Globals.CSV_TAG_ATTR_NAME.keys()) + list(Globals.CSV_NETWORK_ATTR_NAME.keys())[2:]
                df_1 = pd.concat([df_devices, df_network.drop(columns=["Esper Name", "Group"])], axis=1)
                df_1.set_axis(columns, axis=1, inplace=True)
            else:
                df_1 = pd.DataFrame(
                    deviceGridData, columns=Globals.CSV_TAG_ATTR_NAME.keys()
                )
            df_2 = None
            if not Globals.COMBINE_DEVICE_AND_NETWORK_SHEETS:
                df_2 = pd.DataFrame(
                    networkGridData, columns=Globals.CSV_NETWORK_ATTR_NAME.keys()
                )
            df_3 = pd.DataFrame(appGridData, columns=Globals.CSV_APP_ATTR_NAME)

            with pd.ExcelWriter(inFile) as writer1:
                if self.gridPanel.grid_1_contents:
                    df_1.to_excel(writer1, sheet_name="Device", index=False)
                    for column in df_1:
                        column_width = max(
                            df_1[column].astype(str).map(len).max(), len(column)
                        )
                        col_idx = df_1.columns.get_loc(column)
                        writer1.sheets["Device"].set_column(col_idx, col_idx, column_width)
                if self.gridPanel.grid_2_contents and df_2 is not None:
                    df_2.to_excel(writer1, sheet_name="Network", index=False)
                    for column in df_2:
                        column_width = max(
                            df_2[column].astype(str).map(len).max(), len(column)
                        )
                        col_idx = df_2.columns.get_loc(column)
                        writer1.sheets["Network"].set_column(col_idx, col_idx, column_width)
                if self.gridPanel.grid_3_contents:
                    df_3.to_excel(writer1, sheet_name="Application", index=False)
                    for column in df_3:
                        column_width = max(
                            df_3[column].astype(str).map(len).max(), len(column)
                        )
                        col_idx = df_3.columns.get_loc(column)
                        writer1.sheets["Application"].set_column(
                            col_idx, col_idx, column_width
                        )

        self.Logging("---> Info saved to file: " + inFile)
        self.setGaugeValue(100)
        self.gridPanel.enableGridProperties()

        displayMessageBox(
            ("Info saved to file: %s" % inFile, wx.OK | wx.ICON_INFORMATION)
        )

    def getGridDataToSave(self, contents, headers, headerKeys, deviceGridData):
        for entry in contents:
            rowValues = []
            for header in headers:
                value = ""
                if header in entry:
                    value = entry[header]
                elif headerKeys[header] in entry:
                    value = entry[headerKeys[header]]
                rowValues.append(value)
            deviceGridData.append(rowValues)
        return deviceGridData

    # @api_tool_decorator()
    # def saveAppInfo(self, event):
    #     if type(event) is str:
    #         self.setCursorBusy()
    #         self.toggleEnabledState(False)
    #         self.gridPanel.disableGridProperties()
    #         thread = wxThread.GUIThread(self, self.saveAppInfoAsFile, (event))
    #         thread.startWithRetry()
    #         return True
    #     if self.gridPanel.grid_3.GetNumberRows() > 0:
    #         dlg = wx.FileDialog(
    #             self,
    #             message="Save App Info CSV...",
    #             defaultFile="",
    #             wildcard="Microsoft Excel Open XML Spreadsheet (*.xlsx)|*.xlsx|CSV files (*.csv)|*.csv",
    #             defaultDir=str(self.defaultDir),
    #             style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
    #         )
    #         result = dlg.ShowModal()
    #         inFile = dlg.GetPath()
    #         dlg.DestroyLater()

    #         if result == wx.ID_OK:  # Save button was pressed
    #             self.setCursorBusy()
    #             self.toggleEnabledState(False)
    #             self.gridPanel.disableGridProperties()
    #             thread = wxThread.GUIThread(self, self.saveAppInfoAsFile, (inFile))
    #             thread.startWithRetry()
    #             return True
    #         elif (
    #             result == wx.ID_CANCEL
    #         ):  # Either the cancel button was pressed or the window was closed
    #             return False

    def saveAppInfoAsFile(self, inFile):
        gridData = []
        gridData.append(Globals.CSV_APP_ATTR_NAME)
        createNewFile(inFile)

        num = 1
        for entry in self.gridPanel.grid_3_contents:
            gridData.append(list(entry.values()))
            val = (num / len(self.gridPanel.grid_3_contents)) * 100
            if val <= 95:
                self.setGaugeValue(int(val))
            num += 1

        with open(inFile, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerows(gridData)

        self.Logging("---> Info saved to csv file - " + inFile)
        self.setGaugeValue(100)
        self.toggleEnabledState(True)
        self.setCursorDefault()
        self.gridPanel.enableGridProperties()

        displayMessageBox(
            ("Info saved to csv file - " + inFile, wx.OK | wx.ICON_INFORMATION)
        )

    @api_tool_decorator()
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
            "Open Device Spreedsheet File",
            wildcard="Spreadsheet Files (*.csv;*.xlsx)|*.csv;*.xlsx|CSV Files (*.csv)|*.csv|Microsoft Excel Open XML Spreadsheet (*.xlsx)|*.xlsx",
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
                thread = None
                if self.WINDOWS:
                    thread = wxThread.GUIThread(
                        self, self.openDeviceCSV, (csv_auth_path), name="openDeviceCSV"
                    )
                    thread.startWithRetry()
                else:
                    self.openDeviceCSV(csv_auth_path)
                wxThread.GUIThread(
                    self,
                    self.waitForThreadsThenSetCursorDefault,
                    ([thread], 2),
                    name="waitForThreadsThenSetCursorDefault_2",
                ).startWithRetry()
            elif result == wx.ID_CANCEL:
                self.setCursorDefault()
                return  # the user changed their mind

    def openDeviceCSV(self, csv_auth_path):
        self.isUploading = True
        if csv_auth_path.endswith(".csv"):
            try:
                with open(csv_auth_path, "r", encoding="utf-8-sig") as csvFile:
                    reader = csv.reader(
                        csvFile, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True
                    )
                    data = list(reader)
                    self.processDeviceCSVUpload(data)
            except:
                with open(csv_auth_path, "r") as csvFile:
                    reader = csv.reader(
                        csvFile, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True
                    )
                    data = list(reader)
                    self.processDeviceCSVUpload(data)
        elif csv_auth_path.endswith(".xlsx"):
            try:
                dfs = pd.read_excel(
                    csv_auth_path, sheet_name=None, keep_default_na=False
                )
                self.processXlsxUpload(dfs)
            except:
                pass
        postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE_LATER, (3000, 0))
        postEventToFrame(
            eventUtil.myEVT_DISPLAY_NOTIFICATION,
            ("E.A.S.T.", "Device CSV Upload Completed"),
        )
        self.setCursorDefault()
        self.isUploading = False

    def processXlsxUpload(self, data):
        self.CSVUploaded = True
        self.toggleEnabledState(False)
        self.sidePanel.groupChoice.Enable(False)
        self.sidePanel.deviceChoice.Enable(False)
        self.gridPanel.disableGridProperties()
        self.gridPanel.grid_1.Freeze()
        self.gridPanel.grid_2.Freeze()
        dataList = []
        if "Device" in data:
            dataList.append(data["Device"].columns.values.tolist())
            dataList += data["Device"].values.tolist()
            self.processCsvDataByGrid(
                self.gridPanel.grid_1,
                dataList,
                Globals.CSV_TAG_ATTR_NAME,
                Globals.grid1_lock,
            )
        if "Network" in data:
            dataList.append(data["Network"].columns.values.tolist())
            dataList += data["Network"].values.tolist()
            self.processCsvDataByGrid(
                self.gridPanel.grid_2,
                dataList,
                Globals.CSV_NETWORK_ATTR_NAME,
                Globals.grid2_lock,
            )

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

    @api_tool_decorator(locks=[Globals.grid1_lock, Globals.grid2_lock])
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
                            str(header[fileCol]).replace(" ", "").lower()
                            if len(header) > fileCol
                            else ""
                        )
                        if colValue == "--":
                            colValue = ""
                        if colName == "storenumber":
                            colName = "Alias"
                            header[fileCol] = "Alias"
                        if colName == "tag":
                            colName = "Tags"
                            header[fileCol] = "Tags"
                        if (
                            (
                                expectedCol == "Device Name"
                                or expectedCol == "Esper Name"
                            )
                            and colName == "espername"
                            and grid == self.gridPanel.grid_2
                        ):
                            colName = "devicename"
                        if expectedCol == "Esper Name" and colName == "devicename":
                            colName = "devicename"
                            expectedCol = "devicename"
                        if (
                            fileCol < len(header)
                            and str(header[fileCol]).strip()
                            in Globals.CSV_DEPRECATED_HEADER_LABEL
                        ) or (
                            fileCol < len(header)
                            and str(header[fileCol]).strip() not in headers.keys()
                            and colName != "devicename"
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
                                                or colValue.count("’") % 2 != 0
                                            )
                                            or (
                                                '"' not in colValue
                                                and "'" not in colValue
                                                and "’" not in colValue
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
                            break
                        fileCol += 1
                    toolCol += 1
        if lock:
            lock.release()

    @api_tool_decorator()
    def PopulateConfig(self, auth=None, event=None, getItemForName=None):
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
        returnItem = None
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
                    self.setGaugeValue(int(float(num / maxRow) * 25))
                    num += 1
                    if "name" in row:
                        self.sidePanel.configChoice[row["name"]] = row
                        item = self.menubar.configMenu.Append(
                            wx.ID_ANY, row["name"], row["name"], kind=wx.ITEM_CHECK
                        )
                        self.Bind(wx.EVT_MENU, self.loadConfiguartion, item)
                        self.menubar.configMenuOptions.append(item)
                        if str(getItemForName) == row["name"]:
                            returnItem = item
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
                "---> Please Select an Endpoint From the Configuartion Menu (defaulting to first Config)"
            )
            defaultConfigItem = self.menubar.configMenuOptions[0]
            defaultConfigItem.Check(True)
            self.loadConfiguartion(defaultConfigItem)
        else:
            self.Logging(
                "---> "
                + configfile
                + " not found - PLEASE Quit and create configuration file"
            )
            defaultConfigVal = self.menubar.configMenu.Append(
                wx.ID_NONE, "No Loaded Configurations", "No Loaded Configurations"
            )
            self.menubar.configMenuOptions.append(defaultConfigVal)
            self.Bind(wx.EVT_MENU, self.AddEndpoint, defaultConfigVal)
        postEventToFrame(
            eventUtil.myEVT_PROCESS_FUNCTION,
            (wx.CallLater, (3000, self.setGaugeValue, 0)),
        )
        return returnItem

    @api_tool_decorator()
    def setCursorDefault(self):
        """ Set cursor icon to default state """
        try:
            self.isBusy = False
            myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
            self.SetCursor(myCursor)
        except:
            pass

    @api_tool_decorator()
    def setCursorBusy(self):
        """ Set cursor icon to busy state """
        self.isBusy = True
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)

    @api_tool_decorator()
    def loadConfiguartion(self, event, *args, **kwargs):
        """Populate Frame Layout With Device Configuration"""
        self.configMenuItem = self.menubar.configMenu.FindItemById(event.Id)
        self.onClearGrids(None)
        clearKnownGroups()
        try:
            if self.groupManage:
                self.groupManage.Destroy()
        except:
            pass
        self.sidePanel.groups = {}
        self.sidePanel.devices = {}
        self.sidePanel.clearSelections(clearApp=True)
        self.sidePanel.destroyMultiChoiceDialogs()
        self.sidePanel.deviceChoice.Enable(False)
        self.sidePanel.removeEndpointBtn.Enable(False)
        self.frame_toolbar.search.SetValue("")
        self.sidePanel.clearStoredApps()
        self.toggleEnabledState(False)
        self.setCursorBusy()

        for thread in threading.enumerate():
            if thread.name == "fetchUpdateDataActionThread":
                if hasattr(thread, "stop"):
                    thread.stop()

        try:
            self.Logging(
                "--->Attempting to load configuration: %s."
                % self.configMenuItem.GetItemLabelText()
            )
            selectedConfig = self.sidePanel.configChoice[
                self.configMenuItem.GetItemLabelText()
            ]

            for item in self.configMenuItem.Menu.MenuItems:
                if item != self.configMenuItem:
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
                "---> An Error has occured while loading the configuration, please try again."
            )
            print(e)
            ApiToolLog().LogError(e)
            self.configMenuItem.Check(False)

    @api_tool_decorator()
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
            Globals.IS_TOKEN_VALID = False

            if "https" in str(host):
                Globals.configuration.host = host.strip()
                Globals.configuration.api_key["Authorization"] = key.strip()
                Globals.configuration.api_key_prefix["Authorization"] = prefix.strip()
                Globals.enterprise_id = entId.strip()

                wxThread.GUIThread(
                    self,
                    self.validateToken,
                    None,
                    name="validateToken",
                ).startWithRetry()

                self.setGaugeValue(50)
                threads = []
                if Globals.HAS_INTERNET is None:
                    Globals.HAS_INTERNET = checkEsperInternetConnection()
                if Globals.HAS_INTERNET:
                    groupThread = self.PopulateGroups()
                    appThread = self.PopulateApps()
                    threads = [groupThread, appThread]
                wxThread.GUIThread(
                    self,
                    self.waitForThreadsThenSetCursorDefault,
                    (threads, 0),
                    name="waitForThreadsThenSetCursorDefault_0",
                ).startWithRetry()
                return True
        else:
            displayMessageBox(("Invalid Configuration", wx.ICON_ERROR))
            return False

    @api_tool_decorator(locks=[Globals.token_lock])
    def validateToken(self):
        Globals.token_lock.acquire()
        res = getTokenInfo()
        if res and hasattr(res, "expires_on"):
            Globals.IS_TOKEN_VALID = True
            if res.expires_on <= datetime.now(res.expires_on.tzinfo) or not res:
                Globals.IS_TOKEN_VALID = False
                # self.promptForNewToken()
                postEventToFrame(
                    eventUtil.myEVT_PROCESS_FUNCTION,
                    (self.promptForNewToken),
                )
        elif (
            res
            and hasattr(res, "body")
            and "Authentication credentials were not provided" in res.body
        ):
            Globals.IS_TOKEN_VALID = False
            postEventToFrame(
                eventUtil.myEVT_PROCESS_FUNCTION,
                (self.promptForNewToken),
            )

        if res and hasattr(res, "scope"):
            if "write" not in res.scope:
                self.menubar.fileAddUser.Enable(False)
        if Globals.token_lock.locked():
            Globals.token_lock.release()

    def promptForNewToken(self):
        newToken = ""
        while not newToken:
            with TextEntryDialog(
                self,
                "Please enter a new API Token for %s" % Globals.configuration.host,
                "%s - API Token has expired!" % self.configMenuItem.GetItemLabelText(),
            ) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    newToken = dlg.GetValue()
                else:
                    break
            newToken = newToken.strip()
            if newToken:
                csvRow = [
                    self.configMenuItem.GetItemLabelText(),
                    Globals.configuration.host,
                    Globals.enterprise_id,
                    newToken,
                    Globals.configuration.api_key_prefix["Authorization"],
                ]
                valid = self.addEndpointEntry(
                    self.configMenuItem.GetItemLabelText(),
                    Globals.configuration.host,
                    Globals.enterprise_id,
                    newToken,
                    Globals.configuration.api_key_prefix["Authorization"],
                    csvRow,
                )
                if not valid:
                    newToken = ""

    @api_tool_decorator()
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
            self.gridPanel.setColVisibility()
            self.sidePanel.sortAndPopulateAppChoice()
            self.sidePanel.groupChoice.Enable(True)
            self.sidePanel.actionChoice.Enable(True)
            self.sidePanel.removeEndpointBtn.Enable(True)
        if source == 1:
            if not self.sidePanel.devices:
                self.sidePanel.selectedDevices.Append("No Devices Found", "")
                self.sidePanel.deviceChoice.Enable(False)
                self.menubar.setSaveMenuOptionsEnableState(False)
                self.menubar.enableConfigMenu()
                self.Logging("---> No Devices found")
            else:
                self.sidePanel.deviceChoice.Enable(True)
                if (
                    self.preferences
                    and "getAppsForEachDevice" in self.preferences
                    and self.preferences["getAppsForEachDevice"]
                ) or Globals.GET_APP_EACH_DEVICE:
                    newThreads = []
                    self.Logging("---> Attempting to populate Application list")
                    self.gauge.Pulse()
                    for deviceId in self.sidePanel.devices.values():
                        thread = wxThread.GUIThread(
                            self,
                            getdeviceapps,
                            (deviceId, True, Globals.USE_ENTERPRISE_APP),
                            eventType=eventUtil.myEVT_APPS,
                            name="GetDeviceAppsToPopulateApps",
                        )
                        thread.startWithRetry()
                        newThreads.append(thread)
                        limitActiveThreads(newThreads)
                    num = 0
                    for thread in newThreads:
                        thread.join()
                        num += 1
                        if not self.preferences or (
                            "enableDevice" in self.preferences
                            and self.preferences["enableDevice"]
                        ):
                            self.setGaugeValue(
                                int(float(num / len(newThreads) / 2) * 100)
                            )
                self.sidePanel.sortAndPopulateAppChoice()
                self.Logging("---> Application list populated")
                if not self.isRunning:
                    self.menubar.enableConfigMenu()
                self.menubar.setSaveMenuOptionsEnableState(True)
            if (
                not self.preferences
                or (
                    "enableDevice" in self.preferences
                    and self.preferences["enableDevice"]
                )
            ) and self.sidePanel.devices:
                self.sidePanel.deviceChoice.Enable(True)
            else:
                self.sidePanel.deviceChoice.Enable(False)
            self.displayNotification("Finished loading devices", "")
        if source == 2:
            indx = self.sidePanel.actionChoice.GetItems().index(
                list(Globals.GRID_ACTIONS.keys())[0]
            )
            if self.sidePanel.actionChoice.GetSelection() < indx:
                self.sidePanel.actionChoice.SetSelection(indx)
            # TODO: FIX
            if self.WINDOWS:
                if self.gridPanel.grid_1.IsFrozen():
                    self.gridPanel.grid_1.Thaw()
                if self.gridPanel.grid_2.IsFrozen():
                    self.gridPanel.grid_2.Thaw()
                if self.gridPanel.grid_3.IsFrozen():
                    self.gridPanel.grid_3.Thaw()
                self.gridPanel.enableGridProperties()
                self.gridPanel.autoSizeGridsColumns()
                self.sidePanel.groupChoice.Enable(True)
                self.sidePanel.deviceChoice.Enable(True)
            else:
                if self.gridPanel.grid_1.IsFrozen():
                    postEventToFrame(
                        eventUtil.myEVT_PROCESS_FUNCTION, self.gridPanel.grid_1.Thaw
                    )
                if self.gridPanel.grid_2.IsFrozen():
                    postEventToFrame(
                        eventUtil.myEVT_PROCESS_FUNCTION, self.gridPanel.grid_2.Thaw
                    )
                if self.gridPanel.grid_3.IsFrozen():
                    postEventToFrame(
                        eventUtil.myEVT_PROCESS_FUNCTION, self.gridPanel.grid_3.Thaw
                    )
                postEventToFrame(
                    eventUtil.myEVT_PROCESS_FUNCTION,
                    self.gridPanel.enableGridProperties,
                )
                postEventToFrame(
                    eventUtil.myEVT_PROCESS_FUNCTION,
                    self.gridPanel.enableGridProperties,
                )
                postEventToFrame(
                    eventUtil.myEVT_PROCESS_FUNCTION,
                    (self.sidePanel.groupChoice.Enable, True),
                )
                postEventToFrame(
                    eventUtil.myEVT_PROCESS_FUNCTION,
                    (self.sidePanel.deviceChoice.Enable, True),
                )
        if source == 3:
            cmdResults = []
            if (
                action == GeneralActions.SET_KIOSK.value
                or action == GeneralActions.SET_MULTI.value
                or action == GeneralActions.SET_APP_STATE.value
                or action == GeneralActions.REMOVE_NON_WHITELIST_AP.value
                or action == GeneralActions.MOVE_GROUP.value
                or action == GeneralActions.INSTALL_APP.value
                or action == GeneralActions.UNINSTALL_APP.value
                or action == GridActions.SET_APP_STATE.value
                or action == GridActions.MOVE_GROUP.value
                or action == GridActions.FACTORY_RESET.value
            ):
                for t in threads:
                    if t.result:
                        if type(t.result) == list:
                            cmdResults = cmdResults + t.result
                        else:
                            cmdResults.append(t.result)
            if action and action == GeneralActions.CLEAR_APP_DATA.value:
                for t in threads:
                    if t.result:
                        displayMessageBox(
                            (
                                "Clear App Data Command has been sent to the device(s).\nPlease check devices' event feeds for command status.",
                                wx.ICON_INFORMATION,
                            )
                        )
                        break
            postEventToFrame(eventUtil.myEVT_COMPLETE, (True, action, cmdResults))
        self.toggleEnabledState(not self.isRunning and not self.isSavingPrefs)
        self.setCursorDefault()
        self.setGaugeValue(100)

    @api_tool_decorator()
    def PopulateGroups(self):
        """ Populate Group Choice """
        self.sidePanel.groupChoice.Enable(False)
        self.Logging("--->Attempting to populate groups...")
        self.setCursorBusy()
        thread = wxThread.GUIThread(
            self,
            getAllGroups,
            None,
            eventType=eventUtil.myEVT_GROUP,
            name="PopulateGroupsGetAll",
        )
        thread.startWithRetry()
        return thread

    @api_tool_decorator()
    def addGroupsToGroupChoice(self, event):
        """ Populate Group Choice """
        results = (
            event.GetValue().results
            if hasattr(event.GetValue(), "results")
            else event.GetValue()
        )
        num = 1
        self.groups = results
        self.sidePanel.groupsResp = event.GetValue()
        if results:
            results = sorted(
                results,
                key=lambda i: i.name.lower() if hasattr(i, "name") else i["name"].lower() if type(i) is dict else i,
            )
        if results and len(results):
            for group in results:
                if group.name not in self.sidePanel.groups:
                    self.sidePanel.groups[group.name] = group.id
                else:
                    self.sidePanel.groups[group.path] = group.id
                if group.id not in Globals.knownGroups:
                    Globals.knownGroups[group.id] = group.name
                self.setGaugeValue(50 + int(float(num / len(results)) * 25))
                num += 1
        self.sidePanel.groupChoice.Enable(True)
        self.sidePanel.actionChoice.Enable(True)

    @api_tool_decorator()
    def PopulateDevices(self, event):
        """ Populate Device Choice """
        self.menubar.setSaveMenuOptionsEnableState(False)
        self.SetFocus()
        self.Logging("--->Attempting to populate devices of selected group(s)")
        self.setCursorBusy()
        if not self.preferences or (
            "enableDevice" in self.preferences and self.preferences["enableDevice"]
        ):
            self.sidePanel.runBtn.Enable(False)
            self.frame_toolbar.EnableTool(self.frame_toolbar.rtool.Id, False)
            self.frame_toolbar.EnableTool(self.frame_toolbar.cmdtool.Id, False)
            self.setGaugeValue(0)
            self.gauge.Pulse()
        else:
            if not self.isRunning or not self.isBusy:
                self.sidePanel.runBtn.Enable(True)
                self.frame_toolbar.EnableTool(self.frame_toolbar.rtool.Id, True)
        self.frame_toolbar.EnableTool(self.frame_toolbar.cmdtool.Id, True)
        threads = []
        for clientData in self.sidePanel.selectedGroupsList:
            thread = wxThread.GUIThread(
                self,
                self.addDevicesToDeviceChoice,
                clientData,
                name="AddDevicesToDeviceChoice",
            )
            thread.startWithRetry()
            threads.append(thread)
        wxThread.GUIThread(
            self,
            self.waitForThreadsThenSetCursorDefault,
            (threads, 1),
            name="waitForThreadsThenSetCursorDefault_1",
        ).startWithRetry()

    @api_tool_decorator()
    def addDevicesToDeviceChoice(self, groupId):
        """ Populate Device Choice """
        api_response = getAllDevices(
            groupId, limit=Globals.limit, fetchAll=Globals.GROUP_FETCH_ALL
        )
        self.sidePanel.deviceResp = api_response
        if hasattr(api_response, "results") and len(api_response.results):
            self.Logging("---> Processing fetched devices...")
            if not Globals.SHOW_DISABLED_DEVICES:
                api_response.results = list(filter(filterDeviceList, api_response.results))
            api_response.results = sorted(
                api_response.results,
                key=lambda i: i.device_name.lower(),
            )
            splitResults = splitListIntoChunks(api_response.results)
            threads = []
            for chunk in splitResults:
                t = wxThread.GUIThread(
                    self,
                    self.processAddDeviceToChoice,
                    args=(chunk),
                    name="addDeviceToDeviceChoice",
                )
                threads.append(t)
                t.startWithRetry()
            joinThreadList(threads)
        elif type(api_response) is dict and len(api_response["results"]):
            self.Logging("---> Processing fetched devices...")
            if not Globals.SHOW_DISABLED_DEVICES:
                api_response["results"] = list(filter(filterDeviceList, api_response["results"]))
            api_response["results"] = sorted(
                api_response["results"],
                key=lambda i: i["device_name"].lower(),
            )
            splitResults = splitListIntoChunks(api_response["results"])
            threads = []
            for chunk in splitResults:
                t = wxThread.GUIThread(
                    self,
                    self.processAddDeviceToChoice,
                    args=(chunk),
                    name="addDeviceToDeviceChoice",
                )
                threads.append(t)
                t.startWithRetry()
            joinThreadList(threads)

    def processAddDeviceToChoice(self, chunk):
        for device in chunk:
            name = ""
            if hasattr(device, "hardware_info"):
                name = "%s %s %s %s" % (
                    device.hardware_info["manufacturer"],
                    device.hardware_info["model"],
                    device.device_name,
                    device.alias_name if device.alias_name else "",
                )
            else:
                name = "%s %s %s %s" % (
                    device["hardwareInfo"]["manufacturer"],
                    device["hardwareInfo"]["model"],
                    device["device_name"],
                    device["alias_name"] if device["alias_name"] else "",
                )
            if name and name not in self.sidePanel.devices:
                if hasattr(device, "id"):
                    self.sidePanel.devices[name] = device.id
                else:
                    self.sidePanel.devices[name] = device["id"]

    @api_tool_decorator()
    def PopulateApps(self):
        """ Populate App Choice """
        self.Logging("--->Attempting to populate apps...")
        self.setCursorBusy()
        thread = wxThread.GUIThread(
            self, self.fetchAllInstallableApps, None, name="PopulateApps"
        )
        thread.startWithRetry()
        return thread

    # def fetchAllApps(self):
    #     resp = getAllApplications()
    #     self.addAppsToAppChoice(resp)

    @api_tool_decorator(locks=[Globals.token_lock])
    def fetchAllInstallableApps(self):
        Globals.token_lock.acquire()
        Globals.token_lock.release()
        if Globals.IS_TOKEN_VALID:
            resp = getAllInstallableApps()
            self.addAppsToAppChoice(resp)

    def addAppstoAppChoiceThread(self, event):
        api_response = None
        if hasattr(event, "GetValue"):
            api_response = event.GetValue()
        else:
            api_response = event
        if hasattr(api_response, "results"):
            api_response = api_response.results
        elif type(api_response) == tuple and "results" in api_response[1]:
            api_response = api_response[1]["results"]
        elif type(api_response) == dict:
            api_response = api_response["results"]
        if api_response:
            thread = wxThread.GUIThread(
                self,
                self.addAppsToAppChoice,
                args=(api_response),
                name="addAppstoAppChoiceThread",
            )
            thread.startWithRetry()

    @api_tool_decorator()
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
        elif type(api_response) == tuple and "results" in api_response[1]:
            results = api_response[1]["results"]
        elif type(api_response) == dict:
            results = api_response["results"]

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
        elif results and type(results[0]) == dict and "application_name" in results[0]:
            results = sorted(
                results,
                key=lambda i: i["application_name"].lower(),
            )
        elif results:
            results = sorted(
                results,
                key=lambda i: i["app_name"].lower(),
            )

        if results and len(results):
            for app in results:
                self.addAppToAppList(app)

    @api_tool_decorator()
    def addAppToAppList(self, app):
        entry = getAppDictEntry(app)
        if (
            entry
            and entry not in self.sidePanel.enterpriseApps
            and ("isValid" in entry and entry["isValid"])
        ):
            self.sidePanel.enterpriseApps.append(entry)

    @api_tool_decorator()
    def onRun(self, event=None):
        """ Try to run the specifed Action on a group or device """
        if not Globals.HAS_INTERNET:
            displayMessageBox(
                (
                    "ERROR: An internet connection is required when using the tool!",
                    wx.OK | wx.ICON_ERROR | wx.CENTRE,
                )
            )
            return

        if self.isBusy or not self.sidePanel.runBtn.IsEnabled():
            return
        self.start_time = time.time()
        self.setCursorBusy()
        self.isRunning = True
        self.setGaugeValue(0)
        self.toggleEnabledState(False)
        self.AppState = None
        self.sleepInhibitor.inhibit()

        self.gridPanel.grid_1.UnsetSortingColumn()
        self.gridPanel.grid_2.UnsetSortingColumn()
        self.gridPanel.grid_3.UnsetSortingColumn()

        appSelection = self.sidePanel.selectedApp.GetSelection()
        actionSelection = self.sidePanel.actionChoice.GetSelection()
        actionClientData = self.sidePanel.actionChoice.GetClientData(actionSelection)

        allDevicesSelected = (
            True
            if hasattr(self.sidePanel.deviceResp, "count")
            and len(self.sidePanel.selectedDevicesList)
            == self.sidePanel.deviceResp.count
            else False
        )

        appLabel = (
            self.sidePanel.selectedAppEntry["name"]
            if self.sidePanel.selectedAppEntry
            else ""
        )
        actionLabel = (
            self.sidePanel.actionChoice.Items[actionSelection]
            if len(self.sidePanel.actionChoice.Items) > 0
            and self.sidePanel.actionChoice.Items[actionSelection]
            else ""
        )
        if actionClientData == GeneralActions.REMOVE_NON_WHITELIST_AP.value:
            with LargeTextEntryDialog(
                self,
                "Enter Wifi SSIDs you want whitelisted, as a comma seperated list:",
                "Wifi Access Point Whitelist",
            ) as textDialog:
                if textDialog.ShowModal() == wx.ID_OK:
                    apList = textDialog.GetValue()
                    whitelist = []
                    parts = apList.split(",")
                    for part in parts:
                        whitelist.append(part.strip())
                    Globals.WHITELIST_AP = whitelist
                    with LargeTextEntryDialog(
                        self,
                        "Do you wish to proceed with this Wifi SSID Whitelist?",
                        "Wifi Access Point Whitelist",
                        "\n".join(Globals.WHITELIST_AP),
                        False,
                    ) as textDialog2:
                        if textDialog2.ShowModal() != wx.ID_OK:
                            self.sleepInhibitor.uninhibit()
                            self.isRunning = False
                            self.setCursorDefault()
                            self.toggleEnabledState(True)
                            return
                else:
                    self.sleepInhibitor.uninhibit()
                    self.isRunning = False
                    self.setCursorDefault()
                    self.toggleEnabledState(True)
                    return
        if actionClientData == GeneralActions.MOVE_GROUP.value:
            self.moveGroup()
            self.sleepInhibitor.uninhibit()
            return
        if (
            actionClientData == GeneralActions.SET_APP_STATE.value
            or actionClientData == GridActions.SET_APP_STATE.value
        ):
            self.displayAppStateChoiceDlg()
            if not self.AppState:
                self.sleepInhibitor.uninhibit()
                self.isRunning = False
                self.setCursorDefault()
                self.toggleEnabledState(True)
                return
        if actionClientData == GeneralActions.SET_DEVICE_MODE.value:
            res = None
            with wx.SingleChoiceDialog(
                self, "Select Device Mode:", "", ["Multi-App", "Kiosk"]
            ) as dlg:
                res = dlg.ShowModal()
                if res == wx.ID_OK:
                    if dlg.GetStringSelection() == "Multi-App":
                        actionClientData = GeneralActions.SET_MULTI.value
                    else:
                        actionClientData = GeneralActions.SET_KIOSK.value
            if not res or res == wx.ID_CANCEL:
                self.sleepInhibitor.uninhibit()
                self.isRunning = False
                self.setCursorDefault()
                self.toggleEnabledState(True)
                return
        if (
            self.sidePanel.selectedGroupsList
            and (not self.sidePanel.selectedDevicesList or allDevicesSelected)
            and actionSelection > 0
            and actionClientData > 0
            and actionClientData < GridActions.MODIFY_ALIAS_AND_TAGS.value
        ):
            # run action on group
            if self.checkAppRequirement(actionClientData, appSelection, appLabel):
                self.sleepInhibitor.uninhibit()
                return
            self.gridPanel.grid_1_contents = []
            self.gridPanel.grid_2_contents = []
            self.gridPanel.grid_3_contents = []
            self.gridPanel.userEdited = []
            self.gridPanel.disableGridProperties()

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
                ),
                name="TakeActionOnGroups",
            ).startWithRetry()
        elif (
            self.sidePanel.selectedDevicesList
            and actionSelection > 0
            and actionClientData > 0
            and actionClientData < GridActions.MODIFY_ALIAS_AND_TAGS.value
        ):
            # run action on device
            if self.checkAppRequirement(actionClientData, appSelection, appLabel):
                self.sleepInhibitor.uninhibit()
                return
            self.gridPanel.grid_1_contents = []
            self.gridPanel.grid_2_contents = []
            self.gridPanel.grid_3_contents = []
            self.gridPanel.userEdited = []
            self.gridPanel.disableGridProperties()
            for deviceId in self.sidePanel.selectedDevicesList:
                deviceLabel = None
                try:
                    deviceLabel = list(self.sidePanel.devices.keys())[
                        list(self.sidePanel.devices.values()).index(deviceId)
                    ]
                except:
                    deviceLabel = list(self.sidePanel.devicesExtended.keys())[
                        list(self.sidePanel.devicesExtended.values()).index(deviceId)
                    ]
                self.Logging(
                    '---> Attempting to run action, "%s", on device, %s.'
                    % (actionLabel, deviceLabel)
                )
            self.gauge.Pulse()
            wxThread.GUIThread(
                self,
                TakeAction,
                (self, self.sidePanel.selectedDevicesList, actionClientData, True),
                name="TakeActionOnDevices",
            ).startWithRetry()
        elif actionClientData >= GridActions.MODIFY_ALIAS_AND_TAGS.value:
            # run grid action
            if self.gridPanel.grid_1.GetNumberRows() > 0:
                runAction = True
                result = None
                if Globals.SHOW_GRID_DIALOG:
                    result = CheckboxMessageBox(
                        "Confirmation",
                        "The %s will attempt to process the action on all devices in the Device Info grid.\n\nREMINDER: Only %s tags MAX may be currently applied to a device!\n\nContinue?"
                        % (Globals.TITLE, Globals.MAX_TAGS),
                    )

                    if result.ShowModal() != wx.ID_OK:
                        runAction = False
                if result and result.getCheckBoxValue():
                    Globals.SHOW_GRID_DIALOG = False
                    self.preferences["gridDialog"] = Globals.SHOW_GRID_DIALOG
                if runAction:
                    if self.checkAppRequirement(
                        actionClientData, appSelection, appLabel
                    ):
                        self.sleepInhibitor.uninhibit()
                        return
                    self.Logging(
                        '---> Attempting to run grid action, "%s".' % actionLabel
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
                    ).startWithRetry()
                else:
                    self.sleepInhibitor.uninhibit()
                    self.isRunning = False
                    self.setCursorDefault()
                    self.toggleEnabledState(True)
            else:
                displayMessageBox(
                    (
                        "Make sure the grid has data to perform the action on",
                        wx.OK | wx.ICON_ERROR,
                    )
                )
                self.sleepInhibitor.uninhibit()
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
            self.sleepInhibitor.uninhibit()
            self.isRunning = False
            self.setCursorDefault()
            self.toggleEnabledState(True)

    @api_tool_decorator()
    def checkAppRequirement(self, actionClientData, appSelection, appLabel):
        if (
            actionClientData == GeneralActions.SET_KIOSK.value
            or actionClientData == GeneralActions.CLEAR_APP_DATA.value
            or actionClientData == GeneralActions.INSTALL_APP.value
            or actionClientData == GeneralActions.UNINSTALL_APP.value
            or actionClientData == GeneralActions.SET_APP_STATE.value
            or actionClientData == GridActions.INSTALL_APP.value
            or actionClientData == GridActions.UNINSTALL_APP.value
        ) and (appSelection < 0 or appLabel == "No available app(s) on this device"):
            displayMessageBox(
                ("Please select a valid application", wx.OK | wx.ICON_ERROR)
            )
            self.sidePanel.notebook_1.SetSelection(2)
            self.isRunning = False
            self.setCursorDefault()
            self.toggleEnabledState(True)
            return True
        return False

    @api_tool_decorator()
    def showConsole(self, event):
        """ Toggle Console Display """
        if not self.consoleWin:
            self.consoleWin = Console(parent=self)
            self.menubar.clearConsole.Enable(True)
            self.Bind(wx.EVT_MENU, self.onClear, self.menubar.clearConsole)
        else:
            self.consoleWin.DestroyLater()
            self.menubar.clearConsole.Enable(False)

    @api_tool_decorator()
    def onClear(self, event):
        """ Clear Console """
        if self.consoleWin:
            self.consoleWin.onClear()

    @api_tool_decorator()
    def onCommand(self, event, value="{\n\n}", level=0):
        """ When the user wants to run a command show the command dialog """
        if level < Globals.MAX_RETRY:
            self.setCursorBusy()
            self.setGaugeValue(0)

            if self.sidePanel.selectedGroupsList:
                result = None
                cmdArgs = None
                commandType = None
                schArgs = None
                schType = None
                with CommandDialog("Enter JSON Command", value=value) as cmdDialog:
                    result = cmdDialog.ShowModal()
                    if result == wx.ID_OK:
                        try:
                            (
                                cmdArgs,
                                commandType,
                                schArgs,
                                schType,
                            ) = cmdDialog.GetValue()
                            if cmdArgs is not None:
                                createCommand(
                                    self, cmdArgs, commandType, schArgs, schType
                                )
                        except Exception as e:
                            displayMessageBox(
                                (
                                    "An error occurred while process the inputted JSON object, please make sure it is formatted correctly",
                                    wx.OK | wx.ICON_ERROR,
                                )
                            )
                            ApiToolLog().LogError(e)
                    cmdDialog.DestroyLater()
            else:
                displayMessageBox(
                    ("Please select an group and or device", wx.OK | wx.ICON_ERROR)
                )

            self.setCursorDefault()

    @api_tool_decorator()
    def onCommandDone(self, event):
        """ Tell user to check the Esper Console for detailed results """
        cmdResult = None
        msg = ""
        if hasattr(event, "GetValue"):
            cmdResult = event.GetValue()
        else:
            cmdResult = event
        if type(cmdResult) == tuple:
            msg = cmdResult[0]
            cmdResult = cmdResult[1]
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
                "Action has been executed.",
                "%s\n\nCheck the Esper Console for details. Last known status listed below."
                % msg
                + "\n"
                if msg
                else "",
                "Command(s) have been fired.",
                result,
            ) as dialog:
                res = dialog.ShowModal()
        # wx.CallLater(3000, self.setGaugeValue, 0)
        postEventToFrame(
            eventUtil.myEVT_PROCESS_FUNCTION,
            (wx.CallLater, (3000, self.setGaugeValue, 0)),
        )

    @api_tool_decorator()
    def setStatus(self, status, orgingalMsg, isError=False):
        """ Set status bar text """
        self.sbText.SetLabel(status)
        if orgingalMsg:
            self.sbText.SetToolTip(orgingalMsg.replace("--->", ""))
        if isError:
            self.sbText.SetForegroundColour(Color.red.value)
        else:
            self.sbText.SetForegroundColour(Color.black.value)

    @api_tool_decorator()
    def onFetch(self, event):
        evtValue = event.GetValue()
        if evtValue:
            action = evtValue[0]
            entId = evtValue[1]
            deviceList = evtValue[2]

            wxThread.GUIThread(
                self,
                self.processFetch,
                (action, entId, deviceList, True, len(deviceList) * 3),
                name="ProcessFetch",
            ).startWithRetry()

    @api_tool_decorator()
    def processFetch(self, action, entId, deviceList, updateGauge=False, maxGauge=None):
        """ Given device data perform the specified action """
        threads = []
        appToUse = None
        appVersion = None
        if self.sidePanel.selectedAppEntry:
            appToUse = self.sidePanel.selectedAppEntry["pkgName"]
            appVersion = self.sidePanel.selectedAppEntry["version"]
        if (
            action == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value
            or action == GeneralActions.GENERATE_APP_REPORT.value
            or action == GeneralActions.GENERATE_INFO_REPORT.value
        ):
            self.gridPanel.disableGridProperties()
        num = len(deviceList)
        print("Fetch Execution time: %s" % (time.time() - self.start_time))
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

            deviceId = None
            if hasattr(device, "id"):
                deviceId = device.id
            else:
                deviceId = device["id"]

            if action == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value:
                if len(self.gridPanel.grid_1_contents) < Globals.MAX_GRID_LOAD + 1:
                    if self.WINDOWS:
                        deviceThread = wxThread.GUIThread(
                            self,
                            self.gridPanel.addDeviceToDeviceGrid,
                            (deviceInfo),
                            name="addDeviceToDeviceGrid",
                        )
                        deviceThread.startWithRetry()
                        networkThread = wxThread.GUIThread(
                            self,
                            self.gridPanel.addDeviceToNetworkGrid,
                            (device, deviceInfo),
                            name="addDeviceToNetworkGrid",
                        )
                        networkThread.startWithRetry()
                        appThread = wxThread.GUIThread(
                            self,
                            self.gridPanel.populateAppGrid,
                            (device, deviceInfo, deviceInfo["appObj"]),
                            name="populateAppGrid",
                        )
                        appThread.startWithRetry()
                        threads.append(deviceThread)
                        threads.append(networkThread)
                        threads.append(appThread)
                    else:
                        self.gridPanel.addDeviceToDeviceGrid(deviceInfo)
                        self.gridPanel.addDeviceToNetworkGrid, (device, deviceInfo)
                        self.gridPanel.populateAppGrid, (
                            device,
                            deviceInfo,
                            deviceInfo["appObj"],
                        )
                else:
                    # construct and add info to grid contents
                    self.gridPanel.constructDeviceGridContent(deviceInfo)
                    self.gridPanel.constructNetworkGridContent(device, deviceInfo)
                    self.gridPanel.constructAppGridContent(
                        device, deviceInfo, deviceInfo["appObj"]
                    )
            elif action == GeneralActions.SET_KIOSK.value:
                thread = wxThread.GUIThread(
                    self, setKiosk, (self, device, deviceInfo), name="SetKiosk"
                )
                thread.startWithRetry()
                threads.append(thread)
            elif action == GeneralActions.SET_MULTI.value:
                thread = wxThread.GUIThread(
                    self, setMulti, (self, device, deviceInfo), name="SetMulti"
                )
                thread.startWithRetry()
                threads.append(thread)
            elif action == GeneralActions.CLEAR_APP_DATA.value:
                thread = wxThread.GUIThread(
                    self,
                    clearAppData,
                    (self, device),
                    name="clearAppData",
                )
                thread.startWithRetry()
                threads.append(thread)
            elif (
                action == GeneralActions.SET_APP_STATE.value
                and self.AppState == "DISABLE"
            ):
                thread = wxThread.GUIThread(
                    self,
                    setAppState,
                    (deviceId, appToUse, appVersion, "DISABLE"),
                    name="SetAppDisable",
                )
                thread.startWithRetry()
                threads.append(thread)
            elif (
                action == GeneralActions.SET_APP_STATE.value and self.AppState == "HIDE"
            ):
                thread = wxThread.GUIThread(
                    self,
                    setAppState,
                    (deviceId, appToUse, appVersion, "HIDE"),
                    name="SetAppHide",
                )
                thread.startWithRetry()
                threads.append(thread)
            elif (
                action == GeneralActions.SET_APP_STATE.value and self.AppState == "SHOW"
            ):
                thread = wxThread.GUIThread(
                    self,
                    setAppState,
                    (deviceId, appToUse, appVersion, "SHOW"),
                    name="SetAppShow",
                )
                thread.startWithRetry()
                threads.append(thread)
            elif action == GeneralActions.REMOVE_NON_WHITELIST_AP.value:
                thread = wxThread.GUIThread(
                    self,
                    removeNonWhitelisted,
                    (deviceId, deviceInfo),
                    name="removeNonWhitelisted",
                )
                thread.startWithRetry()
                threads.append(thread)
            elif action == GeneralActions.INSTALL_APP.value:
                thread = wxThread.GUIThread(
                    self,
                    installAppOnDevices,
                    (appToUse, appVersion, deviceId),
                    name="installAppOnDevices",
                )
                thread.startWithRetry()
                threads.append(thread)
            elif action == GeneralActions.UNINSTALL_APP.value:
                thread = wxThread.GUIThread(
                    self,
                    uninstallAppOnDevice,
                    (appToUse, deviceId),
                    name="uninstallAppOnDevice",
                )
                thread.startWithRetry()
                threads.append(thread)
            elif action == GeneralActions.GENERATE_APP_REPORT.value:
                if len(self.gridPanel.grid_3_contents) < Globals.MAX_GRID_LOAD + 1:
                    if self.WINDOWS:
                        appThread = wxThread.GUIThread(
                            self,
                            self.gridPanel.populateAppGrid,
                            (device, deviceInfo, deviceInfo["appObj"]),
                            name="populateAppGrid",
                        )
                        appThread.startWithRetry()
                        threads.append(appThread)
                    else:
                        self.gridPanel.populateAppGrid(
                            device, deviceInfo, deviceInfo["appObj"]
                        )
                else:
                    self.gridPanel.constructAppGridContent(
                        device, deviceInfo, deviceInfo["appObj"]
                    )
            elif action == GeneralActions.GENERATE_INFO_REPORT.value:
                if len(self.gridPanel.grid_1_contents) < Globals.MAX_GRID_LOAD + 1:
                    if self.WINDOWS:
                        deviceThread = wxThread.GUIThread(
                            self,
                            self.gridPanel.addDeviceToDeviceGrid,
                            (deviceInfo),
                            name="addDeviceToDeviceGrid",
                        )
                        deviceThread.startWithRetry()
                        networkThread = wxThread.GUIThread(
                            self,
                            self.gridPanel.addDeviceToNetworkGrid,
                            (device, deviceInfo),
                            name="addDeviceToNetworkGrid",
                        )
                        networkThread.startWithRetry()
                        threads.append(deviceThread)
                        threads.append(networkThread)
                    else:
                        self.gridPanel.addDeviceToDeviceGrid(deviceInfo)
                        self.gridPanel.addDeviceToNetworkGrid(device, deviceInfo)
                else:
                    # construct and add info to grid contents
                    self.gridPanel.constructDeviceGridContent(deviceInfo)
                    self.gridPanel.constructNetworkGridContent(device, deviceInfo)
            elif action == GeneralActions.GENERATE_DEVICE_REPORT.value:
                if len(self.gridPanel.grid_1_contents) < Globals.MAX_GRID_LOAD + 1:
                    if self.WINDOWS:
                        deviceThread = wxThread.GUIThread(
                            self,
                            self.gridPanel.addDeviceToDeviceGrid,
                            (deviceInfo),
                            name="addDeviceToDeviceGrid",
                        )
                        deviceThread.startWithRetry()
                        threads.append(deviceThread)
                    else:
                        self.gridPanel.addDeviceToDeviceGrid(deviceInfo)
                else:
                    # construct and add info to grid contents
                    self.gridPanel.constructDeviceGridContent(deviceInfo)
            joinThreadList(threads)

            value = int(num / maxGauge * 100)
            if updateGauge and value <= 99:
                num += 1
                self.setGaugeValue(value)
        wxThread.GUIThread(
            self,
            self.waitForThreadsThenSetCursorDefault,
            (threads, 3, action),
            name="waitForThreadsThenSetCursorDefault_3",
        ).startWithRetry()

    @api_tool_decorator()
    def onDeviceSelections(self, event):
        """ When the user selects a device showcase apps related to that device """
        self.menubar.setSaveMenuOptionsEnableState(False)
        self.SetFocus()
        self.gauge.Pulse()
        self.setCursorBusy()
        if len(self.sidePanel.selectedDevicesList) > 0 and Globals.GET_APP_EACH_DEVICE:
            self.sidePanel.runBtn.Enable(False)
            wxThread.GUIThread(
                self,
                self.addDevicesApps,
                args=None,
                eventType=eventUtil.myEVT_COMPLETE,
                eventArg=(not self.isRunning and not self.isSavingPrefs),
                sendEventArgInsteadOfResult=True,
                name="addDeviceApps",
            ).startWithRetry()
        else:
            evt = eventUtil.CustomEvent(eventUtil.myEVT_COMPLETE, -1, True)
            wx.PostEvent(self, evt)

    @api_tool_decorator()
    def addDevicesApps(self):
        num = 1
        appAdded = False
        self.sidePanel.selectedDeviceApps = []
        if not Globals.USE_ENTERPRISE_APP:
            self.sidePanel.apps = self.sidePanel.enterpriseApps
        else:
            self.sidePanel.apps = (
                self.sidePanel.selectedDeviceApps + self.sidePanel.enterpriseApps
            )
        for deviceId in self.sidePanel.selectedDevicesList:
            _, _ = getdeviceapps(
                deviceId, createAppList=True, useEnterprise=Globals.USE_ENTERPRISE_APP
            )
            if len(self.sidePanel.selectedDevicesList) > 0:
                self.setGaugeValue(
                    int(float(num / len(self.sidePanel.selectedDevicesList)) * 100)
                )
            num += 1
        if not appAdded:
            self.sidePanel.selectedApp.Append("No available app(s) on this device")
            self.sidePanel.selectedApp.SetSelection(0)
        self.menubar.setSaveMenuOptionsEnableState(True)

    @api_tool_decorator()
    def MacReopenApp(self, event):
        """Called when the doc icon is clicked, and ???"""
        self.onActivate(self, event, skip=False)
        if event.GetActive():
            try:
                self.GetTopWindow().Raise()
            except:
                self.tryToMakeActive()
        event.Skip()

    @api_tool_decorator()
    def MacNewFile(self):
        pass

    @api_tool_decorator()
    def MacPrintFile(self, file_path):
        pass

    @api_tool_decorator(locks=[Globals.gauge_lock])
    def setGaugeValue(self, value):
        """ Attempt to set Gauge to the specififed value """
        if Globals.gauge_lock.locked():
            return
        Globals.gauge_lock.acquire()
        if hasattr(value, "GetValue"):
            value = value.GetValue()
        if bool(self.gauge):
            maxValue = self.gauge.GetRange()
            if value > maxValue:
                value = maxValue
            if value < 0:
                value = 0
            if value >= 0 and value <= maxValue:
                self.gauge.SetValue(value)
        if Globals.gauge_lock.locked():
            Globals.gauge_lock.release()

    @api_tool_decorator()
    def onComplete(self, event, isError=False):
        """ Things that should be done once an Action is completed """
        enable = False
        action = None
        cmdResults = None
        if event:
            eventVal = None
            if hasattr(event, "GetValue"):
                eventVal = event.GetValue()
            else:
                eventVal = event
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
        title = "Action Completed"
        msg = ""
        if not self.IsActive() and not isError:
            if (
                self.sidePanel.actionChoice.GetClientData(
                    self.sidePanel.actionChoice.GetSelection()
                )
                == action
            ):
                actionName = self.sidePanel.actionChoice.GetValue().replace(
                    "Action -> ", ""
                )
                msg = "%s has completed." % actionName
            else:
                msg = "Action has completed."
        if self.IsFrozen():
            self.Thaw()
        self.gridPanel.button_2.Enable(self.gridArrowState["next"])
        self.gridPanel.button_1.Enable(self.gridArrowState["prev"])
        if self.gridPanel.grid_1.IsFrozen():
            self.gridPanel.grid_1.Thaw()
        if self.gridPanel.grid_2.IsFrozen():
            self.gridPanel.grid_2.Thaw()
        if self.gridPanel.grid_3.IsFrozen():
            self.gridPanel.grid_3.Thaw()
        if self.gridPanel.disableProperties:
            self.gridPanel.enableGridProperties()
        self.gridPanel.autoSizeGridsColumns()
        if self.isRunning or enable:
            self.toggleEnabledState(True)
        self.isRunning = False
        if (
            action == GeneralActions.GENERATE_INFO_REPORT.value
            or action == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value
        ):
            self.gridPanel.notebook_2.SetSelection(0)
        elif action == GeneralActions.GENERATE_APP_REPORT.value:
            self.gridPanel.notebook_2.SetSelection(2)
        self.sidePanel.sortAndPopulateAppChoice()
        if not self.IsIconized() and self.IsActive():
            postEventToFrame(
                eventUtil.myEVT_PROCESS_FUNCTION,
                (wx.CallLater, (3000, self.setGaugeValue, 0)),
            )
            # wx.CallLater(3000, self.setGaugeValue, 0)
        if cmdResults:
            self.onCommandDone(cmdResults)
        self.menubar.enableConfigMenu()
        self.Logging("---> Completed Action")
        self.displayNotification(title, msg)
        # gc.collect()
        self.sleepInhibitor.uninhibit()
        if hasattr(self, "start_time"):
            print("Run Execution time: %s" % (time.time() - self.start_time))

    @api_tool_decorator()
    def onActivate(self, event, skip=True):
        if not self.isRunning and not self.isUploading and not self.isBusy:
            wx.CallLater(3000, self.setGaugeValue, 0)
        if self.notification:
            self.notification.Close()
        self.Refresh()
        if skip:
            event.Skip()

    @api_tool_decorator()
    def onClearGrids(self, event):
        """ Empty Grids """
        thread = wxThread.GUIThread(
            self,
            self.gridPanel.emptyDeviceGrid,
            None,
            eventType=None,
            name="emptyDeviceGrid",
        )
        thread.startWithRetry()
        netThread = wxThread.GUIThread(
            self,
            self.gridPanel.emptyNetworkGrid,
            None,
            eventType=None,
            name="emptyNetworkGrid",
        )
        netThread.startWithRetry()
        appThread = wxThread.GUIThread(
            self,
            self.gridPanel.emptyAppGrid,
            None,
            eventType=None,
            name="emptyAppGrid",
        )
        appThread.startWithRetry()

    @api_tool_decorator()
    def readAuthCSV(self):
        if os.path.exists(Globals.csv_auth_path):
            if self.key and crypto().isFileEncrypt(Globals.csv_auth_path, self.key):
                crypto().decrypt(Globals.csv_auth_path, self.key, True)
            with open(Globals.csv_auth_path, "r") as csvFile:
                reader = csv.reader(
                    csvFile, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True
                )
                self.auth_data = list(reader)

    @api_tool_decorator()
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

    @api_tool_decorator()
    def savePrefs(self, dialog):
        """ Save Preferences """
        self.preferences = dialog.GetPrefs()
        with open(self.prefPath, "w") as outfile:
            json.dump(self.preferences, outfile)
        evt = eventUtil.CustomEvent(eventUtil.myEVT_LOG, -1, "---> Preferences' Saved")
        wx.PostEvent(self, evt)

    @api_tool_decorator()
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
            save.startWithRetry()
            if self.sidePanel.selectedGroupsList and self.preferences["enableDevice"]:
                self.PopulateDevices(None)
            if self.sidePanel.selectedDevicesList:
                self.sidePanel.selectedDeviceApps = []
                self.onDeviceSelections(None)
            self.setFontSizeForLabels()
        if self.preferences["enableDevice"]:
            self.sidePanel.deviceChoice.Enable(True)
        else:
            self.sidePanel.deviceChoice.Enable(False)
        self.isSavingPrefs = False

    @api_tool_decorator()
    def onFail(self, event):
        """ Try to showcase rows in the grid on which an action failed on """
        failed = event.GetValue()
        if self.gridPanel.grid_1_contents and self.gridPanel.grid_2_contents:
            if type(failed) == list:
                for device in failed:
                    if "Queued" in device or "Scheduled" in device:
                        self.gridPanel.applyTextColorToDevice(
                            device[0], Color.orange.value, bgColor=Color.warnBg.value
                        )
                    else:
                        self.gridPanel.applyTextColorToDevice(
                            device, Color.red.value, bgColor=Color.errorBg.value
                        )
            elif type(failed) == tuple:
                if "Queued" in failed or "Scheduled" in failed:
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

    @api_tool_decorator()
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

    @api_tool_decorator()
    def onClone(self, event):
        with TemplateDialog(self.sidePanel.configChoice, parent=self) as self.tmpDialog:
            result = self.tmpDialog.ShowModal()
            if result == wx.ID_OK:
                self.prepareClone(self.tmpDialog)
            self.tmpDialog.DestroyLater()

    @api_tool_decorator()
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
        clone.startWithRetry()

    @api_tool_decorator()
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
            clone.startWithRetry()
        else:
            self.isRunning = False
            self.setGaugeValue(0)
            self.setCursorDefault()
        if result and result.getCheckBoxValue():
            Globals.SHOW_TEMPLATE_DIALOG = False
            self.preferences["templateDialog"] = Globals.SHOW_TEMPLATE_DIALOG

    @api_tool_decorator()
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
            clone.startWithRetry()
        else:
            self.isRunning = False
            self.setGaugeValue(0)
            self.setCursorDefault()
        if result and result.getCheckBoxValue():
            Globals.SHOW_TEMPLATE_UPDATE = False
            self.preferences["templateUpdate"] = Globals.SHOW_TEMPLATE_UPDATE

    @api_tool_decorator()
    def createClone(
        self, util, templateFound, toApi, toKey, toEntId, update=False, level=0
    ):
        if level == 0:
            templateFound = util.processDeviceGroup(templateFound)
            templateFound = util.processWallpapers(templateFound)
        self.Logging("Attempting to copy template...")
        res = None
        if update:
            res = util.updateTemplate(toApi, toKey, toEntId, templateFound)
        else:
            res = util.createTemplate(toApi, toKey, toEntId, templateFound, level + 1)
        if "errors" not in res:
            action = "created" if not update else "updated"
            self.Logging("Template sucessfully %s." % action)
            displayMessageBox(
                ("Template sucessfully %s." % action, wx.OK | wx.ICON_INFORMATION)
            )
        elif (
            "errors" in res
            and res["errors"]
            and "EMM" in res["errors"][0]
            and level < 2
        ):
            del templateFound["template"]["application"]["managed_google_play_disabled"]
            self.createClone(
                util, templateFound, toApi, toKey, toEntId, update, level + 1
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
        evt = eventUtil.CustomEvent(eventUtil.myEVT_COMPLETE, -1, None)
        wx.PostEvent(self, evt)

    @api_tool_decorator()
    def onSearch(self, event=None):
        queryString = ""
        if hasattr(event, "GetString"):
            queryString = event.GetString()
        elif isinstance(event, str):
            queryString = event
        else:
            queryString = self.frame_toolbar.search.GetValue()

        if self.searchThreads:
            for thread in self.searchThreads:
                if thread.is_alive():
                    if hasattr(thread, "stop"):
                        thread.stop()
            self.searchThreads = []

        t = wxThread.GUIThread(
            self,
            self.processSearch,
            args=(event, queryString),
            name="processSearch",
        )
        t.startWithRetry()
        self.searchThreads.append(t)

    def processSearch(self, event, queryString):
        if self.searchThreads:
            for thread in self.searchThreads:
                if thread.is_alive() and threading.current_thread() != thread:
                    thread.join()

        self.setCursorBusy()
        self.gridPanel.setGridsCursor(wx.Cursor(wx.CURSOR_WAIT))
        self.gridPanel.disableGridProperties()
        if (
            hasattr(event, "EventType")
            and (
                (wx.EVT_TEXT.typeId == event.EventType and not queryString)
                or (wx.EVT_SEARCH.typeId == event.EventType and not queryString)
                or wx.EVT_SEARCH_CANCEL.typeId == event.EventType
            )
            or wx.EVT_CHAR.typeId == event
        ):
            self.applySearchColor(queryString, Color.white.value, True)
        if queryString:
            self.applySearchColor(queryString, Color.lightYellow.value)
            self.Logging("--> Search for %s completed" % queryString)
        else:
            self.frame_toolbar.search.SetValue("")
            self.applySearchColor(queryString, Color.white.value, True)
        self.setCursorDefault()
        self.gridPanel.setGridsCursor(wx.Cursor(wx.CURSOR_DEFAULT))
        self.gridPanel.enableGridProperties()

    def applySearchColor(self, queryString, color, applyAll=False):
        self.gridPanel.applyTextColorMatchingGridRow(
            self.gridPanel.grid_1, queryString, color, applyAll
        )
        self.gridPanel.applyTextColorMatchingGridRow(
            self.gridPanel.grid_2, queryString, color, applyAll
        )
        self.gridPanel.applyTextColorMatchingGridRow(
            self.gridPanel.grid_3, queryString, color, applyAll
        )

    @api_tool_decorator()
    def toggleEnabledState(self, state):
        self.sidePanel.runBtn.Enable(state)
        self.sidePanel.actionChoice.Enable(state)
        self.sidePanel.removeEndpointBtn.Enable(state)

        if not self.sidePanel.appChoice.IsEnabled() and state:
            action = self.sidePanel.actionChoice.GetValue()
            clientData = None
            if action in Globals.GENERAL_ACTIONS:
                clientData = Globals.GENERAL_ACTIONS[action]
            elif action in Globals.GRID_ACTIONS:
                clientData = Globals.GRID_ACTIONS[action]
            self.sidePanel.setAppChoiceState(clientData)
        else:
            self.sidePanel.appChoice.Enable(state)

        self.frame_toolbar.EnableTool(self.frame_toolbar.otool.Id, state)
        self.frame_toolbar.EnableTool(self.frame_toolbar.rtool.Id, state)
        self.frame_toolbar.EnableTool(self.frame_toolbar.cmdtool.Id, state)

        self.menubar.fileOpenConfig.Enable(state)
        self.menubar.pref.Enable(state)
        self.menubar.collection.Enable(state)
        self.menubar.eqlQuery.Enable(state)
        self.menubar.run.Enable(state)
        self.menubar.installedDevices.Enable(state)
        self.menubar.clone.Enable(state)
        self.menubar.command.Enable(state)
        self.menubar.collectionSubMenu.Enable(state)
        self.menubar.groupSubMenu.Enable(state)
        self.menubar.setSaveMenuOptionsEnableState(state)

    @api_tool_decorator()
    def onInstalledDevices(self, event):
        if self.sidePanel.apps:
            self.setCursorBusy()
            self.setGaugeValue(0)
            self.toggleEnabledState(False)
            with InstalledDevicesDlg(self.sidePanel.apps) as dlg:
                res = dlg.ShowModal()
                if res == wx.ID_OK:
                    app, version = dlg.getAppValues()
                    if app and version:
                        self.onClearGrids(None)
                        self.gauge.Pulse()
                        self.isRunning = True
                        resp = getInstallDevices(version, app)
                        res = []
                        for r in resp.results:
                            if r:
                                res.append(r.to_dict())
                        if res:
                            wxThread.GUIThread(
                                self,
                                processInstallDevices,
                                res,
                                name="iterateThroughDeviceList",
                            ).startWithRetry()
                        else:
                            displayMessageBox(
                                (
                                    "No device with that app version found",
                                    wx.ICON_INFORMATION,
                                )
                            )
                            postEventToFrame(
                                eventUtil.myEVT_UPDATE_GAUGE_LATER, (3000, 0)
                            )
                            self.setCursorDefault()
                            self.toggleEnabledState(True)
                    else:
                        displayMessageBox(
                            (
                                "Failed to get app id or version",
                                wx.ICON_INFORMATION,
                            )
                        )
                        postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE_LATER, (3000, 0))
                        self.setCursorDefault()
                        self.toggleEnabledState(True)
                dlg.DestroyLater()
        else:
            displayMessageBox(
                (
                    "No apps found",
                    wx.ICON_INFORMATION,
                )
            )
            postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE_LATER, (3000, 0))
            self.setCursorDefault()
            self.toggleEnabledState(True)

    @api_tool_decorator()
    def moveGroup(self, event=None):
        if self.sidePanel.selectedDevicesList:
            choices = list(self.sidePanel.groups.keys())
            groupMultiDialog = MultiSelectSearchDlg(
                self,
                choices,
                label="Select Group to move to",
                title="Select Group to move to",
                single=True,
                resp=self.sidePanel.groupsResp,
            )

            if groupMultiDialog.ShowModal() == wx.ID_OK:
                selections = groupMultiDialog.GetSelections()
                if selections:
                    selction = selections[0]
                    groups = getAllGroups(name=selction)
                if groups.results:
                    resp = moveGroup(
                        groups.results[0].id, self.sidePanel.selectedDevicesList
                    )
                    if resp and resp.status_code == 200:
                        displayMessageBox(
                            "Selected device(s) have been moved to the %s Group."
                            % groups.results[0].name
                        )
                        self.sidePanel.clearSelections()
                    elif resp:
                        displayMessageBox(str(resp))
                else:
                    displayMessageBox("No Group found with the name: %s" % selction)
                evt = eventUtil.CustomEvent(eventUtil.myEVT_COMPLETE, -1, True)
                wx.PostEvent(self, evt)
                return
            else:
                self.isRunning = False
                self.setCursorDefault()
                self.toggleEnabledState(True)
                return
        else:
            displayMessageBox(
                (
                    "Please select a Group and then the device(s) you wish to move from the selectors!",
                    wx.OK | wx.ICON_ERROR,
                )
            )
            self.isRunning = False
            self.setCursorDefault()
            self.toggleEnabledState(True)

    @api_tool_decorator()
    def createGroup(self, event):
        if not self.groupManage:
            self.groupManage = GroupManagement(self.groups)
        with self.groupManage as manage:
            manage.ShowModal()

    @api_tool_decorator()
    def installApp(self, event):
        if self.sidePanel.selectedGroupsList or self.sidePanel.selectedDevicesList:
            res = version = pkg = None
            with InstalledDevicesDlg(
                self.sidePanel.enterpriseApps, title="Install Application"
            ) as dlg:
                res = dlg.ShowModal()
                if res == wx.ID_OK:
                    _, version, pkg = dlg.getAppValues(returnPkgName=True)
            if pkg:
                t = None
                if self.sidePanel.selectedDevicesList:
                    t = wxThread.GUIThread(
                        self,
                        installAppOnDevices,
                        args=(pkg, version),
                        eventType=eventUtil.myEVT_COMMAND,
                        name="installAppOnDevices",
                    )
                elif self.sidePanel.selectedGroupsList:
                    t = wxThread.GUIThread(
                        self,
                        installAppOnGroups,
                        args=(pkg, version),
                        eventType=eventUtil.myEVT_COMMAND,
                        name="installAppOnGroups",
                    )
                if t:
                    t.startWithRetry()
        else:
            displayMessageBox(
                (
                    "Please select the group(s) and or device(s) you wish to install an app to!",
                    wx.OK | wx.ICON_ERROR,
                )
            )

    @api_tool_decorator()
    def uninstallApp(self, event):
        if self.sidePanel.selectedGroupsList or self.sidePanel.selectedDevicesList:
            res = pkg = None
            with InstalledDevicesDlg(
                self.sidePanel.apps, hide_version=True, title="Uninstall Application"
            ) as dlg:
                res = dlg.ShowModal()
            if res == wx.ID_OK:
                _, _, pkg = dlg.getAppValues(returnPkgName=True)
            if pkg:
                t = None
                if self.sidePanel.selectedDevicesList:
                    t = wxThread.GUIThread(
                        self,
                        uninstallAppOnDevice,
                        args=(pkg),
                        eventType=eventUtil.myEVT_COMMAND,
                        name="uninstallAppOnDevice",
                    )
                elif self.sidePanel.selectedGroupsList:
                    t = wxThread.GUIThread(
                        self,
                        uninstallAppOnGroup,
                        args=(pkg),
                        eventType=eventUtil.myEVT_COMMAND,
                        name="uninstallAppOnGroup",
                    )
                if t:
                    t.startWithRetry()
        else:
            displayMessageBox(
                (
                    "Please select the group(s) and or device(s) you wish to uninstall an app from!",
                    wx.OK | wx.ICON_ERROR,
                )
            )

    def callSetGaugeLater(self, event):
        delayMs = 3000
        value = 0
        if event and hasattr(event, "GetValue"):
            val = event.GetValue()
            if type(val) == tuple:
                delayMs = val[0]
                value = val[1]
        wx.CallLater(delayMs, self.setGaugeValue, value)

    def displayNotificationEvent(self, event):
        title = msg = ""
        if event and hasattr(event, "GetValue"):
            val = event.GetValue()
            if type(val) == tuple:
                title = val[0]
                msg = val[1]
        self.displayNotification(title, msg)

    def displayNotification(self, title, msg, displayActive=False):
        if not self.IsActive() or displayActive:
            self.notification = wxadv.NotificationMessage(title, msg, self)
            if self.notification:
                if hasattr(self.notification, "MSWUseToasts"):
                    try:
                        self.notification.MSWUseToasts()
                    except:
                        pass
                self.notification.Show()

    def onSuspend(self, event):
        if (
            self.isRunning
            or self.isRunningUpdate
            or self.isSavingPrefs
            or self.isUploading
            or self.isBusy
            and hasattr(event, "Veto")
        ):
            event.Veto()

    def displayAppStateChoiceDlg(self):
        res = None
        with wx.SingleChoiceDialog(
            self, "Select App State:", "", ["DISABLE", "HIDE", "SHOW"]
        ) as dlg:
            res = dlg.ShowModal()
            if res == wx.ID_OK:
                self.AppState = dlg.GetStringSelection()
            else:
                self.AppState = None

    def uploadApplication(self, event=None, title="", joinThread=False):
        with wx.FileDialog(
            self,
            "Upload APK" if not title else title,
            wildcard="APK files (*.apk)|*.apk",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
            defaultDir=str(self.defaultDir),
        ) as fileDialog:
            result = fileDialog.ShowModal()
            if result == wx.ID_OK:
                apk_path = fileDialog.GetPath()
                t = wxThread.GUIThread(self, uploadAppToEndpoint, (apk_path))
                t.startWithRetry()
                if joinThread:
                    t.join()
        if event:
            event.Skip()

    def processFunc(self, event):
        """ Primarily used to execute functions on the main thread (e.g. execute GUI actions on Mac)"""
        fun = event.GetValue()
        if callable(fun):
            fun()
        elif type(fun) == tuple and callable(fun[0]):
            if type(fun[1]) == tuple:
                fun[0](*fun[1])
            else:
                fun[0](fun[1])

    def onBulkFactoryReset(self, event):
        with BulkFactoryReset() as dlg:
            res = dlg.ShowModal()

            if res == wx.ID_OK:
                self.gauge.Pulse()
                ids = dlg.getIdentifiers()
                bulkFactoryReset(ids)

    def onGeofence(self, event):
        with GeofenceDialog() as dlg:
            dlg.ShowModal()
