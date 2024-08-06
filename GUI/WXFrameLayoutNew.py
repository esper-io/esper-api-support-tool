#!/usr/bin/env python

import csv
import json
import os.path
import platform
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import wx
import wx.adv as wxadv
from wx.core import TextEntryDialog

import Common.ApiTracker as ApiTracker
import Common.Globals as Globals
import GUI.EnhancedStatusBar as ESB
import Utility.API.EsperTemplateUtil as templateUtil
import Utility.EventUtility as eventUtil
import Utility.Threading.wxThread as wxThread
from Common.decorator import api_tool_decorator
from Common.enum import Color, GeneralActions, GridActions
from Common.SleepInhibitor import SleepInhibitor
from GUI.ConfigureWidget import WidgetPicker
from GUI.consoleWindow import Console
from GUI.Dialogs.BlueprintsConvertDialog import BlueprintsConvertDialog
from GUI.Dialogs.BlueprintsDialog import BlueprintsDialog
from GUI.Dialogs.CheckboxMessageBox import CheckboxMessageBox
from GUI.Dialogs.CommandDialog import CommandDialog
from GUI.Dialogs.ConfirmTextDialog import ConfirmTextDialog
from GUI.Dialogs.GeofenceDialog import GeofenceDialog
from GUI.Dialogs.InstalledDevicesDlg import InstalledDevicesDlg
from GUI.Dialogs.LargeTextEntryDialog import LargeTextEntryDialog
from GUI.Dialogs.MultiSelectSearchDlg import MultiSelectSearchDlg
from GUI.Dialogs.NewEndpointDialog import NewEndpointDialog
from GUI.Dialogs.PreferencesDialog import PreferencesDialog
from GUI.Dialogs.ScheduleCmdDialog import ScheduleCmdDialog
from GUI.Dialogs.TemplateDialog import TemplateDialog
from GUI.gridPanel import GridPanel
from GUI.menuBar import ToolMenuBar
from GUI.sidePanel import SidePanel
from GUI.toolBar import ToolsToolBar
from Utility.API.AppUtilities import getAllInstallableApps, getAppDictEntry
from Utility.API.AuditPosting import AuditPosting
from Utility.API.BlueprintUtility import (checkFeatureFlags, getAllBlueprints,
                                          modifyAppsInBlueprints,
                                          prepareBlueprintClone,
                                          prepareBlueprintConversion,
                                          pushBlueprintUpdate)
from Utility.API.CommandUtility import createCommand, sendPowerDownCommand
from Utility.API.DeviceUtility import getAllDevices
from Utility.API.EsperAPICalls import getTokenInfo, validateConfiguration
from Utility.API.GroupUtility import getAllGroups, moveGroup
from Utility.API.UserUtility import (getAllPendingUsers, getAllUsers,
                                     getSpecificUser)
from Utility.API.WidgetUtility import setWidget
from Utility.crypto import crypto
from Utility.EastUtility import (TakeAction, clearKnownGlobalVariables,
                                 fetchInstalledDevices, filterDeviceList,
                                 getAllDeviceInfo, removeNonWhitelisted,
                                 uploadAppToEndpoint)
from Utility.FileUtility import (getToolDataPath, read_csv_via_pandas,
                                 read_data_from_csv,
                                 read_data_from_csv_as_dict,
                                 read_excel_via_openpyxl, read_json_file,
                                 save_csv_pandas, save_excel_pandas_xlxswriter,
                                 write_data_to_csv, write_json_file)
from Utility.GridActionUtility import iterateThroughGridRows
from Utility.GridUtilities import createDataFrameFromDict, split_dataframe
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Resource import (checkEsperInternetConnection,
                              checkForInternetAccess,
                              checkIfCurrentThreadStopped, correctSaveFileName,
                              createNewFile, determineDoHereorMainThread,
                              displayFileDialog, displayMessageBox,
                              joinThreadList, openWebLinkInBrowser,
                              postEventToFrame, processFunc, resourcePath,
                              splitListIntoChunks, updateErrorTracker)


