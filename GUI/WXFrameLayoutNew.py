import wx
import wx.grid as gridlib
import wx.adv as adv
import esperclient
import time
import csv
import os.path
import logging
import Common.Globals as Globals
import platform
import json
import Utility.wxThread as wxThread
import GUI.EnhancedStatusBar as ESB
import tempfile
import re
import ast

from functools import partial

from Common.decorator import api_tool_decorator

from GUI.consoleWindow import Console

from Utility.deviceInfo import (
    getSecurityPatch,
    getWifiStatus,
    getCellularStatus,
    getDeviceName,
)

from esperclient import ApiClient
from esperclient.rest import ApiException
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
)

from GUI.CustomDialogs import (
    CheckboxMessageBox,
    CommandDialog,
    ProgressCheckDialog,
    PreferencesDialog,
    CmdConfirmDialog,
)


class NewFrameLayout(wx.Frame):
    def __init__(self, *args, **kwds):
        self.configMenuOptions = []
        self.WINDOWS = True
        self.prefPath = ""
        if platform.system() == "Windows":
            self.WINDOWS = True
            self.prefPath = (
                "%s\\EsperApiTool\\prefs.json"
                % tempfile.gettempdir().replace("Local", "Roaming").replace("Temp", "")
            )
        else:
            self.WINDOWS = False
            self.prefPath = "%s/EsperApiTool/prefs.json" % tempfile.gettempdir()
        self.configChoice = {}
        self.consoleWin = None
        self.grid_1_contents = []
        self.grid_2_contents = []
        self.apps = []
        self.checkConsole = None
        self.preferences = None
        self.prefDialog = PreferencesDialog(self.preferences, parent=self)

        wx.Frame.__init__(self, None, title=Globals.TITLE, style=wx.DEFAULT_FRAME_STYLE)
        self.SetSize((900, 600))

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
        foa = wx.MenuItem(fileMenu, wx.ID_OPEN, "&Open Auth CSV\tCtrl+O")
        fileOpenAuth = fileMenu.Append(foa)

        foc = wx.MenuItem(fileMenu, wx.ID_APPLY, "&Open Device CSV\tCtrl+D")
        fileOpenConfig = fileMenu.Append(foc)

        self.recent = wx.Menu()
        self.loadRecentMenu()
        fileMenu.Append(wx.ID_ANY, "&Open Recent Auth", self.recent)

        fileMenu.Append(wx.ID_SEPARATOR)
        fs = wx.MenuItem(fileMenu, wx.ID_SAVE, "&Save Device Info As\tCtrl+S")
        fileSave = fileMenu.Append(fs)

        fsa = wx.MenuItem(fileMenu, wx.ID_SAVEAS, "&Save Network Info As\tCtrl+Shift+S")
        fileSaveAs = fileMenu.Append(fsa)

        fileMenu.Append(wx.ID_SEPARATOR)
        fi = wx.MenuItem(fileMenu, wx.ID_EXIT, "&Quit\tCtrl+Q")
        fileItem = fileMenu.Append(fi)

        self.configMenu = wx.Menu()
        defaultConfigVal = self.configMenu.Append(
            wx.ID_NONE, "No Loaded Configurations", "No Loaded Configurations"
        )
        self.configMenuOptions.append(defaultConfigVal)

        editMenu = wx.Menu()
        pref = wx.MenuItem(editMenu, wx.ID_ANY, "&Preferences\tCtrl+P")
        self.pref = editMenu.Append(pref)

        runMenu = wx.Menu()
        runItem = wx.MenuItem(runMenu, wx.ID_RETRY, "&Run\tCtrl+R")
        self.run = runMenu.Append(runItem)

        commandItem = wx.MenuItem(runMenu, wx.ID_ANY, "&Execute Command\tCtrl+Shift+C")
        self.command = runMenu.Append(commandItem)

        viewMenu = wx.Menu()
        self.viewMenuOptions = {}
        colNum = 1
        for header in Globals.CSV_NETWORK_ATTR_NAME.keys():
            if header == "Device Name":
                continue
            item = viewMenu.Append(
                wx.ID_ANY, "Show %s" % header, "Show %s" % header, kind=wx.ITEM_CHECK
            )
            item.Check(True)
            self.Bind(wx.EVT_MENU, self.toggleColVisibilityInGridTwo, item)
            self.viewMenuOptions[item.Id] = colNum
            colNum += 1
        colNum = 1
        viewMenu.Append(wx.ID_SEPARATOR)
        for header in Globals.CSV_TAG_ATTR_NAME.keys():
            if header == "Esper Name":
                continue
            item = viewMenu.Append(
                wx.ID_ANY, "Show %s" % header, "Show %s" % header, kind=wx.ITEM_CHECK
            )
            item.Check(True)
            self.Bind(wx.EVT_MENU, self.toggleColVisibilityInGridOne, item)
            self.viewMenuOptions[item.Id] = colNum
            colNum += 1
        viewMenu.Append(wx.ID_SEPARATOR)
        self.consoleView = viewMenu.Append(
            wx.MenuItem(viewMenu, wx.ID_ANY, "Show Console", kind=wx.ITEM_CHECK)
        )
        self.Bind(wx.EVT_MENU, self.showConsole, self.consoleView)
        self.clearConsole = viewMenu.Append(
            wx.MenuItem(viewMenu, wx.ID_ANY, "Clear Console")
        )
        viewMenu.Append(wx.ID_SEPARATOR)
        self.clearGrids = viewMenu.Append(
            wx.MenuItem(viewMenu, wx.ID_ANY, "Clear Grids")
        )
        self.Bind(wx.EVT_MENU, self.onClearGrids, self.clearGrids)

        helpMenu = wx.Menu()
        about = helpMenu.Append(wx.ID_HELP, "About", "&About")
        self.Bind(wx.EVT_MENU, self.onAbout, about)

        self.menubar.Append(fileMenu, "&File")
        self.menubar.Append(editMenu, "&Edit")
        self.menubar.Append(viewMenu, "&View")
        self.menubar.Append(self.configMenu, "&Configurations")
        self.menubar.Append(runMenu, "&Run")
        self.menubar.Append(helpMenu, "&Help")
        self.SetMenuBar(self.menubar)

        self.Bind(wx.EVT_MENU, self.OnOpen, defaultConfigVal)
        self.Bind(wx.EVT_MENU, self.OnOpen, fileOpenAuth)
        self.Bind(wx.EVT_MENU, self.onUploadCSV, fileOpenConfig)
        self.Bind(wx.EVT_MENU, self.OnQuit, fileItem)
        self.Bind(wx.EVT_MENU, self.onSave, fileSave)
        self.Bind(wx.EVT_MENU, self.onSaveAs, fileSaveAs)
        self.Bind(wx.EVT_MENU, self.onRun, self.run)
        self.Bind(wx.EVT_MENU, self.onCommand, self.command)
        self.Bind(wx.EVT_MENU, self.onPref, self.pref)
        # Menu Bar end

        # Tool Bar
        self.frame_toolbar = wx.ToolBar(self, -1)
        self.SetToolBar(self.frame_toolbar)

        close_icon = wx.ArtProvider.GetBitmap(wx.ART_QUIT, wx.ART_TOOLBAR, (16, 16))
        qtool = self.frame_toolbar.AddTool(wx.ID_ANY, "Quit", close_icon, "Quit")
        self.frame_toolbar.AddSeparator()

        open_icon = wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR, (16, 16))
        otool = self.frame_toolbar.AddTool(
            wx.ID_ANY, "Open Auth CSV", open_icon, "Open Auth CSV"
        )
        self.frame_toolbar.AddSeparator()

        save_icon = wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR, (16, 16))
        stool = self.frame_toolbar.AddTool(
            wx.ID_ANY, "Save Device Info", save_icon, "Save Device Info"
        )
        saveas_icon = wx.ArtProvider.GetBitmap(
            wx.ART_FILE_SAVE_AS, wx.ART_TOOLBAR, (16, 16)
        )
        sstool = self.frame_toolbar.AddTool(
            wx.ID_ANY, "Save Network Info", saveas_icon, "Save Network Info"
        )
        self.frame_toolbar.AddSeparator()

        exe_icon = wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_TOOLBAR, (16, 16))
        rtool = self.frame_toolbar.AddTool(
            wx.ID_ANY, "Run Action", exe_icon, "Run Action"
        )

        cmd_icon = wx.ArtProvider.GetBitmap(
            wx.ART_EXECUTABLE_FILE, wx.ART_TOOLBAR, (16, 16)
        )
        cmdtool = self.frame_toolbar.AddTool(
            wx.ID_ANY, "Run Command", cmd_icon, "Run Command"
        )

        self.Bind(wx.EVT_TOOL, self.OnQuit, qtool)
        self.Bind(wx.EVT_TOOL, self.OnOpen, otool)
        self.Bind(wx.EVT_TOOL, self.onSave, stool)
        self.Bind(wx.EVT_TOOL, self.onSaveAs, sstool)
        self.Bind(wx.EVT_TOOL, self.onRun, rtool)
        self.Bind(wx.EVT_TOOL, self.onCommand, cmdtool)
        # Tool Bar end

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
        self.Bind(wx.EVT_ACTIVATE_APP, self.MacReopenApp)

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
        icon.CopyFromBitmap(wx.Bitmap("Images/icon.png", wx.BITMAP_TYPE_PNG))
        self.SetIcon(icon)

        self.loadPref()
        self.__set_properties()
        self.__do_layout()
        self.Raise()
        self.Iconize(False)
        self.SetFocus()

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
        self.run.Enable(False)
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
            "Application for Kiosk Mode",
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
            self.setStatus(entry, isError)
        except:
            pass

    @api_tool_decorator
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
            self.PopulateConfig()

    @api_tool_decorator
    def OnQuit(self, e):
        if self.consoleWin:
            self.consoleWin.Close()
            self.consoleWin.Destroy()
            self.consoleWin = None
        if self.prefDialog:
            self.prefDialog.Close()
            self.prefDialog.Destroy()
        if e.EventType != wx.EVT_CLOSE.typeId:
            self.Close()
        self.savePrefs(self.prefDialog)
        self.Destroy()

    @api_tool_decorator
    def onSave(self, event):
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
                self.save(inFile, self.grid_1, Globals.CSV_TAG_ATTR_NAME.keys())
                return True
            elif (
                result == wx.ID_CANCEL
            ):  # Either the cancel button was pressed or the window was closed
                return False

    @api_tool_decorator
    def onSaveAs(self, event):
        if self.grid_2.GetNumberRows() > 0:
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
                self.save(inFile, self.grid_2, Globals.CSV_NETWORK_ATTR_NAME.keys())
                return True
            elif (
                result == wx.ID_CANCEL
            ):  # Either the cancel button was pressed or the window was closed
                return False

    def save(self, inFile, grid, header):
        numRows = grid.GetNumberRows()
        numCols = grid.GetNumberCols()
        gridData = []
        gridData.append(header)

        self.createNewFile(inFile)

        for row in range(numRows):
            rowValues = []
            for col in range(numCols):
                value = grid.GetCellValue(row, col)
                rowValues.append(value)
            gridData.append(rowValues)

        with open(inFile, "w", newline="") as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerows(gridData)

        self.Logging("---> Info saved to csv file - " + inFile)

    def createNewFile(self, filePath):
        if not os.path.exists(filePath):
            parentPath = os.path.abspath(os.path.join(filePath, os.pardir))
            if not os.path.exists(parentPath):
                os.makedirs(parentPath)
            with open(filePath, "w"):
                pass

    @api_tool_decorator
    def onUploadCSV(self, event):
        if not Globals.enterprise_id:
            self.loadConfigPrompt()
            return

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
                num = 0
                with open(Globals.csv_auth_path, "r") as csvFile:
                    reader = csv.reader(
                        csvFile, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True
                    )
                    header = None
                    grid_headers = list(Globals.CSV_TAG_ATTR_NAME.keys())
                    data = list(reader)
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
                                    if (
                                        header[fileCol]
                                        in Globals.CSV_DEPRECATED_HEADER_LABEL
                                        or header[fileCol]
                                        not in Globals.CSV_TAG_ATTR_NAME.keys()
                                    ):
                                        fileCol += 1
                                        continue
                                    if colName == expectedCol.replace(" ", "").lower():
                                        self.grid_1.SetCellValue(
                                            self.grid_1.GetNumberRows() - 1,
                                            toolCol,
                                            str(colValue),
                                        )
                                        isEditable = True
                                        if (
                                            grid_headers[toolCol]
                                            in Globals.CSV_EDITABLE_COL
                                        ):
                                            isEditable = False
                                        self.grid_1.SetReadOnly(
                                            self.grid_1.GetNumberRows() - 1,
                                            toolCol,
                                            isEditable,
                                        )
                                    fileCol += 1
                                toolCol += 1
                    self.grid_1.AutoSizeColumns()
            elif result == wx.ID_CANCEL:
                return  # the user changed their mind

    @api_tool_decorator
    def PopulateConfig(self, auth=None, authItem=None, event=None):
        """Populates Configuration From CSV"""
        self.Logging("--->Loading Configurations from %s" % Globals.csv_auth_path)
        if auth:
            if Globals.csv_auth_path != auth:
                Globals.csv_auth_path = auth
            else:
                return
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
                        self.Bind(wx.EVT_MENU, self.OnOpen, defaultConfigVal)
                        return
            self.Logging(
                "--->**** Please Select an Endpoint From the Configuartion Menu (defaulting to first Config)"
            )
            if Globals.csv_auth_path in self.preferences["recentAuth"]:
                self.preferences["recentAuth"].remove(Globals.csv_auth_path)
                if authItem:
                    self.recent.Delete(authItem)
            self.preferences["recentAuth"].append(Globals.csv_auth_path)
            self.preferences["lastAuth"] = Globals.csv_auth_path
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
            self.Bind(wx.EVT_MENU, self.OnOpen, defaultConfigVal)

    def setCursorDefault(self):
        try:
            myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
            self.SetCursor(myCursor)
        except:
            pass

    def setCursorBusy(self):
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)

    @api_tool_decorator
    def loadConfiguartion(self, event, *args, **kwargs):
        """Populate Frame Layout With Device Configuration"""
        menuItem = self.configMenu.FindItemById(event.Id)
        self.onClearGrids(None)
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

            self.groupChoice.Enable(True)
            self.actionChoice.Enable(True)
        except Exception as e:
            self.Logging(
                "--->****An Error has occured while loading the configuration, please try again."
            )
            print(e)
            menuItem.Check(False)
        self.setCursorDefault()

    @api_tool_decorator
    def PopulateGroups(self):
        """create an instance of the API class"""
        self.Logging("--->Attemptting to populate groups...")
        self.setCursorBusy()
        self.setGaugeValue(0)
        self.gauge.Pulse()
        self.groupChoice.Clear()
        wxThread.doAPICallInThread(
            self, getAllGroups, eventType=wxThread.myEVT_GROUP, waitForJoin=False
        )

    @api_tool_decorator
    def addGroupsToGroupChoice(self, event):
        results = event.GetValue().results
        num = 1
        if len(results):
            for group in results:
                self.groupChoice.Append(group.name, group.id)
                self.setGaugeValue(int(num / len(results) * 100))
                num += 1
            self.Bind(wx.EVT_COMBOBOX, self.PopulateDevices, self.groupChoice)
        self.runBtn.Enable(True)
        self.run.Enable(True)
        self.command.Enable(True)
        self.groupChoice.Enable(True)
        self.actionChoice.Enable(True)
        self.setCursorDefault()

    @api_tool_decorator
    def PopulateDevices(self, event):
        self.SetFocus()
        self.Logging(
            "--->Attemptting to populate devices of selected group (%s)..."
            % event.String
        )
        self.deviceChoice.Clear()
        self.appChoice.Clear()
        if not self.preferences or self.preferences["enableDevice"] == True:
            self.runBtn.Enable(False)
            self.setGaugeValue(0)
            self.gauge.Pulse()
            self.setCursorBusy()
        else:
            self.runBtn.Enable(True)
        for app in self.apps:
            self.appChoice.Append(list(app.keys())[0], list(app.values())[0])
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
        api_response = event.GetValue()
        if len(api_response.results):
            if not self.preferences or self.preferences["enableDevice"] == True:
                self.deviceChoice.Enable(True)
            else:
                self.deviceChoice.Enable(False)
            self.deviceChoice.Append("", "")
            num = 1
            for device in api_response.results:
                name = "%s %s %s" % (
                    device.hardware_info["manufacturer"],
                    device.hardware_info["model"],
                    device.device_name,
                )
                self.deviceChoice.Append(name, device.id)
                if not self.preferences or self.preferences["enableDevice"] == True:
                    self.setGaugeValue(int(num / len(api_response.results) * 100))
                num += 1
        else:
            self.deviceChoice.Append("No Devices Found", "")
            self.deviceChoice.Enable(False)
            self.Logging("---> No Devices found in group")
        self.setCursorDefault()
        self.runBtn.Enable(True)

    @api_tool_decorator
    def PopulateApps(self):
        """create an instance of the API class"""
        self.Logging("--->Attemptting to populate apps...")
        self.setCursorBusy()
        self.appChoice.Clear()
        wxThread.doAPICallInThread(
            self, getAllApplications, eventType=wxThread.myEVT_APPS, waitForJoin=False
        )

    @api_tool_decorator
    def addAppsToAppChoice(self, event):
        api_response = event.GetValue()
        self.appChoice.Append("", "")
        if len(api_response.results):
            num = 1
            for app in api_response.results:
                self.appChoice.Append(app.application_name, app.package_name)
                self.apps.append({app.application_name: app.package_name})
                self.setGaugeValue(int(num / len(api_response.results) * 100))
                num += 1
        self.setCursorDefault()

    @api_tool_decorator
    def onRun(self, event):
        self.setCursorBusy()
        self.gauge.Pulse()
        self.runBtn.Enable(False)

        self.grid_1_contents = []
        self.grid_2_contents = []

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
            if actionSelection == Globals.SET_KIOSK and appSelection < 0:
                wx.MessageBox(
                    "Please select a valid application", style=wx.OK | wx.ICON_ERROR
                )
                self.setCursorDefault()
                return
            self.Logging(
                '---> Attempting to run action, "%s", on group, %s.'
                % (actionLabel, groupLabel)
            )
            TakeAction(
                self,
                groupSelection,
                actionSelection,
                groupLabel,
            )
        elif deviceSelection > 0 and gridSelection <= 0 and actionSelection > 0:
            # run action on device
            if actionSelection == Globals.SET_KIOSK and (
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
            TakeAction(
                self, deviceSelection, actionSelection, deviceLabel, isDevice=True
            )
        elif gridSelection > 0:
            # run grid action
            if self.grid_1.GetNumberRows() > 0:
                runAction = True
                if Globals.SHOW_GRID_DIALOG:
                    result = CheckboxMessageBox(
                        "Confirmation",
                        "The %s will attempt to process the action on all devices in the Device Info grid. \n\nContinue?"
                        % Globals.TITLE,
                    ).ShowModal()
                    if result != wx.ID_OK:
                        runAction = False
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
    def emptyDeviceGrid(self):
        self.grid_1.ClearGrid()
        if self.grid_1.GetNumberRows() > 0:
            self.grid_1.DeleteRows(0, self.grid_1.GetNumberRows())
        self.grid_1.SetScrollLineX(15)
        self.grid_1.SetScrollLineY(15)
        self.fillDeviceGridHeaders()

    @api_tool_decorator
    def emptyNetworkGrid(self):
        self.grid_2.ClearGrid()
        if self.grid_2.GetNumberRows() > 0:
            self.grid_2.DeleteRows(0, self.grid_2.GetNumberRows())
        self.grid_2.SetScrollLineX(15)
        self.grid_2.SetScrollLineY(15)
        self.fillNetworkGridHeaders()

    @api_tool_decorator
    def addDeviceToDeviceGrid(self, device_info):
        num = 0
        self.grid_1.AppendRows(1)
        device = {}

        for attribute in Globals.CSV_TAG_ATTR_NAME:
            value = (
                device_info[Globals.CSV_TAG_ATTR_NAME[attribute]]
                if Globals.CSV_TAG_ATTR_NAME[attribute] in device_info
                else ""
            )
            device[Globals.CSV_TAG_ATTR_NAME[attribute]] = str(value)
            self.grid_1.SetCellValue(self.grid_1.GetNumberRows() - 1, num, str(value))
            isEditable = True
            if attribute in Globals.CSV_EDITABLE_COL:
                isEditable = False
            self.grid_1.SetReadOnly(self.grid_1.GetNumberRows() - 1, num, isEditable)
            num += 1

        self.grid_1.AutoSizeColumns()
        if device not in self.grid_1_contents:
            self.grid_1_contents.append(device)

    @api_tool_decorator
    def addDeviceToNetworkGrid(self, device, deviceInfo):
        networkInfo = {}
        networkInfo["Security Patch"] = getSecurityPatch(device)
        wifiStatus = getWifiStatus(deviceInfo).split(",")
        networkInfo["[WIFI ACCESS POINTS]"] = wifiStatus[0]
        networkInfo["[Current WIFI Connection]"] = wifiStatus[1]
        cellStatus = getCellularStatus(deviceInfo).split(",")
        networkInfo["[Cellular Access Point]"] = cellStatus[0]
        networkInfo["Active Connection"] = cellStatus[1]
        networkInfo["Device Name"] = getDeviceName(device)

        for key, value in Globals.CSV_NETWORK_ATTR_NAME.items():
            if value:
                if value in deviceInfo:
                    networkInfo[key] = str(deviceInfo[value])
                else:
                    networkInfo[key] = str([])

        self.addToNetworkGrid(networkInfo)

    def addToNetworkGrid(self, networkInfo):
        num = 0
        self.grid_2.AppendRows(1)

        for attribute in Globals.CSV_NETWORK_ATTR_NAME.keys():
            value = networkInfo[attribute] if attribute in networkInfo else ""
            self.grid_2.SetCellValue(self.grid_2.GetNumberRows() - 1, num, str(value))
            isEditable = True
            if attribute in Globals.CSV_EDITABLE_COL:
                isEditable = False
            self.grid_2.SetReadOnly(self.grid_2.GetNumberRows() - 1, num, isEditable)
            num += 1

        self.grid_2.AutoSizeColumns()
        if networkInfo not in self.grid_2_contents:
            self.grid_2_contents.append(networkInfo)

    def toggleColVisibilityInGridOne(self, event):
        index = (
            self.viewMenuOptions[event.Id] if event.Id in self.viewMenuOptions else None
        )
        isShown = self.grid_1.IsColShown(index)
        if isShown:
            self.grid_1.HideCol(index)
        else:
            self.grid_1.ShowCol(index)

    def toggleColVisibilityInGridTwo(self, event):
        index = (
            self.viewMenuOptions[event.Id] if event.Id in self.viewMenuOptions else None
        )
        isShown = self.grid_2.IsColShown(index)
        if isShown:
            self.grid_2.HideCol(index)
        else:
            self.grid_2.ShowCol(index)

    def loadConfigPrompt(self):
        wx.MessageBox("Please load a configuration first!", style=wx.OK | wx.ICON_ERROR)

    @api_tool_decorator
    def getDeviceTagsFromGrid(self):
        tagList = {}
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, 0)
                indx = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Tags")
                tags = self.grid_1.GetCellValue(rowNum, indx)
                properTagList = []
                for r in re.findall(r"'.+?'|[\w-]+", tags):
                    processedTag = r.replace("'", "")  # strip qoutes around tag
                    if processedTag:
                        properTagList.append(processedTag)
                tagList[esperName] = properTagList
        return tagList

    @api_tool_decorator
    def getDeviceAliasFromGrid(self):
        aliasList = {}
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, 0)
                indx = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Alias")
                alias = self.grid_1.GetCellValue(rowNum, indx)
                aliasList[esperName] = alias
        return aliasList

    def onGridActionSelection(self, event):
        if event and event.String:
            self.actionChoice.SetSelection(0)
            self.appChoice.Enable(False)
            self.appChoice.SetSelection(-1)
        self.SetFocus()

    def onActionSelection(self, event):
        if event and event.String:
            self.gridActions.SetSelection(0)

            if event and event.String == Globals.GENERAL_ACTIONS[Globals.SET_KIOSK]:
                self.appChoice.Enable(True)
            else:
                self.appChoice.SetSelection(-1)
                self.appChoice.Enable(False)
        self.SetFocus()

    def onCellChange(self, event):
        self.grid_1.AutoSizeColumns()

    @api_tool_decorator
    def updateTagCell(self, name, tags=None):
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
        if not self.consoleWin:
            self.consoleWin = Console(parent=self)
            self.clearConsole.Enable(True)
            self.Bind(wx.EVT_MENU, self.onClear, self.clearConsole)
        else:
            self.consoleWin.Destroy()
            self.clearConsole.Enable(False)

    def onClear(self, event):
        if self.consoleWin:
            self.consoleWin.onClear()

    def onAbout(self, event):
        info = adv.AboutDialogInfo()

        info.SetIcon(wx.Icon("Images/logo.png", wx.BITMAP_TYPE_PNG))
        info.SetName(Globals.TITLE)
        info.SetVersion(Globals.VERSION)
        info.SetDescription(Globals.DESCRIPTION)
        info.SetCopyright("(C) 2020 Esper - All Rights Reserved")
        info.SetWebSite("https://esper.io/")
        for dev in Globals.DEVS:
            info.AddDeveloper(dev)

        adv.AboutBox(info)

    @api_tool_decorator
    def onCommand(self, event, value="{\n\n}", level=0):
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
                            cmd = json.loads(config)
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
        cmdResult = event.GetValue()
        self.setGaugeValue(100)
        if hasattr(cmdResult, "state"):
            wx.MessageBox(
                "Command State: %s \n\n Check the console for detailed command results."
                % cmdResult.state,
                style=wx.OK,
            )

    def confirmCommand(self, cmd, commandType):
        deviceSelection = self.deviceChoice.GetSelection()
        groupSelection = self.groupChoice.GetSelection()
        groupToUse = self.groupChoice.GetClientData(groupSelection)
        deviceToUse = (
            self.deviceChoice.GetClientData(deviceSelection)
            if deviceSelection > 0
            else ""
        )
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
        self.sbText.SetLabel(status)
        if isError:
            self.sbText.SetForegroundColour(wx.Colour(255, 0, 0))
        else:
            self.sbText.SetForegroundColour(wx.Colour(0, 0, 0))

    @api_tool_decorator
    def onDeviceGridSort(self, event):
        col = event.Col
        keyName = list(Globals.CSV_TAG_ATTR_NAME.values())[col]

        curSortCol = self.grid_1.GetSortingColumn()
        descending = False
        if curSortCol == col:
            descending = True
        self.grid_1.SetSortingColumn(col, bool(not descending))

        if keyName == "androidVersion":
            self.grid_1_contents = sorted(
                self.grid_1_contents,
                key=lambda i: list(map(int, i[keyName].split("."))),
                reverse=descending,
            )
        else:
            self.grid_1_contents = sorted(
                self.grid_1_contents, key=lambda i: i[keyName], reverse=descending
            )
        self.Logging("---> Sorting Device Grid on Column: %s" % keyName)
        self.setGaugeValue(0)
        self.emptyDeviceGrid()
        num = 1
        for device in self.grid_1_contents:
            self.addDeviceToDeviceGrid(device)
            self.setGaugeValue(int(num / len(self.grid_1_contents) * 100))
            num += 1
        self.grid_1.MakeCellVisible(0, col)

    @api_tool_decorator
    def onNetworkGridSort(self, event):
        col = event.Col
        keyName = list(Globals.CSV_NETWORK_ATTR_NAME.keys())[col]

        curSortCol = self.grid_2.GetSortingColumn()
        descending = False
        if curSortCol == col:
            descending = True
        self.grid_2.SetSortingColumn(col, bool(not descending))
        self.grid_2_contents = sorted(
            self.grid_2_contents, key=lambda i: i[keyName], reverse=descending
        )
        self.Logging("---> Sorting Network Grid on Column: %s" % keyName)
        self.setGaugeValue(0)
        self.emptyNetworkGrid()
        num = 1
        for info in self.grid_2_contents:
            self.addToNetworkGrid(info)
            self.setGaugeValue(int(num / len(self.grid_2_contents) * 100))
            num += 1
        self.grid_2.MakeCellVisible(0, col)

    def toogleViewMenuItem(self, event):
        """
        Disable native headers ability to hide columns when clicking an entry from the context menu
        """
        return

    @api_tool_decorator
    def onUpdate(self, event):
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

    def onUpdateComplete(self, event):
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

    @api_tool_decorator
    def onDeviceSelection(self, event):
        self.SetFocus()
        self.appChoice.Clear()
        self.setGaugeValue(0)
        num = 1
        if self.deviceChoice.GetSelection() > 0:
            deviceId = self.deviceChoice.GetClientData(self.deviceChoice.GetSelection())

            appList = getdeviceapps(deviceId)
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
                self.appChoice.Append(list(app.keys())[0], list(app.values())[0])
                self.setGaugeValue(int(num / len(self.apps) * 100))
                num += 1
        self.setGaugeValue(100)

    def MacReopenApp(self, event):
        """Called when the doc icon is clicked, and ???"""
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
        self.Logging("---> API Response Returned")
        evtValue = event.GetValue()
        response = evtValue[0]
        callback = evtValue[1]
        cbArgs = evtValue[2]

        if callback:
            self.Logging("---> Attempting to Process API Response")
            callback(*(*cbArgs, response))

    def onComplete(self, event):
        self.setCursorDefault()
        self.setGaugeValue(100)
        self.runBtn.Enable(True)
        self.Logging("---> Completed Action")

    def onClearGrids(self, event):
        self.emptyDeviceGrid()
        self.emptyNetworkGrid()

    @api_tool_decorator
    def loadPref(self):
        if (
            os.path.isfile(self.prefPath)
            and os.path.exists(self.prefPath)
            and os.access(self.prefPath, os.R_OK)
        ):
            with open(self.prefPath) as jsonFile:
                self.preferences = json.load(jsonFile)
            self.prefDialog.SetPrefs(self.preferences)
            if "lastAuth" in self.preferences and self.preferences["lastAuth"]:
                self.PopulateConfig(auth=self.preferences["lastAuth"])
        else:
            self.createNewFile(self.prefPath)
            self.savePrefs(self.prefDialog)

    @api_tool_decorator
    def savePrefs(self, dialog):
        self.preferences = dialog.GetPrefs()
        with open(self.prefPath, "w") as outfile:
            json.dump(self.preferences, outfile)

    def onPref(self, event):
        if self.prefDialog.ShowModal() == wx.ID_APPLY:
            self.savePrefs(self.prefDialog)
        if self.preferences["enableDevice"]:
            self.deviceChoice.Enable(True)
        else:
            self.deviceChoice.Enable(False)

    @api_tool_decorator
    def loadRecentMenu(self):
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
        self.consoleView.Check(False)

    @api_tool_decorator
    def onFail(self, event):
        failed = event.GetValue()
        red = wx.Colour(255, 0, 0)
        errorBg = wx.Colour(255, 192, 203)
        if type(failed) == list:
            for device in failed:
                self.applyTextColorToDevice(device, red, bgColor=errorBg)
        elif failed:
            self.applyTextColorToDevice(failed, red, bgColor=errorBg)

    def applyTextColorToDevice(self, device, color, bgColor=None, applyAll=False):
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, 0)
                if (device and esperName == device.device_name) or applyAll:
                    for colNum in range(self.grid_1.GetNumberCols()):
                        if rowNum < self.grid_1.GetNumberCols():
                            self.grid_1.SetCellTextColour(rowNum, colNum, color)
                            if bgColor:
                                self.grid_1.SetCellBackgroundColour(
                                    rowNum, colNum, bgColor
                                )
        self.grid_1.ForceRefresh()
