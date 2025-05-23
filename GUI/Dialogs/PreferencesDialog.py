#!/usr/bin/env python

import os
import platform

import wx
import wx.adv as wxadv

import Common.Globals as Globals
from Common.decorator import api_tool_decorator
from Common.enum import FontStyles
from GUI.Dialogs.LargeTextEntryDialog import LargeTextEntryDialog
from Utility.Resource import getFont, onDialogEscape, uiThreadCheck


class PreferencesDialog(wx.Dialog):
    def __init__(self, parent=None):
        self.ready = False
        self.size = (900, 500)
        super(PreferencesDialog, self).__init__(
            parent,
            wx.ID_ANY,
            size=self.size,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.SetTitle("Preferences")
        self.SetSize(self.size)
        self.SetMinSize(self.size)
        self.SetThemeEnabled(False)
        self.file_location = os.getcwd()

        self.parent = parent
        self.prefs = {}
        self.prefKeys = [
            "enableDevice",
            "limit",
            "gridDialog",
            "windowSize",
            "windowPosition",
            "isMaximized",
            "getAllApps",
            "showPkg",
            "reachQueueStateOnly",
            "gridDialog",
            "templateDialog",
            "templateUpdate",
            "colSize",
            "setStateShow",
            "useJsonForCmd",
            "runCommandOn",
            "aliasDayDelta",
            "fontSize",
            "saveColVisibility",
            "replaceSerial",
            "showDisabledDevices",
            "lastSeenAsDate",
            "appsInDeviceGrid",
            "inhibitSleep",
            "appVersionNameInsteadOfCode",
            "combineDeviceAndNetworkSheets",
            "showGroupPath",
            "last_endpoint",
            "prereleaseUpdate",
            "appFilter",
            "maxSplitFileSize",
            "allowAutoIssuePost",
            "appColFilter",
            "scheduleSaveLocation",
            "scheduleSaveType",
            "scheduleEnabled",
            "scheduleReportType",
            "scheduleInterval",
            "showDisclaimer",
            "showAppFilter",
            "getTemplateLanguage",
            "pullAppleDevices",
        ]
        self.appColFilter = Globals.APP_COL_FILTER

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        panel_1 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(panel_1, 1, wx.ALL | wx.EXPAND, 5)

        sizer_3 = wx.BoxSizer(wx.VERTICAL)

        self.window_1 = wx.SplitterWindow(panel_1, wx.ID_ANY)
        self.window_1.SetMinimumPaneSize(20)
        sizer_3.Add(self.window_1, 1, wx.EXPAND, 0)

        self.window_1_pane_1 = wx.Panel(self.window_1, wx.ID_ANY)

        sizer_4 = wx.GridSizer(1, 1, 0, 0)

        self.list_box_1 = wx.ListBox(
            self.window_1_pane_1,
            wx.ID_ANY,
            choices=[],
            style=wx.LB_NEEDED_SB | wx.LB_SINGLE,
        )
        self.list_box_1.SetFont(getFont(FontStyles.NORMAL.value))
        sizer_4.Add(self.list_box_1, 0, wx.EXPAND, 5)

        self.window_1_pane_2 = wx.ScrolledWindow(self.window_1, wx.ID_ANY, style=wx.BORDER_SIMPLE | wx.TAB_TRAVERSAL)
        self.window_1_pane_2.SetScrollRate(10, 10)

        sizer_5 = wx.BoxSizer(wx.VERTICAL)

        ### General Preferences
        self.general = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        self.general.Hide()
        sizer_5.Add(self.general, 1, wx.EXPAND, 0)

        sizer_6 = wx.FlexGridSizer(6, 1, 0, 0)

        (
            _,
            _,
            self.checkbox_21,
        ) = self.addPrefToPanel(
            self.general,
            sizer_6,
            "Inhibit Sleep When Running",
            wx.CheckBox,
            "Try to prevent the device from Sleeping while running a job.",
        )
        self.checkbox_21.Set3StateValue(wx.CHK_UNCHECKED if not Globals.INHIBIT_SLEEP else wx.CHK_CHECKED)

        (
            _,
            _,
            self.checkbox_25,
        ) = self.addPrefToPanel(
            self.general,
            sizer_6,
            "Include Pre-release in Update Check",
            wx.CheckBox,
            "When checking for updates, include Pre-Releases.",
        )

        ### Report Options
        self.report = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        self.report.Hide()
        sizer_5.Add(self.report, 1, wx.EXPAND, 0)
        sizer_10 = wx.FlexGridSizer(13, 1, 0, 0)

        (
            _,
            _,
            self.checkbox_1,
        ) = self.addPrefToPanel(
            self.report,
            sizer_10,
            "Enable Device Selection",
            wx.CheckBox,
            "Allow user to specify actions on a selections of devices within a group.",
        )

        (
            _,
            _,
            self.checkbox_32,
        ) = self.addPrefToPanel(
            self.report,
            sizer_10,
            "Pull Apple Devices",
            wx.CheckBox,
            "Pull Apple Devices in addition to Android Devices, if available.",
        )

        (
            _,
            _,
            self.checkbox_16,
        ) = self.addPrefToPanel(
            self.report,
            sizer_10,
            "Fetch all devices in one page",
            wx.CheckBox,
            "Attempts to fetch all info for devices in a group and display them in one page (For Groups). May impact performance.",
        )

        static_line_4 = wx.StaticLine(self.report, wx.ID_ANY)
        sizer_10.Add(
            static_line_4,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.EXPAND | wx.TOP,
            5,
        )

        (
            _,
            _,
            self.checkbox_18,
        ) = self.addPrefToPanel(
            self.report,
            sizer_10,
            "Show Disabled Devices",
            wx.CheckBox,
            "Show device entries for device that are disabled (e.g. Devices that have been wiped).",
        )
        self.checkbox_18.Set3StateValue(wx.CHK_UNCHECKED if not Globals.SHOW_DISABLED_DEVICES else wx.CHK_CHECKED)

        (
            _,
            _,
            self.checkbox_29,
        ) = self.addPrefToPanel(
            self.report,
            sizer_10,
            "Get Template Language",
            wx.CheckBox,
            "Fetches Language from the Initial Template used to provision the device.\nWill increase report generation speed.\nNot applicable for Blueprint Tenants.",
        )
        self.checkbox_29.Set3StateValue(wx.CHK_UNCHECKED if not Globals.GET_DEVICE_LANGUAGE else wx.CHK_CHECKED)

        (
            _,
            _,
            self.combobox_2,
        ) = self.addPrefToPanel(
            self.report,
            sizer_10,
            "Filter App State",
            wx.ComboBox,
            "Filter Apps shown in the App Report by their State (SHOW, HIDE, DISBALED). Default: All App States Shown",
            choice=Globals.APP_FILTER_TYPES,
        )
        self.combobox_2.SetSelection(0)

        (
            _,
            _,
            self.checkbox_17,
        ) = self.addPrefToPanel(
            self.report,
            sizer_10,
            "Replace Serial Number with Custom",
            wx.CheckBox,
            "Replaces Serial Number entry with Custom Serial Number, if available.",
        )

        (
            _,
            _,
            self.checkbox_19,
        ) = self.addPrefToPanel(
            self.report,
            sizer_10,
            "Last Seen As Date",
            wx.CheckBox,
            "Value displayed in the “Last Seen” column will be a Date instead of a time estimation.",
        )

        (
            _,
            _,
            self.checkbox_20,
        ) = self.addPrefToPanel(
            self.report,
            sizer_10,
            "Show Apps In Device Grid",
            wx.CheckBox,
            "Show a list of applications in the Device Info Grid. Note: Re-adding the column will append it to the end.",
        )

        (
            _,
            _,
            self.checkbox_24,
        ) = self.addPrefToPanel(
            self.report,
            sizer_10,
            "Show Group Path Instead of Name",
            wx.CheckBox,
            "Show the entire Group Path instead of just a name in the Group column.",
        )

        static_line_3 = wx.StaticLine(self.report, wx.ID_ANY)
        sizer_10.Add(
            static_line_3,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.EXPAND | wx.TOP,
            5,
        )

        (
            _,
            _,
            self.spin_ctrl_1,
        ) = self.addPrefToPanel(
            self.report,
            sizer_10,
            "API Request Limit",
            wx.SpinCtrl,
            "Maximum amount of results that the API will return. Min: %s Max: %s" % (Globals.MIN_LIMIT, Globals.MAX_LIMIT),
        )
        self.spin_ctrl_1.SetMin(Globals.MIN_LIMIT)
        self.spin_ctrl_1.SetMax(Globals.MAX_LIMIT)
        self.spin_ctrl_1.SetValue(Globals.limit)

        ### Display Options
        self.display = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        self.display.Hide()
        sizer_5.Add(self.display, 1, wx.EXPAND, 0)
        sizer_11 = wx.FlexGridSizer(5, 1, 0, 0)
        (
            _,
            _,
            self.spin_ctrl_10,
        ) = self.addPrefToPanel(
            self.display,
            sizer_11,
            "Font Size",
            wx.SpinCtrl,
            "Font size. Min: 10 Max: 72",
        )
        self.spin_ctrl_10.SetMin(Globals.MIN_FONT_SIZE)
        self.spin_ctrl_10.SetMax(Globals.MAX_FONT_SIZE)
        self.spin_ctrl_10.SetValue(Globals.FONT_SIZE)

        self.themeChoice = ["Light", "Dark", "System"]
        if platform.system() == "Darwin":
            self.themeChoice = ["System"]
        (
            _,
            _,
            self.combo_theme,
        ) = self.addPrefToPanel(
            self.display,
            sizer_11,
            "Theme",
            wx.ComboBox,
            "Theme of the application.",
            choice=self.themeChoice,
        )
        self.combo_theme.SetSelection(self.themeChoice.index("System"))

        ### Save Options
        self.save = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        self.save.Hide()
        sizer_5.Add(self.save, 1, wx.EXPAND, 0)
        sizer_12 = wx.FlexGridSizer(5, 1, 0, 0)
        (
            _,
            _,
            self.checkbox_15,
        ) = self.addPrefToPanel(
            self.save,
            sizer_12,
            "Save only visible columns",
            wx.CheckBox,
            "When saving to a CSV file, only the columns visible in the Grids will be saved to the file.",
        )

        (
            _,
            _,
            self.checkbox_23,
        ) = self.addPrefToPanel(
            self.save,
            sizer_12,
            "Combine Device And Network Sheets",
            wx.CheckBox,
            "When saving a xlxs file combine the device and network sheets.",
        )
        self.checkbox_23.Set3StateValue(wx.CHK_UNCHECKED if not Globals.INHIBIT_SLEEP else wx.CHK_CHECKED)

        static_line_5 = wx.StaticLine(self.save, wx.ID_ANY)
        sizer_12.Add(
            static_line_5,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.EXPAND | wx.TOP,
            5,
        )

        (
            _,
            _,
            self.spin_ctrl_12,
        ) = self.addPrefToPanel(
            self.save,
            sizer_12,
            "Maximum Split Sheet Size",
            wx.SpinCtrl,
            "Most Spreadsheet programs have issues display large amounts of data."
            + "\nThis preference specifies the max amount of rows saved to a sheet."
            + "\nWill use Spinner value * 1000.\nMax (Default): {:,} -> {:,}\nMin: {:,} -> {:,}".format(
                Globals.MAX_SHEET_CHUNK_SIZE / 1000,
                Globals.MAX_SHEET_CHUNK_SIZE,
                Globals.MIN_SHEET_CHUNK_SIZE / 1000,
                Globals.MIN_SHEET_CHUNK_SIZE,
            ),
        )
        self.spin_ctrl_12.SetMin(int(Globals.MIN_SHEET_CHUNK_SIZE / 1000))
        self.spin_ctrl_12.SetMax(int(Globals.MAX_SHEET_CHUNK_SIZE / 1000))
        self.spin_ctrl_12.SetValue(int(Globals.SHEET_CHUNK_SIZE / 1000))

        ### Command Preferences
        self.command = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        self.command.Hide()
        sizer_5.Add(self.command, 1, wx.EXPAND, 0)

        sizer_14 = wx.FlexGridSizer(7, 1, 0, 0)

        (
            _,
            _,
            self.spin_ctrl_6,
        ) = self.addPrefToPanel(
            self.command,
            sizer_14,
            "Command Timeout (seconds)",
            wx.SpinCtrl,
            "How long a command should wait on the status check before skipping. Min: 0 Max: 100",
        )
        self.spin_ctrl_6.SetMin(0)
        self.spin_ctrl_6.SetMin(100)
        self.spin_ctrl_6.SetValue(Globals.COMMAND_TIMEOUT)

        (
            _,
            _,
            self.checkbox_5,
        ) = self.addPrefToPanel(
            self.command,
            sizer_14,
            "Reach Queued Command State Only",
            wx.CheckBox,
            "Allow the tool to wait until a command has reached the Queued state, don't wait for the other state changes.",
        )

        (
            _,
            _,
            self.combobox_1,
        ) = self.addPrefToPanel(
            self.command,
            sizer_14,
            "Device Type",
            wx.ComboBox,
            "Types of devices that a command should be run on.",
            choice=Globals.CMD_DEVICE_TYPES,
        )
        self.combobox_1.SetSelection(0)

        static_line_1 = wx.StaticLine(self.command, wx.ID_ANY)
        sizer_14.Add(
            static_line_1,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.EXPAND | wx.TOP,
            5,
        )

        ### Command Dialog
        (
            _,
            __file__,
            self.checkbox_12,
        ) = self.addPrefToPanel(
            self.command,
            sizer_14,
            "Use Json Input for Commands",
            wx.CheckBox,
            "Use Json Input for Commands",
        )

        static_line_2 = wx.StaticLine(self.command, wx.ID_ANY)
        sizer_14.Add(
            static_line_2,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.EXPAND | wx.TOP,
            5,
        )

        ### Alias Command Option
        (
            _,
            _,
            self.spin_ctrl_9,
        ) = self.addPrefToPanel(
            self.command,
            sizer_14,
            "Date Delta for Alias Command",
            wx.SpinCtrl,
            "Time difference for when the Alias command schedule should end. Min: %s Max: %s" % (0, Globals.ALIAS_MAX_DAY_DELTA),
        )
        self.spin_ctrl_9.SetMin(0)
        self.spin_ctrl_9.SetMax(Globals.ALIAS_MAX_DAY_DELTA)
        self.spin_ctrl_9.SetValue(Globals.ALIAS_DAY_DELTA)

        ### Grid Preferences
        self.grid = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        self.grid.Hide()
        sizer_5.Add(self.grid, 1, wx.EXPAND, 0)

        sizer_16 = wx.FlexGridSizer(7, 1, 0, 0)

        ### Grid Display
        (
            _,
            _,
            self.checkbox_10,
        ) = self.addPrefToPanel(
            self.grid,
            sizer_16,
            "Allow Column Resizing",
            wx.CheckBox,
            "Allow user to resize grid columns",
        )

        ### App Preferences
        self.app = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        self.app.Hide()
        sizer_5.Add(self.app, 1, wx.EXPAND, 0)

        sizer_9 = wx.FlexGridSizer(8, 1, 0, 0)

        (
            _,
            _,
            self.checkbox_2,
        ) = self.addPrefToPanel(
            self.app,
            sizer_9,
            "Fetch All Installed Apps on Device",
            wx.CheckBox,
            "Fetches all installed applications, including those that are hidden.\nDefault is Enterprise apps only.",
        )

        (
            _,
            _,
            self.checkbox_33,
        ) = self.addPrefToPanel(
            self.app,
            sizer_9,
            "Fetch VPP iOS Apps",
            wx.CheckBox,
            "Fetches VPP iOS Apps allowed on the Tenant.\nDefault is False.",
        )

        static_line_6 = wx.StaticLine(self.app, wx.ID_ANY)
        sizer_9.Add(
            static_line_6,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.EXPAND | wx.TOP,
            5,
        )

        (
            _,
            _,
            self.checkbox_11,
        ) = self.addPrefToPanel(
            self.app,
            sizer_9,
            "Set App State To SHOW before Set Kiosk",
            wx.CheckBox,
            "Set App State to SHOW before setting the application as a Kiosk app on device.",
        )

        static_line_7 = wx.StaticLine(self.app, wx.ID_ANY)
        sizer_9.Add(
            static_line_7,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.EXPAND | wx.TOP,
            5,
        )

        (
            _,
            _,
            self.checkbox_4,
        ) = self.addPrefToPanel(
            self.app,
            sizer_9,
            "Show App's Package Name",
            wx.CheckBox,
            "Displays an Application's Package Name (e.g., In Tags or the Application input)",
        )

        (
            _,
            _,
            self.checkbox_22,
        ) = self.addPrefToPanel(
            self.app,
            sizer_9,
            "Display Version Name Instead of Code",
            wx.CheckBox,
            "Displays the App Version Name instead of the Version Code",
        )

        (
            _,
            _,
            self.btn_appFilter,
        ) = self.addPrefToPanel(
            self.app,
            sizer_9,
            "Filter App Column And Report",
            wx.Button,
            "Filter the Application Column and Report to only show particular applications.",
        )

        ### Schedule Preferences
        self.schedule = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        self.schedule.Hide()
        sizer_5.Add(self.schedule, 1, wx.EXPAND, 0)

        sizer_20 = wx.FlexGridSizer(7, 1, 0, 0)

        (
            _,
            _,
            self.checkbox_26,
        ) = self.addPrefToPanel(
            self.schedule,
            sizer_20,
            "Enable Schedule Report",
            wx.CheckBox,
            "Generates a report at the specified time (if the tool is open) and again some interval later."
            + " If the tool is being used when the scheduled time arrives the report will be delayed until the task is done."
            + " The report will be auto saved at the appointed location. Report will generate a report for the whole endpoint.",
        )

        (
            _,
            _,
            self.btn_save_report,
        ) = self.addPrefToPanel(
            self.schedule,
            sizer_20,
            "Report Location",
            wx.Button,
            "Where the report should be saved.",
        )
        self.btn_save_report.Bind(wx.EVT_BUTTON, self.reportSaveLocation)

        self.reportSaveTypes = ["xlsx", "csv"]
        (
            _,
            _,
            self.reportSaveType,
        ) = self.addPrefToPanel(
            self.schedule,
            sizer_20,
            "Save File Format",
            wx.ComboBox,
            "File type the report should be saved as.",
            choice=self.reportSaveTypes,
        )
        self.reportSaveType.SetSelection(0)

        (
            _,
            _,
            self.reportType,
        ) = self.addPrefToPanel(
            self.schedule,
            sizer_20,
            "Report Type",
            wx.ComboBox,
            "The type of report should be generated at the appointed time. Options: Device, Device & Network, App, All.",
            choice=["Device", "Device & Network", "App", "All"],
        )
        self.reportType.SetSelection(1)

        (
            _,
            _,
            self.spin_ctrl_13,
        ) = self.addPrefToPanel(
            self.schedule,
            sizer_20,
            "Schedule Interval",
            wx.SpinCtrl,
            "Schedule Interval when the report will be regenerated. Interval is in Hours.",
        )
        self.spin_ctrl_13.SetValue(Globals.SCHEDULE_INTERVAL)
        self.spin_ctrl_13.SetMin(Globals.MIN_SCHEDULE_INTERVAL)
        self.spin_ctrl_13.SetMax(Globals.MAX_SCHEDULE_INTERVAL)

        ### Prompts Preferences
        self.prompts = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        self.prompts.Hide()
        sizer_5.Add(self.prompts, 1, wx.EXPAND, 0)

        sizer_19 = wx.FlexGridSizer(4, 1, 0, 0)

        (
            _,
            _,
            self.checkbox_8,
        ) = self.addPrefToPanel(
            self.prompts,
            sizer_19,
            "Grid Confirmation Prompt",
            wx.CheckBox,
            "Grid Confirmation Prompt",
        )

        (
            _,
            _,
            self.checkbox_7,
        ) = self.addPrefToPanel(
            self.prompts,
            sizer_19,
            "Template Confirmation Prompt",
            wx.CheckBox,
            "Template Confirmation Prompt",
        )

        (
            _,
            _,
            self.checkbox_30,
        ) = self.addPrefToPanel(
            self.prompts,
            sizer_19,
            "Show Terms and Conditions",
            wx.CheckBox,
            "Show Terms and Conditions",
        )

        (
            _,
            _,
            self.checkbox_31,
        ) = self.addPrefToPanel(
            self.prompts,
            sizer_19,
            "Show App Filter Dialog",
            wx.CheckBox,
            "Show App Filter Dialog",
        )

        sizer_2 = wx.StdDialogButtonSizer()
        sizer_1.Add(sizer_2, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

        self.button_APPLY = wx.Button(self, wx.ID_APPLY, "")
        self.button_APPLY.Bind(wx.EVT_BUTTON, self.OnApply)
        sizer_2.AddButton(self.button_APPLY)

        sizer_2.Realize()

        sizer_20.AddGrowableCol(0)
        self.schedule.SetSizer(sizer_20)

        sizer_19.AddGrowableCol(0)
        self.prompts.SetSizer(sizer_19)

        sizer_9.AddGrowableCol(0)
        self.app.SetSizer(sizer_9)

        sizer_16.AddGrowableCol(0)
        self.grid.SetSizer(sizer_16)

        sizer_14.AddGrowableCol(0)
        self.command.SetSizer(sizer_14)

        sizer_6.AddGrowableCol(0)
        self.general.SetSizer(sizer_6)

        sizer_10.AddGrowableCol(0)
        self.report.SetSizer(sizer_10)

        sizer_11.AddGrowableCol(0)
        self.display.SetSizer(sizer_11)

        sizer_12.AddGrowableCol(0)
        self.save.SetSizer(sizer_12)

        self.window_1_pane_2.SetSizer(sizer_5)

        self.window_1_pane_1.SetSizer(sizer_4)

        self.window_1.SplitVertically(self.window_1_pane_1, self.window_1_pane_2)

        panel_1.SetSizer(sizer_3)

        self.SetSizer(sizer_1)

        self.Layout()

        self.sections = {
            "General": self.general,
            "Display": self.display,
            "Save": self.save,
            "Application": self.app,
            "Command": self.command,
            "Grid": self.grid,
            "Report": self.report,
            "Schedule": self.schedule,
            "Prompts": self.prompts,
        }
        for key in self.sections.keys():
            self.list_box_1.Append(key)

        self.Bind(wx.EVT_LISTBOX, self.showMatchingPanel, self.list_box_1)
        self.Bind(wx.EVT_SIZE, self.onResize, self)
        self.Bind(wx.EVT_CHAR_HOOK, self.onEscapePressed)
        self.btn_appFilter.Bind(wx.EVT_BUTTON, self.appFilterDlg)

        exitId = wx.NewId()
        self.Bind(wx.EVT_MENU, self.onClose, id=exitId)
        accel_table = wx.AcceleratorTable(
            [
                (wx.ACCEL_CTRL, ord("W"), exitId),
                (wx.ACCEL_CMD, ord("W"), exitId),
            ]
        )
        self.SetAcceleratorTable(accel_table)

        self.Fit()
        self.ready = True

    @api_tool_decorator()
    def onEscapePressed(self, event):
        onDialogEscape(self, event)

    @api_tool_decorator()
    def onClose(self, event):
        if event.EventType != wx.EVT_CLOSE.typeId:
            if self.IsModal():
                self.EndModal(event.EventObject.Id)
            elif self.IsShown():
                self.Close()

    @api_tool_decorator()
    def showMatchingPanel(self, event):
        event.Skip()
        for key, value in self.sections.items():
            if key == event.GetString():
                value.Show()
            else:
                value.Hide()
        self.window_1_pane_2.GetSizer().Layout()
        self.Layout()
        if self.GetSize() == self.size:
            self.Fit()
        self.Refresh()

    @api_tool_decorator()
    def OnApply(self, event):
        self.prefs = {
            "enableDevice": self.checkbox_1.IsChecked(),
            "pullAppleDevices": self.checkbox_32.IsChecked(),
            "limit": self.spin_ctrl_1.GetValue(),
            "gridDialog": self.checkbox_8.IsChecked(),
            "templateDialog": self.checkbox_7.IsChecked(),
            "templateUpdate": self.checkbox_7.IsChecked(),
            "commandTimeout": self.spin_ctrl_6.GetValue(),
            "windowSize": (tuple(self.parent.GetSize()) if self.parent else Globals.MIN_SIZE),
            "windowPosition": (tuple(self.parent.GetPosition()) if self.parent else str(wx.CENTRE)),
            "isMaximized": self.parent.IsMaximized() if self.parent else False,
            "getAllApps": self.checkbox_2.IsChecked(),
            "fetchVPP": self.checkbox_33.IsChecked(),
            "showPkg": self.checkbox_4.IsChecked(),
            "reachQueueStateOnly": self.checkbox_5.IsChecked(),
            "colSize": self.checkbox_10.IsChecked(),
            "setStateShow": self.checkbox_11.IsChecked(),
            "useJsonForCmd": self.checkbox_12.IsChecked(),
            "runCommandOn": self.combobox_1.GetValue(),
            "aliasDayDelta": self.spin_ctrl_9.GetValue(),
            "colVisibility": self.parent.gridPanel.getColVisibility(),
            "fontSize": self.spin_ctrl_10.GetValue(),
            "theme": self.combo_theme.GetValue(),
            "saveColVisibility": self.checkbox_15.IsChecked(),
            "replaceSerial": self.checkbox_17.IsChecked(),
            "showDisabledDevices": self.checkbox_18.IsChecked(),
            "lastSeenAsDate": self.checkbox_19.IsChecked(),
            "appsInDeviceGrid": self.checkbox_20.IsChecked(),
            "inhibitSleep": self.checkbox_21.IsChecked(),
            "appVersionNameInsteadOfCode": self.checkbox_22.IsChecked(),
            "combineDeviceAndNetworkSheets": self.checkbox_23.IsChecked(),
            "showGroupPath": self.checkbox_24.IsChecked(),
            "prereleaseUpdate": self.checkbox_25.IsChecked(),
            "appFilter": self.combobox_2.GetValue(),
            "maxSplitFileSize": self.spin_ctrl_12.GetValue(),
            "appColFilter": self.appColFilter,
            "scheduleSaveLocation": self.file_location,
            "scheduleSaveType": self.reportSaveType.GetValue(),
            "scheduleEnabled": self.checkbox_26.IsChecked(),
            "scheduleReportType": self.reportType.GetValue(),
            "scheduleInterval": self.spin_ctrl_13.GetValue(),
            "showDisclaimer": self.checkbox_30.IsChecked(),
            "showAppFilter": self.checkbox_31.IsChecked(),
            "getTemplateLanguage": self.checkbox_29.IsChecked(),
        }

        Globals.THEME = self.prefs["theme"]
        Globals.PULL_APPLE_DEVICES = self.prefs["pullAppleDevices"]
        Globals.FONT_SIZE = int(self.prefs["fontSize"])
        Globals.HEADER_FONT_SIZE = Globals.FONT_SIZE + 7
        Globals.SET_APP_STATE_AS_SHOW = self.prefs["setStateShow"]
        Globals.SHOW_GRID_DIALOG = self.prefs["gridDialog"]
        Globals.SHOW_TEMPLATE_UPDATE = self.prefs["templateDialog"]
        Globals.SHOW_TEMPLATE_DIALOG = self.prefs["templateUpdate"]
        Globals.REACH_QUEUED_ONLY = self.prefs["reachQueueStateOnly"]
        Globals.SHOW_PKG_NAME = self.prefs["showPkg"]
        Globals.limit = self.prefs["limit"]
        Globals.COMMAND_TIMEOUT = int(self.prefs["commandTimeout"])
        Globals.COMMAND_JSON_INPUT = self.checkbox_12.IsChecked()
        Globals.CMD_DEVICE_TYPE = self.combobox_1.GetValue().lower()
        Globals.ALIAS_DAY_DELTA = self.prefs["aliasDayDelta"]
        Globals.SAVE_VISIBILITY = self.prefs["saveColVisibility"]
        Globals.REPLACE_SERIAL = self.prefs["replaceSerial"]
        Globals.SHOW_DISABLED_DEVICES = self.prefs["showDisabledDevices"]
        Globals.LAST_SEEN_AS_DATE = self.prefs["lastSeenAsDate"]
        Globals.APPS_IN_DEVICE_GRID = self.prefs["appsInDeviceGrid"]
        Globals.INHIBIT_SLEEP = self.prefs["inhibitSleep"]
        Globals.VERSON_NAME_INSTEAD_OF_CODE = self.prefs["appVersionNameInsteadOfCode"]
        Globals.COMBINE_DEVICE_AND_NETWORK_SHEETS = self.prefs["combineDeviceAndNetworkSheets"]
        Globals.SHOW_GROUP_PATH = self.prefs["showGroupPath"]
        Globals.CHECK_PRERELEASES = self.prefs["prereleaseUpdate"]
        Globals.APP_FILTER = self.combobox_2.GetValue().lower()
        Globals.SHEET_CHUNK_SIZE = int(self.prefs["maxSplitFileSize"]) * 1000
        if Globals.SHEET_CHUNK_SIZE < Globals.MIN_SHEET_CHUNK_SIZE:
            Globals.SHEET_CHUNK_SIZE = Globals.MIN_SHEET_CHUNK_SIZE
        elif Globals.SHEET_CHUNK_SIZE > Globals.MAX_SHEET_CHUNK_SIZE:
            Globals.SHEET_CHUNK_SIZE = Globals.MAX_SHEET_CHUNK_SIZE
        Globals.APP_COL_FILTER = self.appColFilter
        Globals.SHOW_DISCLAIMER = self.prefs["showDisclaimer"]
        Globals.SHOW_APP_FILTER_DIALOG = self.prefs["showAppFilter"]
        Globals.GET_DEVICE_LANGUAGE = self.prefs["getTemplateLanguage"]

        Globals.SCHEDULE_ENABLED = self.prefs["scheduleEnabled"]
        Globals.SCHEDULE_INTERVAL = self.prefs["scheduleInterval"]
        Globals.SCHEDULE_LOCATION = self.prefs["scheduleSaveLocation"]
        Globals.SCHEDULE_SAVE = self.prefs["scheduleSaveType"]
        Globals.SCHEDULE_TYPE = self.prefs["scheduleReportType"]
        Globals.FETCH_VPP = self.prefs["fetchVPP"]

        if self.prefs["getAllApps"]:
            Globals.USE_ENTERPRISE_APP = False
        else:
            Globals.USE_ENTERPRISE_APP = True

        if self.parent:
            if self.checkbox_10.IsChecked():
                self.parent.gridPanel.enableGridProperties(True, True, False)
            else:
                self.parent.gridPanel.disableGridProperties(False, False, True)

        if event and self.IsModal():
            self.EndModal(event.EventObject.Id)
        elif self.IsShown():
            self.Close()

    @api_tool_decorator()
    def SetPrefs(self, prefs, onBoot=True):
        if not self.ready:
            wx.CallLater(100, self.SetPrefs, prefs, onBoot)
            return

        if uiThreadCheck(self.SetPrefs, prefs, onBoot):
            return

        self.prefs = prefs
        if not self.prefs:
            return

        screenSize = wx.DisplaySize()

        if "pullAppleDevices" in self.prefs:
            self.checkbox_32.SetValue(self.prefs["pullAppleDevices"])
            Globals.PULL_APPLE_DEVICES = self.prefs["pullAppleDevices"]
        else:
            self.checkbox_32.Set3StateValue(wx.CHK_CHECKED)

        if "templateDialog" in self.prefs and type(self.prefs["templateDialog"]) == bool:
            Globals.SHOW_TEMPLATE_DIALOG = self.prefs["templateDialog"]

        if "templateUpdate" in self.prefs and type(self.prefs["templateUpdate"]) == bool:
            Globals.SHOW_TEMPLATE_UPDATE = self.prefs["templateUpdate"]

        state = wx.CHK_CHECKED if Globals.SHOW_TEMPLATE_UPDATE and Globals.SHOW_TEMPLATE_DIALOG else wx.CHK_UNCHECKED
        self.checkbox_7.Set3StateValue(state)

        if "windowSize" in self.prefs and self.prefs["windowSize"] and onBoot:
            if self.parent:
                size = Globals.MIN_SIZE
                try:
                    size = tuple(
                        int(num)
                        for num in self.prefs["windowSize"].replace("(", "").replace(")", "").replace("...", "").split(", ")
                    )
                except:
                    sizes = tuple(int(num) for num in self.prefs["windowSize"])
                    size = (sizes[0], sizes[1])
                if size[0] < Globals.MIN_SIZE[0]:
                    size = (Globals.MIN_SIZE[0], size[1])
                if size[1] < Globals.MIN_SIZE[1]:
                    size = (size[0], Globals.MIN_SIZE[1])
                # ensure we don't exceed the screen size
                if size[0] > screenSize[0]:
                    size = (screenSize[0], size[1])
                if size[1] > screenSize[1]:
                    size = (size[0], screenSize[1])
                self.parent.SetSize(size)

        if "isMaximized" in self.prefs and isinstance(self.prefs["isMaximized"], bool) and onBoot and self.parent:
            self.parent.Maximize(self.prefs["isMaximized"])

        if "windowPosition" in self.prefs and self.prefs["windowPosition"] and onBoot:
            if self.parent:
                if self.prefs["windowPosition"] == "1":
                    self.parent.Centre()
                else:
                    if not self.parent.IsMaximized():
                        pos = tuple(self.prefs["windowPosition"])
                        if pos[0] > screenSize[0] or pos[1] > screenSize[1] or pos[0] < 0 or pos[1] < 0:
                            pos = (0, 0)
                        self.parent.SetPosition(wx.Point(pos[0], pos[1]))

        if "theme" in self.prefs:
            val = self.prefs["theme"]
            if val in self.themeChoice:
                self.combo_theme.SetSelection(self.themeChoice.index(val))
                Globals.THEME = self.prefs["theme"]
            else:
                self.combo_theme.SetSelection(self.themeChoice.index("System"))
                Globals.THEME = "System"
        if self.Parent and hasattr(self.Parent, "onThemeChange"):
            self.Parent.onThemeChange(None)

        self.colVisibilty = []
        if "colVisibility" in self.prefs:
            self.colVisibilty = self.prefs["colVisibility"]
            if self.prefs["colVisibility"]:
                self.parent.gridPanel.grid1ColVisibility = self.prefs["colVisibility"][0]
            if self.prefs["colVisibility"] and len(self.prefs["colVisibility"]) > 1:
                self.parent.gridPanel.grid2ColVisibility = self.prefs["colVisibility"][1]

        if "last_endpoint" in self.prefs and self.prefs["last_endpoint"]:
            Globals.LAST_OPENED_ENDPOINT = self.prefs["last_endpoint"]
        else:
            Globals.LAST_OPENED_ENDPOINT = 0

        if "appColFilter" in self.prefs and type(self.prefs["appColFilter"]) is list:
            Globals.APP_COL_FILTER = self.prefs["appColFilter"]

        if "scheduleSaveLocation" in self.prefs and self.prefs["scheduleSaveLocation"]:
            self.file_location = self.prefs["scheduleSaveLocation"]
            Globals.SCHEDULE_LOCATION = self.prefs["scheduleSaveLocation"]
        else:
            self.file_location = Globals.SCHEDULE_LOCATION

        if "scheduleSaveType" in self.prefs and self.prefs["scheduleSaveType"]:
            Globals.SCHEDULE_SAVE = self.prefs["scheduleSaveType"]
            self.reportSaveType.SetSelection(self.reportSaveTypes.index(Globals.SCHEDULE_SAVE))

        # Set Checkbox Values
        self.checkBooleanValuePrefAndSet("enableDevice", self.checkbox_1, wx.CHK_UNCHECKED)
        Globals.USE_ENTERPRISE_APP = self.checkBooleanValuePrefAndSet("getAllApps", self.checkbox_2, wx.CHK_UNCHECKED)
        Globals.SHOW_PKG_NAME = self.checkBooleanValuePrefAndSet("showPkg", self.checkbox_4, wx.CHK_CHECKED)
        Globals.REACH_QUEUED_ONLY = self.checkBooleanValuePrefAndSet("reachQueueStateOnly", self.checkbox_5, wx.CHK_CHECKED)
        Globals.SHOW_GRID_DIALOG = self.checkBooleanValuePrefAndSet("getgridDialogAllApps", self.checkbox_8, wx.CHK_UNCHECKED)
        Globals.SET_APP_STATE_AS_SHOW = self.checkBooleanValuePrefAndSet("setStateShow", self.checkbox_11, wx.CHK_UNCHECKED)
        Globals.COMMAND_JSON_INPUT = self.checkBooleanValuePrefAndSet("useJsonForCmd", self.checkbox_12, wx.CHK_CHECKED)
        Globals.SAVE_VISIBILITY = self.checkBooleanValuePrefAndSet("saveColVisibility", self.checkbox_16, wx.CHK_UNCHECKED)
        Globals.REPLACE_SERIAL = self.checkBooleanValuePrefAndSet("replaceSerial", self.checkbox_17)
        Globals.SHOW_DISABLED_DEVICES = self.checkBooleanValuePrefAndSet(
            "showDisabledDevices", self.checkbox_18, wx.CHK_UNCHECKED
        )
        Globals.LAST_SEEN_AS_DATE = self.checkBooleanValuePrefAndSet("lastSeenAsDate", self.checkbox_19, wx.CHK_CHECKED)
        Globals.APPS_IN_DEVICE_GRID = self.checkBooleanValuePrefAndSet("appsInDeviceGrid", self.checkbox_20, wx.CHK_CHECKED)
        Globals.INHIBIT_SLEEP = self.checkBooleanValuePrefAndSet("inhibitSleep", self.checkbox_21)
        Globals.VERSON_NAME_INSTEAD_OF_CODE = self.checkBooleanValuePrefAndSet("appVersionNameInsteadOfCode", self.checkbox_22)
        Globals.COMBINE_DEVICE_AND_NETWORK_SHEETS = self.checkBooleanValuePrefAndSet(
            "combineDeviceAndNetworkSheets", self.checkbox_23
        )
        Globals.SHOW_GROUP_PATH = self.checkBooleanValuePrefAndSet("showGroupPath", self.checkbox_24)
        Globals.CHECK_PRERELEASES = self.checkBooleanValuePrefAndSet("prereleaseUpdate", self.checkbox_25)
        Globals.SCHEDULE_ENABLED = self.checkBooleanValuePrefAndSet("scheduleEnabled", self.checkbox_26)
        Globals.GET_DEVICE_LANGUAGE = self.checkBooleanValuePrefAndSet("getTemplateLanguage", self.checkbox_29)
        Globals.SHOW_DISCLAIMER = self.checkBooleanValuePrefAndSet("showDisclaimer", self.checkbox_30, wx.CHK_UNCHECKED)
        Globals.SHOW_APP_FILTER_DIALOG = self.checkBooleanValuePrefAndSet("showAppFilter", self.checkbox_31, wx.CHK_CHECKED)
        Globals.FETCH_VPP = self.checkBooleanValuePrefAndSet("fetchVPP", self.checkbox_33, wx.CHK_UNCHECKED)

        # Set Combobox values
        Globals.SCHEDULE_TYPE = self.checkStringValPrefAndSet(
            "scheduleReportType", self.reportType, self.prefs["scheduleReportType"]
        ).lower()
        Globals.APP_FILTER = self.checkStringValPrefAndSet(
            "appFilter", self.combobox_2, self.prefs["appFilter"], isValueUpper=True
        )
        Globals.CMD_DEVICE_TYPE = self.checkStringValPrefAndSet(
            "runCommandOn",
            self.combobox_1,
            self.prefs["runCommandOn"],
            isValCapital=True,
        ).lower()

        # Set SpinCtrl values
        Globals.SCHEDULE_INTERVAL = self.checkNumberValPrefAndSet(
            "scheduleInterval",
            self.spin_ctrl_13,
            Globals.SCHEDULE_INTERVAL,
            Globals.MIN_SCHEDULE_INTERVAL,
            Globals.MAX_SCHEDULE_INTERVAL,
        )
        Globals.limit = self.checkNumberValPrefAndSet(
            "limit",
            self.spin_ctrl_1,
            Globals.limit,
            Globals.MIN_LIMIT,
            Globals.MAX_LIMIT,
        )
        Globals.COMMAND_TIMEOUT = self.checkNumberValPrefAndSet(
            "commandTimeout", self.spin_ctrl_6, Globals.COMMAND_TIMEOUT, 0, 100
        )
        Globals.FONT_SIZE = self.checkNumberValPrefAndSet(
            "fontSize",
            self.spin_ctrl_10,
            Globals.FONT_SIZE,
            Globals.MIN_FONT_SIZE,
            Globals.MAX_FONT_SIZE,
        )
        Globals.SHEET_CHUNK_SIZE = (
            self.checkNumberValPrefAndSet(
                "maxSplitFileSize",
                self.spin_ctrl_12,
                Globals.SHEET_CHUNK_SIZE / 1000,
                Globals.MIN_SHEET_CHUNK_SIZE / 1000,
                Globals.MAX_SHEET_CHUNK_SIZE / 1000,
            )
            * 1000
        )
        Globals.ALIAS_DAY_DELTA = self.checkNumberValPrefAndSet(
            "aliasDayDelta",
            self.spin_ctrl_9,
            Globals.ALIAS_DAY_DELTA,
            0,
            Globals.ALIAS_MAX_DAY_DELTA,
        )

    def checkStringValPrefAndSet(self, key, combobox, default, isValueUpper=False, isValCapital=False) -> str:
        if key in self.prefs and self.prefs[key]:
            if isinstance(self.prefs[key], str):
                val = self.prefs[key].strip()
                if isValueUpper:
                    val = val.upper()
                if isValCapital:
                    val = val.capitalize()
                if val in combobox.Items:
                    indx = combobox.GetItems().index(val)
                    combobox.SetSelection(indx)
                elif default and default in combobox.Items():
                    combobox.SetTextSelection(default)
                elif len(combobox.Items) > 0:
                    combobox.SetSelection(0)
            elif type(self.prefs[key]) == int:
                combobox.SetSelection(self.prefs[key])
            elif default and default in combobox.Items():
                combobox.SetTextSelection(default)
            elif len(combobox.Items) > 0:
                combobox.SetSelection(0)
        return combobox.GetValue()

    def checkBooleanValuePrefAndSet(self, key, checkbox, default=wx.CHK_UNCHECKED):
        isEnabled = default
        if key in self.prefs:
            if (isinstance(self.prefs[key], str) and self.prefs[key].lower() == "true") or self.prefs[key] is True:
                checkbox.Set3StateValue(wx.CHK_CHECKED)
                isEnabled = True
            else:
                checkbox.Set3StateValue(wx.CHK_UNCHECKED)
                isEnabled = False
        else:
            if default == wx.CHK_UNCHECKED:
                checkbox.Set3StateValue(wx.CHK_UNCHECKED)
                isEnabled = False
            else:
                checkbox.Set3StateValue(wx.CHK_CHECKED)
                isEnabled = True

        return isEnabled

    def checkNumberValPrefAndSet(self, key, spinCtrl, default=0, min=0, max=None) -> int:
        if key in self.prefs and self.prefs[key]:
            try:
                val = int(self.prefs[key])
                if val < min:
                    val = min
                elif max and val > max:
                    val = max
                spinCtrl.SetValue(int(val))
            except ValueError:
                spinCtrl.SetValue(default)
        else:
            spinCtrl.SetValue(default)
        return spinCtrl.GetValue()

    @api_tool_decorator()
    def GetPrefs(self):
        if not self.prefs:
            self.prefs = {}

        self.prefs["windowPosition"] = self.getDefaultKeyValue("windowPosition")
        self.prefs["windowSize"] = self.getDefaultKeyValue("windowSize")
        self.prefs["isMaximized"] = self.getDefaultKeyValue("isMaximized")

        for key in self.prefKeys:
            defaultVal = self.getDefaultKeyValue(key)
            if key not in self.prefs or self.prefs[key] is None:
                self.prefs[key] = defaultVal

        return self.prefs

    @api_tool_decorator()
    def SetPref(self, pref, value):
        if self.prefs:
            self.prefs[pref] = value

    @api_tool_decorator()
    def getDefaultKeyValue(self, key):
        if key == "enableDevice":
            return True
        if key == "pullAppleDevices":
            return Globals.PULL_APPLE_DEVICES
        elif key == "limit":
            return Globals.MAX_LIMIT
        elif key == "gridDialog":
            return Globals.SHOW_GRID_DIALOG
        elif key == "templateDialog":
            return Globals.SHOW_TEMPLATE_DIALOG
        elif key == "templateUpdate":
            return Globals.SHOW_TEMPLATE_UPDATE
        elif key == "commandTimeout":
            return Globals.COMMAND_TIMEOUT
        elif key == "windowSize":
            return tuple(self.parent.GetSize()) if self.parent else Globals.MIN_SIZE
        elif key == "isMaximized":
            return self.parent.IsMaximized() if self.parent else False
        elif key == "windowPosition":
            return tuple(self.parent.GetPosition()) if self.parent else str(wx.CENTRE)
        elif key == "getAllApps":
            return Globals.USE_ENTERPRISE_APP
        elif key == "showPkg":
            return Globals.SHOW_PKG_NAME
        elif key == "reachQueueStateOnly":
            return Globals.REACH_QUEUED_ONLY
        elif key == "colSize":
            return True
        elif key == "setStateShow":
            return Globals.SET_APP_STATE_AS_SHOW
        elif key == "useJsonForCmd":
            return Globals.COMMAND_JSON_INPUT
        elif key == "runCommandOn":
            return Globals.CMD_DEVICE_TYPE
        elif key == "aliasDayDelta":
            return Globals.ALIAS_DAY_DELTA
        elif key == "fontSize":
            return Globals.FONT_SIZE
        elif key == "theme":
            return Globals.THEME
        elif key == "saveColVisibility":
            return Globals.SAVE_VISIBILITY
        elif key == "replaceSerial":
            return Globals.REPLACE_SERIAL
        elif key == "showDisabledDevices":
            return Globals.SHOW_DISABLED_DEVICES
        elif key == "lastSeenAsDate":
            return Globals.LAST_SEEN_AS_DATE
        elif key == "appsInDeviceGrid":
            return Globals.APPS_IN_DEVICE_GRID
        elif key == "inhibitSleep":
            return Globals.INHIBIT_SLEEP
        elif key == "appVersionNameInsteadOfCode":
            return Globals.VERSON_NAME_INSTEAD_OF_CODE
        elif key == "combineDeviceAndNetworkSheets":
            return Globals.COMBINE_DEVICE_AND_NETWORK_SHEETS
        elif key == "showGroupPath":
            return Globals.SHOW_GROUP_PATH
        elif key == "last_endpoint":
            return Globals.LAST_OPENED_ENDPOINT
        elif key == "appFilter":
            return Globals.APP_FILTER
        elif key == "maxSplitFileSize":
            return Globals.SHEET_CHUNK_SIZE
        elif key == "appColFilter":
            return Globals.APP_COL_FILTER
        elif key == "scheduleSaveLocation":
            return Globals.SCHEDULE_LOCATION
        elif key == "scheduleSaveType":
            return Globals.SCHEDULE_SAVE
        elif key == "scheduleEnabled":
            return Globals.SCHEDULE_ENABLED
        elif key == "scheduleReportType":
            return Globals.SCHEDULE_TYPE
        elif key == "scheduleInterval":
            return Globals.SCHEDULE_INTERVAL
        elif key == "showDisclaimer":
            return Globals.SHOW_DISCLAIMER
        elif key == "showAppFilter":
            return Globals.SHOW_APP_FILTER_DIALOG
        elif key == "getTemplateLanguage":
            return Globals.GET_DEVICE_LANGUAGE
        elif key == "fetchVPP":
            return Globals.FETCH_VPP
        else:
            return None

    def onResize(self, event):
        self.Refresh()
        event.Skip()

    def addPrefToPanel(
        self,
        sourcePanel,
        sourceSizer,
        labelText,
        inputObjType,
        toolTip="",
        choice=[],
    ):
        panel = wx.Panel(sourcePanel, wx.ID_ANY)
        if sourceSizer.GetEffectiveRowsCount() >= sourceSizer.GetRows():
            sourceSizer.SetRows(sourceSizer.GetRows() + 1)
        sourceSizer.Add(panel, 1, wx.ALL | wx.EXPAND, 5)

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(
            panel,
            wx.ID_ANY,
            labelText,
            style=wx.ST_ELLIPSIZE_END,
        )
        label.SetToolTip(toolTip)
        currentFont = label.GetFont()
        wxFont = getFont(FontStyles.NORMAL.value)
        label.SetFont(wxFont)
        sizer.Add(label, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        panel_2 = wx.Panel(panel, wx.ID_ANY)
        sizer.Add(panel_2, 1, wx.EXPAND, 0)

        grid_sizer = wx.GridSizer(1, 1, 0, 0)

        inputObj = None
        if inputObjType == wx.CheckBox:
            inputObj = wx.CheckBox(panel_2, wx.ID_ANY, "")
        elif inputObjType == wx.SpinCtrl:
            inputObj = wx.SpinCtrl(panel_2, wx.ID_ANY)
        elif inputObjType == wx.ComboBox:
            inputObj = wx.ComboBox(
                panel_2,
                wx.ID_ANY,
                choices=choice,
                style=wx.CB_DROPDOWN | wx.CB_READONLY,
            )
        elif inputObjType == wx.Button:
            inputObj = wx.Button(panel_2, id=wx.ID_ANY, label=labelText)
        elif inputObjType == wxadv.TimePickerCtrl:
            inputObj = wxadv.TimePickerCtrl(panel_2, id=wx.ID_ANY)
        if inputObj:
            inputObj.SetToolTip(toolTip)
            grid_sizer.Add(inputObj, 0, wx.ALIGN_RIGHT | wx.EXPAND, 0)

        if hasattr(inputObj, "SetFont"):
            inputObj.SetFont(wxFont)

        panel.SetSizer(sizer)
        panel_2.SetSizer(grid_sizer)

        return panel, panel_2, inputObj

    def appFilterDlg(self, event):
        with LargeTextEntryDialog(
            Globals.frame,
            "Enter the package names, in a comma seperated format, of the applications you want to appear in the Application column",
            "App Column Filter",
            textPlaceHolder=(
                ",".join(self.appColFilter)
                if self.appColFilter
                else (",".join(Globals.APP_COL_FILTER) if Globals.APP_COL_FILTER else "")
            ),
        ) as textDialog:
            Globals.OPEN_DIALOGS.append(textDialog)
            if textDialog.ShowModal() == wx.ID_OK:
                appList = textDialog.GetValue()
                splitList = appList.split(",")
                properAppList = []
                for app in splitList:
                    cleanPkgName = app.strip()
                    if cleanPkgName:
                        properAppList.append(cleanPkgName)
                self.appColFilter = properAppList
            Globals.OPEN_DIALOGS.remove(textDialog)

    def reportSaveLocation(self, event):
        dlg = wx.DirDialog(
            self,
            message="Report Save Location and File Type",
            defaultPath=str(self.file_location),
        )
        Globals.OPEN_DIALOGS.append(dlg)
        result = dlg.ShowModal()
        Globals.OPEN_DIALOGS.remove(dlg)
        if result == wx.ID_OK:
            self.file_location = dlg.GetPath()
