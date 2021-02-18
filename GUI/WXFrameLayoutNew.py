#!/usr/bin/env python

import wx
import wx.grid as gridlib
import wx.adv as adv
import time
import csv
import os.path
import platform
import json
import tempfile
import re
import ast
import webbrowser

import Common.Globals as Globals
import GUI.EnhancedStatusBar as ESB
import Utility.wxThread as wxThread
import Utility.EsperTemplateUtil as templateUtil

from functools import partial

from datetime import datetime

from GUI.consoleWindow import Console
from GUI.Dialogs.CheckboxMessageBox import CheckboxMessageBox
from GUI.Dialogs.TemplateDialog import TemplateDialog
from GUI.Dialogs.CommandDialog import CommandDialog
from GUI.Dialogs.ProgressCheckDialog import ProgressCheckDialog
from GUI.Dialogs.PreferencesDialog import PreferencesDialog
from GUI.Dialogs.CmdConfirmDialog import CmdConfirmDialog
from GUI.Dialogs.ColumnVisibilityDialog import ColumnVisibilityDialog
from GUI.Dialogs.NewEndpointDialog import NewEndpointDialog

from Common.decorator import api_tool_decorator

from Utility.deviceInfo import constructNetworkInfo
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
    powerOffDevice,
    getTokenInfo,
    clearAppData,
)

from Utility.Resource import (
    resourcePath,
    scale_bitmap,
    createNewFile,
    checkEsperInternetConnection,
)


