#!/usr/bin/env python

from Common.decorator import api_tool_decorator
import Common.Globals as Globals
import wx


class PreferencesDialog(wx.Dialog):
    def __init__(self, prefDict, parent=None):
        super(PreferencesDialog, self).__init__(
            None,
            wx.ID_ANY,
            size=(525, 400),
            style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP | wx.RESIZE_BORDER,
        )
        self.SetTitle("Preferences")
        self.SetSize((525, 400))
        self.SetMinSize((525, 400))

        self.parent = parent
        self.prefs = prefDict
        self.prefKeys = [
            "enableDevice",
            "limit",
            "offset",
            "gridDialog",
            "updateRate",
            "enableGridUpdate",
            "windowSize",
            "windowPosition",
            "isMaximized",
            "getAllApps",
            "showPkg",
            "reachQueueStateOnly",
            "getAppsForEachDevice",
            "gridDialog",
            "templateDialog",
            "templateUpdate",
            "colSize",
            "setStateShow",
            "useJsonForCmd",
            "runCommandOn",
            "maxThread",
        ]

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_1, 1, wx.ALL | wx.EXPAND, 5)

        sizer_3 = wx.BoxSizer(wx.VERTICAL)

        self.window_1 = wx.SplitterWindow(self.panel_1, wx.ID_ANY)
        self.window_1.SetMinimumPaneSize(20)
        sizer_3.Add(self.window_1, 1, wx.EXPAND, 0)

        self.window_1_pane_1 = wx.Panel(self.window_1, wx.ID_ANY)

        sizer_4 = wx.GridSizer(1, 1, 0, 0)

        self.list_box_1 = wx.ListBox(
            self.window_1_pane_1,
            wx.ID_ANY,
            choices=["General", "Grid", "Application", "Command", "Prompts"],
            style=wx.LB_NEEDED_SB | wx.LB_SINGLE,
        )
        sizer_4.Add(self.list_box_1, 0, wx.EXPAND, 5)

        self.window_1_pane_2 = wx.ScrolledWindow(
            self.window_1, wx.ID_ANY, style=wx.BORDER_SIMPLE | wx.TAB_TRAVERSAL
        )
        self.window_1_pane_2.SetScrollRate(10, 10)

        sizer_5 = wx.BoxSizer(wx.VERTICAL)

        # General Preferences
        self.general = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        self.general.Hide()
        sizer_5.Add(self.general, 1, wx.EXPAND, 0)

        sizer_6 = wx.FlexGridSizer(4, 1, 0, 0)

        self.panel_3 = wx.Panel(self.general, wx.ID_ANY)
        sizer_6.Add(self.panel_3, 1, wx.ALL | wx.EXPAND, 5)

        sizer_7 = wx.BoxSizer(wx.HORIZONTAL)

        label_1 = wx.StaticText(
            self.panel_3,
            wx.ID_ANY,
            "Enable Device Selection",
            style=wx.ST_ELLIPSIZE_END,
        )
        label_1.SetToolTip(
            "Allow user to specify actions on a selections of devices within a group."
        )
        sizer_7.Add(label_1, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.panel_4 = wx.Panel(self.panel_3, wx.ID_ANY)
        sizer_7.Add(self.panel_4, 1, wx.EXPAND, 0)

        grid_sizer_1 = wx.GridSizer(1, 1, 0, 0)

        self.checkbox_1 = wx.CheckBox(self.panel_4, wx.ID_ANY, "")
        grid_sizer_1.Add(self.checkbox_1, 0, wx.ALIGN_RIGHT | wx.EXPAND, 0)

        self.panel_5 = wx.Panel(self.general, wx.ID_ANY)
        sizer_6.Add(self.panel_5, 1, wx.ALL | wx.EXPAND, 5)

        sizer_8 = wx.BoxSizer(wx.HORIZONTAL)

        label_2 = wx.StaticText(
            self.panel_5,
            wx.ID_ANY,
            "API Request Limit",
            style=wx.ST_ELLIPSIZE_END,
        )
        label_2.SetToolTip("Maximum amount of results that the API will return.")
        sizer_8.Add(label_2, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.panel_6 = wx.Panel(self.panel_5, wx.ID_ANY)
        sizer_8.Add(self.panel_6, 1, wx.EXPAND, 0)

        grid_sizer_2 = wx.GridSizer(1, 1, 0, 0)

        self.spin_ctrl_1 = wx.SpinCtrl(
            self.panel_6,
            wx.ID_ANY,
            min=Globals.MIN_LIMIT,
            max=Globals.MAX_LIMIT,
            initial=Globals.limit,
        )
        grid_sizer_2.Add(
            self.spin_ctrl_1, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0
        )

        self.panel_9 = wx.Panel(self.general, wx.ID_ANY)
        sizer_6.Add(self.panel_9, 1, wx.ALL | wx.EXPAND, 5)

        sizer_10 = wx.BoxSizer(wx.HORIZONTAL)

        label_4 = wx.StaticText(
            self.panel_9,
            wx.ID_ANY,
            "API Request Offset",
            style=wx.ST_ELLIPSIZE_END,
        )
        label_4.SetToolTip("Page of results the API sends back (starts at 0)")
        sizer_10.Add(label_4, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.panel_10 = wx.Panel(self.panel_9, wx.ID_ANY)
        sizer_10.Add(self.panel_10, 1, wx.EXPAND, 0)

        grid_sizer_4 = wx.GridSizer(1, 1, 0, 0)

        self.spin_ctrl_2 = wx.SpinCtrl(
            self.panel_10, wx.ID_ANY, min=0, initial=Globals.offset
        )
        grid_sizer_4.Add(
            self.spin_ctrl_2, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0
        )

        self.panel_43 = wx.Panel(self.general, wx.ID_ANY)
        sizer_6.Add(self.panel_43, 1, wx.ALL | wx.EXPAND, 5)

        sizer_30 = wx.BoxSizer(wx.HORIZONTAL)
        self.panel_43.SetSizer(sizer_30)

        label_1 = wx.StaticText(
            self.panel_43,
            wx.ID_ANY,
            "Max Threads",
            style=wx.ST_ELLIPSIZE_END,
        )
        label_1.SetToolTip(
            "Maximum number of threads that will be created to perform an action."
        )
        sizer_30.Add(label_1, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.panel_44 = wx.Panel(self.panel_43, wx.ID_ANY)
        sizer_30.Add(self.panel_44, 1, wx.EXPAND, 0)

        grid_sizer_21 = wx.GridSizer(1, 1, 0, 0)
        self.panel_44.SetSizer(grid_sizer_21)

        self.spin_ctrl_8 = wx.SpinCtrl(
            self.panel_44, wx.ID_ANY, min=10, max=100, initial=Globals.MAX_THREAD_COUNT
        )
        grid_sizer_21.Add(self.spin_ctrl_8, 0, wx.ALIGN_RIGHT | wx.EXPAND, 0)

        # Command Preferences
        self.command = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        self.command.Hide()
        sizer_5.Add(self.command, 1, wx.EXPAND, 0)

        sizer_14 = wx.FlexGridSizer(4, 1, 0, 0)

        self.panel_25 = wx.Panel(self.command, wx.ID_ANY)
        sizer_14.Add(self.panel_25, 1, wx.ALL | wx.EXPAND, 5)

        sizer_21 = wx.BoxSizer(wx.HORIZONTAL)

        label_12 = wx.StaticText(
            self.panel_25,
            wx.ID_ANY,
            "Command Timeout (seconds)",
            style=wx.ST_ELLIPSIZE_END,
        )
        label_12.SetToolTip(
            "How long a command should wait on the status check before skipping."
        )
        sizer_21.Add(label_12, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.panel_26 = wx.Panel(self.panel_25, wx.ID_ANY)
        sizer_21.Add(self.panel_26, 1, wx.EXPAND, 0)

        grid_sizer_12 = wx.GridSizer(1, 1, 0, 0)

        self.spin_ctrl_6 = wx.SpinCtrl(
            self.panel_26, wx.ID_ANY, min=0, initial=Globals.COMMAND_TIMEOUT
        )
        grid_sizer_12.Add(
            self.spin_ctrl_6, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0
        )

        self.panel_27 = wx.Panel(self.command, wx.ID_ANY)
        sizer_14.Add(self.panel_27, 1, wx.ALL | wx.EXPAND, 5)

        sizer_22 = wx.BoxSizer(wx.HORIZONTAL)

        label_13 = wx.StaticText(
            self.panel_27,
            wx.ID_ANY,
            "Reach Queued Command State Only",
            style=wx.ST_ELLIPSIZE_END,
        )
        label_13.SetToolTip(
            "Allow the tool to wait until a command has reached the Queued state, don't wait for the other state changes."
        )
        sizer_22.Add(label_13, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.panel_28 = wx.Panel(self.panel_27, wx.ID_ANY)
        sizer_22.Add(self.panel_28, 1, wx.EXPAND, 0)

        grid_sizer_13 = wx.GridSizer(1, 1, 0, 0)

        self.checkbox_5 = wx.CheckBox(self.panel_28, wx.ID_ANY, "")
        grid_sizer_13.Add(
            self.checkbox_5, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0
        )

        self.panel_39 = wx.Panel(self.command, wx.ID_ANY)
        sizer_14.Add(self.panel_39, 1, wx.ALL | wx.EXPAND, 5)

        sizer_28 = wx.BoxSizer(wx.HORIZONTAL)
        self.panel_39.SetSizer(sizer_28)

        label_17 = wx.StaticText(
            self.panel_39,
            wx.ID_ANY,
            "Use Json Input for Commands",
            style=wx.ST_ELLIPSIZE_END,
        )
        sizer_28.Add(label_17, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.panel_40 = wx.Panel(self.panel_39, wx.ID_ANY)
        sizer_28.Add(self.panel_40, 1, wx.EXPAND, 0)

        grid_sizer_19 = wx.GridSizer(1, 1, 0, 0)
        self.panel_40.SetSizer(grid_sizer_19)

        self.checkbox_12 = wx.CheckBox(self.panel_40, wx.ID_ANY, "")
        grid_sizer_19.Add(
            self.checkbox_12, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0
        )

        self.panel_41 = wx.Panel(self.command, wx.ID_ANY)
        sizer_14.Add(self.panel_41, 1, wx.ALL | wx.EXPAND, 5)

        sizer_29 = wx.BoxSizer(wx.HORIZONTAL)
        self.panel_41.SetSizer(sizer_29)

        label_18 = wx.StaticText(
            self.panel_41,
            wx.ID_ANY,
            "Device Type",
            style=wx.ST_ELLIPSIZE_END,
        )
        label_18.SetToolTip("Types of devices that a command should be run on.")
        sizer_29.Add(label_18, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.panel_42 = wx.Panel(self.panel_41, wx.ID_ANY)
        sizer_29.Add(self.panel_42, 1, wx.EXPAND, 0)

        grid_sizer_20 = wx.GridSizer(1, 1, 0, 0)
        self.panel_42.SetSizer(grid_sizer_20)

        self.combobox_1 = wx.ComboBox(
            self.panel_42,
            wx.ID_ANY,
            choices=Globals.CMD_DEVICE_TYPES,
            style=wx.CB_DROPDOWN | wx.CB_READONLY,
        )
        self.combobox_1.SetSelection(0)
        grid_sizer_20.Add(
            self.combobox_1, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0
        )

        # Grid Preferences
        self.grid = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        self.grid.Hide()
        sizer_5.Add(self.grid, 1, wx.EXPAND, 0)

        sizer_16 = wx.FlexGridSizer(4, 1, 0, 0)

        self.panel_19 = wx.Panel(self.grid, wx.ID_ANY)
        sizer_16.Add(self.panel_19, 1, wx.ALL | wx.EXPAND, 5)

        sizer_17 = wx.BoxSizer(wx.HORIZONTAL)

        label_9 = wx.StaticText(
            self.panel_19,
            wx.ID_ANY,
            "Enable Grid Refresh",
            style=wx.ST_ELLIPSIZE_END,
        )
        label_9.SetToolTip(
            "Allows the Grids to update cell data.\nOnly runs for datasets of %s or less.\nMay lock or prevent operations when updating."
            % Globals.MAX_UPDATE_COUNT
        )
        sizer_17.Add(label_9, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.panel_20 = wx.Panel(self.panel_19, wx.ID_ANY)
        sizer_17.Add(self.panel_20, 1, wx.EXPAND, 0)

        grid_sizer_9 = wx.GridSizer(1, 1, 0, 0)

        self.checkbox_3 = wx.CheckBox(self.panel_20, wx.ID_ANY, "")
        grid_sizer_9.Add(self.checkbox_3, 0, wx.ALIGN_RIGHT | wx.EXPAND, 0)

        self.panel_21 = wx.Panel(self.grid, wx.ID_ANY)
        sizer_16.Add(self.panel_21, 1, wx.ALL | wx.EXPAND, 5)

        sizer_18 = wx.BoxSizer(wx.HORIZONTAL)

        label_10 = wx.StaticText(
            self.panel_21,
            wx.ID_ANY,
            "Grid Refresh Rate (seconds)",
            style=wx.ST_ELLIPSIZE_END,
        )
        label_10.SetToolTip("How often the Grid should update its cell data.")
        sizer_18.Add(label_10, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.panel_22 = wx.Panel(self.panel_21, wx.ID_ANY)
        sizer_18.Add(self.panel_22, 1, wx.EXPAND, 0)

        grid_sizer_10 = wx.GridSizer(1, 1, 0, 0)

        self.spin_ctrl_7 = wx.SpinCtrl(
            self.panel_22,
            wx.ID_ANY,
            min=Globals.GRID_UPDATE_RATE,
            max=Globals.MAX_GRID_UPDATE_RATE,
            initial=Globals.GRID_UPDATE_RATE,
        )
        grid_sizer_10.Add(
            self.spin_ctrl_7, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0
        )

        self.panel_35 = wx.Panel(self.grid, wx.ID_ANY)
        sizer_16.Add(self.panel_35, 1, wx.ALL | wx.EXPAND, 5)

        sizer_26 = wx.BoxSizer(wx.HORIZONTAL)
        self.panel_35.SetSizer(sizer_26)

        label_10 = wx.StaticText(
            self.panel_35,
            wx.ID_ANY,
            "Allow Column Resizing",
            style=wx.ST_ELLIPSIZE_END,
        )
        label_10.SetToolTip("Allow user to resize grid columns")
        sizer_26.Add(label_10, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.panel_36 = wx.Panel(self.panel_35, wx.ID_ANY)
        sizer_26.Add(self.panel_36, 1, wx.EXPAND, 0)

        grid_sizer_17 = wx.GridSizer(1, 1, 0, 0)
        self.panel_36.SetSizer(grid_sizer_17)

        self.checkbox_10 = wx.CheckBox(self.panel_36, wx.ID_ANY, "")
        grid_sizer_17.Add(self.checkbox_10, 0, wx.ALIGN_RIGHT | wx.EXPAND, 0)

        # App Preferences
        self.app = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        self.app.Hide()
        sizer_5.Add(self.app, 1, wx.EXPAND, 0)

        sizer_9 = wx.FlexGridSizer(4, 1, 0, 0)

        self.panel_7 = wx.Panel(self.app, wx.ID_ANY)
        sizer_9.Add(self.panel_7, 1, wx.ALL | wx.EXPAND, 5)

        sizer_12 = wx.BoxSizer(wx.HORIZONTAL)

        label_3 = wx.StaticText(
            self.panel_7,
            wx.ID_ANY,
            "Fetch All Installed Applications",
            style=wx.ST_ELLIPSIZE_END,
        )
        label_3.SetToolTip(
            "Fetches all installed applications, including those that are hidden.\nDefault is Enterprise apps only."
        )
        sizer_12.Add(label_3, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.panel_8 = wx.Panel(self.panel_7, wx.ID_ANY)
        sizer_12.Add(self.panel_8, 1, wx.EXPAND, 0)

        grid_sizer_3 = wx.GridSizer(1, 1, 0, 0)

        self.checkbox_2 = wx.CheckBox(self.panel_8, wx.ID_ANY, "")
        grid_sizer_3.Add(self.checkbox_2, 0, wx.ALIGN_RIGHT | wx.EXPAND, 0)

        self.panel_13 = wx.Panel(self.app, wx.ID_ANY)
        sizer_9.Add(self.panel_13, 1, wx.ALL | wx.EXPAND, 5)

        sizer_13 = wx.BoxSizer(wx.HORIZONTAL)

        label_6 = wx.StaticText(
            self.panel_13,
            wx.ID_ANY,
            "Show Application's Package Name",
            style=wx.ST_ELLIPSIZE_END,
        )
        label_6.SetToolTip(
            "Displays an Application's Package Name (e.g., In Tags or the Application input)"
        )
        sizer_13.Add(label_6, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.panel_14 = wx.Panel(self.panel_13, wx.ID_ANY)
        sizer_13.Add(self.panel_14, 1, wx.EXPAND, 0)

        grid_sizer_6 = wx.GridSizer(1, 1, 0, 0)

        self.checkbox_4 = wx.CheckBox(self.panel_14, wx.ID_ANY, "")
        grid_sizer_6.Add(self.checkbox_4, 0, wx.ALIGN_RIGHT | wx.EXPAND, 0)

        self.panel_15 = wx.Panel(self.app, wx.ID_ANY)
        sizer_9.Add(self.panel_15, 1, wx.ALL | wx.EXPAND, 5)

        sizer_15 = wx.BoxSizer(wx.HORIZONTAL)

        label_7 = wx.StaticText(
            self.panel_15,
            wx.ID_ANY,
            "Get Applications For Each Device",
            style=wx.ST_ELLIPSIZE_END,
        )
        label_7.SetToolTip(
            "Fetch all applications for every device within a group.\nPerformance may be slower if enabled."
        )
        sizer_15.Add(label_7, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.panel_16 = wx.Panel(self.panel_15, wx.ID_ANY)
        sizer_15.Add(self.panel_16, 1, wx.EXPAND, 0)

        grid_sizer_7 = wx.GridSizer(1, 1, 0, 0)

        self.checkbox_6 = wx.CheckBox(self.panel_16, wx.ID_ANY, "")
        grid_sizer_7.Add(self.checkbox_6, 0, wx.ALIGN_RIGHT | wx.EXPAND, 0)

        self.panel_38 = wx.Panel(self.app, wx.ID_ANY)
        sizer_9.Add(self.panel_38, 1, wx.ALL | wx.EXPAND, 5)

        sizer_27 = wx.BoxSizer(wx.HORIZONTAL)

        label_16 = wx.StaticText(
            self.panel_38,
            wx.ID_ANY,
            "Set App State To SHOW before Set Kiosk",
            style=wx.ST_ELLIPSIZE_END,
        )
        label_16.SetToolTip(
            "Set App State to SHOW before setting the application as a Kiosk app on device."
        )
        sizer_27.Add(label_16, 0, wx.ALIGN_CENTER_VERTICAL, 2)

        self.panel_37 = wx.Panel(self.panel_38, wx.ID_ANY)
        sizer_27.Add(self.panel_37, 1, wx.EXPAND, 0)

        grid_sizer_18 = wx.GridSizer(1, 1, 0, 0)

        self.checkbox_11 = wx.CheckBox(self.panel_37, wx.ID_ANY, "")
        grid_sizer_18.Add(self.checkbox_11, 0, wx.ALIGN_RIGHT | wx.EXPAND, 0)

        # Prompts Preferences
        self.prompts = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        self.prompts.Hide()
        sizer_5.Add(self.prompts, 1, wx.EXPAND, 0)

        sizer_19 = wx.FlexGridSizer(2, 1, 0, 0)

        self.panel_29 = wx.Panel(self.prompts, wx.ID_ANY)
        sizer_19.Add(self.panel_29, 1, wx.ALL | wx.EXPAND, 5)

        sizer_23 = wx.BoxSizer(wx.HORIZONTAL)

        label_14 = wx.StaticText(
            self.panel_29,
            wx.ID_ANY,
            "Grid Confirmation Prompt",
            style=wx.ST_ELLIPSIZE_END,
        )
        sizer_23.Add(label_14, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.panel_30 = wx.Panel(self.panel_29, wx.ID_ANY)
        sizer_23.Add(self.panel_30, 1, wx.EXPAND, 0)

        grid_sizer_14 = wx.GridSizer(1, 1, 0, 0)

        self.checkbox_8 = wx.CheckBox(self.panel_30, wx.ID_ANY, "")
        grid_sizer_14.Add(self.checkbox_8, 0, wx.ALIGN_RIGHT, 0)

        self.panel_31 = wx.Panel(self.prompts, wx.ID_ANY)
        sizer_19.Add(self.panel_31, 1, wx.ALL | wx.EXPAND, 5)

        sizer_24 = wx.BoxSizer(wx.HORIZONTAL)

        label_15 = wx.StaticText(
            self.panel_31,
            wx.ID_ANY,
            "Template Confirmation Prompt",
            style=wx.ST_ELLIPSIZE_END,
        )
        sizer_24.Add(label_15, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.panel_32 = wx.Panel(self.panel_31, wx.ID_ANY)
        sizer_24.Add(self.panel_32, 1, wx.EXPAND, 0)

        grid_sizer_15 = wx.GridSizer(1, 1, 0, 0)

        self.checkbox_7 = wx.CheckBox(self.panel_32, wx.ID_ANY, "")
        grid_sizer_15.Add(
            self.checkbox_7, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0
        )

        sizer_2 = wx.StdDialogButtonSizer()
        sizer_1.Add(sizer_2, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

        self.button_APPLY = wx.Button(self, wx.ID_APPLY, "")
        self.button_APPLY.Bind(wx.EVT_BUTTON, self.OnApply)
        sizer_2.AddButton(self.button_APPLY)

        sizer_2.Realize()

        self.panel_32.SetSizer(grid_sizer_15)

        self.panel_31.SetSizer(sizer_24)

        self.panel_30.SetSizer(grid_sizer_14)

        self.panel_29.SetSizer(sizer_23)

        sizer_19.AddGrowableCol(0)
        self.prompts.SetSizer(sizer_19)

        self.panel_16.SetSizer(grid_sizer_7)

        self.panel_15.SetSizer(sizer_15)

        self.panel_38.SetSizer(sizer_27)

        self.panel_37.SetSizer(grid_sizer_18)

        self.panel_14.SetSizer(grid_sizer_6)

        self.panel_13.SetSizer(sizer_13)

        self.panel_8.SetSizer(grid_sizer_3)

        self.panel_7.SetSizer(sizer_12)

        sizer_9.AddGrowableCol(0)
        self.app.SetSizer(sizer_9)

        self.panel_22.SetSizer(grid_sizer_10)

        self.panel_21.SetSizer(sizer_18)

        self.panel_20.SetSizer(grid_sizer_9)

        self.panel_19.SetSizer(sizer_17)

        sizer_16.AddGrowableCol(0)
        self.grid.SetSizer(sizer_16)

        self.panel_28.SetSizer(grid_sizer_13)

        self.panel_27.SetSizer(sizer_22)

        self.panel_26.SetSizer(grid_sizer_12)

        self.panel_25.SetSizer(sizer_21)

        sizer_14.AddGrowableCol(0)
        self.command.SetSizer(sizer_14)

        self.panel_10.SetSizer(grid_sizer_4)

        self.panel_9.SetSizer(sizer_10)

        self.panel_6.SetSizer(grid_sizer_2)

        self.panel_5.SetSizer(sizer_8)

        self.panel_4.SetSizer(grid_sizer_1)

        self.panel_3.SetSizer(sizer_7)

        sizer_6.AddGrowableCol(0)
        self.general.SetSizer(sizer_6)

        self.window_1_pane_2.SetSizer(sizer_5)

        self.window_1_pane_1.SetSizer(sizer_4)

        self.window_1.SplitVertically(self.window_1_pane_1, self.window_1_pane_2)

        self.panel_1.SetSizer(sizer_3)

        self.SetSizer(sizer_1)

        self.Layout()

        self.Bind(wx.EVT_LISTBOX, self.showMatchingPanel, self.list_box_1)

        if prefDict and not prefDict["enableDevice"]:
            self.checkbox_1.Set3StateValue(wx.CHK_UNCHECKED)
        else:
            self.checkbox_1.Set3StateValue(wx.CHK_CHECKED)

        if prefDict and not prefDict["enableGridUpdate"]:
            self.checkbox_3.Set3StateValue(wx.CHK_UNCHECKED)
            Globals.ENABLE_GRID_UPDATE = False
        elif prefDict and prefDict["enableGridUpdate"]:
            self.checkbox_3.Set3StateValue(wx.CHK_CHECKED)
            Globals.ENABLE_GRID_UPDATE = True
            if Globals.ENABLE_GRID_UPDATE and self.parent != None:
                self.parent.startUpdateThread()
        else:
            self.checkbox_3.Set3StateValue(wx.CHK_UNCHECKED)
            Globals.ENABLE_GRID_UPDATE = False

        if not prefDict or (prefDict and not prefDict["getAllApps"]):
            self.checkbox_2.Set3StateValue(wx.CHK_UNCHECKED)
            Globals.USE_ENTERPRISE_APP = True
        elif prefDict and prefDict["getAllApps"]:
            self.checkbox_2.Set3StateValue(wx.CHK_CHECKED)
            Globals.USE_ENTERPRISE_APP = False
            if (
                isinstance(self.prefs["getAllApps"], str)
                and prefDict["getAllApps"].lower() == "true"
            ) or prefDict["getAllApps"] == True:
                self.checkbox_2.Set3StateValue(wx.CHK_CHECKED)
                Globals.USE_ENTERPRISE_APP = False
            else:
                self.checkbox_2.Set3StateValue(wx.CHK_UNCHECKED)

        if not prefDict or (prefDict and not prefDict["showPkg"]):
            self.checkbox_4.Set3StateValue(wx.CHK_UNCHECKED)
            Globals.SHOW_PKG_NAME = False
        elif prefDict and prefDict["showPkg"]:
            if (
                isinstance(self.prefs["showPkg"], str)
                and prefDict["showPkg"].lower() == "true"
            ) or prefDict["showPkg"] == True:
                self.checkbox_4.Set3StateValue(wx.CHK_CHECKED)
                Globals.SHOW_PKG_NAME = False
            else:
                self.checkbox_4.Set3StateValue(wx.CHK_UNCHECKED)
                Globals.SHOW_PKG_NAME = False

        if not prefDict or (prefDict and not prefDict["getAppsForEachDevice"]):
            self.checkbox_6.Set3StateValue(wx.CHK_UNCHECKED)
            Globals.SHOW_PKG_NAME = False
        elif prefDict and prefDict["getAppsForEachDevice"]:
            if (
                isinstance(self.prefs["getAppsForEachDevice"], str)
                and prefDict["getAppsForEachDevice"].lower() == "true"
            ) or prefDict["getAppsForEachDevice"] == True:
                self.checkbox_6.Set3StateValue(wx.CHK_CHECKED)
                Globals.GET_APP_EACH_DEVICE = True
            else:
                self.checkbox_6.Set3StateValue(wx.CHK_UNCHECKED)
                Globals.GET_APP_EACH_DEVICE = False

        if not prefDict or (prefDict and not prefDict["reachQueueStateOnly"]):
            self.checkbox_5.Set3StateValue(wx.CHK_CHECKED)
            Globals.REACH_QUEUED_ONLY = True
        elif prefDict and prefDict["reachQueueStateOnly"]:
            if (
                isinstance(self.prefs["reachQueueStateOnly"], str)
                and prefDict["reachQueueStateOnly"].lower() == "true"
            ) or prefDict["reachQueueStateOnly"] == True:
                self.checkbox_5.Set3StateValue(wx.CHK_CHECKED)
                Globals.REACH_QUEUED_ONLY = True
            else:
                self.checkbox_5.Set3StateValue(wx.CHK_UNCHECKED)
                Globals.REACH_QUEUED_ONLY = False

        if not prefDict or (
            prefDict
            and not prefDict["templateDialog"]
            and not prefDict["templateUpdate"]
        ):
            self.checkbox_7.Set3StateValue(wx.CHK_CHECKED)
            Globals.SHOW_TEMPLATE_DIALOG = True
            Globals.SHOW_TEMPLATE_UPDATE = True
        elif prefDict and prefDict["templateDialog"]:
            if (
                isinstance(self.prefs["templateDialog"], str)
                and prefDict["templateDialog"].lower() == "true"
            ) or prefDict["templateDialog"] == True:
                self.checkbox_7.Set3StateValue(wx.CHK_CHECKED)
                Globals.SHOW_TEMPLATE_DIALOG = True
                Globals.SHOW_TEMPLATE_UPDATE = True
            else:
                self.checkbox_7.Set3StateValue(wx.CHK_UNCHECKED)
                Globals.SHOW_TEMPLATE_DIALOG = False
                Globals.SHOW_TEMPLATE_UPDATE = False
        elif prefDict and prefDict["templateUpdate"]:
            if (
                isinstance(self.prefs["templateUpdate"], str)
                and prefDict["templateUpdate"].lower() == "true"
            ) or prefDict["templateUpdate"] == True:
                self.checkbox_7.Set3StateValue(wx.CHK_CHECKED)
                Globals.SHOW_TEMPLATE_DIALOG = True
                Globals.SHOW_TEMPLATE_UPDATE = True
            else:
                self.checkbox_7.Set3StateValue(wx.CHK_UNCHECKED)
                Globals.SHOW_TEMPLATE_DIALOG = False
                Globals.SHOW_TEMPLATE_UPDATE = False
        else:
            if Globals.SHOW_TEMPLATE_DIALOG and Globals.SHOW_TEMPLATE_UPDATE:
                self.checkbox_7.Set3StateValue(wx.CHK_CHECKED)
            else:
                self.checkbox_7.Set3StateValue(wx.CHK_UNCHECKED)

        if not prefDict or (prefDict and not prefDict["gridDialog"]):
            self.checkbox_8.Set3StateValue(wx.CHK_CHECKED)
            Globals.SHOW_GRID_DIALOG = True
        elif prefDict and prefDict["gridDialog"]:
            if (
                isinstance(self.prefs["gridDialog"], str)
                and prefDict["gridDialog"].lower() == "true"
            ) or prefDict["gridDialog"] == True:
                self.checkbox_8.Set3StateValue(wx.CHK_CHECKED)
                Globals.SHOW_GRID_DIALOG = True
            else:
                self.checkbox_8.Set3StateValue(wx.CHK_UNCHECKED)
                Globals.SHOW_GRID_DIALOG = False
        else:
            if Globals.SHOW_GRID_DIALOG:
                self.checkbox_8.Set3StateValue(wx.CHK_CHECKED)
            else:
                self.checkbox_8.Set3StateValue(wx.CHK_UNCHECKED)

        if not prefDict or (prefDict and not prefDict["colSize"]):
            self.checkbox_10.Set3StateValue(wx.CHK_CHECKED)
            if self.parent:
                self.parent.gridPanel.enableGridProperties(True, True, False)
        elif prefDict and prefDict["colSize"]:
            if (
                isinstance(self.prefs["colSize"], str)
                and prefDict["colSize"].lower() == "true"
            ) or prefDict["colSize"] == True:
                self.checkbox_10.Set3StateValue(wx.CHK_CHECKED)
                if self.parent:
                    self.parent.gridPanel.enableGridProperties(True, True, False)
            else:
                self.checkbox_10.Set3StateValue(wx.CHK_UNCHECKED)
                if self.parent:
                    self.parent.gridPanel.disableGridProperties(False, False, True)

        if not prefDict or (prefDict and not prefDict["setStateShow"]):
            self.checkbox_11.Set3StateValue(wx.CHK_UNCHECKED)
            Globals.SET_APP_STATE_AS_SHOW = False
        elif prefDict and prefDict["setStateShow"]:
            if (
                isinstance(self.prefs["setStateShow"], str)
                and prefDict["setStateShow"].lower() == "true"
            ) or prefDict["setStateShow"] == True:
                self.checkbox_11.Set3StateValue(wx.CHK_CHECKED)
                Globals.SET_APP_STATE_AS_SHOW = True
            else:
                self.checkbox_11.Set3StateValue(wx.CHK_UNCHECKED)
                Globals.SET_APP_STATE_AS_SHOW = False

        if not prefDict or (prefDict and not prefDict["useJsonForCmd"]):
            self.checkbox_12.Set3StateValue(wx.CHK_CHECKED)
            Globals.COMMAND_JSON_INPUT = True
        elif prefDict and prefDict["useJsonForCmd"]:
            if (
                isinstance(self.prefs["useJsonForCmd"], str)
                and prefDict["useJsonForCmd"].lower() == "true"
            ) or prefDict["useJsonForCmd"] == True:
                self.checkbox_12.Set3StateValue(wx.CHK_CHECKED)
                Globals.COMMAND_JSON_INPUT = True
            else:
                self.checkbox_12.Set3StateValue(wx.CHK_UNCHECKED)
                Globals.COMMAND_JSON_INPUT = False

        if not prefDict or (prefDict and not prefDict["runCommandOn"]):
            self.combobox_1.SetSelection(0)
        elif prefDict and prefDict["runCommandOn"]:
            if isinstance(self.prefs["runCommandOn"], str):
                indx = self.combobox_1.GetItems().index(self.prefs["runCommandOn"])
                self.combobox_1.SetSelection(indx)
            else:
                self.combobox_1.SetSelection(self.prefs["runCommandOn"])
        Globals.CMD_DEVICE_TYPE = self.combobox_1.GetValue().lower()

    @api_tool_decorator
    def showMatchingPanel(self, event):
        event.Skip()
        if event.GetString() == "Grid":
            self.app.Hide()
            self.general.Hide()
            self.command.Hide()
            self.prompts.Hide()
            self.grid.Show()
        elif event.GetString() == "Command":
            self.app.Hide()
            self.general.Hide()
            self.grid.Hide()
            self.prompts.Hide()
            self.command.Show()
        elif event.GetString() == "General":
            self.app.Hide()
            self.grid.Hide()
            self.command.Hide()
            self.prompts.Hide()
            self.general.Show()
        elif event.GetString() == "Application":
            self.grid.Hide()
            self.general.Hide()
            self.command.Hide()
            self.prompts.Hide()
            self.app.Show()
        elif event.GetString() == "Prompts":
            self.app.Hide()
            self.general.Hide()
            self.command.Hide()
            self.prompts.Show()
            self.grid.Hide()
        self.window_1_pane_2.GetSizer().Layout()
        self.Layout()

    @api_tool_decorator
    def OnApply(self, event):
        self.prefs = {
            "enableDevice": self.checkbox_1.IsChecked(),
            "limit": self.spin_ctrl_1.GetValue(),
            "offset": self.spin_ctrl_2.GetValue(),
            "gridDialog": self.checkbox_8.IsChecked(),
            "templateDialog": self.checkbox_7.IsChecked(),
            "templateUpdate": self.checkbox_7.IsChecked(),
            "commandTimeout": self.spin_ctrl_6.GetValue(),
            "updateRate": self.spin_ctrl_7.GetValue(),
            "enableGridUpdate": self.checkbox_3.IsChecked(),
            "windowSize": self.parent.GetSize() if self.parent else Globals.MIN_SIZE,
            "windowPosition": tuple(self.parent.GetPosition())
            if self.parent
            else str(wx.CENTRE),
            "isMaximized": self.parent.IsMaximized() if self.parent else False,
            "getAllApps": self.checkbox_2.IsChecked(),
            "showPkg": self.checkbox_4.IsChecked(),
            "reachQueueStateOnly": self.checkbox_5.IsChecked(),
            "getAppsForEachDevice": self.checkbox_6.IsChecked(),
            "colSize": self.checkbox_10.IsChecked(),
            "setStateShow": self.checkbox_11.IsChecked(),
            "useJsonForCmd": self.checkbox_12.IsChecked(),
            "runCommandOn": self.combobox_1.GetValue(),
            "maxThread": self.spin_ctrl_8.GetValue(),
        }

        Globals.SET_APP_STATE_AS_SHOW = False
        Globals.SHOW_GRID_DIALOG = self.prefs["gridDialog"]
        Globals.SHOW_TEMPLATE_UPDATE = self.prefs["templateDialog"]
        Globals.SHOW_TEMPLATE_DIALOG = self.prefs["templateUpdate"]
        Globals.REACH_QUEUED_ONLY = self.prefs["reachQueueStateOnly"]
        Globals.GET_APP_EACH_DEVICE = self.prefs["getAppsForEachDevice"]
        Globals.SHOW_PKG_NAME = self.prefs["showPkg"]
        Globals.limit = self.prefs["limit"]
        Globals.offset = self.prefs["offset"]
        Globals.COMMAND_TIMEOUT = int(self.prefs["commandTimeout"])
        Globals.GRID_UPDATE_RATE = int(self.prefs["updateRate"])
        Globals.ENABLE_GRID_UPDATE = self.checkbox_3.IsChecked()
        Globals.COMMAND_JSON_INPUT = self.checkbox_12.IsChecked()
        Globals.CMD_DEVICE_TYPE = self.combobox_1.GetValue().lower()
        Globals.MAX_THREAD_COUNT = self.prefs["maxThread"]

        if self.prefs["getAllApps"]:
            Globals.USE_ENTERPRISE_APP = False
        else:
            Globals.USE_ENTERPRISE_APP = True

        if Globals.ENABLE_GRID_UPDATE and self.parent != None:
            self.parent.startUpdateThread()

        if self.parent:
            if self.checkbox_10.IsChecked():
                self.parent.gridPanel.enableGridProperties(True, True, False)
            else:
                self.parent.gridPanel.disableGridProperties(False, False, True)

        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        else:
            self.Close()

    @api_tool_decorator
    def SetPrefs(self, prefs, onBoot=True):
        self.prefs = prefs
        if not self.prefs:
            return

        if "enableDevice" in self.prefs:
            self.checkbox_1.SetValue(self.prefs["enableDevice"])
        if "limit" in self.prefs and self.prefs["limit"]:
            Globals.limit = self.prefs["limit"]
            if Globals.limit > Globals.MAX_LIMIT:
                Globals.limit = Globals.MAX_LIMIT
            elif Globals.limit < Globals.MIN_LIMIT:
                Globals.limit = Globals.MIN_LIMIT
            self.spin_ctrl_1.SetValue(Globals.limit)
        if "offset" in self.prefs and self.prefs["offset"]:
            Globals.offset = self.prefs["offset"]
            if Globals.offset < 0:
                Globals.offset = 0
            self.spin_ctrl_2.SetValue(Globals.offset)
        if "gridDialog" in self.prefs and type(self.prefs["gridDialog"]) == bool:
            Globals.SHOW_GRID_DIALOG = self.prefs["gridDialog"]
            if Globals.SHOW_GRID_DIALOG:
                self.checkbox_8.Set3StateValue(wx.CHK_CHECKED)
            else:
                self.checkbox_8.Set3StateValue(wx.CHK_UNCHECKED)
        if (
            "templateDialog" in self.prefs
            and type(self.prefs["templateDialog"]) == bool
        ):
            Globals.SHOW_TEMPLATE_DIALOG = self.prefs["templateDialog"]
        if (
            "templateUpdate" in self.prefs
            and type(self.prefs["templateUpdate"]) == bool
        ):
            Globals.SHOW_TEMPLATE_UPDATE = self.prefs["templateUpdate"]
        if Globals.SHOW_TEMPLATE_UPDATE and Globals.SHOW_TEMPLATE_DIALOG:
            self.checkbox_7.Set3StateValue(wx.CHK_CHECKED)
        else:
            self.checkbox_7.Set3StateValue(wx.CHK_UNCHECKED)
        if "commandTimeout" in self.prefs and self.prefs["commandTimeout"]:
            Globals.COMMAND_TIMEOUT = int(self.prefs["commandTimeout"])
            self.spin_ctrl_6.SetValue(Globals.COMMAND_TIMEOUT)
        if "updateRate" in self.prefs and self.prefs["updateRate"]:
            Globals.GRID_UPDATE_RATE = int(self.prefs["updateRate"])
            self.spin_ctrl_7.SetValue(Globals.GRID_UPDATE_RATE)
        if "enableGridUpdate" in self.prefs and self.prefs["enableGridUpdate"]:
            self.checkbox_3.SetValue(self.prefs["enableGridUpdate"])
            Globals.ENABLE_GRID_UPDATE = self.checkbox_2.IsChecked()
            if Globals.ENABLE_GRID_UPDATE and self.parent != None:
                self.parent.startUpdateThread()
        if "windowSize" in self.prefs and self.prefs["windowSize"] and onBoot:
            if self.parent:
                size = tuple(
                    int(num)
                    for num in self.prefs["windowSize"]
                    .replace("(", "")
                    .replace(")", "")
                    .replace("...", "")
                    .split(", ")
                )
                self.parent.SetSize(size)
        if "isMaximized" in self.prefs and self.prefs["isMaximized"] and onBoot:
            if self.parent:
                self.parent.Maximize(self.prefs["isMaximized"])
        if "windowPosition" in self.prefs and self.prefs["windowPosition"] and onBoot:
            if self.parent:
                if self.prefs["windowPosition"] == "1":
                    self.parent.Centre()
                else:
                    if not self.parent.IsMaximized():
                        pos = tuple(self.prefs["windowPosition"])
                        self.parent.SetPosition(wx.Point(pos[0], pos[1]))
        if "getAppsForEachDevice" in self.prefs and self.prefs["getAppsForEachDevice"]:
            if (
                isinstance(self.prefs["getAppsForEachDevice"], str)
                and self.prefs["getAppsForEachDevice"].lower() == "false"
            ) or not self.prefs["getAppsForEachDevice"]:
                Globals.SHOW_PKG_NAME = False
                self.checkbox_6.Set3StateValue(wx.CHK_UNCHECKED)
            elif (
                isinstance(self.prefs["getAppsForEachDevice"], str)
                and self.prefs["getAppsForEachDevice"].lower()
            ) == "true" or self.prefs["getAppsForEachDevice"]:
                Globals.SHOW_PKG_NAME = True
                self.checkbox_6.Set3StateValue(wx.CHK_CHECKED)
            else:
                Globals.SHOW_PKG_NAME = True
                self.checkbox_6.Set3StateValue(wx.CHK_UNCHECKED)
        if "getAllApps" in self.prefs:
            if (
                isinstance(self.prefs["getAllApps"], str)
                and self.prefs["getAllApps"].lower() == "false"
            ) or not self.prefs["getAllApps"]:
                Globals.USE_ENTERPRISE_APP = False
                self.checkbox_2.Set3StateValue(wx.CHK_CHECKED)
            elif (
                isinstance(self.prefs["getAllApps"], str)
                and self.prefs["getAllApps"].lower()
            ) == "true" or self.prefs["getAllApps"]:
                Globals.USE_ENTERPRISE_APP = True
                self.checkbox_2.Set3StateValue(wx.CHK_UNCHECKED)
            else:
                Globals.USE_ENTERPRISE_APP = True
                self.checkbox_2.Set3StateValue(wx.CHK_UNCHECKED)
        if "showPkg" in self.prefs:
            if (
                isinstance(self.prefs["showPkg"], str)
                and self.prefs["showPkg"].lower() == "false"
            ) or not self.prefs["showPkg"]:
                Globals.SHOW_PKG_NAME = False
                self.checkbox_4.Set3StateValue(wx.CHK_UNCHECKED)
            elif (
                isinstance(self.prefs["showPkg"], str)
                and self.prefs["showPkg"].lower() == "true"
            ) or self.prefs["showPkg"]:
                Globals.SHOW_PKG_NAME = True
                self.checkbox_4.Set3StateValue(wx.CHK_CHECKED)
            else:
                Globals.SHOW_PKG_NAME = True
                self.checkbox_4.Set3StateValue(wx.CHK_CHECKED)
        if "setStateShow" in self.prefs:
            if (
                isinstance(self.prefs["setStateShow"], str)
                and self.prefs["setStateShow"].lower() == "false"
            ) or not self.prefs["setStateShow"]:
                Globals.SET_APP_STATE_AS_SHOW = False
                self.checkbox_11.Set3StateValue(wx.CHK_UNCHECKED)
            elif (
                isinstance(self.prefs["setStateShow"], str)
                and self.prefs["setStateShow"].lower() == "true"
            ) or self.prefs["setStateShow"]:
                Globals.SET_APP_STATE_AS_SHOW = True
                self.checkbox_11.Set3StateValue(wx.CHK_CHECKED)
            else:
                Globals.SET_APP_STATE_AS_SHOW = False
                self.checkbox_11.Set3StateValue(wx.CHK_UNCHECKED)
        if "useJsonForCmd" in self.prefs and self.prefs["useJsonForCmd"]:
            if (
                isinstance(self.prefs["useJsonForCmd"], str)
                and self.prefs["useJsonForCmd"].lower() == "false"
            ) or not self.prefs["useJsonForCmd"]:
                Globals.COMMAND_JSON_INPUT = False
                self.checkbox_12.Set3StateValue(wx.CHK_UNCHECKED)
            elif (
                isinstance(self.prefs["useJsonForCmd"], str)
                and self.prefs["useJsonForCmd"].lower() == "true"
            ) or self.prefs["useJsonForCmd"]:
                Globals.COMMAND_JSON_INPUT = True
                self.checkbox_12.Set3StateValue(wx.CHK_CHECKED)
            else:
                Globals.COMMAND_JSON_INPUT = True
                self.checkbox_12.Set3StateValue(wx.CHK_CHECKED)
        if "runCommandOn" in self.prefs and self.prefs["runCommandOn"]:
            if isinstance(self.prefs["runCommandOn"], str):
                indx = self.combobox_1.GetItems().index(
                    self.prefs["runCommandOn"].capitalize()
                )
                self.combobox_1.SetSelection(indx)
            else:
                self.combobox_1.SetSelection(self.prefs["runCommandOn"])
            Globals.CMD_DEVICE_TYPE = self.combobox_1.GetValue().lower()
        if "maxThread" in self.prefs and self.prefs["maxThread"]:
            maxThread = Globals.MAX_THREAD_COUNT
            maxThread = int(self.prefs["maxThread"])
            if maxThread < 10:
                self.spin_ctrl_8.SetValue(10)
            elif maxThread > 100:
                self.spin_ctrl_8.SetValue(100)
            else:
                self.spin_ctrl_8.SetValue(maxThread)
        if "reachQueueStateOnly" in self.prefs and self.prefs["reachQueueStateOnly"]:
            if (
                isinstance(self.prefs["reachQueueStateOnly"], str)
                and self.prefs["reachQueueStateOnly"].lower() == "true"
            ) or self.prefs["reachQueueStateOnly"] == True:
                self.checkbox_5.Set3StateValue(wx.CHK_CHECKED)
                Globals.REACH_QUEUED_ONLY = True
            else:
                self.checkbox_5.Set3StateValue(wx.CHK_UNCHECKED)
                Globals.REACH_QUEUED_ONLY = False

    @api_tool_decorator
    def GetPrefs(self):
        if not self.prefs:
            self.prefs = {}
        for key in self.prefKeys:
            if key not in self.prefs.keys():
                self.prefs[key] = self.getDefaultKeyValue(key)

        self.prefs["reachQueueStateOnly"] = Globals.REACH_QUEUED_ONLY
        self.prefs["getAppsForEachDevice"] = Globals.GET_APP_EACH_DEVICE
        self.prefs["getAllApps"] = Globals.USE_ENTERPRISE_APP
        self.prefs["showPkg"] = Globals.SHOW_PKG_NAME
        self.prefs["useJsonForCmd"] = Globals.COMMAND_JSON_INPUT
        self.prefs[
            "gridDialog"
        ] = Globals.SHOW_GRID_DIALOG  # update pref value to match global value
        self.prefs["windowSize"] = (
            str(self.parent.GetSize()) if self.parent else Globals.MIN_SIZE
        )
        self.prefs["isMaximized"] = self.parent.IsMaximized() if self.parent else False
        self.prefs["templateDialog"] = Globals.SHOW_TEMPLATE_DIALOG
        self.prefs["templateUpdate"] = Globals.SHOW_TEMPLATE_UPDATE
        self.prefs["runCommandOn"] = Globals.CMD_DEVICE_TYPE
        self.prefs["maxThread"] = Globals.MAX_THREAD_COUNT

        return self.prefs

    @api_tool_decorator
    def getDefaultKeyValue(self, key):
        if key == "enableDevice":
            return True
        elif key == "limit":
            return Globals.MAX_LIMIT
        elif key == "offset":
            return Globals.offset
        elif key == "gridDialog":
            return Globals.SHOW_GRID_DIALOG
        elif key == "templateDialog":
            return Globals.SHOW_TEMPLATE_DIALOG
        elif key == "templateUpdate":
            return Globals.SHOW_TEMPLATE_UPDATE
        elif key == "commandTimeout":
            return Globals.COMMAND_TIMEOUT
        elif key == "updateRate":
            return Globals.GRID_UPDATE_RATE
        elif key == "enableGridUpdate":
            return Globals.ENABLE_GRID_UPDATE
        elif key == "windowSize":
            return self.parent.GetSize() if self.parent else Globals.MIN_SIZE
        elif key == "isMaximized":
            return self.parent.IsMaximized() if self.parent else False
        elif key == "windowPosition":
            return tuple(self.parent.GetPosition()) if self.parent else str(wx.CENTRE)
        elif key == "getAllApps":
            return Globals.USE_ENTERPRISE_APP
        elif key == "showPkg":
            return Globals.SHOW_PKG_NAME
        elif key == "getAppsForEachDevice":
            return Globals.GET_APP_EACH_DEVICE
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
        elif key == "maxThread":
            return Globals.MAX_THREAD_COUNT
        else:
            return None