class NewFrameLayout(wx.Frame):
    def __init__(self):
        self.prefPath = ""
        self.authPath = ""

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
        self.SpreadsheetUploaded = False
        self.defaultDir = os.getcwd()
        self.groups = None
        self.groupManage = None
        self.AppState = None
        self.searchThreads = []
        self.blueprintsEnabled = False
        self.previousGroupFetchThread = None
        self.firstRun = True
        self.changedBlueprints = []
        self.groupThread = None
        self.appThread = None

        self.scheduleReport = None
        self.delayScheduleReport = True
        self.scheduleReportRunning = False
        self.scheduleCallLater = []

        self.isSaving = False

        basePath = getToolDataPath()
        if platform.system() == "Windows":
            self.WINDOWS = True
        else:
            self.WINDOWS = False
        self.prefPath = "%s/prefs.json" % basePath
        self.authPath = "%s/auth.csv" % basePath
        self.keyPath = "%s/east.key" % basePath

        wx.Frame.__init__(
            self, None, title=Globals.TITLE, style=wx.DEFAULT_FRAME_STYLE
        )
        self.SetSize(Globals.MIN_SIZE)
        self.SetMinSize(Globals.MIN_SIZE)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)

        sizer_4 = wx.FlexGridSizer(1, 2, 0, 0)
        self.sidePanel = SidePanel(self, self.panel_1)
        sizer_4.Add(self.sidePanel, 1, wx.EXPAND, 0)

        self.gridPanel = GridPanel(self, self.panel_1, wx.ID_ANY)
        sizer_4.Add(
            self.gridPanel, 1, wx.TOP | wx.BOTTOM | wx.RIGHT | wx.EXPAND, 4
        )

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
        self.statusBar.AddStaicTextAndGauge()
        # End Status Bar

        # Set Icon
        icon = wx.Icon()
        icon.CopyFromBitmap(
            wx.Bitmap(resourcePath("Images/icon.png"), wx.BITMAP_TYPE_PNG)
        )
        self.SetIcon(icon)

        self.notification = None

        self.audit = AuditPosting()

        # Bound Events
        self.DragAcceptFiles(True)
        self.Bind(wx.EVT_DROP_FILES, self.onFileDrop)
        self.Bind(eventUtil.EVT_FETCH, self.onFetch)
        self.Bind(eventUtil.EVT_GROUP, self.addGroupsToGroupChoice)
        self.Bind(eventUtil.EVT_COMPLETE, self.onComplete)
        self.Bind(eventUtil.EVT_LOG, self.onLog)
        self.Bind(eventUtil.EVT_COMMAND, self.onCommandDone)
        self.Bind(eventUtil.EVT_UPDATE_GAUGE, self.statusBar.setGaugeValue)
        self.Bind(eventUtil.EVT_UNCHECK_CONSOLE, self.menubar.uncheckConsole)
        self.Bind(eventUtil.EVT_CONFIRM_CLONE, self.confirmClone)
        self.Bind(eventUtil.EVT_CONFIRM_CLONE_UPDATE, self.confirmCloneUpdate)
        self.Bind(eventUtil.EVT_MESSAGE_BOX, displayMessageBox)
        self.Bind(
            eventUtil.EVT_THREAD_WAIT, self.waitForThreadsThenSetCursorDefault
        )
        self.Bind(eventUtil.EVT_PROCESS_FUNCTION, processFunc)
        self.Bind(eventUtil.EVT_AUDIT, self.audit.postOperation)
        self.Bind(wx.EVT_ACTIVATE_APP, self.MacReopenApp)
        self.Bind(wx.EVT_ACTIVATE, self.onActivate)
        self.Bind(eventUtil.EVT_UPDATE_GAUGE_LATER, self.callSetGaugeLater)
        self.Bind(
            eventUtil.EVT_DISPLAY_NOTIFICATION, self.displayNotificationEvent
        )
        self.Bind(wx.EVT_POWER_SUSPENDING, self.onSuspend)

        if self.kill:
            return

        self.prefDialog = PreferencesDialog(parent=self)

        Globals.frame = self

        self.loadPref()
        self.__set_properties()
        self.Layout()
        self.Centre()
        self.tryToMakeActive()

        if self.kill:
            return

        self.internetCheck = wxThread.GUIThread(
            self, checkForInternetAccess, (self), name="InternetCheck"
        )
        self.internetCheck.startWithRetry()
        self.errorTracker = wxThread.GUIThread(
            self, updateErrorTracker, None, name="updateErrorTracker"
        )
        self.errorTracker.startWithRetry()
        self.menubar.onUpdateCheck(showDlg=True)

        # Display disclaimer unless they have opt'd out.
        if Globals.SHOW_DISCLAIMER:
            self.preferences["showDisclaimer"] = self.menubar.onDisclaimer(
                showCheckBox=True
            )
            Globals.SHOW_DISCLAIMER = self.preferences["showDisclaimer"]

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
        determineDoHereorMainThread(self.Refresh)

    @api_tool_decorator()
    def onLog(self, event):
        """Event trying to log data"""
        evtValue = event.GetValue()
        if type(evtValue) is tuple:
            self.Logging(evtValue[0], evtValue[1])
        else:
            self.Logging(evtValue)

    @api_tool_decorator()
    def Logging(self, entry, isError=False):
        """Frame UI Logging"""
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
                shortMsg = entry[
                    0 : Globals.MAX_STATUS_CHAR - len(longEntryMsg)
                ]
                shortMsg += longEntryMsg
            self.setStatus(shortMsg, entry, isError)
        except:
            pass

    @api_tool_decorator()
    def AddEndpoint(self, event):
        """Try to open and load an Auth CSV"""
        isValid = False
        errorMsg = None
        name = host = entId = key = None
        while not isValid:
            with NewEndpointDialog(
                errorMsg=errorMsg, name=name, host=host, entId=entId, key=key
            ) as dialog:
                Globals.OPEN_DIALOGS.append(dialog)
                res = dialog.ShowModal()
                Globals.OPEN_DIALOGS.remove(dialog)
                if res == wx.ID_ADD:
                    try:
                        name, host, entId, key, prefix = dialog.getInputValues()
                        csvRow = dialog.getCSVRowEntry()
                        isValid = self.addEndpointEntry(
                            name, host, entId, key, prefix, csvRow
                        )
                        if isValid and type(isValid) == wx.MenuItem:
                            self.loadConfiguartion(isValid)
                        else:
                            _, host, _, _ = dialog.getUserInput()
                            ApiToolLog().Log(
                                "Failed to validate configuration via API; possible wrong input or internet connection issue."
                            )
                            displayMessageBox(
                                (
                                    "ERROR: An error occured when attempting to add the tenant.\nCheck inputs values and your internet connection.",
                                    wx.ICON_ERROR,
                                )
                            )
                    except Exception as e:
                        ApiToolLog().LogError(e)
                        _, host, _, _ = dialog.getUserInput()
                        displayMessageBox(
                            (
                                "ERROR: An error occured when attempting to add the tenant (%s).\nCheck inputs values and your internet connection."
                                % str(e),
                                wx.ICON_ERROR,
                            )
                        )
                else:
                    self.readAuthCSV()
                    if self.auth_data:
                        isValid = True
                    elif res == wx.ID_CANCEL and not self.IsShown():
                        self.OnQuit(event)
                    elif res == wx.ID_CANCEL:
                        break
        if event and hasattr(event, "Skip"):
            event.Skip()

    def addEndpointEntry(self, name, host, entId, key, prefix, csvRow):
        isValid = validateConfiguration(host, entId, key, prefix=prefix)
        if isValid:
            matchingConfig = []
            if self.auth_data:
                matchingConfig = list(
                    filter(
                        lambda x: x["enterprise"] == entId or x["name"] == name,
                        self.auth_data,
                    )
                )
                if matchingConfig:
                    matchingConfig = matchingConfig[0]
            if (
                not self.auth_data or csvRow not in self.auth_data
            ) and not matchingConfig:
                write_data_to_csv(self.authPath, csvRow, "a")
                Globals.csv_auth_path = self.authPath
                self.readAuthCSV()
                isValid = self.PopulateConfig(
                    auth=self.authPath, getItemForName=name
                )
                displayMessageBox(
                    ("Tenant has been added", wx.ICON_INFORMATION)
                )
            elif csvRow in self.auth_data or matchingConfig:
                self.auth_data_tmp = []
                for entry in self.auth_data:
                    if entry["apiHost"] == matchingConfig["apiHost"]:
                        self.auth_data_tmp.append(csvRow)
                    else:
                        self.auth_data_tmp.append(entry)
                self.auth_data = self.auth_data_tmp

                tmp = [["name", "apiHost", "enterprise", "apiKey", "apiPrefix"]]
                for auth in self.auth_data:
                    authEntry = []
                    indx = 0
                    if isinstance(auth, dict):
                        for val in auth.values():
                            if indx > len(tmp[0]):
                                break
                            authEntry.append(val)
                            indx += 1
                    else:
                        authEntry = auth
                    if authEntry not in tmp:
                        tmp.append(authEntry)
                write_data_to_csv(self.authPath, tmp)
                self.readAuthCSV()
                isValid = self.PopulateConfig(
                    auth=self.authPath, getItemForName=name
                )
                displayMessageBox(
                    ("Tenant has been added", wx.ICON_INFORMATION)
                )
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
        """Actions to take when frame is closed"""
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
        Globals.THREAD_POOL.abort()
        wx.Exit()

    @api_tool_decorator()
    def onSaveBoth(self, event):
        self.isSaving = True
        inFile = displayFileDialog(
            "Save Reports as...",
            "Microsoft Excel Open XML Spreadsheet (*.xlsx)|*.xlsx|CSV files (*.csv)|*.csv",
        )

        if inFile:  # Save button was pressed
            self.setCursorBusy()
            self.toggleEnabledState(False)
            self.gridPanel.disableGridProperties()
            Globals.THREAD_POOL.enqueue(self.saveFile, inFile)
            return True
        else:  # Either the cancel button was pressed or the window was closed
            self.isSaving = False
            return False

    @api_tool_decorator()
    def onSaveBothAll(self, event, action=None):
        if (
            self.sidePanel.selectedDevicesList
            or self.sidePanel.selectedGroupsList
        ):
            self.isSaving = True
            inFile = displayFileDialog(
                "Save Reports as...",
                "Microsoft Excel Open XML Spreadsheet (*.xlsx)|*.xlsx|CSV files (*.csv)|*.csv",
            )

            if inFile:  # Save button was pressed
                self.setCursorBusy()
                self.toggleEnabledState(False)
                self.gridPanel.disableGridProperties()
                self.Logging("Attempting to save file at %s" % inFile)
                self.statusBar.gauge.Pulse()
                Globals.THREAD_POOL.enqueue(
                    self.saveAllFile, inFile, action=action
                )
                return True
            else:  # Either the cancel button was pressed or the window was closed
                self.isSaving = False
                self.setCursorDefault()
                self.toggleEnabledState(True)
                if self.isRunning:
                    self.isRunning = False
                return False
        else:
            displayMessageBox(
                (
                    "Please select a group and or device(s) first!",
                    wx.OK | wx.ICON_ERROR,
                )
            )

    @api_tool_decorator()
    def saveAllFile(
        self, inFile, action=None, showDlg=True, allDevices=False, tolarance=1
    ):
        self.sleepInhibitor.inhibit()
        self.Logging("Obtaining Device data....")
        deviceList = getAllDeviceInfo(
            self, action=action, allDevices=allDevices, tolarance=tolarance
        )
        num = 1
        self.Logging("Processing device information for file")
        if (
            action == GeneralActions.GENERATE_DEVICE_REPORT.value
            or action == GeneralActions.GENERATE_INFO_REPORT.value
            or action == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value
        ):
            df = createDataFrameFromDict(
                Globals.CSV_TAG_ATTR_NAME, deviceList.values(), True
            )
            self.gridPanel.device_grid_contents = df
        if (
            action == GeneralActions.GENERATE_INFO_REPORT.value
            or action == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value
        ):
            df = createDataFrameFromDict(
                Globals.CSV_NETWORK_ATTR_NAME, deviceList.values(), True
            )
            self.gridPanel.network_grid_contents = df
        if (
            action == GeneralActions.GENERATE_APP_REPORT.value
            or action == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value
        ):
            input = []
            for item in deviceList.values():
                input.extend(item["AppsEntry"] if "AppsEntry" in item else [])
                postEventToFrame(
                    eventUtil.myEVT_UPDATE_GAUGE,
                    (int(num / len(deviceList.values())) * 35) + 50,
                )
                num += 1
            df = createDataFrameFromDict(Globals.CSV_APP_ATTR_NAME, input, True)
            self.gridPanel.app_grid_contents = df
        postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 50)

        self.Logging("Finished compiling information. Saving to file...")
        postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 85)

        self.saveGridData(
            inFile,
            action=action,
            tolarance=tolarance,
        )
        self.sleepInhibitor.uninhibit()
        postEventToFrame(eventUtil.myEVT_COMPLETE, (True, -1))

    @api_tool_decorator()
    def saveFile(self, inFile):
        self.Logging("Preparing to save data to: %s" % inFile)
        self.defaultDir = Path(inFile).parent
        self.saveGridData(
            inFile,
            action=GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value,
        )
        postEventToFrame(eventUtil.myEVT_COMPLETE, (True, -1))

    @api_tool_decorator()
    def saveGridData(
        self,
        inFile,
        action=None,
        showDlg=True,
        renameAppCsv=True,
        tolarance=1,
    ):
        deviceData, networkData, appData = self.gridPanel.getGridDataForSave()
        if inFile.endswith(".csv"):
            if (deviceData is not None and len(deviceData) > 0) or (
                networkData is not None and len(networkData) > 0
            ):
                result = pd.merge(
                    deviceData,
                    networkData,
                    on=["Esper Name", "Group"],
                    how="outer",
                )
                result = result.dropna(
                    axis=0, how="all", thresh=None, subset=None
                )
                save_csv_pandas(inFile, result)
            if (
                not action
                or action == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value
                or action == GeneralActions.GENERATE_APP_REPORT.value
            ) and renameAppCsv:
                if inFile.endswith(".csv"):
                    inFile = inFile[:-4]
                inFile += "_app-report.csv"

            if (
                not action
                or action == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value
                or action == GeneralActions.GENERATE_APP_REPORT.value
            ) and len(appData) > 0:
                save_csv_pandas(inFile, appData)
        elif inFile.endswith(".xlsx"):
            df_dict = {}
            if (
                not action
                or action <= GeneralActions.GENERATE_DEVICE_REPORT.value
                and Globals.COMBINE_DEVICE_AND_NETWORK_SHEETS
            ):
                if deviceData is not None and networkData is not None:
                    result = pd.merge(
                        deviceData,
                        networkData,
                        on=["Esper Name", "Group"],
                        how="outer",
                    )
                    result = result.dropna(
                        axis=0,
                        how="all",
                        thresh=None,
                        subset=None,
                    )
                    df_dict = self.subdivideSheetData(
                        "Device & Network", result, df_dict
                    )
                else:
                    deviceNetworkResults = pd.merge(
                        self.gridPanel.device_grid.createEmptyDataFrame(),
                        self.gridPanel.network_grid.createEmptyDataFrame(),
                        on=["Esper Name", "Group"],
                        how="outer",
                    )
                    df_dict = self.subdivideSheetData(
                        "Device & Network", deviceNetworkResults, df_dict
                    )
            elif deviceData is not None and len(deviceData) > 0:
                df_dict = self.subdivideSheetData("Device", deviceData, df_dict)
                if (
                    not action
                    or action <= GeneralActions.GENERATE_INFO_REPORT.value
                ):
                    df_dict = self.subdivideSheetData(
                        "Network", networkData, df_dict
                    )
            if (
                not action
                or (
                    action
                    and action == GeneralActions.GENERATE_APP_REPORT.value
                    or action
                    == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value
                )
                and appData is not None
                and len(appData) > 0
            ):
                df_dict = self.subdivideSheetData(
                    "Application", appData, df_dict
                )
            save_excel_pandas_xlxswriter(inFile, df_dict)

        Globals.THREAD_POOL.join(tolerance=tolarance)

        self.Logging("---> Info saved to file: " + inFile)
        postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 100)
        self.gridPanel.enableGridProperties()

        if showDlg:
            res = displayMessageBox(
                (
                    "Report Saved\n\n File saved at: %s\n\nWould you like to navigate to the file?"
                    % inFile,
                    wx.YES_NO | wx.ICON_INFORMATION,
                )
            )
            if res == wx.YES:
                parentDirectory = Path(inFile).parent.absolute()
                openWebLinkInBrowser(parentDirectory, isfile=True)
        self.isSaving = False
        self.toggleEnabledState(True)
        self.setCursorDefault()

    def subdivideSheetData(self, sheetName, sheetData, sheetContainer):
        if len(sheetData) > Globals.SHEET_CHUNK_SIZE:
            df_list = split_dataframe(sheetData, Globals.SHEET_CHUNK_SIZE)
            num = 1
            for df in df_list:
                newSheetName = sheetName + " Part " + str(num)
                sheetContainer[newSheetName] = df
                num += 1
        else:
            sheetContainer[sheetName] = sheetData
        return sheetContainer

    @api_tool_decorator()
    def onUploadSpreadsheet(self, event):
        """Upload device CSV to the device Grid"""
        if not Globals.enterprise_id:
            displayMessageBox(
                ("Please load a configuration first!", wx.OK | wx.ICON_ERROR)
            )
            return

        if self.isRunning:
            return

        self.setCursorBusy()
        self.gridPanel.EmptyGrids()
        postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 0)
        with wx.FileDialog(
            self,
            "Open Device Spreedsheet File",
            wildcard="Spreadsheet Files (*.csv;*.xlsx)|*.csv;*.xlsx|CSV Files (*.csv)|*.csv|Microsoft Excel Open XML Spreadsheet (*.xlsx)|*.xlsx",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
            defaultDir=str(self.defaultDir),
        ) as fileDialog:
            Globals.OPEN_DIALOGS.append(fileDialog)
            result = fileDialog.ShowModal()
            Globals.OPEN_DIALOGS.remove(fileDialog)
            if result == wx.ID_OK:
                # Proceed loading the file chosen by the user
                csv_auth_path = fileDialog.GetPath()
                self.defaultDir = Path(fileDialog.GetPath()).parent
                self.Logging(
                    "--->Attempting to load device data from %s" % csv_auth_path
                )
                self.toggleEnabledState(False)
                if self.WINDOWS:
                    Globals.THREAD_POOL.enqueue(
                        self.openDeviceSpreadsheet, csv_auth_path
                    )
                else:
                    self.openDeviceSpreadsheet(csv_auth_path)
                Globals.THREAD_POOL.enqueue(
                    self.waitForThreadsThenSetCursorDefault,
                    Globals.THREAD_POOL.threads,
                    2,
                    tolerance=1,
                )
            elif result == wx.ID_CANCEL:
                self.setCursorDefault()
                return  # the user changed their mind

    def openDeviceSpreadsheet(self, csv_auth_path):
        self.isUploading = True
        self.statusBar.gauge.Pulse()
        self.Logging("Reading Spreadsheet file: %s" % csv_auth_path)
        dfs = None
        if csv_auth_path.endswith(".csv"):
            dfs = read_csv_via_pandas(csv_auth_path)
        elif csv_auth_path.endswith(".xlsx"):
            try:
                dfs = read_excel_via_openpyxl(csv_auth_path)
            except Exception as e:
                print(e)
                pass
        if not hasattr(dfs, "dropna"):
            dfs = pd.concat(dfs, ignore_index=True)
        if dfs is not None:
            dfs = dfs.dropna(axis=0, how="all", thresh=None, subset=None)
            self.processSpreadsheetUpload(dfs)
        self.gridPanel.notebook_2.SetSelection(0)

    def processSpreadsheetUpload(self, data):
        self.SpreadsheetUploaded = True
        self.toggleEnabledState(False)
        self.sidePanel.groupChoice.Enable(False)
        self.sidePanel.deviceChoice.Enable(False)
        self.gridPanel.disableGridProperties()
        self.gridPanel.freezeGrids()
        self.Logging("Processing Spreadsheet data...")
        self.gridPanel.device_grid.applyNewDataFrame(data, resetPosition=True)
        self.gridPanel.device_grid_contents = data.copy(deep=True)

    @api_tool_decorator()
    def PopulateConfig(self, auth=None, getItemForName=None):
        """Populates Configuration From CSV"""
        self.Logging("--->Loading Tenants from %s" % Globals.csv_auth_path)
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

        postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 0)
        returnItem = None
        if os.path.isfile(configfile):
            if self.auth_data:
                auth_csv_reader = self.auth_data
                maxRow = len(auth_csv_reader)
                num = 1

                # Handle empty File
                if maxRow == 0:
                    self.Logging(
                        "--->ERROR: Empty Auth File, please add an Tenant!"
                    )
                    self.AddEndpoint(None)
                    return

                for row in auth_csv_reader:
                    postEventToFrame(
                        eventUtil.myEVT_UPDATE_GAUGE,
                        int(float(num / maxRow) * 25),
                    )
                    num += 1
                    if "name" in row:
                        self.sidePanel.configChoice[row["name"]] = row
                        item = self.menubar.configMenu.Append(
                            wx.ID_ANY,
                            row["name"],
                            row["name"],
                            kind=wx.ITEM_CHECK,
                        )
                        self.Bind(wx.EVT_MENU, self.loadConfiguartion, item)
                        self.menubar.configMenuOptions.append(item)
                        if (
                            str(getItemForName) == row["name"]
                            or str(getItemForName).lower()
                            == row["name"].lower()
                        ):
                            returnItem = item
                    else:
                        self.Logging(
                            "--->ERROR: Please check that the Auth CSV is set up correctly!"
                        )
                        defaultConfigVal = self.menubar.configMenu.Append(
                            wx.ID_NONE,
                            "No Loaded Tenants",
                            "No Loaded Tenants",
                        )
                        self.menubar.configMenuOptions.append(defaultConfigVal)
                        self.Bind(
                            wx.EVT_MENU, self.AddEndpoint, defaultConfigVal
                        )
                        return
            self.Logging(
                "---> Please Select an Tenant From the Configuartion Menu (defaulting to first Config)"
            )
            indx = 0
            if type(Globals.LAST_OPENED_ENDPOINT) is str:
                found = False
                for item in self.menubar.configMenuOptions:
                    if item.GetItemLabelText() == Globals.LAST_OPENED_ENDPOINT:
                        found = True
                        break
                    indx += 1
                if not found:
                    indx = 0
            else:
                indx = Globals.LAST_OPENED_ENDPOINT
                if indx > len(self.menubar.configMenuOptions):
                    indx = len(self.menubar.configMenuOptions) - 1
                    Globals.LAST_OPENED_ENDPOINT = indx
            if indx >= 0 and len(self.menubar.configMenuOptions) > indx:
                defaultConfigItem = self.menubar.configMenuOptions[indx]
                defaultConfigItem.Check(True)
                self.loadConfiguartion(defaultConfigItem)
        else:
            self.Logging(
                "---> "
                + configfile
                + " not found - PLEASE Quit and create configuration file"
            )
            defaultConfigVal = self.menubar.configMenu.Append(
                wx.ID_NONE, "No Loaded Tenants", "No Loaded Tenants"
            )
            self.menubar.configMenuOptions.append(defaultConfigVal)
            self.Bind(wx.EVT_MENU, self.AddEndpoint, defaultConfigVal)
        postEventToFrame(
            eventUtil.myEVT_PROCESS_FUNCTION,
            (wx.CallLater, (300, self.statusBar.setGaugeValue, 0)),
        )
        return returnItem

    @api_tool_decorator()
    def setCursorDefault(self):
        """Set cursor icon to default state"""
        try:
            self.isBusy = False
            myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
            self.SetCursor(myCursor)
        except:
            pass

    @api_tool_decorator()
    def setCursorBusy(self):
        """Set cursor icon to busy state"""
        self.isBusy = True
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)

    @api_tool_decorator()
    def loadConfiguartion(self, event, *args, **kwargs):
        """Populate Frame Layout With Device Configuration"""
        self.configMenuItem = self.menubar.configMenu.FindItemById(event.Id)
        if not self.firstRun:
            Globals.THREAD_POOL.clearQueue()
        self.onClearGrids()
        clearKnownGlobalVariables()
        try:
            if self.groupManage:
                self.groupManage.Destroy()
        except:
            pass
        # Reset Side Panel
        self.sidePanel.groups = {}
        self.sidePanel.devices = {}
        self.sidePanel.groupDeviceCount = {}
        self.sidePanel.clearSelections()
        self.sidePanel.destroyMultiChoiceDialogs()
        self.sidePanel.deviceChoice.Enable(False)
        self.sidePanel.removeEndpointBtn.Enable(False)
        self.sidePanel.notebook_1.SetSelection(0)
        # Clear Search Input
        self.frame_toolbar.search.SetValue("")
        # Disable other options
        self.toggleEnabledState(False)
        self.setCursorBusy()

        self.firstRun = False

        if ApiTracker.API_REQUEST_SESSION_TRACKER > 0:
            thread = ApiToolLog().LogApiRequestOccurrence(
                None, ApiTracker.API_REQUEST_TRACKER, True
            )
            if thread:
                thread.join()
            resetDict = {}
            for key in ApiTracker.API_REQUEST_TRACKER.keys():
                resetDict[key] = 0
            ApiTracker.API_REQUEST_TRACKER = resetDict
            ApiTracker.API_REQUEST_SESSION_TRACKER = 0
        try:
            self.Logging(
                "--->Attempting to load configuration: %s."
                % self.configMenuItem.GetItemLabelText()
            )
            selectedConfig = self.sidePanel.configChoice[
                self.configMenuItem.GetItemLabelText()
            ]

            indx = 0
            found = False
            foundItem = None
            for item in self.configMenuItem.Menu.MenuItems:
                if item != self.configMenuItem:
                    item.Check(False)
                else:
                    item.Check(True)
                    found = True
                    foundItem = item
                if not found:
                    indx += 1
            Globals.LAST_OPENED_ENDPOINT = foundItem.GetItemLabelText()
            if self.prefDialog:
                self.prefDialog.SetPref(
                    "last_endpoint", Globals.LAST_OPENED_ENDPOINT
                )
                Globals.THREAD_POOL.enqueue(self.savePrefs, self.prefDialog)

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

        if not prefix:
            prefix = "Bearer"

        if host and key and prefix and entId:
            self.sidePanel.configList.AppendText("API Host = " + host + "\n")
            self.sidePanel.configList.ShowPosition(0)
            Globals.IS_TOKEN_VALID = False

            if "https" in str(host):
                Globals.configuration.host = host.strip()
                Globals.configuration.api_key["Authorization"] = key.strip()
                Globals.configuration.api_key_prefix["Authorization"] = (
                    prefix.strip()
                )
                Globals.enterprise_id = entId.strip()

                Globals.THREAD_POOL.enqueue(self.validateToken)

                postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 50)
                if Globals.HAS_INTERNET is None:
                    Globals.HAS_INTERNET = checkEsperInternetConnection()
                threads = []
                if Globals.HAS_INTERNET:
                    self.toggleEnabledState(False)
                    if self.groupThread and self.groupThread.is_alive():
                        self.groupThread.stop()
                    self.groupThread = self.PopulateGroups()
                    if self.appThread and self.appThread.is_alive():
                        self.appThread.stop()
                    self.fetchApplications()
                    blueprints = wxThread.GUIThread(
                        self,
                        self.loadConfigCheckBlueprint,
                        config,
                        name="loadConfigCheckBlueprint",
                    )
                    blueprints.start()
                    threads = [self.groupThread, self.appThread, blueprints]
                Globals.THREAD_POOL.enqueue(
                    self.waitForThreadsThenSetCursorDefault,
                    threads,
                    0,
                    tolerance=1,
                )
                return True
        else:
            displayMessageBox(("Invalid Configuration", wx.ICON_ERROR))
            return False

    @api_tool_decorator(locks=[Globals.token_lock])
    def validateToken(self):
        Globals.token_lock.acquire()
        try:
            res = getTokenInfo(maxAttempt=2)
        except:
            pass
        Globals.IS_TOKEN_VALID = True
        if (
            (
                res
                and hasattr(res, "expires_on")
                and res.expires_on <= datetime.now(res.expires_on.tzinfo)
            )
            or (
                res
                and hasattr(res, "body")
                and (
                    "Authentication credentials were not provided" in res.body
                    or "Invalid or missing credentials" in res.body
                )
                or (hasattr(res, "status") and res.status >= 300)
            )
            or res is None
        ):
            Globals.IS_TOKEN_VALID = False
            determineDoHereorMainThread(self.promptForNewToken)

        if res and hasattr(res, "user"):
            Globals.TOKEN_USER = getSpecificUser(res.user)
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
                "Please enter a new API Token for %s"
                % Globals.configuration.host,
                "%s - API Token has expired or is invalid!"
                % self.configMenuItem.GetItemLabelText(),
            ) as dlg:
                Globals.OPEN_DIALOGS.append(dlg)
                if dlg.ShowModal() == wx.ID_OK:
                    newToken = dlg.GetValue()
                else:
                    Globals.OPEN_DIALOGS.remove(dlg)
                    break
                Globals.OPEN_DIALOGS.remove(dlg)
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
    def waitForThreadsThenSetCursorDefault(
        self, threads, source=None, action=None, tolerance=0
    ):
        if hasattr(threads, "GetValue"):
            evtVal = threads.GetValue()
            threads = evtVal[0]
            if len(evtVal) > 1:
                source = evtVal[1]
            if len(evtVal) > 2:
                action = evtVal[2]
        if threads == Globals.THREAD_POOL.threads:
            time.sleep(3)
            Globals.THREAD_POOL.join(tolerance=tolerance)
        else:
            joinThreadList(threads)
        determineDoHereorMainThread(
            self.processWaitForThreadsThenSetCursorDefault,
            threads,
            source,
            action,
            tolerance,
        )

    def processWaitForThreadsThenSetCursorDefault(
        self, threads, source=None, action=None, tolerance=0
    ):
        if source == 0:
            self.gridPanel.setColVisibility()
            self.sidePanel.groupChoice.Enable(True)
            self.sidePanel.actionChoice.Enable(True)
            self.sidePanel.removeEndpointBtn.Enable(True)
            self.handleScheduleReportPref()
        if source == 1:
            if not self.sidePanel.devices:
                self.sidePanel.selectedDevices.Append("No Devices Found", "")
                self.sidePanel.deviceChoice.Enable(False)
                self.menubar.setSaveMenuOptionsEnableState(False)
                self.menubar.enableConfigMenu()
                self.Logging("---> No Devices found")
            else:
                self.sidePanel.deviceChoice.Enable(True)
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
            self.isUploading = False
            if self.sidePanel.actionChoice.GetSelection() < indx:
                self.sidePanel.actionChoice.SetSelection(indx)
            determineDoHereorMainThread(self.gridPanel.autoSizeGridsColumns)
            determineDoHereorMainThread(self.sidePanel.groupChoice.Enable, True)
            determineDoHereorMainThread(
                self.sidePanel.deviceChoice.Enable, True
            )
            determineDoHereorMainThread(self.gridPanel.enableGridProperties)
            determineDoHereorMainThread(self.gridPanel.thawGridsIfFrozen)

            postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE_LATER, (3000, 0))
            postEventToFrame(
                eventUtil.myEVT_DISPLAY_NOTIFICATION,
                ("E.A.S.T.", "Device Spreadsheet Upload Complete"),
            )
            self.Logging("Upload Complete.")
        if source == 3:
            cmdResults = []
            if (
                action == GeneralActions.REMOVE_NON_WHITELIST_AP.value
                or action == GeneralActions.MOVE_GROUP.value
                or action == GridActions.MOVE_GROUP.value
            ):
                if threads == Globals.THREAD_POOL.threads:
                    resp = Globals.THREAD_POOL.results()
                    for t in resp:
                        if t:
                            if type(t) == list:
                                cmdResults = cmdResults + t
                            else:
                                cmdResults.append(t)
                else:
                    for t in threads:
                        if t.result:
                            if type(t.result) == list:
                                cmdResults = cmdResults + t.result
                            else:
                                cmdResults.append(t.result)
            self.onComplete((True, action, cmdResults))
        self.toggleEnabledState(not self.isRunning and not self.isSavingPrefs)
        self.setCursorDefault()
        postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 100)
        postEventToFrame(
            eventUtil.myEVT_PROCESS_FUNCTION,
            self.Refresh,
        )

    @api_tool_decorator()
    def PopulateGroups(self):
        """Populate Group Choice"""
        self.sidePanel.groupChoice.Enable(False)
        self.Logging("---> Attempting to populate groups...")
        self.setCursorBusy()
        if self.previousGroupFetchThread:
            self.previousGroupFetchThread.stop()
        thread = wxThread.GUIThread(
            self,
            getAllGroups,
            (
                "",
                None,
                None,
                Globals.MAX_RETRY,
                1,
            ),
            eventType=eventUtil.myEVT_GROUP,
            name="PopulateGroupsGetAll",
        )
        thread.startWithRetry()
        self.previousGroupFetchThread = thread
        return thread

    def fetchApplications(self):
        thread = wxThread.GUIThread(
            self,
            self.fetchAppsHelper,
            (),
            name="FetchApplications",
        )
        thread.startWithRetry()
        self.appThread = thread
        return thread

    def fetchAppsHelper(self):
        if self.groupThread and self.groupThread.is_alive():
            self.groupThread.join()
        Globals.token_lock.acquire()
        Globals.token_lock.release()
        if Globals.IS_TOKEN_VALID:
            self.Logging("---> Attempting to fetch applications...")
            appResp = getAllInstallableApps(1)
            if appResp:
                appList = appResp.get("results", [])
                for app in appList:
                    entry = getAppDictEntry(app)
                    if (
                        entry
                        and entry not in Globals.knownApplications
                        and ("isValid" in entry and entry["isValid"])
                    ):
                        Globals.knownApplications.append(entry)
            self.Logging("---> Finished fetching applications...")

    @api_tool_decorator()
    def PopulateBlueprints(self):
        self.Logging("--->Attempting to fetch blueprints...")
        self.setCursorBusy()
        thread = wxThread.GUIThread(
            self, self.fetchAllInstallableApps, None, name="PopulateBlueprints"
        )
        thread.startWithRetry()
        return thread

    def fetchAllKnownBlueprints(self):
        resp = getAllBlueprints(tolerance=1, useThreadPool=False)
        for item in resp.get("content").get("results", []):
            Globals.knownBlueprints[item["id"]] = item

    @api_tool_decorator()
    def addGroupsToGroupChoice(self, event):
        """Populate Group Choice"""
        self.Logging("--->Processing groups...")
        self.sidePanel.groupsResp = event.GetValue()
        results = None
        if hasattr(self.sidePanel.groupsResp, "results"):
            results = self.sidePanel.groupsResp.results
        elif (
            type(self.sidePanel.groupsResp) is dict
            and "results" in self.sidePanel.groupsResp
        ):
            results = self.sidePanel.groupsResp["results"]
        num = 1
        self.groups = results
        if results:
            results = sorted(
                results,
                key=lambda i: (
                    i.name.lower()
                    if hasattr(i, "name")
                    else i["name"].lower() if type(i) is dict else i
                ),
            )
            results.insert(0, Globals.ALL_DEVICES_IN_TENANT)
        if results and len(results):
            for group in results:
                if type(group) is dict:
                    if Globals.enterprise_id not in group["enterprise"]:
                        return
                    groupEntryId = group["path"]
                    if groupEntryId not in self.sidePanel.groups:
                        self.sidePanel.groups[groupEntryId] = group["id"]

                    pathParts = group["path"].split("/")
                    path = ""
                    for p in pathParts:
                        if path:
                            path = path + "/" + p
                        else:
                            path = p
                        if path in self.sidePanel.groupDeviceCount:
                            self.sidePanel.groupDeviceCount[path] += group[
                                "device_count"
                            ]
                        else:
                            self.sidePanel.groupDeviceCount[path] = group[
                                "device_count"
                            ]

                    if group["id"] not in Globals.knownGroups:
                        Globals.knownGroups[group["id"]] = group
                elif type(group) is str:
                    if group not in self.sidePanel.groups:
                        self.sidePanel.groups[group] = ""
                    if group not in Globals.knownGroups:
                        Globals.knownGroups[group] = ""
                    self.sidePanel.groupDeviceCount[group] = -1
                postEventToFrame(
                    eventUtil.myEVT_UPDATE_GAUGE,
                    50 + int(float(num / len(results)) * 25),
                )
                num += 1
        self.Logging("--->Finished Processing groups...")
        self.sidePanel.groupChoice.Enable(True)
        self.sidePanel.actionChoice.Enable(True)
        postEventToFrame(
            eventUtil.myEVT_PROCESS_FUNCTION,
            self.Refresh,
        )

    @api_tool_decorator()
    def PopulateDevices(self, event):
        """Populate Device Choice"""
        self.menubar.setSaveMenuOptionsEnableState(False)
        self.SetFocus()
        self.Logging("--->Attempting to populate devices of selected group(s)")
        self.sidePanel.deviceChoice.Enable(False)
        self.setCursorBusy()
        if not self.preferences or (
            "enableDevice" in self.preferences
            and self.preferences["enableDevice"]
        ):
            self.sidePanel.runBtn.Enable(False)
            self.frame_toolbar.EnableTool(self.frame_toolbar.rtool.Id, False)
            self.frame_toolbar.EnableTool(self.frame_toolbar.cmdtool.Id, False)
            postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 0)
            self.statusBar.gauge.Pulse()
        else:
            if not self.isRunning or not self.isBusy:
                self.sidePanel.runBtn.Enable(True)
                self.frame_toolbar.EnableTool(self.frame_toolbar.rtool.Id, True)
        self.frame_toolbar.EnableTool(self.frame_toolbar.cmdtool.Id, True)
        self.toggleEnabledState(False)
        Globals.THREAD_POOL.enqueue(self.addDevicesToDeviceChoice, tolerance=2)
        Globals.THREAD_POOL.enqueue(
            self.waitForThreadsThenSetCursorDefault,
            Globals.THREAD_POOL.threads,
            1,
            tolerance=1,
        )

    @api_tool_decorator()
    def addDevicesToDeviceChoice(self, tolerance=0):
        """Populate Device Choice"""
        self.Logging("--->Processing devices...")
        for clientData in self.sidePanel.selectedGroupsList:
            api_response = getAllDevices(
                clientData,
                limit=Globals.limit,
                fetchAll=True,
                tolarance=tolerance,
            )
            self.sidePanel.deviceResp = api_response
            splitResults = None
            if hasattr(api_response, "results") and len(api_response.results):
                self.Logging("---> Processing fetched devices...")
                if not Globals.SHOW_DISABLED_DEVICES:
                    api_response.results = list(
                        filter(filterDeviceList, api_response.results)
                    )
                api_response.results = sorted(
                    api_response.results,
                    key=lambda i: i.device_name.lower(),
                )
                splitResults = splitListIntoChunks(api_response.results)
            elif type(api_response) is dict and len(api_response["results"]):
                self.Logging("---> Processing fetched devices...")
                if not Globals.SHOW_DISABLED_DEVICES:
                    api_response["results"] = list(
                        filter(filterDeviceList, api_response["results"])
                    )
                api_response["results"] = sorted(
                    api_response["results"],
                    key=lambda i: (
                        i["device_name"].lower()
                        if "device_name" in i
                        else i["name"].lower()
                    ),
                )
                splitResults = splitListIntoChunks(api_response["results"])

            if splitResults:
                for chunk in splitResults:
                    Globals.THREAD_POOL.enqueue(
                        self.processAddDeviceToChoice, chunk
                    )
                Globals.THREAD_POOL.join(tolerance=tolerance)
        self.Logging("--->Finished Processing devices...")

    def processAddDeviceToChoice(self, chunk):
        for device in chunk:
            name = ""
            if hasattr(device, "hardware_info"):
                name = "%s ~ %s ~ %s %s" % (
                    (
                        device.hardware_info["manufacturer"]
                        if "manufacturer" in device.hardware_info
                        else ""
                    ),
                    (
                        device.hardware_info["model"]
                        if "model" in device.hardware_info
                        else ""
                    ),
                    device.device_name,
                    "~ %s" % device.alias_name if device.alias_name else "",
                )
            elif "hardwareInfo" in device:
                name = "%s ~ %s ~ %s %s" % (
                    (
                        device["hardwareInfo"]["manufacturer"]
                        if "manufacturer" in device["hardwareInfo"]
                        else ""
                    ),
                    (
                        device["hardwareInfo"]["model"]
                        if "model" in device["hardwareInfo"]
                        else ""
                    ),
                    device["device_name"],
                    (
                        "~ %s" % device["alias_name"]
                        if device["alias_name"]
                        else ""
                    ),
                )
            elif "hardware_info" in device:
                name = "%s ~ %s ~ %s %s" % (
                    (
                        device["hardware_info"]["brand"]
                        if "brand" in device["hardware_info"]
                        else ""
                    ),
                    (
                        device["hardware_info"]["model"]
                        if "model" in device["hardware_info"]
                        else ""
                    ),
                    device["name"],
                    "~ %s" % device["alias"] if device["alias"] else "",
                )
            if name and name not in self.sidePanel.devices:
                if hasattr(device, "id"):
                    self.sidePanel.devices[name] = device.id
                else:
                    self.sidePanel.devices[name] = device["id"]

    @api_tool_decorator()
    def onRun(self, event=None):
        """Try to run the specifed Action on a group or device"""
        if not Globals.HAS_INTERNET:
            displayMessageBox(
                (
                    "ERROR: An internet connection is required when using the tool!",
                    wx.OK | wx.ICON_ERROR | wx.CENTRE,
                )
            )
            return

        if (
            self.isBusy
            or not self.sidePanel.runBtn.IsEnabled()
            or self.scheduleReportRunning
        ):
            return

        end_time = time.time() + 120
        while (
            self.isRunning
            or self.isRunningUpdate
            or self.isSavingPrefs
            or self.isUploading
            or self.isBusy
        ) and time.time() < end_time:
            time.sleep(1)
        self.start_time = time.time()
        self.setCursorBusy()
        self.isRunning = True
        postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 0)
        self.toggleEnabledState(False)
        self.AppState = None
        self.sleepInhibitor.inhibit()

        self.gridPanel.UnsetSortingColumns()

        actionSelection = self.sidePanel.actionChoice.GetSelection()
        actionClientData = self.sidePanel.actionChoice.GetClientData(
            actionSelection
        )

        allDevicesSelected = (
            True
            if self.sidePanel.deviceResp
            and len(self.sidePanel.selectedDevicesList)
            == len(self.sidePanel.deviceResp["results"])
            else False
        )

        actionLabel = (
            self.sidePanel.actionChoice.Items[actionSelection]
            if len(self.sidePanel.actionChoice.Items) > 0
            and self.sidePanel.actionChoice.Items[actionSelection]
            else ""
        )

        estimatedDeviceCount = len(self.sidePanel.selectedDevicesList)
        if not self.sidePanel.selectedDevicesList:
            for group in self.sidePanel.selectedGroupsList:
                match = list(filter(lambda x: x["id"] == group, self.groups))
                if match:
                    match = match[0]
                    if type(match) == dict and "device_count" in match:
                        match = list(
                            filter(
                                lambda x: x.endswith(match["name"]),
                                self.sidePanel.groupDeviceCount.keys(),
                            )
                        )
                        if match:
                            match = match[0]
                            estimatedDeviceCount += (
                                self.sidePanel.groupDeviceCount[match]
                            )
                    elif hasattr(match, "device_count"):
                        match = list(
                            filter(
                                lambda x: x.endswith(match.name),
                                self.sidePanel.groupDeviceCount.keys(),
                            )
                        )
                        if match:
                            match = match[0]
                            estimatedDeviceCount += (
                                self.sidePanel.groupDeviceCount[match]
                            )

        if (
            (
                actionClientData < GeneralActions.GENERATE_APP_REPORT.value
                and estimatedDeviceCount > Globals.MAX_DEVICE_COUNT
            )
            or (
                (
                    actionClientData == GeneralActions.GENERATE_APP_REPORT.value
                    or actionClientData
                    == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value
                )
                and estimatedDeviceCount > (Globals.MAX_DEVICE_COUNT / 25)
            )
            or ("" in self.sidePanel.selectedGroupsList)
        ):
            if (
                Globals.APPS_IN_DEVICE_GRID
                and actionClientData
                == GeneralActions.GENERATE_DEVICE_REPORT.value
            ) or (
                actionClientData
                == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value
                or actionClientData == GeneralActions.GENERATE_APP_REPORT.value
            ):
                self.displayAppFilterPrompt()

            res = displayMessageBox(
                (
                    "Looks like you are generating a report for a large subset of devices.\nThe report will be directly save to a file.",
                    wx.ICON_INFORMATION | wx.CENTRE | wx.OK,
                )
            )
            if res == wx.OK:
                self.onClearGrids()
                postEventToFrame(
                    eventUtil.myEVT_AUDIT,
                    {
                        "operation": "LargeReportGeneration",
                        "data": "Action: %s Targets:%s"
                        % (
                            actionLabel,
                            (
                                self.sidePanel.selectedGroupsList
                                if not self.sidePanel.selectedDevicesList
                                else self.sidePanel.selectedDevicesList
                            ),
                        ),
                    },
                )
                return self.onSaveBothAll(None, action=actionClientData)
            else:
                return

        if actionClientData == GeneralActions.REMOVE_NON_WHITELIST_AP.value:
            with LargeTextEntryDialog(
                self,
                "Enter Wifi SSIDs you want whitelisted, as a comma seperated list:",
                "Wifi Access Point Whitelist",
            ) as textDialog:
                Globals.OPEN_DIALOGS.append(textDialog)
                if textDialog.ShowModal() == wx.ID_OK:
                    Globals.OPEN_DIALOGS.remove(textDialog)
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
                        Globals.OPEN_DIALOGS.append(textDialog2)
                        if textDialog2.ShowModal() != wx.ID_OK:
                            Globals.OPEN_DIALOGS.remove(textDialog2)
                            self.sleepInhibitor.uninhibit()
                            self.isRunning = False
                            self.setCursorDefault()
                            self.toggleEnabledState(True)
                            return
                        else:
                            postEventToFrame(
                                eventUtil.myEVT_AUDIT,
                                {
                                    "operation": "ApplySSIDWhitelist",
                                    "data": Globals.WHITELIST_AP,
                                },
                            )
                        Globals.OPEN_DIALOGS.remove(textDialog2)
                else:
                    Globals.OPEN_DIALOGS.remove(textDialog)
                    self.sleepInhibitor.uninhibit()
                    self.isRunning = False
                    self.setCursorDefault()
                    self.toggleEnabledState(True)
                    return
        if (
            self.sidePanel.selectedGroupsList
            and actionSelection > 0
            and actionClientData > 0
            and actionClientData < GridActions.MODIFY_ALIAS.value
        ):
            self.gridPanel.EmptyGrids()
            self.gridPanel.disableGridProperties()

            postEventToFrame(
                eventUtil.myEVT_AUDIT,
                {
                    "operation": "ReportGeneration",
                    "data": "Action: %s" % (actionLabel),
                },
            )

            if (
                Globals.APPS_IN_DEVICE_GRID
                and actionClientData <= GeneralActions.GENERATE_APP_REPORT.value
            ) or (
                actionClientData
                == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value
                or actionClientData == GeneralActions.GENERATE_APP_REPORT.value
            ):
                self.displayAppFilterPrompt()

            isDevice = False
            if not self.sidePanel.selectedDevicesList or allDevicesSelected:
                groupLabel = ""
                for groupId in self.sidePanel.selectedGroupsList:
                    groupLabel = list(self.sidePanel.groups.keys())[
                        list(self.sidePanel.groups.values()).index(groupId)
                    ]
                    self.Logging(
                        '---> Attempting to run action, "%s", on group, %s.'
                        % (actionLabel, groupLabel)
                    )
            else:
                isDevice = True
                for deviceId in self.sidePanel.selectedDevicesList:
                    deviceLabel = None
                    try:
                        deviceLabel = list(self.sidePanel.devices.keys())[
                            list(self.sidePanel.devices.values()).index(
                                deviceId
                            )
                        ]
                    except:
                        deviceLabel = list(
                            self.sidePanel.devicesExtended.keys()
                        )[
                            list(self.sidePanel.devicesExtended.values()).index(
                                deviceId
                            )
                        ]
                    self.Logging(
                        '---> Attempting to run action, "%s", on device, %s.'
                        % (actionLabel, deviceLabel)
                    )
            self.statusBar.gauge.Pulse()
            Globals.THREAD_POOL.enqueue(
                TakeAction,
                self,
                (
                    self.sidePanel.selectedGroupsList
                    if not isDevice
                    else self.sidePanel.selectedDevicesList
                ),
                actionClientData,
                isDevice,
            )
        elif actionClientData >= GridActions.MODIFY_ALIAS.value:
            # run grid action
            if self.gridPanel.device_grid.GetNumberRows() > 0:
                runAction = True
                result = None
                if Globals.SHOW_GRID_DIALOG:
                    result = CheckboxMessageBox(
                        "Confirmation",
                        "The %s will attempt to process the action on all devices in the Device Info grid.\n\nREMINDER: Only %s tags MAX may be currently applied to a device!\n\nContinue?"
                        % (Globals.TITLE, Globals.MAX_TAGS),
                    )
                    Globals.OPEN_DIALOGS.append(result)
                    if result.ShowModal() != wx.ID_OK:
                        runAction = False
                    Globals.OPEN_DIALOGS.remove(result)
                if result and result.getCheckBoxValue():
                    Globals.SHOW_GRID_DIALOG = False
                    self.preferences["gridDialog"] = Globals.SHOW_GRID_DIALOG
                if runAction:
                    self.Logging(
                        '---> Attempting to run grid action, "%s".'
                        % actionLabel
                    )
                    self.gridPanel.applyTextColorToDevice(
                        None,
                        Color.black.value,
                        bgColor=Color.white.value,
                        applyAll=True,
                    )
                    self.gridPanel.disableGridProperties()
                    self.frame_toolbar.search.SetValue("")
                    self.statusBar.gauge.Pulse()
                    Globals.THREAD_POOL.enqueue(
                        iterateThroughGridRows, self, actionClientData
                    )
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
    def showConsole(self, event):
        """Toggle Console Display"""
        if not self.consoleWin:
            self.consoleWin = Console(parent=self)
            self.menubar.clearConsole.Enable(True)
            self.Bind(wx.EVT_MENU, self.onClear, self.menubar.clearConsole)
        else:
            self.consoleWin.DestroyLater()
            self.menubar.clearConsole.Enable(False)

    @api_tool_decorator()
    def onClear(self, event):
        """Clear Console"""
        if self.consoleWin:
            self.consoleWin.onClear()

    @api_tool_decorator()
    def onCommand(self, event, value="{\n\n}", level=0):
        """When the user wants to run a command show the command dialog"""
        if level < Globals.MAX_RETRY:
            self.setCursorBusy()
            postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 0)

            if self.sidePanel.selectedGroupsList:
                result = None
                cmdArgs = None
                commandType = None
                schArgs = None
                schType = None
                with CommandDialog(
                    "Enter JSON Command", value=value
                ) as cmdDialog:
                    Globals.OPEN_DIALOGS.append(cmdDialog)
                    result = cmdDialog.ShowModal()
                    Globals.OPEN_DIALOGS.remove(cmdDialog)
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
                                    self,
                                    cmdArgs,
                                    commandType,
                                    schArgs,
                                    schType,
                                    combineRequests=True,
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
                    (
                        "Please select an group and or device",
                        wx.OK | wx.ICON_ERROR,
                    )
                )

            self.setCursorDefault()

    def onPowerDown(self, event):
        self.setCursorBusy()
        postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 0)

        if (
            self.sidePanel.selectedGroupsList
            or self.sidePanel.selectedDevicesList
        ):
            sendPowerDownCommand()
        else:
            displayMessageBox(
                ("Please select an group and or device", wx.OK | wx.ICON_ERROR)
            )

            self.setCursorDefault()

    @api_tool_decorator()
    def onCommandDone(self, event):
        """Tell user to check the Esper Console for detailed results"""
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
        postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 100)
        if cmdResult:
            result = ""
            for res in cmdResult:
                formattedRes = ""
                try:
                    formattedRes = json.dumps(res, indent=2).replace(
                        "\\n", "\n"
                    )
                except:
                    formattedRes = json.dumps(str(res), indent=2).replace(
                        "\\n", "\n"
                    )
                if formattedRes:
                    result += formattedRes
                    result += "\n\n"
            with ConfirmTextDialog(
                "Action has been executed.",
                (
                    "%s\n\nCheck the Esper Console for details. Last known status listed below."
                    % msg
                    + "\n"
                    if msg
                    else ""
                ),
                "Command(s) have been fired.",
                result,
                parent=self,
            ) as dialog:
                Globals.OPEN_DIALOGS.append(dialog)
                res = dialog.ShowModal()
                Globals.OPEN_DIALOGS.append(dialog)
        postEventToFrame(
            eventUtil.myEVT_PROCESS_FUNCTION,
            (wx.CallLater, (3000, self.statusBar.setGaugeValue, 0)),
        )

    @api_tool_decorator()
    def setStatus(self, status, orgingalMsg, isError=False):
        """Set status bar text"""
        try:
            self.statusBar.sbText.SetLabel(status)
            if orgingalMsg:
                self.statusBar.sbText.SetToolTip(
                    orgingalMsg.replace("--->", "")
                )
            if isError:
                self.statusBar.sbText.SetForegroundColour(Color.red.value)
            else:
                self.statusBar.sbText.SetForegroundColour(Color.black.value)
        except Exception as e:
            ApiToolLog().LogError(e)

    @api_tool_decorator()
    def onFetch(self, event):
        evtValue = event.GetValue()
        self.toggleEnabledState(False)
        if evtValue:
            action = evtValue[0]
            entId = evtValue[1]
            deviceList = evtValue[2]

            Globals.THREAD_POOL.enqueue(
                self.processFetch,
                action,
                entId,
                deviceList,
                True,
                len(deviceList) * 3,
            )

    @api_tool_decorator()
    def processFetch(
        self, action, entId, deviceList, updateGauge=False, maxGauge=None
    ):
        """Given device data perform the specified action"""
        if action <= GeneralActions.GENERATE_APP_REPORT.value:
            self.gridPanel.disableGridProperties()

        isGroup = True
        if len(Globals.frame.sidePanel.selectedDevicesList) > 0:
            isGroup = False

        if action == GeneralActions.REMOVE_NON_WHITELIST_AP.value:
            Globals.THREAD_POOL.enqueue(
                removeNonWhitelisted, deviceList, None, isGroup=isGroup
            )
        else:
            # Populate Network sheet
            if (
                action == GeneralActions.GENERATE_INFO_REPORT.value
                or action == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value
            ):
                df = createDataFrameFromDict(
                    Globals.CSV_NETWORK_ATTR_NAME, deviceList.values()
                )
                self.gridPanel.network_grid.applyNewDataFrame(
                    df, checkColumns=False, resetPosition=True, autosize=True
                )
                self.gridPanel.network_grid_contents = df.copy(deep=True)
            # Populate Device sheet
            if (
                action == GeneralActions.GENERATE_DEVICE_REPORT.value
                or action == GeneralActions.GENERATE_INFO_REPORT.value
                or action == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value
            ):
                df = createDataFrameFromDict(
                    Globals.CSV_TAG_ATTR_NAME, deviceList.values()
                )
                self.gridPanel.device_grid.applyNewDataFrame(
                    df, checkColumns=False, resetPosition=True, autosize=True
                )
                self.gridPanel.device_grid_contents = df.copy(deep=True)
            # Populate App sheet
            if (
                action == GeneralActions.GENERATE_APP_REPORT.value
                or action == GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value
            ):
                input = []
                for data in deviceList.values():
                    input.extend(data.get("AppsEntry", []))
                df = createDataFrameFromDict(Globals.CSV_APP_ATTR_NAME, input)
                self.gridPanel.app_grid.applyNewDataFrame(
                    df, checkColumns=False, resetPosition=True, autosize=True
                )
                self.gridPanel.app_grid_contents = df.copy(deep=True)

        Globals.THREAD_POOL.enqueue(
            self.waitForThreadsThenSetCursorDefault,
            Globals.THREAD_POOL.threads,
            3,
            action,
            tolerance=1,
        )

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

    @api_tool_decorator()
    def onComplete(self, event, isError=False):
        """Things that should be done once an Action is completed"""
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
        postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 100)
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
        self.gridPanel.thawGridsIfFrozen()
        if self.gridPanel.disableProperties:
            self.gridPanel.enableGridProperties()
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
        if self.isSaving:
            self.isSaving = False
        if not self.IsIconized() and self.IsActive():
            postEventToFrame(
                eventUtil.myEVT_PROCESS_FUNCTION,
                (wx.CallLater, (3000, self.statusBar.setGaugeValue, 0)),
            )
        if cmdResults:
            postEventToFrame(
                eventUtil.myEVT_PROCESS_FUNCTION,
                (self.onCommandDone, (cmdResults,)),
            )
        self.menubar.enableConfigMenu()
        self.Logging("---> Completed Action")
        self.displayNotification(title, msg)
        self.sleepInhibitor.uninhibit()
        postEventToFrame(
            eventUtil.myEVT_PROCESS_FUNCTION,
            self.Refresh,
        )

    @api_tool_decorator()
    def onActivate(self, event, skip=True):
        if not self.isRunning and not self.isUploading and not self.isBusy:
            wx.CallLater(3000, self.statusBar.setGaugeValue, 0)
        if Globals.OPEN_DIALOGS:
            for window in Globals.OPEN_DIALOGS:
                if window and hasattr(window, "Raise") and not self.isSaving:
                    window.Raise()
                elif (
                    window
                    and hasattr(window, "tryToMakeActive")
                    and not self.isSaving
                ):
                    window.tryToMakeActive()
        if self.notification:
            self.notification.Close()
        self.Refresh()
        if skip:
            event.Skip()

    @api_tool_decorator()
    def onClearGrids(self, event=None):
        """Empty Grids"""
        self.gridPanel.EmptyGrids()
        self.ToolBar.search.SetValue("")
        if event and hasattr(event, "Skip"):
            event.Skip()

    @api_tool_decorator()
    def readAuthCSV(self):
        if os.path.exists(Globals.csv_auth_path):
            if self.key and crypto().isFileEncrypt(
                Globals.csv_auth_path, self.key
            ):
                crypto().decrypt(Globals.csv_auth_path, self.key, True)
            self.auth_data = read_data_from_csv_as_dict(Globals.csv_auth_path)
            if self.auth_data:
                self.auth_data = sorted(
                    self.auth_data,
                    key=lambda i: list(
                        map(str, i["name"].lower() if "name" in i else "")
                    ),
                )

    @api_tool_decorator()
    def loadPref(self):
        """Attempt to load preferences from file system"""
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
            write_data_to_csv(
                self.authPath,
                ["name", "apiHost", "enterprise", "apiKey", "apiPrefix"],
            )
            self.AddEndpoint(None)

        if self.kill:
            return

        if (
            os.path.isfile(self.prefPath)
            and os.path.exists(self.prefPath)
            and os.access(self.prefPath, os.R_OK)
        ):
            if os.path.getsize(self.prefPath) > 2:
                try:
                    self.preferences = read_json_file(self.prefPath)
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
        self.PopulateConfig()

    @api_tool_decorator()
    def savePrefs(self, dialog):
        """Save Preferences"""
        self.preferences = dialog.GetPrefs()
        write_json_file(self.prefPath, self.preferences)
        postEventToFrame(eventUtil.myEVT_LOG, "---> Preferences' Saved")

    @api_tool_decorator()
    def onPref(self, event):
        """Update Preferences when they are changed"""
        if self.isRunning:
            return
        self.prefDialog.SetPrefs(self.preferences, onBoot=False)
        self.prefDialog.appColFilter = Globals.APP_COL_FILTER
        Globals.OPEN_DIALOGS.append(self.prefDialog)
        if self.prefDialog.ShowModal() == wx.ID_APPLY:
            self.isSavingPrefs = True
            Globals.THREAD_POOL.enqueue(self.savePrefs, self.prefDialog)
            if (
                self.sidePanel.selectedGroupsList
                and self.preferences["enableDevice"]
            ):
                self.PopulateDevices(None)
            self.setFontSizeForLabels()
            self.handleScheduleReportPref()
        Globals.OPEN_DIALOGS.remove(self.prefDialog)
        if self.preferences and self.preferences["enableDevice"]:
            self.sidePanel.deviceChoice.Enable(True)
        else:
            self.sidePanel.deviceChoice.Enable(False)
        self.isSavingPrefs = False

    @api_tool_decorator()
    def onFileDrop(self, event):
        if self.isRunning:
            return

        self.isUploading = True
        for file in event.Files:
            if file.endswith(".csv"):
                data = read_data_from_csv(file)
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
                    self.toggleEnabledState(False)
                    if self.WINDOWS:
                        Globals.THREAD_POOL.enqueue(
                            self.processDeviceCSVUpload, data
                        )
                        Globals.THREAD_POOL.enqueue(
                            self.waitForThreadsThenSetCursorDefault,
                            Globals.THREAD_POOL.threads,
                            2,
                            tolerance=1,
                        )
                    else:
                        self.processDeviceCSVUpload(data)
                        postEventToFrame(eventUtil.myEVT_COMPLETE, True)
            elif file.endswith(".xlxs"):
                self.toggleEnabledState(False)
                if self.WINDOWS:
                    Globals.THREAD_POOL.enqueue(
                        self.openDeviceSpreadsheet, file
                    )
                    Globals.THREAD_POOL.enqueue(
                        self.waitForThreadsThenSetCursorDefault,
                        Globals.THREAD_POOL.threads,
                        2,
                        tolerance=1,
                    )
                else:
                    self.openDeviceSpreadsheet(file)
                    postEventToFrame(eventUtil.myEVT_COMPLETE, True)

    @api_tool_decorator()
    def onClone(self, event):
        with TemplateDialog(
            self.sidePanel.configChoice, parent=self
        ) as self.tmpDialog:
            Globals.OPEN_DIALOGS.append(self.tmpDialog)
            result = self.tmpDialog.ShowModal()
            Globals.OPEN_DIALOGS.remove(self.tmpDialog)
            if result == wx.ID_OK:
                self.prepareClone(self.tmpDialog)
            self.tmpDialog.DestroyLater()

    @api_tool_decorator()
    def prepareClone(self, tmpDialog):
        self.setCursorBusy()
        self.isRunning = True
        self.statusBar.gauge.Pulse()
        util = templateUtil.EsperTemplateUtil(*tmpDialog.getInputSelections())
        Globals.THREAD_POOL.enqueue(
            util.prepareTemplate,
            tmpDialog.destTemplate,
            tmpDialog.chosenTemplate,
        )

    @api_tool_decorator()
    def confirmClone(self, event):
        result = None
        res = None
        (util, toApi, toKey, toEntId, templateFound, missingApps) = (
            event.GetValue()
        )
        if Globals.SHOW_TEMPLATE_DIALOG:
            result = CheckboxMessageBox(
                "Confirmation",
                "The %s will attempt to clone to template.\nThe following apps are missing: %s\n\nContinue?"
                % (Globals.TITLE, missingApps if missingApps else None),
            )
            Globals.OPEN_DIALOGS.append(result)
            res = result.ShowModal()
            Globals.OPEN_DIALOGS.remove(result)
        else:
            res = wx.ID_OK
        if res == wx.ID_OK:
            Globals.THREAD_POOL.enqueue(
                self.createClone,
                util,
                templateFound,
                toApi,
                toKey,
                toEntId,
                False,
            )
        else:
            self.isRunning = False
            postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 0)
            self.setCursorDefault()
        if result and result.getCheckBoxValue():
            Globals.SHOW_TEMPLATE_DIALOG = False
            self.preferences["templateDialog"] = Globals.SHOW_TEMPLATE_DIALOG

    @api_tool_decorator()
    def confirmCloneUpdate(self, event):
        result = None
        res = None
        (util, toApi, toKey, toEntId, templateFound, missingApps) = (
            event.GetValue()
        )
        if Globals.SHOW_TEMPLATE_UPDATE:
            result = CheckboxMessageBox(
                "Confirmation",
                "The Template already exists on the destination tenant.\nThe following apps are missing: %s\n\nWould you like to update the template?"
                % (missingApps if missingApps else None),
            )
            Globals.OPEN_DIALOGS.append(result)
            res = result.ShowModal()
            Globals.OPEN_DIALOGS.remove(result)
        else:
            res = wx.ID_OK
        if res == wx.ID_OK:
            Globals.THREAD_POOL.enqueue(
                self.createClone,
                util,
                templateFound,
                toApi,
                toKey,
                toEntId,
                True,
            )
        else:
            self.isRunning = False
            postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 0)
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
        try:
            if update:
                res = util.updateTemplate(toApi, toKey, toEntId, templateFound)
            else:
                res = util.createTemplate(
                    toApi, toKey, toEntId, templateFound, level + 1
                )
        except Exception as e:
            res = e
        if type(res) == dict and "errors" not in res:
            action = "created" if not update else "updated"
            self.Logging("Template sucessfully %s." % action)
            displayMessageBox(
                (
                    "Template sucessfully %s." % action,
                    wx.OK | wx.ICON_INFORMATION,
                )
            )
        elif (
            type(res) == dict
            and "errors" in res
            and res["errors"]
            and "EMM" in res["errors"][0]
            and level < 2
        ) or (isinstance(res, Exception) and "EMM" in str(res)):
            del templateFound["template"]["application"][
                "managed_google_play_disabled"
            ]
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
        postEventToFrame(eventUtil.myEVT_COMPLETE, True)

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

        if queryString:
            self.Logging("--> Searching for %s" % queryString)
        else:
            self.Logging("--> Clearing Search")
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
            determineDoHereorMainThread(
                self.applySearchColor, queryString, Color.white.value, True
            )
        if queryString:
            determineDoHereorMainThread(
                self.applySearchColor,
                queryString,
                Color.lightYellow.value,
                True,
            )
            self.Logging("--> Search for %s completed" % queryString)
        else:
            self.frame_toolbar.search.SetValue("")
            determineDoHereorMainThread(
                self.applySearchColor, queryString, Color.white.value, True
            )
            self.Logging("--> Search Clearing completed")
        self.setCursorDefault()
        self.gridPanel.setGridsCursor(wx.Cursor(wx.CURSOR_DEFAULT))
        self.gridPanel.enableGridProperties()

    def applySearchColor(self, queryString, color, applyAll=False):
        self.gridPanel.applyTextColorMatchingGridRow(
            self.gridPanel.device_grid, queryString, color, applyAll
        )
        self.gridPanel.applyTextColorMatchingGridRow(
            self.gridPanel.network_grid, queryString, color, applyAll
        )
        self.gridPanel.applyTextColorMatchingGridRow(
            self.gridPanel.app_grid, queryString, color, applyAll
        )

    @api_tool_decorator()
    def toggleEnabledState(self, state):
        determineDoHereorMainThread(self.sidePanel.runBtn.Enable, state)
        determineDoHereorMainThread(self.sidePanel.actionChoice.Enable, state)
        determineDoHereorMainThread(
            self.sidePanel.removeEndpointBtn.Enable, state
        )

        determineDoHereorMainThread(
            self.frame_toolbar.EnableTool, self.frame_toolbar.otool.Id, state
        )
        determineDoHereorMainThread(
            self.frame_toolbar.EnableTool, self.frame_toolbar.rtool.Id, state
        )
        determineDoHereorMainThread(
            self.frame_toolbar.EnableTool, self.frame_toolbar.cmdtool.Id, state
        )
        determineDoHereorMainThread(
            self.frame_toolbar.EnableTool, self.frame_toolbar.atool.Id, state
        )

        # Toggle Menu Bar Items
        determineDoHereorMainThread(self.menubar.fileOpenAuth.Enable, state)
        for option in self.menubar.sensitiveMenuOptions:
            determineDoHereorMainThread(self.menubar.EnableTop, option, state)
        determineDoHereorMainThread(self.menubar.fileOpenConfig.Enable, state)
        determineDoHereorMainThread(self.menubar.pref.Enable, state)
        determineDoHereorMainThread(self.menubar.run.Enable, state)
        determineDoHereorMainThread(self.menubar.installedDevices.Enable, state)
        determineDoHereorMainThread(self.menubar.command.Enable, state)
        determineDoHereorMainThread(self.menubar.groupSubMenu.Enable, state)
        determineDoHereorMainThread(
            self.menubar.setSaveMenuOptionsEnableState, state
        )

    @api_tool_decorator()
    def onInstalledDevices(self, event):
        reset = True
        if Globals.knownApplications:
            self.setCursorBusy()
            postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 0)
            self.toggleEnabledState(False)
            with InstalledDevicesDlg(Globals.knownApplications) as dlg:
                Globals.OPEN_DIALOGS.append(dlg)
                res = dlg.ShowModal()
                Globals.OPEN_DIALOGS.remove(dlg)
                if res == wx.ID_OK:
                    app, version = dlg.getAppValues()
                    if app and version:
                        defaultFileName = "%s_%s_installed_devices.xlsx" % (
                            dlg.selectedAppName.strip()
                            .replace(" ", "-")
                            .lower(),
                            (
                                str(dlg.selectedVersion)
                                if not "All" in dlg.selectedVersion
                                else "all-versions"
                            ),
                        )
                        inFile = displayFileDialog(
                            "Save Installed Devices to CSV",
                            "Microsoft Excel Open XML Spreadsheet (*.xlsx)|*.xlsx|CSV files (*.csv)|*.csv",
                            defaultFile=defaultFileName,
                        )
                        if inFile:
                            self.onClearGrids()
                            self.statusBar.gauge.Pulse()
                            self.setCursorBusy()
                            self.isRunning = True
                            self.toggleEnabledState(False)
                            self.sleepInhibitor.inhibit()
                            reset = False
                            Globals.THREAD_POOL.enqueue(
                                fetchInstalledDevices, app, version, inFile
                            )
                        else:
                            self.setCursorDefault()
                            self.toggleEnabledState(True)
                    else:
                        displayMessageBox(
                            (
                                "Failed to get app id or version",
                                wx.ICON_INFORMATION,
                            )
                        )
                        postEventToFrame(
                            eventUtil.myEVT_UPDATE_GAUGE_LATER, (3000, 0)
                        )
                        self.setCursorDefault()
                        self.toggleEnabledState(True)
                dlg.DestroyLater()
        else:
            displayMessageBox(
                (
                    "No apps found. Please try reloading the configuration.",
                    wx.ICON_INFORMATION,
                )
            )
        if reset:
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
            Globals.OPEN_DIALOGS.append(groupMultiDialog)
            if groupMultiDialog.ShowModal() == wx.ID_OK:
                Globals.OPEN_DIALOGS.remove(groupMultiDialog)
                user_selection = groupMultiDialog.GetSelections()
                if user_selection:
                    selection = user_selection[0]
                    groupId = (
                        self.sidePanel.groups[selection]
                        if selection in self.sidePanel.groups
                        else None
                    )
                    if groupId:
                        resp = moveGroup(
                            groupId, self.sidePanel.selectedDevicesList
                        )
                        if resp and resp.status_code == 200:
                            displayMessageBox(
                                "Selected device(s) have been moved to %s."
                                % selection
                            )
                            self.sidePanel.clearSelections()
                        elif resp:
                            displayMessageBox(str(resp))
                    else:
                        displayMessageBox(
                            "Failed to obtain group data: %s" % selection
                        )
                postEventToFrame(eventUtil.myEVT_COMPLETE, True)
                return
            else:
                Globals.OPEN_DIALOGS.remove(groupMultiDialog)
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
    def callSetGaugeLater(self, event):
        delayMs = 3000
        value = 0
        if event and hasattr(event, "GetValue"):
            val = event.GetValue()
            if type(val) == tuple:
                delayMs = val[0]
                value = val[1]
        wx.CallLater(delayMs, self.statusBar.setGaugeValue, value)

    @api_tool_decorator()
    def displayNotificationEvent(self, event):
        title = msg = ""
        if event and hasattr(event, "GetValue"):
            val = event.GetValue()
            if type(val) == tuple:
                title = val[0]
                msg = val[1]
        self.displayNotification(title, msg)

    @api_tool_decorator()
    def displayNotification(self, title, msg, displayActive=False):
        if not self.IsActive() or displayActive:
            self.notification = wxadv.NotificationMessage(title, msg, self)
            if self.notification:
                if hasattr(self.notification, "MSWUseToasts"):
                    try:
                        self.notification.MSWUseToasts()
                    except:
                        pass
            try:
                self.notification.Show()
            except Exception as e:
                ApiToolLog().LogError(e)

    @api_tool_decorator()
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

    @api_tool_decorator()
    def displayAppStateChoiceDlg(self):
        res = None
        with wx.SingleChoiceDialog(
            self, "Select App State:", "", ["DISABLE", "HIDE", "SHOW"]
        ) as dlg:
            Globals.OPEN_DIALOGS.append(dlg)
            res = dlg.ShowModal()
            Globals.OPEN_DIALOGS.remove(dlg)
            if res == wx.ID_OK:
                self.AppState = dlg.GetStringSelection()
            else:
                self.AppState = None

    @api_tool_decorator()
    def uploadApplication(self, event=None, title="", joinThread=False):
        with wx.FileDialog(
            self,
            "Upload APK" if not title else title,
            wildcard="APK files (*.apk)|*.apk",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
            defaultDir=str(self.defaultDir),
        ) as fileDialog:
            Globals.OPEN_DIALOGS.append(fileDialog)
            result = fileDialog.ShowModal()
            Globals.OPEN_DIALOGS.remove(fileDialog)
            if result == wx.ID_OK:
                apk_path = fileDialog.GetPath()
                Globals.THREAD_POOL.enqueue(uploadAppToEndpoint, apk_path)
                if joinThread:
                    Globals.THREAD_POOL.join()
        if event:
            event.Skip()

    @api_tool_decorator()
    def onGeofence(self, event):
        with GeofenceDialog() as dlg:
            Globals.OPEN_DIALOGS.append(dlg)
            dlg.ShowModal()
            Globals.OPEN_DIALOGS.remove(dlg)

    @api_tool_decorator()
    def onCloneBP(self, event):
        with BlueprintsDialog(self.sidePanel.configChoice, parent=self) as dlg:
            Globals.OPEN_DIALOGS.append(dlg)
            result = dlg.ShowModal()
            Globals.OPEN_DIALOGS.remove(dlg)
            if result == wx.ID_OK:
                prepareBlueprintClone(
                    dlg.getBlueprint(),
                    dlg.toConfig,
                    dlg.fromConfig,
                    dlg.getDestinationGroup(),
                )
                pass
            dlg.DestroyLater()

    @api_tool_decorator()
    def loadConfigCheckBlueprint(self, config):
        Globals.token_lock.acquire()
        Globals.token_lock.release()
        checkFeatureFlags(config)
        self.blueprintsEnabled = config["isBlueprintsEnabled"]

        self.Logging("---> Attempting to fetch Blueprints...")
        self.fetchAllKnownBlueprints()
        self.Logging("---> Blueprints fetched.")

    @api_tool_decorator()
    def onUserReport(self, event):
        defaultFileName = "%s_User-Report" % datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )
        self.isSaving = True
        inFile = displayFileDialog(
            "Save User Report as...",
            "CSV files (*.csv)|*.csv",
            defaultFile=defaultFileName,
        )

        if inFile:  # Save button was pressed
            self.Logging("---> Processing User Report...")
            Globals.THREAD_POOL.enqueue(self.processOnUserReport, inFile)

    def processOnUserReport(self, inFile):
        self.statusBar.gauge.Pulse()
        self.setCursorBusy()
        self.toggleEnabledState(False)
        self.gridPanel.disableGridProperties()
        users = getAllUsers(tolerance=1)
        postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 50)
        data = [
            [
                "User Id",
                "Username",
                "Email",
                "First Name",
                "Last Name",
                "Full Name",
                "Is Active",
                "Role",
                "Groups",
                "Created On",
                "Updated On",
                "Last Login",
            ]
        ]
        num = 1
        bannedRoles = [
            "enterprise device",
            "shoonya admin",
        ]
        for user in users["results"]:
            if user["profile"]["role"].lower() in bannedRoles:
                continue
            entry = []
            entry.append(user["id"])
            entry.append(user["username"])
            entry.append(user["email"])
            entry.append(user["first_name"])
            entry.append(user["last_name"])
            entry.append(user["full_name"])
            entry.append(user["is_active"])
            entry.append(user["profile"]["role"])
            entry.append(user["profile"]["groups"])
            entry.append(user["profile"]["created_on"])
            entry.append(user["profile"]["updated_on"])
            entry.append(user["last_login"])
            data.append(entry)
            postEventToFrame(
                eventUtil.myEVT_UPDATE_GAUGE,
                int(num / len(users["results"]) * 90),
            )
            num += 1
        createNewFile(inFile)

        self.Logging("---> Saving User Report to file: " + inFile)
        write_data_to_csv(inFile, data)

        self.Logging("---> User Report saved to file: " + inFile)
        self.setCursorDefault()
        postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 100)
        self.toggleEnabledState(True)
        self.gridPanel.enableGridProperties()

        res = displayMessageBox(
            (
                "User Report Saved\n\n File saved at: %s\n\nWould you like to navigate to the file?"
                % inFile,
                wx.YES_NO | wx.ICON_INFORMATION,
            )
        )
        self.isSaving = False
        if res == wx.YES:
            parentDirectory = Path(inFile).parent.absolute()
            openWebLinkInBrowser(parentDirectory, isfile=True)

    @api_tool_decorator()
    def onPendingUserReport(self, event):
        defaultFileName = "%s_Pending-User-Report" % datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )
        self.isSaving = True
        inFile = displayFileDialog(
            "Save Pending User Report as...",
            "CSV files (*.csv)|*.csv",
            defaultFile=defaultFileName,
        )

        if inFile:  # Save button was pressed
            self.Logging("---> Processing Pending User Report...")
            Globals.THREAD_POOL.enqueue(self.processOnPendingUserReport, inFile)

    def processOnPendingUserReport(self, inFile):
        self.statusBar.gauge.Pulse()
        self.setCursorBusy()
        self.toggleEnabledState(False)
        self.gridPanel.disableGridProperties()
        users = getAllPendingUsers(tolerance=1)
        postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 50)
        data = [
            [
                "User Id",
                "Email",
                "Is Active",
                "Role",
                "Groups",
                "Created On",
                "Updated On",
            ]
        ]
        num = 1
        for user in users["userinvites"]:
            entry = []
            entry.append(user["id"])
            entry.append(user["email"])
            entry.append(user["meta"]["is_active"])
            entry.append(user["meta"]["profile"]["role"])
            entry.append(
                user["meta"]["profile"]["groups"]
                if "groups" in user["meta"]["profile"]
                else ""
            )
            entry.append(user["created_at"])
            entry.append(user["updated_at"])
            data.append(entry)
            postEventToFrame(
                eventUtil.myEVT_UPDATE_GAUGE,
                int(num / len(users["userinvites"]) * 90),
            )
            num += 1
        createNewFile(inFile)
        self.Logging("---> Saving Pending User Report to file: " + inFile)
        write_data_to_csv(inFile, data)

        self.Logging("---> Pending User Report saved to file: " + inFile)
        self.setCursorDefault()
        postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 100)
        self.toggleEnabledState(True)
        self.gridPanel.enableGridProperties()

        res = displayMessageBox(
            (
                "Pending User Report Saved\n\n File saved at: %s\n\nWould you like to navigate to the file?"
                % inFile,
                wx.YES_NO | wx.ICON_INFORMATION,
            )
        )
        self.isSaving = False
        if res == wx.YES:
            parentDirectory = Path(inFile).parent.absolute()
            openWebLinkInBrowser(parentDirectory, isfile=True)

    @api_tool_decorator()
    def onConvertTemplate(self, event):
        with BlueprintsConvertDialog(
            self.sidePanel.configChoice, parent=self
        ) as dlg:
            Globals.OPEN_DIALOGS.append(dlg)
            result = dlg.ShowModal()
            Globals.OPEN_DIALOGS.remove(dlg)
            if result == wx.ID_OK:
                prepareBlueprintConversion(
                    dlg.getTemplate(),
                    dlg.toConfig,
                    dlg.fromConfig,
                    dlg.getDestinationGroup(),
                )
                pass
            dlg.DestroyLater()

    @api_tool_decorator()
    def downloadGroups(self, event):
        defaultFileName = "%s_Group-Report" % datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )
        self.isSaving = True
        inFile = displayFileDialog(
            "Save Group Report as...",
            "CSV files (*.csv)|*.csv",
            defaultFile=defaultFileName,
        )

        if inFile:  # Save button was pressed
            self.statusBar.gauge.Pulse()
            self.setCursorBusy()
            self.toggleEnabledState(False)
            self.gridPanel.disableGridProperties()

            postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 50)
            data = [
                [
                    "Group Id",
                    "Group Name",
                    "Group Path",
                    "Description",
                    "Device Count",
                    "Count of Child Groups",
                    "Parent Group URL",
                    "Thumbnail",
                    "Blueprint",
                    "Created On",
                    "Updated On",
                ]
            ]
            num = 1
            for group in self.sidePanel.groupsResp["results"]:
                entry = []
                entry.append(group["id"])
                entry.append(group["name"])
                entry.append(group["path"])
                entry.append(group["description"])
                entry.append(group["device_count"])
                entry.append(group["children_count"])
                entry.append(group["parent"] if "parent" in group else "")
                entry.append(group["thumbnail"])
                entry.append(group["blueprint"])
                entry.append(group["created_on"])
                entry.append(group["updated_on"])
                data.append(entry)
                postEventToFrame(
                    eventUtil.myEVT_UPDATE_GAUGE,
                    int(num / len(self.sidePanel.groupsResp["results"]) * 90),
                )
                num += 1
            createNewFile(inFile)

            write_data_to_csv(inFile, data)

            self.Logging("---> User Report saved to file: " + inFile)
            self.setCursorDefault()
            postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 100)
            self.toggleEnabledState(True)
            self.gridPanel.enableGridProperties()

            res = displayMessageBox(
                (
                    "Group Report Saved\n\n File saved at: %s\n\nWould you like to navigate to the file?"
                    % inFile,
                    wx.YES_NO | wx.ICON_INFORMATION,
                )
            )
            self.isSaving = False
            if res == wx.YES:
                parentDirectory = Path(inFile).parent.absolute()
                openWebLinkInBrowser(parentDirectory, isfile=True)

    def onNewBlueprintApp(self, event):
        reset = True
        if Globals.knownApplications:
            self.setCursorBusy()
            postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, 0)
            self.toggleEnabledState(False)
            with InstalledDevicesDlg(
                Globals.knownApplications,
                title="Select New Blueprint App",
                showAllVersionsOption=False,
                showBlueprintInput=True,
            ) as dlg:
                Globals.OPEN_DIALOGS.append(dlg)
                res = dlg.ShowModal()
                Globals.OPEN_DIALOGS.remove(dlg)
                if res == wx.ID_OK:
                    selection, apps = dlg.getBlueprintInputs()
                    self.Logging("Fetching List of Blueprints...")
                    blueprints = getAllBlueprints()
                    self.Logging("Processing List of Blueprints...")
                    Globals.THREAD_POOL.enqueue(
                        modifyAppsInBlueprints,
                        blueprints,
                        apps,
                        self.changedBlueprints,
                        addToAppListIfNotPresent=selection,
                    )
        else:
            displayMessageBox(
                (
                    "No apps found. Please try reloading the configuration.",
                    wx.ICON_INFORMATION,
                )
            )
        if reset:
            postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE_LATER, (3000, 0))
            self.setCursorDefault()
            self.toggleEnabledState(True)

    def displayBlueprintActionDlg(self, success, total):
        res = None
        opt = None
        options = ["Apply Immediatly", "Schedule", "Do Nothing"]
        if success > 0:
            with wx.SingleChoiceDialog(
                self,
                "Successfully changed %s of %s Blueprints.\nWhat action would you like to apply to the changed Blueprints?"
                % (success, total),
                "",
                options,
            ) as dlg:
                Globals.OPEN_DIALOGS.append(dlg)
                res = dlg.ShowModal()
                Globals.OPEN_DIALOGS.remove(dlg)
                if res == wx.ID_OK:
                    opt = dlg.GetStringSelection()
                else:
                    return None

            statusList = []
            if not opt or opt == options[2]:
                return None
            elif opt == options[0]:
                # Push immediately
                num = 1
                for bp in self.changedBlueprints:
                    updateResp, _ = pushBlueprintUpdate(bp["id"], bp["group"])
                    statusList.append(
                        {
                            "Blueprint Id": bp["id"],
                            "Blueprint Name": bp["name"],
                            "Group Id": bp["group"],
                            "Group Path": (
                                Globals.knownGroups[bp["group"]]["path"]
                                if bp["group"] in Globals.knownGroups
                                else "Unknown"
                            ),
                            "Response": updateResp.text,
                        }
                    )
                    postEventToFrame(
                        eventUtil.myEVT_UPDATE_GAUGE,
                        int(num / len(self.changedBlueprints) * 100),
                    )
                    num += 1
            elif opt == options[1]:
                # prompt for schedule
                schedule = None
                scheduleType = "WINDOW"
                with ScheduleCmdDialog() as dlg:
                    Globals.OPEN_DIALOGS.append(dlg)
                    res = dlg.ShowModal()
                    Globals.OPEN_DIALOGS.remove(dlg)
                    if res == wx.ID_OK:
                        if dlg.isRecurring():
                            scheduleType = "RECURRING"
                        schedule = dlg.getScheduleDict()
                    else:
                        return None

                num = 1
                for bp in self.changedBlueprints:
                    updateResp, _ = pushBlueprintUpdate(
                        bp["id"],
                        bp["group"],
                        schedule=schedule,
                        schedule_type=scheduleType,
                    )
                    statusList.append(
                        {
                            "Blueprint Id": bp["id"],
                            "Blueprint Name": bp["name"],
                            "Group Id": bp["group"],
                            "Group Path": (
                                Globals.knownGroups[bp["group"]]["path"]
                                if bp["group"] in Globals.knownGroups
                                else "Unknown"
                            ),
                            "Response": updateResp.text,
                        }
                    )
                    postEventToFrame(
                        eventUtil.myEVT_UPDATE_GAUGE,
                        int(num / len(self.changedBlueprints) * 100),
                    )
                    num += 1

            postEventToFrame(eventUtil.myEVT_COMMAND, statusList)
        else:
            displayMessageBox(
                (
                    "Successfully changed %s of %s Blueprints."
                    & (success, total),
                    wx.ICON_INFORMATION,
                )
            )

    def handleScheduleReportPref(self):
        if Globals.SCHEDULE_ENABLED:
            if self.scheduleReport:
                # Stop exisiting report, just in case timing differs
                self.scheduleReport.stop()
                self.stopOtherScheduledCalls()
            # Start scheduled report
            self.scheduleReport = wxThread.GUIThread(
                self,
                self.beginScheduledReport,
                None,
                name="ScheduledReportThread",
            )
            self.scheduleReport.startWithRetry()
        elif self.scheduleReport:
            # Stop report thread as it should be disabled
            self.scheduleReport.stop()
            self.stopOtherScheduledCalls()

    def beginScheduledReport(self):
        if not Globals.SCHEDULE_ENABLED or checkIfCurrentThreadStopped():
            return

        dirPath = Globals.SCHEDULE_LOCATION
        if not os.path.exists(dirPath):
            os.mkdir(dirPath)
        fileName = "%s_EAST-Report.%s" % (
            datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
            Globals.SCHEDULE_SAVE,
        )
        filePath = os.path.join(dirPath, fileName)

        if self.delayScheduleReport:
            time.sleep(60 * 5)
        self.delayScheduleReport = False

        self.waitUntilNotBusy()

        if not Globals.SCHEDULE_ENABLED or checkIfCurrentThreadStopped():
            return

        self.Logging("Performing scheduled report")
        correctSaveFileName(filePath)
        self.setCursorBusy()
        self.toggleEnabledState(False)
        self.gridPanel.disableGridProperties()
        self.Logging("Attempting to save scheduled report at %s" % filePath)
        self.statusBar.gauge.Pulse()

        reportAction = GeneralActions.GENERATE_INFO_REPORT.value
        if Globals.SCHEDULE_TYPE == "Device":
            reportAction = GeneralActions.GENERATE_DEVICE_REPORT.value
        elif Globals.SCHEDULE_TYPE == "App":
            reportAction = GeneralActions.GENERATE_APP_REPORT.value
        elif Globals.SCHEDULE_TYPE == "All":
            reportAction = GeneralActions.SHOW_ALL_AND_GENERATE_REPORT.value

        postEventToFrame(
            eventUtil.myEVT_AUDIT,
            {
                "operation": "ScheduledReportGeneration",
                "data": "Action: %s Targets:All Devices"
                % (Globals.SCHEDULE_TYPE),
            },
        )

        self.scheduleReportRunning = True
        Globals.THREAD_POOL.enqueue(
            self.saveAllFile,
            filePath,
            action=reportAction,
            showDlg=False,
            allDevices=True,
            tolarance=1,
        )
        Globals.THREAD_POOL.join()

        # Schedule next occurrance of report
        self.processScheduleCallLater()
        self.scheduleReportRunning = False

    def processScheduleCallLater(self):
        self.stopOtherScheduledCalls()
        postEventToFrame(
            eventUtil.myEVT_PROCESS_FUNCTION,
            (self.startScheduleReportCall),
        )

    def startScheduleReportCall(self):
        self.scheduleCallLater.append(
            wx.CallLater(
                Globals.SCHEDULE_INTERVAL * 3600000,
                self.handleScheduleReportPref,
            )
        )

    def stopOtherScheduledCalls(self):
        for entry in self.scheduleCallLater:
            if hasattr(entry, "Stop"):
                entry.Stop()
                wx.CallAfter(entry.Notify)
        self.scheduleCallLater = []

    def waitUntilNotBusy(self, amountSleep=60):
        # Pause until a minute after current task is complete
        while (
            self.isRunning
            or self.scheduleReportRunning
            or self.isRunningUpdate
            or self.isSavingPrefs
            or self.isUploading
            or self.isBusy
            or self.isSaving
            or Globals.OPEN_DIALOGS
        ):
            time.sleep(amountSleep)

    @api_tool_decorator()
    def onConfigureWidgets(self, event):
        res = None
        enable = className = deviceList = None
        with WidgetPicker() as dlg:
            Globals.OPEN_DIALOGS.append(dlg)
            res = dlg.ShowModal()
            enable, className, commandTarget, deviceList = dlg.getInputs()
            Globals.OPEN_DIALOGS.remove(dlg)
        if res == wx.ID_APPLY:
            self.statusBar.gauge.Pulse()
            if commandTarget == 0:
                self.Logging("Creating Widget Command for selected devices")
                Globals.THREAD_POOL.enqueue(
                    setWidget, enable, widgetName=className, devices=deviceList
                )
            else:
                self.Logging("Creating Widget Command for selected groups")
                Globals.THREAD_POOL.enqueue(
                    setWidget, enable, widgetName=className, groups=deviceList
                )

    def displayAppFilterPrompt(self):
        if Globals.SHOW_APP_FILTER_DIALOG:
            dlg = wx.RichMessageDialog(
                self,
                message="Would you like to alter the filter for displayed apps? Filter can also be altered in the Preferences > Application menu.",
                caption="Filter Apps?",
                style=wx.YES_NO | wx.ICON_QUESTION,
            )
            dlg.ShowCheckBox("Do not ask again")
            res = dlg.ShowModal()

            Globals.SHOW_APP_FILTER_DIALOG = not dlg.IsCheckBoxChecked()

            if res == wx.ID_YES:
                self.prefDialog.appFilterDlg(None)
            self.prefDialog.prefs["showAppFilter"] = (
                Globals.SHOW_APP_FILTER_DIALOG
            )
            self.savePrefs(self.prefDialog)