class NewFrameLayout(wx.Frame):
    def __init__(self):
        self.configMenuOptions = []
        self.WINDOWS = True
        self.prefPath = ""
        self.authPath = ""
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
        self.configChoice = {}
        self.consoleWin = None
        self.grid_1_contents = []
        self.grid_2_contents = []
        self.devices = []
        self.apps = []
        self.isBusy = False
        self.isRunning = False
        self.isRunningUpdate = False
        self.isForceUpdate = False
        self.kill = False
        self.deviceDescending = False
        self.networkDescending = False
        self.refresh = None
        self.checkConsole = None
        self.preferences = None
        self.auth_data = None
        self.userEdited = []
        self.prefDialog = PreferencesDialog(self.preferences, parent=self)

        wx.Frame.__init__(self, None, title=Globals.TITLE, style=wx.DEFAULT_FRAME_STYLE)
        self.SetSize((900, 700))
        self.SetMinSize((900, 700))

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.panel_5 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.panel_3 = wx.Panel(self.panel_5, wx.ID_ANY)
        self.configList = wx.TextCtrl(
            self.panel_3, wx.ID_ANY, style=wx.TE_MULTILINE | wx.TE_READONLY
        )
        self.panel_7 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.groupChoice = wx.ComboBox(
            self.panel_7, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY
        )
        self.actionChoice = wx.ComboBox(
            self.panel_7,
            wx.ID_ANY,
            style=wx.CB_DROPDOWN | wx.CB_READONLY,
            choices=Globals.GENERAL_ACTIONS,
        )
        self.deviceChoice = wx.ComboBox(
            self.panel_7, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY
        )
        self.appChoice = wx.ComboBox(
            self.panel_7, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY
        )
        self.gridActions = wx.ComboBox(
            self.panel_7,
            wx.ID_ANY,
            choices=Globals.GRID_ACTIONS,
            style=wx.CB_DROPDOWN | wx.CB_READONLY,
        )
        self.panel_6 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.panel_8 = wx.Panel(self.panel_6, wx.ID_ANY)
        self.runBtn = wx.Button(
            self.panel_8, wx.ID_ANY, "Run", style=wx.EXPAND | wx.SHAPED
        )
        self.panel_2 = wx.Panel(self, wx.ID_ANY)
        self.panel_4 = wx.Panel(self.panel_2, wx.ID_ANY)
        self.grid_2 = wx.grid.Grid(self.panel_4, wx.ID_ANY, size=(1, 1))
        self.panel_9 = wx.Panel(self.panel_2, wx.ID_ANY)
        self.grid_1 = wx.grid.Grid(self.panel_9, wx.ID_ANY, size=(1, 1))

        self.runBtn.SetCursor(wx.Cursor(wx.CURSOR_HAND))

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

        self.configList.Bind(wx.EVT_KEY_DOWN, self.RemoveEndpoint)

        self.Bind(wx.EVT_CLOSE, self.OnQuit)

        self.Bind(wx.EVT_COMBOBOX, self.onActionSelection, self.actionChoice)
        self.Bind(wx.EVT_COMBOBOX, self.onGridActionSelection, self.gridActions)
        self.Bind(wx.EVT_COMBOBOX, self.onDeviceSelection, self.deviceChoice)
        self.Bind(wx.EVT_BUTTON, self.onRun, self.runBtn)
        self.grid_1.Bind(gridlib.EVT_GRID_CELL_CHANGED, self.onCellChange)
        self.grid_1.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.onDeviceGridSort)
        self.grid_2.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.onNetworkGridSort)
        self.grid_1.Bind(gridlib.EVT_GRID_LABEL_RIGHT_CLICK, self.toogleViewMenuItem)
        self.grid_2.Bind(gridlib.EVT_GRID_LABEL_RIGHT_CLICK, self.toogleViewMenuItem)

        # Menu Bar
        self.menubar = wx.MenuBar()

        fileMenu = wx.Menu()
        foa = wx.MenuItem(fileMenu, wx.ID_OPEN, "&Add New Endpoint\tCtrl+O")
        fileOpenAuth = fileMenu.Append(foa)

        foc = wx.MenuItem(fileMenu, wx.ID_APPLY, "&Open Device CSV\tCtrl+D")
        fileOpenConfig = fileMenu.Append(foc)

        self.recent = wx.Menu()

        fileMenu.Append(wx.ID_SEPARATOR)
        fs = wx.MenuItem(fileMenu, wx.ID_SAVE, "&Save Device and Network Info \tCtrl+S")
        fileSave = fileMenu.Append(fs)

        fileMenu.Append(wx.ID_SEPARATOR)
        fi = wx.MenuItem(fileMenu, wx.ID_EXIT, "&Quit\tCtrl+Q")
        fileItem = fileMenu.Append(fi)

        self.configMenu = wx.Menu()
        defaultConfigVal = self.configMenu.Append(
            wx.ID_NONE, "No Loaded Configurations", "No Loaded Configurations"
        )
        self.configMenuOptions.append(defaultConfigVal)

        editMenu = wx.Menu()
        pref = wx.MenuItem(editMenu, wx.ID_ANY, "&Preferences\tCtrl+Shift+P")
        self.pref = editMenu.Append(pref)

        runMenu = wx.Menu()
        runItem = wx.MenuItem(runMenu, wx.ID_RETRY, "&Run\tCtrl+R")
        self.run = runMenu.Append(runItem)

        commandItem = wx.MenuItem(runMenu, wx.ID_ANY, "&Execute Command\tCtrl+Shift+C")
        self.command = runMenu.Append(commandItem)

        cloneItem = wx.MenuItem(runMenu, wx.ID_ANY, "&Clone Template\tCtrl+Shift+T")
        self.clone = runMenu.Append(cloneItem)

        viewMenu = wx.Menu()
        self.deviceColumns = viewMenu.Append(
            wx.MenuItem(viewMenu, wx.ID_ANY, "Toggle Device Columns")
        )
        self.networkColumns = viewMenu.Append(
            wx.MenuItem(viewMenu, wx.ID_ANY, "Toggle Network Columns")
        )
        viewMenu.Append(wx.ID_SEPARATOR)
        self.consoleView = viewMenu.Append(
            wx.MenuItem(
                viewMenu, wx.ID_ANY, "&Show Console Log\tCtrl+L", kind=wx.ITEM_CHECK
            )
        )
        self.Bind(wx.EVT_MENU, self.showConsole, self.consoleView)
        self.clearConsole = viewMenu.Append(
            wx.MenuItem(viewMenu, wx.ID_ANY, "Clear Console Log")
        )
        viewMenu.Append(wx.ID_SEPARATOR)
        self.refreshGrids = viewMenu.Append(
            wx.MenuItem(viewMenu, wx.ID_ANY, "Refresh Grids' Data")
        )
        self.Bind(wx.EVT_MENU, self.updateGrids, self.refreshGrids)
        self.clearGrids = viewMenu.Append(
            wx.MenuItem(viewMenu, wx.ID_ANY, "Clear Grids")
        )
        self.Bind(wx.EVT_MENU, self.onClearGrids, self.clearGrids)

        helpMenu = wx.Menu()
        about = helpMenu.Append(wx.ID_HELP, "About", "&About")
        self.Bind(wx.EVT_MENU, self.onAbout, about)

        helpItem = wx.MenuItem(helpMenu, wx.ID_ANY, "&Help\tF1")
        help = helpMenu.Append(helpItem)
        self.Bind(wx.EVT_MENU, self.onHelp, help)

        self.menubar.Append(fileMenu, "&File")
        self.menubar.Append(editMenu, "&Edit")
        self.menubar.Append(viewMenu, "&View")
        self.menubar.Append(self.configMenu, "&Configurations")
        self.menubar.Append(runMenu, "&Run")
        self.menubar.Append(helpMenu, "&Help")
        self.SetMenuBar(self.menubar)

        self.Bind(wx.EVT_MENU, self.AddEndpoint, defaultConfigVal)
        self.Bind(wx.EVT_MENU, self.AddEndpoint, fileOpenAuth)
        self.Bind(wx.EVT_MENU, self.onUploadCSV, fileOpenConfig)
        self.Bind(wx.EVT_MENU, self.OnQuit, fileItem)
        self.Bind(wx.EVT_MENU, self.onSaveBoth, fileSave)
        self.Bind(wx.EVT_MENU, self.onRun, self.run)
        self.Bind(wx.EVT_MENU, self.onCommand, self.command)
        self.Bind(wx.EVT_MENU, self.onClone, self.clone)
        self.Bind(wx.EVT_MENU, self.onPref, self.pref)
        self.Bind(wx.EVT_MENU, self.onDeviceColumn, self.deviceColumns)
        self.Bind(wx.EVT_MENU, self.onNetworkColumn, self.networkColumns)
        self.grid_1.GetGridWindow().Bind(wx.EVT_MOTION, self.onGridMotion)

        self.DragAcceptFiles(True)
        self.Bind(wx.EVT_DROP_FILES, self.onFileDrop)

        # Menu Bar end

        # Tool Bar
        self.frame_toolbar = wx.ToolBar(self, -1)
        self.SetToolBar(self.frame_toolbar)

        close_icon = scale_bitmap(resourcePath("Images/exit.png"), 16, 16)
        qtool = self.frame_toolbar.AddTool(wx.ID_ANY, "Quit", close_icon, "Quit")
        self.frame_toolbar.AddSeparator()

        open_icon = scale_bitmap(resourcePath("Images/add.png"), 16, 16)
        otool = self.frame_toolbar.AddTool(
            wx.ID_ANY, "Add New Endpoint", open_icon, "Add New Endpoint"
        )
        self.frame_toolbar.AddSeparator()

        save_icon = scale_bitmap(resourcePath("Images/save.png"), 16, 16)
        stool = self.frame_toolbar.AddTool(
            wx.ID_ANY,
            "Save Device & Network Info",
            save_icon,
            "Save Device & Network Info",
        )
        self.frame_toolbar.AddSeparator()

        exe_icon = scale_bitmap(resourcePath("Images/run.png"), 16, 16)
        self.rtool = self.frame_toolbar.AddTool(
            wx.ID_ANY, "Run Action", exe_icon, "Run Action"
        )
        self.frame_toolbar.AddSeparator()

        ref_icon = scale_bitmap(resourcePath("Images/refresh.png"), 16, 16)
        self.rftool = self.frame_toolbar.AddTool(
            wx.ID_ANY, "Refresh Grids", ref_icon, "Refresh Grids"
        )
        self.frame_toolbar.AddSeparator()

        cmd_icon = scale_bitmap(resourcePath("Images/command.png"), 16, 16)
        self.cmdtool = self.frame_toolbar.AddTool(
            wx.ID_ANY, "Run Command", cmd_icon, "Run Command"
        )

        self.frame_toolbar.AddStretchableSpace()
        self.search = wx.SearchCtrl(self.frame_toolbar)
        self.search.SetDescriptiveText("Search Grids")
        self.frame_toolbar.AddControl(self.search)
        self.search.ShowCancelButton(True)

        self.Bind(wx.EVT_TOOL, self.OnQuit, qtool)
        self.Bind(wx.EVT_TOOL, self.AddEndpoint, otool)
        self.Bind(wx.EVT_TOOL, self.onSaveBoth, stool)
        self.Bind(wx.EVT_TOOL, self.onRun, self.rtool)
        self.Bind(wx.EVT_TOOL, self.updateGrids, self.rftool)
        self.Bind(wx.EVT_TOOL, self.onCommand, self.cmdtool)
        self.search.Bind(wx.EVT_SEARCH, self.onSearch)
        self.search.Bind(wx.EVT_SEARCH_CANCEL, self.onSearch)
        # Tool Bar end

        self.Bind(wxThread.EVT_FETCH, self.onFetch)
        self.Bind(wxThread.EVT_UPDATE, self.onUpdate)
        self.Bind(wxThread.EVT_UPDATE_DONE, self.onUpdateComplete)
        self.Bind(wxThread.EVT_GROUP, self.addGroupsToGroupChoice)
        self.Bind(wxThread.EVT_DEVICE, self.addDevicesToDeviceChoice)
        self.Bind(wxThread.EVT_APPS, self.addAppsToAppChoice)
        self.Bind(wxThread.EVT_RESPONSE, self.performAPIResponse)
        self.Bind(wxThread.EVT_COMPLETE, self.onComplete)
        self.Bind(wxThread.EVT_LOG, self.onLog)
        self.Bind(wxThread.EVT_COMMAND, self.onCommandDone)
        self.Bind(wxThread.EVT_UPDATE_GAUGE, self.setGaugeValue)
        self.Bind(wxThread.EVT_UPDATE_TAG_CELL, self.updateTagCell)
        self.Bind(wxThread.EVT_UNCHECK_CONSOLE, self.uncheckConsole)
        self.Bind(wxThread.EVT_ON_FAILED, self.onFail)
        self.Bind(wxThread.EVT_CONFIRM_CLONE, self.confirmClone)
        self.Bind(wxThread.EVT_CONFIRM_CLONE_UPDATE, self.confirmCloneUpdate)
        self.Bind(wx.EVT_ACTIVATE_APP, self.MacReopenApp)
        self.Bind(wx.EVT_ACTIVATE, self.onActivate)

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

        icon = wx.Icon()
        icon.CopyFromBitmap(
            wx.Bitmap(resourcePath("Images/icon.png"), wx.BITMAP_TYPE_PNG)
        )
        self.SetIcon(icon)

        self.loadPref()
        self.__set_properties()
        self.__do_layout()
        self.Raise()
        self.Iconize(False)
        self.SetFocus()

        internetCheck = wxThread.GUIThread(self, self.checkForInternetAccess, None)
        internetCheck.start()

    def __set_properties(self):
        self.SetTitle(Globals.TITLE)
        self.SetBackgroundColour(wx.Colour(192, 192, 192))
        self.SetThemeEnabled(False)

        self.actionChoice.SetSelection(1)
        self.gridActions.SetSelection(0)

        self.actionChoice.Enable(False)
        self.deviceChoice.Enable(False)
        self.groupChoice.Enable(False)
        self.appChoice.Enable(False)
        self.runBtn.Enable(False)
        self.frame_toolbar.EnableTool(self.rtool.Id, False)
        self.frame_toolbar.EnableTool(self.cmdtool.Id, False)
        self.frame_toolbar.EnableTool(self.rftool.Id, False)
        self.run.Enable(False)
        self.clone.Enable(False)
        self.command.Enable(False)
        self.clearConsole.Enable(False)

        self.grid_2.CreateGrid(0, len(Globals.CSV_NETWORK_ATTR_NAME.keys()))
        self.grid_1.CreateGrid(0, len(Globals.CSV_TAG_ATTR_NAME.keys()))
        self.grid_1.UseNativeColHeader()
        self.grid_2.UseNativeColHeader()
        self.grid_1.DisableDragRowSize()
        self.grid_2.DisableDragRowSize()
        self.fillDeviceGridHeaders()
        self.fillNetworkGridHeaders()

        if self.kill:
            return

        self.frame_toolbar.Realize()
        self.panel_1.SetMinSize((400, 900))
        self.panel_2.SetMinSize((2000, 800))
        self.Maximize(True)

    def __do_layout(self):
        sizer_1 = wx.FlexGridSizer(1, 2, 0, 0)
        grid_sizer_2 = wx.GridSizer(2, 1, 0, 0)
        grid_sizer_8 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_4 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_5 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_7 = wx.GridSizer(2, 1, 0, 0)
        sizer_4 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_5 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_6 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_3 = wx.GridSizer(1, 1, 0, 0)
        label_1 = wx.StaticText(
            self.panel_5,
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
        grid_sizer_6.Add(label_1, 0, wx.EXPAND, 0)
        grid_sizer_3.Add(self.configList, 0, wx.EXPAND, 0)
        self.panel_3.SetSizer(grid_sizer_3)
        grid_sizer_6.Add(self.panel_3, 1, wx.EXPAND, 0)
        self.panel_5.SetSizer(grid_sizer_6)
        grid_sizer_1.Add(self.panel_5, 1, wx.EXPAND, 0)
        label_2 = wx.StaticText(
            self.panel_7,
            wx.ID_ANY,
            "Choose a Group :",
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
        grid_sizer_5.Add(label_2, 0, wx.EXPAND, 0)
        grid_sizer_5.Add(self.groupChoice, 0, wx.ALL | wx.EXPAND, 0)
        grid_sizer_5.Add((20, 20), 0, wx.EXPAND, 0)
        label_3 = wx.StaticText(
            self.panel_7,
            wx.ID_ANY,
            "Choose a Specific Device (optional):",
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
        grid_sizer_5.Add(label_3, 0, wx.EXPAND, 0)
        grid_sizer_5.Add(self.deviceChoice, 0, wx.EXPAND, 0)
        grid_sizer_5.Add((20, 20), 0, wx.EXPAND, 0)
        label_6 = wx.StaticText(
            self.panel_7,
            wx.ID_ANY,
            "Action to apply:",
            style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END,
        )
        label_6.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        grid_sizer_5.Add(label_6, 0, wx.EXPAND, 0)
        grid_sizer_5.Add(self.actionChoice, 0, wx.ALL | wx.EXPAND, 0)
        grid_sizer_5.Add((20, 20), 0, wx.EXPAND, 0)
        label_4 = wx.StaticText(
            self.panel_7,
            wx.ID_ANY,
            "Applications:",
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
        grid_sizer_5.Add(label_4, 0, wx.EXPAND, 0)
        grid_sizer_5.Add(self.appChoice, 0, wx.EXPAND, 0)
        grid_sizer_5.Add((20, 20), 0, wx.EXPAND, 0)
        label_5 = wx.StaticText(
            self.panel_7,
            wx.ID_ANY,
            "Device Grid Actions",
            style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END,
        )
        label_5.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        grid_sizer_5.Add(label_5, 0, wx.EXPAND, 0)
        grid_sizer_5.Add(self.gridActions, 0, wx.EXPAND, 0)
        sizer_4.Add(grid_sizer_5, 0, wx.EXPAND, 0)
        self.panel_7.SetSizer(sizer_4)
        grid_sizer_1.Add(self.panel_7, 1, wx.EXPAND, 0)
        grid_sizer_7.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_7.Add(self.runBtn, 0, wx.EXPAND, 0)
        self.panel_8.SetSizer(grid_sizer_7)
        sizer_5.Add(self.panel_8, 1, wx.EXPAND, 0)
        self.panel_6.SetSizer(sizer_5)
        grid_sizer_1.Add(self.panel_6, 1, wx.EXPAND, 0)
        self.panel_1.SetSizer(grid_sizer_1)
        sizer_1.Add(self.panel_1, 0, wx.ALL | wx.EXPAND, 5)
        network_grid = wx.StaticText(self.panel_4, wx.ID_ANY, "Network Information:")
        network_grid.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        grid_sizer_4.Add(network_grid, 0, wx.LEFT, 5)
        grid_sizer_4.Add(self.grid_2, 1, wx.ALL | wx.EXPAND, 5)
        self.panel_4.SetSizer(grid_sizer_4)
        grid_sizer_2.Add(self.panel_4, 1, wx.EXPAND, 0)
        label_8 = wx.StaticText(self.panel_9, wx.ID_ANY, "Device Information:")
        label_8.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        grid_sizer_8.Add(label_8, 0, wx.LEFT, 5)
        grid_sizer_8.Add(self.grid_1, 1, wx.ALL | wx.EXPAND, 5)
        self.panel_9.SetSizer(grid_sizer_8)
        grid_sizer_2.Add(self.panel_9, 1, wx.EXPAND, 0)
        self.panel_2.SetSizer(grid_sizer_2)
        sizer_1.Add(self.panel_2, 0, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(sizer_1)
        self.Layout()
        self.setColorTheme()

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
            Globals.LOGLIST.append(entry)
            if self.consoleWin:
                self.consoleWin.Logging(entry)
            if "error" in entry.lower():
                isError = True
            if len(entry) >= Globals.MAX_STATUS_CHAR:
                longEntryMsg = "....(See console for details)"
                entry = entry[0 : Globals.MAX_STATUS_CHAR - len(longEntryMsg)]
                entry += longEntryMsg
            self.setStatus(entry, isError)
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
        if self.grid_1.GetNumberRows() > 0:
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
                for device in self.grid_1_contents:
                    tempDict = {}
                    tempDict.update(device)
                    deviceListing = list(
                        filter(
                            lambda x: (
                                x["Device Name"]
                                == device[Globals.CSV_TAG_ATTR_NAME["Esper Name"]]
                            ),
                            self.grid_2_contents,
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
        self.emptyDeviceGrid()
        self.emptyNetworkGrid()
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

                with open(Globals.csv_auth_path, "r", encoding="utf-8-sig") as csvFile:
                    reader = csv.reader(
                        csvFile, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True
                    )
                    data = list(reader)
                    self.processDeviceCSVUpload(data)
                    self.grid_1.AutoSizeColumns()
            elif result == wx.ID_CANCEL:
                return  # the user changed their mind
        wx.CallLater(3000, self.setGaugeValue, 0)
        self.setCursorDefault()

    def processDeviceCSVUpload(self, data):
        num = 0
        header = None
        grid_headers = list(Globals.CSV_TAG_ATTR_NAME.keys())
        len_reader = len(data)
        rowCount = 1
        for row in data:
            self.setGaugeValue(int((rowCount) / len_reader * 100))
            rowCount += 1
            if not all("" == val or val.isspace() for val in row):
                if num == 0:
                    header = row
                    num += 1
                    continue
                self.grid_1.AppendRows(1)
                toolCol = 0
                for expectedCol in Globals.CSV_TAG_ATTR_NAME.keys():
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
                            fileCol > len(header)
                            or header[fileCol].strip()
                            in Globals.CSV_DEPRECATED_HEADER_LABEL
                            or header[fileCol].strip()
                            not in Globals.CSV_TAG_ATTR_NAME.keys()
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
                            self.grid_1.SetCellValue(
                                self.grid_1.GetNumberRows() - 1,
                                toolCol,
                                str(colValue),
                            )
                            isEditable = True
                            if grid_headers[toolCol] in Globals.CSV_EDITABLE_COL:
                                isEditable = False
                            self.grid_1.SetReadOnly(
                                self.grid_1.GetNumberRows() - 1,
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

        for item in self.configMenuOptions:
            try:
                self.configMenu.Delete(item)
            except:
                pass
        self.configMenuOptions = []

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
                    self.setGaugeValue(int(num / maxRow * 100))
                    num += 1
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
                        self.Bind(wx.EVT_MENU, self.AddEndpoint, defaultConfigVal)
                        return
            self.Logging(
                "--->**** Please Select an Endpoint From the Configuartion Menu (defaulting to first Config)"
            )
            self.loadRecentMenu()
            defaultConfigItem = self.configMenuOptions[0]
            defaultConfigItem.Check(True)
            self.loadConfiguartion(defaultConfigItem)
        else:
            self.Logging(
                "--->****"
                + configfile
                + " not found - PLEASE Quit and create configuration file"
            )
            defaultConfigVal = self.configMenu.Append(
                wx.ID_NONE, "No Loaded Configurations", "No Loaded Configurations"
            )
            self.configMenuOptions.append(defaultConfigVal)
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
        menuItem = self.configMenu.FindItemById(event.Id)
        self.onClearGrids(None)
        self.groupChoice.Clear()
        self.deviceChoice.Clear()
        self.appChoice.Clear()
        self.setCursorBusy()
        try:
            self.Logging(
                "--->Attempting to load configuration: %s."
                % menuItem.GetItemLabelText()
            )
            selectedConfig = self.configChoice[menuItem.GetItemLabelText()]

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

            self.groupChoice.Enable(True)
            self.actionChoice.Enable(True)
        except Exception as e:
            self.Logging(
                "--->****An Error has occured while loading the configuration, please try again."
            )
            print(e)
            menuItem.Check(False)

    @api_tool_decorator
    def fillInConfigListing(self, config):
        self.configList.Clear()
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
            self.configList.AppendText("API Host = " + host + "\n")
            self.configList.AppendText("API key = " + key + "\n")
            self.configList.AppendText("API Prefix = " + prefix + "\n")
            self.configList.AppendText("Enterprise = " + entId)

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
                appThread = self.PopulateApps()
                threads = [groupThread, appThread]
                wxThread.GUIThread(
                    self,
                    self.waitForThreadsThenSetCursorDefault,
                    threads,
                    passArgAsTuple=True,
                ).start()
                return True
        else:
            wx.MessageBox("Invalid Configuration", style=wx.ICON_ERROR)
            return False

    def waitForThreadsThenSetCursorDefault(self, threads):
        for thread in threads:
            thread.join()
        self.setCursorDefault()
        self.setGaugeValue(100)

    @api_tool_decorator
    def PopulateGroups(self):
        """ Populate Group Choice """
        self.Logging("--->Attemptting to populate groups...")
        self.setCursorBusy()
        self.setGaugeValue(0)
        self.gauge.Pulse()
        self.groupChoice.Clear()
        thread = wxThread.doAPICallInThread(
            self, getAllGroups, eventType=wxThread.myEVT_GROUP, waitForJoin=False
        )
        return thread

    @api_tool_decorator
    def addGroupsToGroupChoice(self, event):
        """ Populate Group Choice """
        results = event.GetValue().results
        num = 1
        # results = sorted(
        #     results,
        #     key=lambda i: i.name.lower(),
        # )
        if len(results):
            for group in results:
                self.groupChoice.Append(group.name, group.id)
                self.setGaugeValue(int(num / len(results) * 100))
                num += 1
            self.Bind(wx.EVT_COMBOBOX, self.PopulateDevices, self.groupChoice)
        self.runBtn.Enable(True)
        self.frame_toolbar.EnableTool(self.rtool.Id, True)
        self.frame_toolbar.EnableTool(self.cmdtool.Id, True)
        self.frame_toolbar.EnableTool(self.rftool.Id, True)
        self.run.Enable(True)
        self.clone.Enable(True)
        self.command.Enable(True)
        self.groupChoice.Enable(True)
        self.actionChoice.Enable(True)
        wx.CallLater(3000, self.setGaugeValue, 0)

    @api_tool_decorator
    def PopulateDevices(self, event):
        """ Populate Device Choice """
        self.SetFocus()
        self.Logging(
            "--->Attemptting to populate devices of selected group (%s)..."
            % event.String
        )
        self.devices = []
        self.deviceChoice.Clear()
        self.appChoice.Clear()
        self.setCursorBusy()
        if not self.preferences or self.preferences["enableDevice"] == True:
            self.runBtn.Enable(False)
            self.frame_toolbar.EnableTool(self.rtool.Id, False)
            self.frame_toolbar.EnableTool(self.rftool.Id, False)
            self.frame_toolbar.EnableTool(self.cmdtool.Id, False)
            self.setGaugeValue(0)
            self.gauge.Pulse()
            self.setCursorBusy()
        else:
            self.runBtn.Enable(True)
            self.frame_toolbar.EnableTool(self.rtool.Id, True)
            self.frame_toolbar.EnableTool(self.rftool.Id, True)
        self.frame_toolbar.EnableTool(self.cmdtool.Id, True)
        # for app in self.apps:
        #     if app:
        #         self.appChoice.Append(list(app.keys())[0], list(app.values())[0])
        clientData = (
            event.ClientData
            if event and event.ClientData
            else self.groupChoice.GetClientData(event.Int)
        )
        wxThread.doAPICallInThread(
            self,
            getAllDevices,
            args=(clientData),
            eventType=wxThread.myEVT_DEVICE,
            waitForJoin=False,
        )

    @api_tool_decorator
    def addDevicesToDeviceChoice(self, event):
        """ Populate Device Choice """
        api_response = event.GetValue()
        self.gauge.Pulse()
        if len(api_response.results):
            if not self.preferences or self.preferences["enableDevice"] == True:
                self.deviceChoice.Enable(True)
            else:
                self.deviceChoice.Enable(False)
            if not "" in self.devices:
                self.devices.append("")
                self.deviceChoice.Append("", "")
            num = 1
            threads = []
            # api_response.results = sorted(
            #     api_response.results,
            #     key=lambda i: i.device_name.lower(),
            # )
            for device in api_response.results:
                name = "%s %s %s" % (
                    device.hardware_info["manufacturer"],
                    device.hardware_info["model"],
                    device.device_name,
                )
                if name and not name in self.devices:
                    self.devices.append(name)
                    self.deviceChoice.Append(name, device.id)
                    num += 1
                    thread = wxThread.doAPICallInThread(
                        self,
                        getdeviceapps,
                        args=(device.id),
                        eventType=wxThread.myEVT_APPS,
                        waitForJoin=False,
                    )
                    threads.append(thread)

            for thread in threads:
                if not self.preferences or self.preferences["enableDevice"] == True:
                    self.setGaugeValue(int(num / len(api_response.results) * 100))
        else:
            self.deviceChoice.Append("No Devices Found", "")
            self.deviceChoice.Enable(False)
            self.Logging("---> No Devices found in group")
        self.setCursorDefault()

    @api_tool_decorator
    def PopulateApps(self):
        """ Populate App Choice """
        self.Logging("--->Attemptting to populate apps...")
        self.setCursorBusy()
        self.appChoice.Clear()
        thread = wxThread.doAPICallInThread(
            self, getAllApplications, eventType=wxThread.myEVT_APPS, waitForJoin=False
        )
        return thread

    @api_tool_decorator
    def addAppsToAppChoice(self, event):
        """ Populate App Choice """
        api_response = event.GetValue()
        if not "" in self.apps:
            self.apps.append("")
            self.appChoice.Append("", "")
        results = None
        if hasattr(api_response, "results"):
            results = api_response.results
        else:
            results = api_response[1]["results"]
        # if hasattr(results[0], "application_name"):
        #     results = sorted(
        #         results,
        #         key=lambda i: i.application_name.lower(),
        #     )
        # else:
        #     results = sorted(
        #         results,
        #         key=lambda i: i["app_name"].lower(),
        #     )
        if len(results):
            num = 1
            for app in results:
                entry = None
                if hasattr(app, "application_name"):
                    if app.application_name not in self.appChoice.Items:
                        self.appChoice.Append(app.application_name, app.package_name)
                    entry = {app.application_name: app.package_name}
                else:
                    if app["app_name"] not in self.appChoice.Items:
                        self.appChoice.Append(app["app_name"], app["package_name"])
                    entry = {app["app_name"]: app["package_name"]}
                if entry not in self.apps:
                    self.apps.append(entry)
                # self.setGaugeValue(int(num / len(results) * 100))
                num += 1
        self.runBtn.Enable(True)
        self.frame_toolbar.EnableTool(self.rtool.Id, True)
        self.frame_toolbar.EnableTool(self.rftool.Id, True)
        self.frame_toolbar.EnableTool(self.cmdtool.Id, True)
        # wx.CallLater(3000, self.setGaugeValue, 0)

    @api_tool_decorator
    def onRun(self, event):
        """ Try to run the specifed Action on a group or device """
        if self.isBusy or not self.runBtn.IsEnabled():
            return
        self.setCursorBusy()
        self.isRunning = True
        self.gauge.Pulse()
        self.runBtn.Enable(False)
        self.frame_toolbar.EnableTool(self.rtool.Id, False)
        self.frame_toolbar.EnableTool(self.rftool.Id, False)
        self.frame_toolbar.EnableTool(self.cmdtool.Id, False)

        self.grid_1.UnsetSortingColumn()
        self.grid_2.UnsetSortingColumn()

        groupSelection = self.groupChoice.GetSelection()
        deviceSelection = self.deviceChoice.GetSelection()
        gridSelection = self.gridActions.GetSelection()
        appSelection = self.appChoice.GetSelection()
        actionSelection = self.actionChoice.GetSelection()

        groupLabel = (
            self.groupChoice.Items[groupSelection]
            if len(self.groupChoice.Items) > 0
            and self.groupChoice.Items[groupSelection]
            else ""
        )
        deviceLabel = (
            self.deviceChoice.Items[deviceSelection]
            if len(self.deviceChoice.Items) > 0
            and self.deviceChoice.Items[deviceSelection]
            else ""
        )
        appLabel = (
            self.appChoice.Items[appSelection]
            if len(self.appChoice.Items) > 0 and self.appChoice.Items[appSelection]
            else ""
        )
        gridLabel = (
            self.gridActions.Items[gridSelection]
            if len(self.gridActions.Items) > 0 and self.gridActions.Items[gridSelection]
            else ""
        )
        actionLabel = (
            self.actionChoice.Items[actionSelection]
            if len(self.actionChoice.Items) > 0
            and self.actionChoice.Items[actionSelection]
            else ""
        )
        self.setGaugeValue(0)
        if (
            groupSelection >= 0
            and deviceSelection <= 0
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
                return
            self.Logging(
                '---> Attempting to run action, "%s", on group, %s.'
                % (actionLabel, groupLabel)
            )
            self.grid_1_contents = []
            self.grid_2_contents = []
            self.userEdited = []
            Globals.LAST_DEVICE_ID = None
            Globals.LAST_GROUP_ID = groupSelection
            TakeAction(
                self,
                groupSelection,
                actionSelection,
                groupLabel,
            )
        elif deviceSelection > 0 and gridSelection <= 0 and actionSelection > 0:
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
                return
            self.Logging(
                '---> Attempting to run action, "%s", on device, %s.'
                % (actionLabel, deviceLabel)
            )
            self.grid_1_contents = []
            self.grid_2_contents = []
            self.userEdited = []
            Globals.LAST_DEVICE_ID = deviceSelection
            Globals.LAST_GROUP_ID = None
            TakeAction(
                self, deviceSelection, actionSelection, deviceLabel, isDevice=True
            )
        elif gridSelection > 0:
            # run grid action
            if self.grid_1.GetNumberRows() > 0:
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
                    self.applyTextColorToDevice(
                        None,
                        wx.Colour(0, 0, 0),
                        bgColor=wx.Colour(255, 255, 255),
                        applyAll=True,
                    )
                    self.search.SetValue("")
                    iterateThroughGridRows(self, gridSelection)
            else:
                wx.MessageBox(
                    "Make sure the grid has data to perform an action on",
                    style=wx.OK | wx.ICON_ERROR,
                )
                self.setCursorDefault()
        else:
            wx.MessageBox(
                "Please select an action to perform on a group or device!",
                style=wx.OK | wx.ICON_ERROR,
            )
            self.setCursorDefault()

    @api_tool_decorator
    def fillDeviceGridHeaders(self):
        """ Populate Device Grid Headers """
        num = 0
        headerLabels = Globals.CSV_TAG_ATTR_NAME.keys()
        try:
            for head in headerLabels:
                if head:
                    if self.grid_1.GetNumberCols() < len(headerLabels):
                        self.grid_1.AppendCols(1)
                    self.grid_1.SetColLabelValue(num, head)
                    num += 1
        except:
            pass
        self.grid_1.AutoSizeColumns()

    @api_tool_decorator
    def fillNetworkGridHeaders(self):
        """ Populate Network Grid Headers """
        num = 0
        headerLabels = Globals.CSV_NETWORK_ATTR_NAME.keys()
        try:
            for head in headerLabels:
                if head:
                    if self.grid_2.GetNumberCols() < len(headerLabels):
                        self.grid_2.AppendCols(1)
                    self.grid_2.SetColLabelValue(num, head)
                    num += 1
        except:
            pass
        self.grid_2.AutoSizeColumns()

    @api_tool_decorator
    def emptyDeviceGrid(self, emptyContents=True):
        """ Empty Device Grid """
        if emptyContents:
            self.grid_1_contents = []
        self.grid_1.ClearGrid()
        if self.grid_1.GetNumberRows() > 0:
            self.grid_1.DeleteRows(0, self.grid_1.GetNumberRows())
        self.grid_1.SetScrollLineX(15)
        self.grid_1.SetScrollLineY(15)
        self.fillDeviceGridHeaders()

    @api_tool_decorator
    def emptyNetworkGrid(self, emptyContents=True):
        """ Empty Network Grid """
        if emptyContents:
            self.grid_2_contents = []
        self.grid_2.ClearGrid()
        if self.grid_2.GetNumberRows() > 0:
            self.grid_2.DeleteRows(0, self.grid_2.GetNumberRows())
        self.grid_2.SetScrollLineX(15)
        self.grid_2.SetScrollLineY(15)
        self.fillNetworkGridHeaders()

    @api_tool_decorator
    def addDeviceToDeviceGrid(self, device_info, isUpdate=False):
        """ Add device info to Device Grid """
        num = 0
        device = {}
        if isUpdate:
            deviceName = device_info[Globals.CSV_TAG_ATTR_NAME["Esper Name"]]
            found = False
            for rowNum in range(self.grid_1.GetNumberRows()):
                if rowNum < self.grid_1.GetNumberRows():
                    esperName = self.grid_1.GetCellValue(rowNum, 0)
                    if deviceName == esperName:
                        found = True
                        deviceListing = list(
                            filter(
                                lambda x: (
                                    x[Globals.CSV_TAG_ATTR_NAME["Esper Name"]]
                                    == esperName
                                ),
                                self.grid_1_contents,
                            )
                        )
                        if deviceListing:
                            deviceListing = deviceListing[0]
                        else:
                            self.addDeviceToDeviceGrid(device_info, isUpdate=False)
                            break
                        deviceListing.update(device)
                        for attribute in Globals.CSV_TAG_ATTR_NAME:
                            indx = list(Globals.CSV_TAG_ATTR_NAME.keys()).index(
                                attribute
                            )
                            cellValue = self.grid_1.GetCellValue(rowNum, indx)
                            fecthValue = (
                                device_info[Globals.CSV_TAG_ATTR_NAME[attribute]]
                                if Globals.CSV_TAG_ATTR_NAME[attribute] in device_info
                                else ""
                            )
                            if (
                                not (
                                    rowNum,
                                    indx,
                                )
                                in self.userEdited
                                and cellValue != str(fecthValue)
                            ):
                                self.grid_1.SetCellValue(rowNum, indx, str(fecthValue))
                                self.setStatusCellColor(fecthValue, rowNum, indx)
                                self.setAlteredCellColor(
                                    self.grid_1,
                                    device_info,
                                    rowNum,
                                    attribute,
                                    indx,
                                )
                                device[Globals.CSV_TAG_ATTR_NAME[attribute]] = str(
                                    fecthValue
                                )
                            else:
                                device[Globals.CSV_TAG_ATTR_NAME[attribute]] = str(
                                    cellValue
                                )
                        break
            if not found:
                self.addDeviceToDeviceGrid(device_info, isUpdate=False)
        else:
            self.grid_1.AppendRows(1)
            esperName = ""
            for attribute in Globals.CSV_TAG_ATTR_NAME:
                value = (
                    device_info[Globals.CSV_TAG_ATTR_NAME[attribute]]
                    if Globals.CSV_TAG_ATTR_NAME[attribute] in device_info
                    else ""
                )
                if "Esper Name" == attribute:
                    esperName = value
                device[Globals.CSV_TAG_ATTR_NAME[attribute]] = str(value)
                self.grid_1.SetCellValue(
                    self.grid_1.GetNumberRows() - 1, num, str(value)
                )
                isEditable = True
                if attribute in Globals.CSV_EDITABLE_COL:
                    isEditable = False
                self.grid_1.SetReadOnly(
                    self.grid_1.GetNumberRows() - 1, num, isEditable
                )
                self.setStatusCellColor(value, self.grid_1.GetNumberRows() - 1, num)
                self.setAlteredCellColor(
                    self.grid_1,
                    device_info,
                    self.grid_1.GetNumberRows() - 1,
                    attribute,
                    num,
                )
                num += 1
            deviceListing = list(
                filter(
                    lambda x: (x[Globals.CSV_TAG_ATTR_NAME["Esper Name"]] == esperName),
                    self.grid_1_contents,
                )
            )
            if device not in self.grid_1_contents and not deviceListing:
                self.grid_1_contents.append(device)
        self.grid_1.AutoSizeColumns()

    def setStatusCellColor(self, value, rowNum, colNum):
        if value == "Offline":
            self.grid_1.SetCellTextColour(rowNum, colNum, wx.Colour(255, 0, 0))
            self.grid_1.SetCellBackgroundColour(
                rowNum, colNum, wx.Colour(255, 235, 234)
            )
        elif value == "Online":
            self.grid_1.SetCellTextColour(rowNum, colNum, wx.Colour(0, 128, 0))
            self.grid_1.SetCellBackgroundColour(
                rowNum, colNum, wx.Colour(229, 248, 229)
            )

    def setAlteredCellColor(self, grid, device_info, rowNum, attribute, indx):
        light_blue = wx.Colour(204, 255, 255)
        if attribute == "Alias" and "OriginalAlias" in device_info:
            # grid.SetCellBackgroundColour(rowNum, indx, light_blue)
            pass
        if attribute == "Tags" and "OriginalTags" in device_info:
            # grid.SetCellBackgroundColour(rowNum, indx, light_blue)
            pass

    @api_tool_decorator
    def addDeviceToNetworkGrid(self, device, deviceInfo, isUpdate=False):
        """ Construct network info and add to grid """
        networkInfo = constructNetworkInfo(device, deviceInfo)
        self.addToNetworkGrid(networkInfo, isUpdate, device_info=deviceInfo)

    def addToNetworkGrid(self, networkInfo, isUpdate=False, device_info=None):
        """ Add info to the network grid """
        num = 0
        if isUpdate:
            deviceName = device_info[Globals.CSV_NETWORK_ATTR_NAME["Device Name"]]
            found = False
            for rowNum in range(self.grid_2.GetNumberRows()):
                if rowNum < self.grid_2.GetNumberRows():
                    esperName = self.grid_2.GetCellValue(rowNum, 0)
                    if deviceName == esperName:
                        found = True
                        deviceListing = list(
                            filter(
                                lambda x: (x["Device Name"] == esperName),
                                self.grid_2_contents,
                            )
                        )
                        if deviceListing:
                            deviceListing = deviceListing[0]
                        else:
                            self.addToNetworkGrid(
                                networkInfo, device_info=device_info, isUpdate=False
                            )
                            break
                        for attribute in Globals.CSV_NETWORK_ATTR_NAME.keys():
                            indx = list(Globals.CSV_NETWORK_ATTR_NAME.keys()).index(
                                attribute
                            )
                            cellValue = self.grid_2.GetCellValue(rowNum, indx)
                            fecthValue = (
                                networkInfo[attribute]
                                if attribute in networkInfo
                                else ""
                            )
                            if (
                                not (
                                    rowNum,
                                    indx,
                                )
                                in self.userEdited
                                and cellValue != str(fecthValue)
                            ):
                                self.grid_2.SetCellValue(rowNum, indx, str(fecthValue))
                            deviceListing.update(networkInfo)
                        break
            if not found:
                self.addToNetworkGrid(
                    networkInfo, device_info=device_info, isUpdate=False
                )
        else:
            self.grid_2.AppendRows(1)
            for attribute in Globals.CSV_NETWORK_ATTR_NAME.keys():
                value = networkInfo[attribute] if attribute in networkInfo else ""
                self.grid_2.SetCellValue(
                    self.grid_2.GetNumberRows() - 1, num, str(value)
                )
                isEditable = True
                if attribute in Globals.CSV_EDITABLE_COL:
                    isEditable = False
                self.grid_2.SetReadOnly(
                    self.grid_2.GetNumberRows() - 1, num, isEditable
                )
                num += 1
            if networkInfo not in self.grid_2_contents:
                self.grid_2_contents.append(networkInfo)
        self.grid_2.AutoSizeColumns()

    def toggleColVisibilityInGridOne(self, event, showState=None):
        """ Toggle Column Visibility in Device Grid """
        index = None
        if isinstance(event, (int, float, complex)) and not isinstance(event, bool):
            index = event
        if index:
            if type(showState) == bool:
                if not showState:
                    self.grid_1.HideCol(index)
                else:
                    self.grid_1.ShowCol(index)
            else:
                isShown = self.grid_1.IsColShown(index)
                if isShown:
                    self.grid_1.HideCol(index)
                else:
                    self.grid_1.ShowCol(index)

    def toggleColVisibilityInGridTwo(self, event, showState):
        """ Toggle Column Visibility in Network Grid """
        index = None
        if isinstance(event, (int, float, complex)) and not isinstance(event, bool):
            index = event
        if index:
            if type(showState) == bool:
                if not showState:
                    self.grid_2.HideCol(index)
                else:
                    self.grid_2.ShowCol(index)
            else:
                isShown = self.grid_2.IsColShown(index)
                if isShown:
                    self.grid_2.HideCol(index)
                else:
                    self.grid_2.ShowCol(index)

    def loadConfigPrompt(self):
        """ Display message to user to load config """
        wx.MessageBox("Please load a configuration first!", style=wx.OK | wx.ICON_ERROR)

    @api_tool_decorator
    def getDeviceTagsFromGrid(self):
        """ Return the tags from Grid """
        tagList = {}
        en_indx = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Esper Name")
        sn_indx = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Serial Number")
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, en_indx)
                serialNum = self.grid_1.GetCellValue(rowNum, sn_indx)
                indx = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Tags")
                tags = self.grid_1.GetCellValue(rowNum, indx)
                properTagList = []
                for r in re.findall(r"\".+?\"|[\w\d '-+\\/^%$#!@$%^&]+", tags):
                    processedTag = r.strip()
                    while processedTag.startswith('"') or processedTag.startswith("'"):
                        processedTag = processedTag[1 : len(processedTag)]
                    while processedTag.endswith('"') or processedTag.endswith("'"):
                        processedTag = processedTag[0 : len(processedTag) - 1]
                    # processedTag = r.replace("'", "")  # strip qoutes around tag
                    if processedTag:
                        properTagList.append(processedTag.strip())
                if esperName:
                    tagList[esperName] = properTagList
                elif serialNum:
                    tagList[serialNum] = properTagList
        return tagList

    @api_tool_decorator
    def getDeviceAliasFromGrid(self):
        """ Return a list of Aliases from the Grid """
        aliasList = {}
        indx = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Alias")
        en_indx = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Esper Name")
        sn_indx = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Serial Number")
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, en_indx)
                serialNum = self.grid_1.GetCellValue(rowNum, sn_indx)
                alias = self.grid_1.GetCellValue(rowNum, indx)
                if esperName and esperName not in aliasList.keys():
                    aliasList[esperName] = alias
                elif serialNum and serialNum not in aliasList.keys():
                    aliasList[serialNum] = alias
        return aliasList

    def getDeviceAliasFromList(self):
        aliasList = {}
        if self.grid_1_contents:
            for device in self.grid_1_contents:
                if device["EsperName"] not in aliasList:
                    aliasList[device["EsperName"]] = device["Alias"]
        else:
            aliasList = self.getDeviceAliasFromGrid()
        return aliasList

    def onGridActionSelection(self, event):
        """ When a Grid Action is selected deselect regular Action """
        if event and event.String:
            self.actionChoice.SetSelection(0)
            self.appChoice.Enable(False)
            self.appChoice.SetSelection(-1)
        self.SetFocus()

    def onActionSelection(self, event):
        """ Depending on Action enable or disable Choice """
        if event and event.String:
            self.gridActions.SetSelection(0)

            if (
                event
                and event.String == Globals.GENERAL_ACTIONS[Globals.SET_KIOSK]
                or event.String == Globals.GENERAL_ACTIONS[Globals.CLEAR_APP_DATA]
            ):
                self.appChoice.Enable(True)
            else:
                self.appChoice.SetSelection(-1)
                self.appChoice.Enable(False)
        self.SetFocus()

    def onCellChange(self, event):
        """ Try to Auto size Columns on change """
        self.userEdited.append((event.Row, event.Col))
        editor = self.grid_1.GetCellEditor(event.Row, event.Col)
        if not editor.IsCreated():
            self.grid_1.AutoSizeColumns()
        self.onCellEdit(event)

    @api_tool_decorator
    def updateTagCell(self, name, tags=None):
        """ Update the Tag Column in the Device Grid """
        if hasattr(name, "GetValue"):
            tple = name.GetValue()
            name = tple[0]
            tags = tple[1]
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, 0)
                if name == esperName:
                    indx = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Tags")
                    if not all("" == s or s.isspace() for s in tags):
                        self.grid_1.SetCellValue(rowNum, indx, str(tags))
                    else:
                        self.grid_1.SetCellValue(rowNum, indx, "")

    def showConsole(self, event):
        """ Toggle Console Display """
        if not self.consoleWin:
            self.consoleWin = Console(parent=self)
            self.clearConsole.Enable(True)
            self.Bind(wx.EVT_MENU, self.onClear, self.clearConsole)
        else:
            self.consoleWin.Destroy()
            self.clearConsole.Enable(False)

    def onClear(self, event):
        """ Clear Console """
        if self.consoleWin:
            self.consoleWin.onClear()

    @api_tool_decorator
    def onAbout(self, event):
        """ About Dialog """
        info = adv.AboutDialogInfo()

        info.SetIcon(wx.Icon(resourcePath("Images/logo.png"), wx.BITMAP_TYPE_PNG))
        info.SetName(Globals.TITLE)
        info.SetVersion(Globals.VERSION)
        info.SetDescription(Globals.DESCRIPTION)
        info.SetCopyright("(C) 2020 Esper - All Rights Reserved")
        info.SetWebSite(Globals.ESPER_LINK)

        adv.AboutBox(info)

    @api_tool_decorator
    def onCommand(self, event, value="{\n\n}", level=0):
        """ When the user wants to run a command show the command dialog """
        if level < Globals.MAX_RETRY:
            self.setCursorBusy()
            self.setGaugeValue(0)

            groupSelection = self.groupChoice.GetSelection()
            if groupSelection >= 0:
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
        if hasattr(cmdResult, "state"):
            wx.MessageBox(
                "Command State: %s \n\n Check the console for detailed command results."
                % cmdResult.state,
                style=wx.OK,
            )
        wx.CallLater(3000, self.setGaugeValue, 0)

    def confirmCommand(self, cmd, commandType):
        """ Ask user to confirm the command they want to run """
        deviceSelection = self.deviceChoice.GetSelection()
        groupSelection = self.groupChoice.GetSelection()
        groupLabel = (
            self.groupChoice.Items[groupSelection]
            if len(self.groupChoice.Items) > 0
            and self.groupChoice.Items[groupSelection]
            else ""
        )
        deviceLabel = (
            self.deviceChoice.Items[deviceSelection]
            if len(self.deviceChoice.Items) > 0
            and self.deviceChoice.Items[deviceSelection]
            else ""
        )
        modal = None
        isGroup = False
        cmd_dict = ast.literal_eval(str(cmd).replace("\n", ""))
        cmdFormatted = json.dumps(cmd_dict, indent=2)
        label = ""
        applyTo = ""
        if deviceSelection > 0 and deviceLabel:
            label = deviceLabel
            applyTo = "device"
        elif groupSelection >= 0 and groupLabel:
            label = groupLabel
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

    def setStatus(self, status, isError=False):
        """ Set status bar text """
        self.sbText.SetLabel(status)
        if isError:
            self.sbText.SetForegroundColour(wx.Colour(255, 0, 0))
        else:
            self.sbText.SetForegroundColour(wx.Colour(0, 0, 0))

    @api_tool_decorator
    def onDeviceGridSort(self, event):
        """ Sort Device Grid """
        if self.isRunning or (
            self.gauge.GetValue() != self.gauge.GetRange()
            and self.gauge.GetValue() != 0
        ):
            return
        if hasattr(event, "Col"):
            col = event.Col
        else:
            col = event
        keyName = list(Globals.CSV_TAG_ATTR_NAME.values())[col]

        curSortCol = self.grid_1.GetSortingColumn()
        if curSortCol == col and hasattr(event, "Col"):
            self.deviceDescending = not self.deviceDescending
        self.grid_1.SetSortingColumn(col, bool(not self.deviceDescending))

        if keyName == "androidVersion":
            self.grid_1_contents = sorted(
                self.grid_1_contents,
                key=lambda i: list(map(int, i[keyName].split("."))),
                reverse=self.deviceDescending,
            )
        else:
            if self.grid_1_contents and all(
                s[keyName].isdigit() for s in self.grid_1_contents
            ):
                self.grid_1_contents = sorted(
                    self.grid_1_contents,
                    key=lambda i: i[keyName] and int(i[keyName]),
                    reverse=self.deviceDescending,
                )
            else:
                self.grid_1_contents = sorted(
                    self.grid_1_contents,
                    key=lambda i: i[keyName],
                    reverse=self.deviceDescending,
                )
        self.Logging(
            "---> Sorting Device Grid on Column: %s Order: %s"
            % (keyName, "Descending" if self.deviceDescending else "Ascending")
        )
        self.setGaugeValue(0)
        self.emptyDeviceGrid(emptyContents=False)
        num = 1
        for device in self.grid_1_contents:
            self.addDeviceToDeviceGrid(device)
            self.setGaugeValue(int(num / len(self.grid_1_contents) * 100))
            num += 1
        self.grid_1.MakeCellVisible(0, col)
        self.onSearch(self.search.GetValue())
        wx.CallLater(3000, self.setGaugeValue, 0)

    @api_tool_decorator
    def onNetworkGridSort(self, event):
        """ Sort the network grid """
        if self.isRunning or (
            self.gauge.GetValue() != self.gauge.GetRange()
            and self.gauge.GetValue() != 0
        ):
            return
        if hasattr(event, "Col"):
            col = event.Col
        else:
            col = event
        keyName = list(Globals.CSV_NETWORK_ATTR_NAME.keys())[col]

        curSortCol = self.grid_2.GetSortingColumn()
        if curSortCol == col and hasattr(event, "Col"):
            self.networkDescending = not self.networkDescending
        self.grid_2.SetSortingColumn(col, bool(not self.networkDescending))
        if self.grid_2_contents and all(
            s[keyName].isdigit() for s in self.grid_2_contents
        ):
            self.grid_2_contents = sorted(
                self.grid_2_contents,
                key=lambda i: i[keyName] and int(i[keyName]),
                reverse=self.networkDescending,
            )
        else:
            self.grid_2_contents = sorted(
                self.grid_2_contents,
                key=lambda i: i[keyName],
                reverse=self.networkDescending,
            )
        self.Logging(
            "---> Sorting Network Grid on Column: %s Order: %s"
            % (keyName, "Descending" if self.networkDescending else "Ascending")
        )
        self.setGaugeValue(0)
        self.emptyNetworkGrid(emptyContents=False)
        num = 1
        for info in self.grid_2_contents:
            self.addToNetworkGrid(info)
            self.setGaugeValue(int(num / len(self.grid_2_contents) * 100))
            num += 1
        self.grid_2.MakeCellVisible(0, col)
        self.onSearch(self.search.GetValue())
        wx.CallLater(3000, self.setGaugeValue, 0)

    def toogleViewMenuItem(self, event):
        """
        Disable native headers ability to hide columns when clicking an entry from the context menu
        """
        return

    @api_tool_decorator
    def onFetch(self, event):
        """ Given device data perform the specified action """
        evtValue = event.GetValue()
        action = evtValue[0]
        deviceList = evtValue[1]
        for entry in deviceList.values():
            self.gauge.Pulse()
            device = entry[0]
            deviceInfo = entry[1]
            if action == Globals.SHOW_ALL_AND_GENERATE_REPORT:
                self.addDeviceToDeviceGrid(deviceInfo)
                self.addDeviceToNetworkGrid(device, deviceInfo)
            elif action == Globals.SET_KIOSK:
                setKiosk(self, device, deviceInfo)
            elif action == Globals.SET_MULTI:
                setMulti(self, device, deviceInfo)
            elif action == Globals.CLEAR_APP_DATA:
                clearAppData(self, device)
            # elif action == Globals.POWER_OFF:
            #     powerOffDevice(self, device, deviceInfo)

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
        if action == Globals.CLEAR_APP_DATA:
            wx.MessageBox(
                "Clear App Data Command has been sent to the device(s). Please check devices' event feeds for command status.",
                style=wx.ICON_INFORMATION,
            )

    @api_tool_decorator
    def onDeviceSelection(self, event):
        """ When the user selects a device showcase apps related to that device """
        self.SetFocus()
        self.appChoice.Clear()
        self.gauge.Pulse()
        self.setCursorBusy()
        num = 1
        if self.deviceChoice.GetSelection() > 0:
            deviceId = self.deviceChoice.GetClientData(self.deviceChoice.GetSelection())
            self.runBtn.Enable(False)
            self.Logging("---> Fetching Apps on Device Through API")
            appList, _ = getdeviceapps(deviceId)
            self.Logging("---> Finished Fetching Apps on Device Through API")
            if len(appList) == 0:
                self.appChoice.Append("No available app(s) on this device")
                self.appChoice.SetSelection(0)
            for app in appList:
                app_name = app.split(" v")[0]
                d = [k for k in self.apps if app_name in k]
                if d:
                    d = d[0]
                    self.appChoice.Append(app_name, d[app_name])
                self.setGaugeValue(int(num / len(appList) * 100))
                num += 1
        else:
            for app in self.apps:
                if app:
                    self.appChoice.Append(list(app.keys())[0], list(app.values())[0])
                self.setGaugeValue(int(num / len(self.apps) * 100))
                num += 1
        self.runBtn.Enable(True)
        self.setGaugeValue(100)
        self.setCursorDefault()
        wx.CallLater(3000, self.setGaugeValue, 0)

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
        evtValue = event.GetValue()
        response = evtValue[0]
        callback = evtValue[1]
        cbArgs = evtValue[2]

        if callback:
            self.Logging("---> Attempting to Process API Response")
            callback(*(*cbArgs, response))

    def onComplete(self, event):
        """ Things that should be done once an Action is completed """
        self.setCursorDefault()
        self.setGaugeValue(100)
        if self.isRunning:
            self.runBtn.Enable(True)
            self.frame_toolbar.EnableTool(self.rtool.Id, True)
            self.frame_toolbar.EnableTool(self.rftool.Id, True)
            self.frame_toolbar.EnableTool(self.cmdtool.Id, True)
        self.isRunning = False
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
        self.emptyDeviceGrid()
        self.emptyNetworkGrid()

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

    def onPref(self, event):
        """ Update Preferences when they are changed """
        if self.prefDialog.ShowModal() == wx.ID_APPLY:
            self.savePrefs(self.prefDialog)
        if self.preferences["enableDevice"]:
            self.deviceChoice.Enable(True)
        else:
            self.deviceChoice.Enable(False)

    @api_tool_decorator
    def loadRecentMenu(self):
        """ Populate the Recently Opened Menu """
        if (
            self.preferences
            and "recentAuth" in self.preferences
            and not all("" == s or s.isspace() for s in self.preferences["recentAuth"])
        ):
            recentItems = self.recent.GetMenuItems()
            for child in recentItems:
                self.recent.Delete(child)
            notExist = []
            revList = self.preferences["recentAuth"]
            revList.reverse()
            for auth in revList:
                if auth and os.path.isfile(auth) and os.path.exists(auth):
                    item = self.recent.Append(wx.ID_ANY, auth)
                    self.Bind(
                        wx.EVT_MENU, partial(self.PopulateConfig, auth, item), item
                    )
                if not os.path.exists(auth):
                    notExist.append(auth)
            for auth in notExist:
                self.preferences["recentAuth"].remove(auth)

    @api_tool_decorator
    def uncheckConsole(self, event):
        """ Uncheck Console menu item """
        self.consoleView.Check(False)

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
                    self.applyTextColorToDevice(device[0], orange, bgColor=warnBg)
                else:
                    self.applyTextColorToDevice(device, red, bgColor=errorBg)
        elif type(failed) == tuple:
            if "Queued" in failed:
                self.applyTextColorToDevice(failed[0], orange, bgColor=warnBg)
            else:
                self.applyTextColorToDevice(failed, red, bgColor=errorBg)
        elif failed:
            self.applyTextColorToDevice(failed, red, bgColor=errorBg)

    def applyTextColorToDevice(self, device, color, bgColor=None, applyAll=False):
        """ Apply a Text or Bg Color to a Grid Row """
        statusIndex = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Status")
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, 0)
                if (device and esperName == device.device_name) or applyAll:
                    for colNum in range(self.grid_1.GetNumberCols()):
                        if (
                            colNum < self.grid_1.GetNumberCols()
                            and colNum != statusIndex
                        ):
                            self.grid_1.SetCellTextColour(rowNum, colNum, color)
                            if bgColor:
                                self.grid_1.SetCellBackgroundColour(
                                    rowNum, colNum, bgColor
                                )
        self.grid_1.ForceRefresh()

    def onDeviceColumn(self, event):
        headerLabels = list(Globals.CSV_TAG_ATTR_NAME.keys())
        if "Esper Name" in headerLabels:
            headerLabels.remove("Esper Name")
        if "Device Name" in headerLabels:
            headerLabels.remove("Device Name")

        with ColumnVisibilityDialog(self.grid_1, choiceData=headerLabels) as dialog:
            if dialog.ShowModal() == wx.ID_APPLY:
                colNum = 0
                for _ in headerLabels:
                    self.toggleColVisibilityInGridOne(
                        colNum + 1, showState=dialog.isChecked(colNum)
                    )
                    colNum += 1

    def onNetworkColumn(self, event):
        headerLabels = list(Globals.CSV_NETWORK_ATTR_NAME.keys())
        if "Esper Name" in headerLabels:
            headerLabels.remove("Esper Name")
        if "Device Name" in headerLabels:
            headerLabels.remove("Device Name")

        with ColumnVisibilityDialog(self.grid_2, choiceData=headerLabels) as dialog:
            if dialog.ShowModal() == wx.ID_APPLY:
                colNum = 0
                for _ in headerLabels:
                    self.toggleColVisibilityInGridTwo(
                        colNum + 1, showState=dialog.isChecked(colNum)
                    )
                    colNum += 1

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
                        self.grid_1.AutoSizeColumns()

    @api_tool_decorator
    def onUpdate(self, event):
        if event:
            deviceList = event.GetValue()
            if deviceList:
                for entry in deviceList.values():
                    device = entry[0]
                    deviceInfo = entry[1]
                    self.addDeviceToDeviceGrid(deviceInfo, isUpdate=True)
                    self.addDeviceToNetworkGrid(device, deviceInfo, isUpdate=True)
                if self.grid_1.GetSortingColumn() != wx.NOT_FOUND:
                    self.onDeviceGridSort(self.grid_1.GetSortingColumn())
                if self.grid_2.GetSortingColumn() != wx.NOT_FOUND:
                    self.onNetworkGridSort(self.grid_2.GetSortingColumn())
                self.frame_toolbar.EnableTool(self.rtool.Id, True)
                self.frame_toolbar.EnableTool(self.rftool.Id, True)
                self.frame_toolbar.EnableTool(self.cmdtool.Id, True)
                self.runBtn.Enable(True)
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
            self.frame_toolbar.EnableTool(self.rtool.Id, False)
            self.frame_toolbar.EnableTool(self.rftool.Id, False)
            self.frame_toolbar.EnableTool(self.cmdtool.Id, False)
            self.runBtn.Enable(False)
            self.gauge.Pulse()
            self.fetchUpdateData(forceUpdate=True)
        else:
            while Globals.ENABLE_GRID_UPDATE:
                time.sleep(Globals.GRID_UPDATE_RATE)
                if self.kill:
                    break
                self.fetchUpdateData()
            self.refresh = None

    @api_tool_decorator
    def fetchUpdateData(self, forceUpdate=False):
        if self.isForceUpdate:
            self.isForceUpdate = forceUpdate
        if (
            not self.isRunning
            and not self.isRunningUpdate
            and (
                (
                    self.grid_1_contents
                    and self.grid_2_contents
                    and len(self.grid_1_contents) <= Globals.MAX_UPDATE_COUNT
                    and len(self.grid_2_contents) <= Globals.MAX_UPDATE_COUNT
                )
                or forceUpdate
            )
        ):
            if Globals.LAST_GROUP_ID and not Globals.LAST_DEVICE_ID:
                self.isRunningUpdate = True
                TakeAction(self, Globals.LAST_GROUP_ID, 1, None, isUpdate=True)
            elif Globals.LAST_DEVICE_ID:
                self.isRunningUpdate = True
                TakeAction(
                    self, Globals.LAST_DEVICE_ID, 1, None, isDevice=True, isUpdate=True
                )
            self.isRunningUpdate = False

    @api_tool_decorator
    def onClone(self, event):
        with TemplateDialog(self.configChoice, parent=self) as self.tmpDialog:
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
            time.sleep(5)

    @api_tool_decorator
    def onHelp(self, event):
        webbrowser.open(Globals.HELP_LINK)

    def RemoveEndpoint(self, event):
        value = None
        if event.KeyCode == wx.WXK_DELETE:
            value = self.configList.GetValue()
            value = value.split("\n")[3].replace("Enterprise = ", "")
            result = list(filter(lambda x: value in x, self.auth_data))
            if result:
                result = result[0]
            if value:
                res = wx.MessageBox(
                    "Are you sure you want to remove the configuration with the Enterprise Id of: %s"
                    % value,
                    style=wx.YES_NO | wx.ICON_WARNING,
                )
                if res == wx.YES:
                    self.auth_data.remove(result)
                    with open(self.authPath, "w", newline="") as csvfile:
                        writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
                        writer.writerows(self.auth_data)
                    for child in self.configMenu.GetMenuItems():
                        if value in self.configChoice[child.GetItemLabel()].values():
                            self.configMenu.Delete(child)
                    self.PopulateConfig()
                    wx.MessageBox(
                        "The configuration has been removed.",
                        style=wx.OK | wx.ICON_INFORMATION,
                    )

    @api_tool_decorator
    def onSearch(self, event):
        queryString = ""
        if hasattr(event, "GetString"):
            queryString = event.GetString()
        elif isinstance(event, str):
            queryString = event
        if hasattr(event, "EventType") and (
            (wx.EVT_TEXT.typeId == event.EventType and not queryString)
            or (wx.EVT_SEARCH.typeId == event.EventType and not queryString)
            or wx.EVT_SEARCH_CANCEL.typeId == event.EventType
        ):
            white = wx.Colour(255, 255, 255)
            self.applyTextColorMatchingGridRow(self.grid_1, queryString, white, True)
            self.applyTextColorMatchingGridRow(self.grid_2, queryString, white, True)
        if queryString:
            light_yellow = wx.Colour(255, 255, 224)
            self.applyTextColorMatchingGridRow(self.grid_1, queryString, light_yellow)
            self.applyTextColorMatchingGridRow(self.grid_2, queryString, light_yellow)
            self.Logging("--> Search for %s completed" % queryString)
        else:
            self.search.SetValue("")

    def applyTextColorMatchingGridRow(self, grid, query, bgColor, applyAll=False):
        """ Apply a Text or Bg Color to a Grid Row """
        white = wx.Colour(255, 255, 255)
        light_yellow = wx.Colour(255, 255, 224)
        statusIndex = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Status")
        for rowNum in range(grid.GetNumberRows()):
            if rowNum < grid.GetNumberRows():
                match = []
                [
                    match.append(grid.GetCellValue(rowNum, colNum))
                    if query.lower() in grid.GetCellValue(rowNum, colNum).lower()
                    else None
                    for colNum in range(grid.GetNumberCols())
                ]
                if match or applyAll:
                    for colNum in range(grid.GetNumberCols()):
                        if (
                            colNum < grid.GetNumberCols()
                            and colNum != statusIndex
                            and (
                                grid.GetCellBackgroundColour(rowNum, colNum) == white
                                or (
                                    applyAll
                                    and grid.GetCellBackgroundColour(rowNum, colNum)
                                    == light_yellow
                                )
                            )
                        ):
                            grid.SetCellBackgroundColour(rowNum, colNum, bgColor)
        grid.ForceRefresh()

    def onGridMotion(self, event):
        indx1 = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Tags")
        indx2 = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Alias")
        grid_win = self.grid_1.GetTargetWindow()

        x, y = self.grid_1.CalcUnscrolledPosition(event.GetX(), event.GetY())
        coords = self.grid_1.XYToCell(x, y)
        col = coords[1]

        if col == indx1 or col == indx2:
            grid_win.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        else:
            grid_win.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        event.Skip()

    def onCellEdit(self, event):
        light_blue = wx.Colour(204, 255, 255)
        white = wx.Colour(255, 255, 255)
        indx1 = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Tags")
        indx2 = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Alias")
        x, y = self.grid_1.GetGridCursorCoords()
        esperName = self.grid_1.GetCellValue(x, 0)
        deviceListing = list(
            filter(
                lambda x: (x[Globals.CSV_TAG_ATTR_NAME["Esper Name"]] == esperName),
                self.grid_1_contents,
            )
        )
        if deviceListing:
            if (
                (
                    y == indx2
                    and not "OriginalAlias" in deviceListing[0]
                    and deviceListing[0][Globals.CSV_TAG_ATTR_NAME["Alias"]]
                    != self.grid_1.GetCellValue(x, y)
                )
                or (
                    y == indx2
                    and "OriginalAlias" in deviceListing[0]
                    and deviceListing[0]["OriginalAlias"]
                    != self.grid_1.GetCellValue(x, y)
                )
                or (
                    y == indx1
                    and not "OriginalTags" in deviceListing[0]
                    and deviceListing[0][Globals.CSV_TAG_ATTR_NAME["Tags"]]
                    != self.grid_1.GetCellValue(x, y)
                )
                or (
                    y == indx1
                    and "OriginalTags" in deviceListing[0]
                    and deviceListing[0]["OriginalTags"]
                    != self.grid_1.GetCellValue(x, y)
                )
            ):
                self.grid_1.SetCellBackgroundColour(x, y, light_blue)
                if y == indx2:
                    deviceListing[0][
                        Globals.CSV_TAG_ATTR_NAME["Alias"]
                    ] = self.grid_1.GetCellValue(x, y)
                if y == indx1:
                    deviceListing[0][
                        Globals.CSV_TAG_ATTR_NAME["Tags"]
                    ] = self.grid_1.GetCellValue(x, y)
                if y == indx2 and not "OriginalAlias" in deviceListing[0]:
                    deviceListing[0]["OriginalAlias"] = event.GetString()
                if y == indx1 and not "OriginalTags" in deviceListing[0]:
                    deviceListing[0]["OriginalTags"] = event.GetString()
            else:
                self.grid_1.SetCellBackgroundColour(x, y, white)
        event.Skip()