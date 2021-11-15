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
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.SetTitle("Preferences")
        self.size = (525, 400)
        self.SetSize(self.size)
        self.SetMinSize(self.size)

        self.parent = parent
        self.prefs = prefDict if prefDict else {}
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
            "syncGridScroll",
            "immediateChild",
            "aliasDayDelta",
            "fontSize",
            "saveColVisibility",
        ]

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

        sizer_6 = wx.FlexGridSizer(5, 1, 0, 0)

        (_, _, self.checkbox_1,) = self.addPrefToPanel(
            self.general,
            sizer_6,
            "Enable Device Selection",
            wx.CheckBox,
            "Allow user to specify actions on a selections of devices within a group.",
        )

        (_, _, self.spin_ctrl_1,) = self.addPrefToPanel(
            self.general,
            sizer_6,
            "API Request Limit",
            wx.SpinCtrl,
            "Maximum amount of results that the API will return. Min: %s Max: %s"
            % (Globals.MIN_LIMIT, Globals.MAX_LIMIT),
        )
        self.spin_ctrl_1.SetMin(Globals.MIN_LIMIT)
        self.spin_ctrl_1.SetMax(Globals.MAX_LIMIT)
        self.spin_ctrl_1.SetValue(Globals.limit)

        (panel_9, _, self.spin_ctrl_2,) = self.addPrefToPanel(
            self.general,
            sizer_6,
            "API Request Offset",
            wx.SpinCtrl,
            "Page of results the API sends back (starts at 0). Min:0 Max: 100",
        )
        panel_9.Hide()
        self.spin_ctrl_2.SetMin(0)
        self.spin_ctrl_2.SetValue(Globals.offset)

        (panel_43, _, self.spin_ctrl_8,) = self.addPrefToPanel(
            self.general,
            sizer_6,
            "Max Threads",
            wx.SpinCtrl,
            "Maximum number of threads that will be created to perform an action. Min: 10 Max: 100",
        )
        panel_43.Hide()
        self.spin_ctrl_8.SetMin(10)
        self.spin_ctrl_8.SetMax(100)
        self.spin_ctrl_8.SetValue(Globals.MAX_THREAD_COUNT)

        (_, _, self.spin_ctrl_10,) = self.addPrefToPanel(
            self.general,
            sizer_6,
            "Font Size",
            wx.SpinCtrl,
            "Font size. Min: 10 Max: 72",
        )
        self.spin_ctrl_10.SetMin(10)
        self.spin_ctrl_10.SetMax(72)
        self.spin_ctrl_10.SetValue(Globals.FONT_SIZE)

        (_, _, self.checkbox_15,) = self.addPrefToPanel(
            self.general,
            sizer_6,
            "Save only visible columns",
            wx.CheckBox,
            "When saving to a CSV file, only the columns visible in the Grids will be saved to the file.",
        )

        # Command Preferences
        self.command = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        self.command.Hide()
        sizer_5.Add(self.command, 1, wx.EXPAND, 0)

        sizer_14 = wx.FlexGridSizer(5, 1, 0, 0)

        (_, _, self.spin_ctrl_6,) = self.addPrefToPanel(
            self.command,
            sizer_14,
            "Command Timeout (seconds)",
            wx.SpinCtrl,
            "How long a command should wait on the status check before skipping. Min: 0 Max: 100",
        )
        self.spin_ctrl_6.SetMin(0)
        self.spin_ctrl_6.SetValue(Globals.COMMAND_TIMEOUT)

        (_, _, self.checkbox_5,) = self.addPrefToPanel(
            self.command,
            sizer_14,
            "Reach Queued Command State Only",
            wx.CheckBox,
            "Allow the tool to wait until a command has reached the Queued state, don't wait for the other state changes.",
        )

        (_, __file__, self.checkbox_12,) = self.addPrefToPanel(
            self.command,
            sizer_14,
            "Use Json Input for Commands",
            wx.CheckBox,
            "Use Json Input for Commands",
        )

        (_, _, self.combobox_1,) = self.addPrefToPanel(
            self.command,
            sizer_14,
            "Device Type",
            wx.ComboBox,
            "Types of devices that a command should be run on.",
            choice=Globals.CMD_DEVICE_TYPES,
        )
        self.combobox_1.SetSelection(0)

        (_, _, self.spin_ctrl_9,) = self.addPrefToPanel(
            self.command,
            sizer_14,
            "Date Delta for Alias Command",
            wx.SpinCtrl,
            "Time difference for when the Alias command schedule should end. Min: %s Max: %s"
            % (0, Globals.ALIAS_MAX_DAY_DELTA),
        )
        self.spin_ctrl_9.SetMin(0)
        self.spin_ctrl_9.SetMax(Globals.ALIAS_MAX_DAY_DELTA)
        self.spin_ctrl_9.SetValue(Globals.ALIAS_DAY_DELTA)

        # Grid Preferences
        self.grid = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        self.grid.Hide()
        sizer_5.Add(self.grid, 1, wx.EXPAND, 0)

        sizer_16 = wx.FlexGridSizer(6, 1, 0, 0)

        (_, _, self.checkbox_3,) = self.addPrefToPanel(
            self.grid,
            sizer_16,
            "Enable Grid Refresh",
            wx.CheckBox,
            "Allows the Grids to update cell data.\nOnly runs for datasets of %s or less.\nMay lock or prevent operations when updating."
            % Globals.MAX_UPDATE_COUNT,
        )

        (_, _, self.spin_ctrl_7,) = self.addPrefToPanel(
            self.grid,
            sizer_16,
            "Grid Refresh Rate (seconds)",
            wx.SpinCtrl,
            "How often the Grid should update its cell data. Min: %s Max: %s"
            % (Globals.GRID_UPDATE_RATE, Globals.MAX_GRID_UPDATE_RATE),
        )
        self.spin_ctrl_7.SetMin(Globals.GRID_UPDATE_RATE)
        self.spin_ctrl_7.SetMax(Globals.MAX_GRID_UPDATE_RATE)
        self.spin_ctrl_7.SetValue(Globals.GRID_UPDATE_RATE)

        (_, _, self.checkbox_10,) = self.addPrefToPanel(
            self.grid,
            sizer_16,
            "Allow Column Resizing",
            wx.CheckBox,
            "Allow user to resize grid columns",
        )

        (_, _, self.checkbox_13,) = self.addPrefToPanel(
            self.grid,
            sizer_16,
            "Sync Grid's Vertical Scroll Position",
            wx.CheckBox,
            "Sync Grid's vertical scroll position. Sync is disabled once a column is sorted.",
        )

        (_, _, self.checkbox_14,) = self.addPrefToPanel(
            self.grid,
            sizer_16,
            "Only Show Immediate Subgroups",
            wx.CheckBox,
            "Only show the immediate subgroups for a particular group. If not enabled it will show all subgroups levels in the grid.",
        )

        # App Preferences
        self.app = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        self.app.Hide()
        sizer_5.Add(self.app, 1, wx.EXPAND, 0)

        sizer_9 = wx.FlexGridSizer(5, 1, 0, 0)

        (_, _, self.checkbox_2,) = self.addPrefToPanel(
            self.app,
            sizer_9,
            "Fetch All Installed Apps on Device",
            wx.CheckBox,
            "Fetches all installed applications, including those that are hidden.\nDefault is Enterprise apps only.",
        )

        (_, _, self.checkbox_4,) = self.addPrefToPanel(
            self.app,
            sizer_9,
            "Show Application's Package Name",
            wx.CheckBox,
            "Displays an Application's Package Name (e.g., In Tags or the Application input)",
        )

        (_, _, self.checkbox_6,) = self.addPrefToPanel(
            self.app,
            sizer_9,
            "Get Applications For Each Device",
            wx.CheckBox,
            "Fetch all applications for every device within a group.\nPerformance may be slower if enabled.",
        )

        (_, _, self.checkbox_11,) = self.addPrefToPanel(
            self.app,
            sizer_9,
            "Set App State To SHOW before Set Kiosk",
            wx.CheckBox,
            "Set App State to SHOW before setting the application as a Kiosk app on device.",
        )

        # Prompts Preferences
        self.prompts = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        self.prompts.Hide()
        sizer_5.Add(self.prompts, 1, wx.EXPAND, 0)

        sizer_19 = wx.FlexGridSizer(2, 1, 0, 0)

        (_, _, self.checkbox_8,) = self.addPrefToPanel(
            self.prompts,
            sizer_19,
            "Grid Confirmation Prompt",
            wx.CheckBox,
            "Grid Confirmation Prompt",
        )

        (_, _, self.checkbox_7,) = self.addPrefToPanel(
            self.prompts,
            sizer_19,
            "Template Confirmation Prompt",
            wx.CheckBox,
            "Template Confirmation Prompt",
        )

        sizer_2 = wx.StdDialogButtonSizer()
        sizer_1.Add(sizer_2, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

        self.button_APPLY = wx.Button(self, wx.ID_APPLY, "")
        self.button_APPLY.Bind(wx.EVT_BUTTON, self.OnApply)
        sizer_2.AddButton(self.button_APPLY)

        sizer_2.Realize()

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

        self.window_1_pane_2.SetSizer(sizer_5)

        self.window_1_pane_1.SetSizer(sizer_4)

        self.window_1.SplitVertically(self.window_1_pane_1, self.window_1_pane_2)

        panel_1.SetSizer(sizer_3)

        self.SetSizer(sizer_1)

        self.Layout()

        self.Bind(wx.EVT_LISTBOX, self.showMatchingPanel, self.list_box_1)
        self.Bind(wx.EVT_SIZE, self.onResize, self)

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
        elif prefDict and "reachQueueStateOnly" in prefDict:
            if (
                isinstance(self.prefs["reachQueueStateOnly"], str)
                and prefDict["reachQueueStateOnly"].lower() == "true"
            ) or prefDict["reachQueueStateOnly"] == True:
                self.checkbox_5.Set3StateValue(wx.CHK_CHECKED)
                Globals.REACH_QUEUED_ONLY = True
            else:
                self.checkbox_5.Set3StateValue(wx.CHK_UNCHECKED)
                Globals.REACH_QUEUED_ONLY = False

        if not prefDict or (prefDict and not prefDict["syncGridScroll"]):
            self.checkbox_13.Set3StateValue(wx.CHK_CHECKED)
            Globals.MATCH_SCROLL_POS = True
        elif prefDict and "syncGridScroll" in prefDict:
            if (
                isinstance(self.prefs["syncGridScroll"], str)
                and prefDict["syncGridScroll"].lower() == "true"
            ) or prefDict["syncGridScroll"] == True:
                self.checkbox_13.Set3StateValue(wx.CHK_CHECKED)
                Globals.MATCH_SCROLL_POS = True
            else:
                self.checkbox_13.Set3StateValue(wx.CHK_UNCHECKED)
                Globals.MATCH_SCROLL_POS = False

        if not prefDict or (prefDict and not prefDict["immediateChild"]):
            self.checkbox_14.Set3StateValue(wx.CHK_UNCHECKED)
            Globals.GET_IMMEDIATE_SUBGROUPS = False
        elif prefDict and "immediateChild" in prefDict:
            if (
                isinstance(self.prefs["immediateChild"], str)
                and prefDict["immediateChild"].lower() == "true"
            ) or prefDict["immediateChild"] == True:
                self.checkbox_14.Set3StateValue(wx.CHK_CHECKED)
                Globals.GET_IMMEDIATE_SUBGROUPS = True
            else:
                self.checkbox_14.Set3StateValue(wx.CHK_UNCHECKED)
                Globals.GET_IMMEDIATE_SUBGROUPS = False

        if prefDict and "aliasDayDelta" in prefDict:
            Globals.ALIAS_DAY_DELTA = int(prefDict["aliasDayDelta"])
            if Globals.ALIAS_DAY_DELTA > Globals.ALIAS_MAX_DAY_DELTA:
                Globals.ALIAS_DAY_DELTA = Globals.ALIAS_MAX_DAY_DELTA
            if Globals.ALIAS_DAY_DELTA < 0:
                Globals.ALIAS_DAY_DELTA = 0
            self.spin_ctrl_9.SetValue(Globals.ALIAS_DAY_DELTA)

        if prefDict and "fontSize" in prefDict:
            Globals.FONT_SIZE = int(prefDict["fontSize"])
            Globals.HEADER_FONT_SIZE = Globals.FONT_SIZE + 7
            self.spin_ctrl_10.SetValue(Globals.FONT_SIZE)

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

        if not prefDict or (prefDict and not prefDict["colVisibility"]):
            self.prefs["colVisibility"] = self.parent.gridPanel.getColVisibility()
        elif prefDict and prefDict["colVisibility"]:
            if self.prefs["colVisibility"]:
                self.parent.gridPanel.grid1ColVisibility = self.prefs["colVisibility"][
                    0
                ]
            if self.prefs["colVisibility"] and len(self.prefs["colVisibility"]) > 1:
                self.parent.gridPanel.grid2ColVisibility = self.prefs["colVisibility"][
                    1
                ]
            self.parent.gridPanel.setColVisibility()

        if prefDict and "saveColVisibility" in prefDict:
            if (
                isinstance(self.prefs["saveColVisibility"], str)
                and prefDict["saveColVisibility"].lower() == "true"
            ) or prefDict["saveColVisibility"] == True:
                self.checkbox_15.Set3StateValue(wx.CHK_CHECKED)
                Globals.SAVE_VISIBILITY = True
            else:
                self.checkbox_15.Set3StateValue(wx.CHK_UNCHECKED)
                Globals.SAVE_VISIBILITY = False
        else:
            self.checkbox_15.Set3StateValue(wx.CHK_UNCHECKED)
            Globals.SAVE_VISIBILITY = False

    @api_tool_decorator()
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
        if self.GetSize() == self.size:
            self.Fit()
        self.Refresh()

    @api_tool_decorator()
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
            "syncGridScroll": self.checkbox_13.IsChecked(),
            "immediateChild": self.checkbox_14.IsChecked(),
            "aliasDayDelta": self.spin_ctrl_9.GetValue(),
            "colVisibility": self.parent.gridPanel.getColVisibility(),
            "fontSize": self.spin_ctrl_10.GetValue(),
            "saveColVisibility": self.checkbox_15.IsChecked(),
        }

        Globals.FONT_SIZE = int(self.prefs["fontSize"])
        Globals.HEADER_FONT_SIZE = Globals.FONT_SIZE + 7
        Globals.SET_APP_STATE_AS_SHOW = self.prefs["setStateShow"]
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
        Globals.MATCH_SCROLL_POS = self.prefs["syncGridScroll"]
        Globals.GET_IMMEDIATE_SUBGROUPS = self.prefs["immediateChild"]
        Globals.ALIAS_DAY_DELTA = self.prefs["aliasDayDelta"]
        Globals.SAVE_VISIBILITY = self.prefs["saveColVisibility"]

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
        elif self.IsShown():
            self.Close()

    @api_tool_decorator()
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
        if "useJsonForCmd" in self.prefs:
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
        if "syncGridScroll" in self.prefs:
            if (
                isinstance(self.prefs["syncGridScroll"], str)
                and self.prefs["syncGridScroll"].lower() == "true"
            ) or self.prefs["syncGridScroll"] == True:
                self.checkbox_13.Set3StateValue(wx.CHK_CHECKED)
                Globals.MATCH_SCROLL_POS = True
            else:
                self.checkbox_13.Set3StateValue(wx.CHK_UNCHECKED)
                Globals.MATCH_SCROLL_POS = False
        if "immediateChild" in self.prefs:
            if (
                isinstance(self.prefs["immediateChild"], str)
                and self.prefs["immediateChild"].lower() == "true"
            ) or self.prefs["immediateChild"] == True:
                self.checkbox_14.Set3StateValue(wx.CHK_CHECKED)
                Globals.GET_IMMEDIATE_SUBGROUPS = True
            else:
                self.checkbox_14.Set3StateValue(wx.CHK_UNCHECKED)
                Globals.GET_IMMEDIATE_SUBGROUPS = False
        if "aliasDayDelta" in self.prefs:
            Globals.ALIAS_DAY_DELTA = int(self.prefs["aliasDayDelta"])
            if Globals.ALIAS_DAY_DELTA > Globals.ALIAS_MAX_DAY_DELTA:
                Globals.ALIAS_DAY_DELTA = Globals.ALIAS_MAX_DAY_DELTA
            if Globals.ALIAS_DAY_DELTA < 0:
                Globals.ALIAS_DAY_DELTA = 0
            self.spin_ctrl_9.SetValue(Globals.ALIAS_DAY_DELTA)
        if "fontSize" in self.prefs:
            Globals.FONT_SIZE = int(self.prefs["fontSize"])
            Globals.HEADER_FONT_SIZE = Globals.FONT_SIZE + 7
            self.spin_ctrl_10.SetValue(Globals.FONT_SIZE)
        if "colVisibility" in self.prefs:
            self.colVisibilty = self.prefs["colVisibility"]
            if self.prefs["colVisibility"]:
                self.parent.gridPanel.grid1ColVisibility = self.prefs["colVisibility"][
                    0
                ]
            if self.prefs["colVisibility"] and len(self.prefs["colVisibility"]) > 1:
                self.parent.gridPanel.grid2ColVisibility = self.prefs["colVisibility"][
                    1
                ]
        if "saveColVisibility" in self.prefs:
            if (
                isinstance(self.prefs["saveColVisibility"], str)
                and self.prefs["saveColVisibility"].lower() == "true"
            ) or self.prefs["saveColVisibility"] == True:
                self.checkbox_15.Set3StateValue(wx.CHK_CHECKED)
                Globals.SAVE_VISIBILITY = True
            else:
                self.checkbox_15.Set3StateValue(wx.CHK_UNCHECKED)
                Globals.SAVE_VISIBILITY = False

    @api_tool_decorator()
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
        self.prefs["syncGridScroll"] = Globals.MATCH_SCROLL_POS
        self.prefs["immediateChild"] = Globals.GET_IMMEDIATE_SUBGROUPS
        self.prefs["aliasDayDelta"] = Globals.ALIAS_DAY_DELTA
        self.prefs["fontSize"] = Globals.FONT_SIZE
        self.prefs["colVisibility"] = self.parent.gridPanel.getColVisibility()
        self.prefs["saveColVisibility"] = Globals.SAVE_VISIBILITY

        return self.prefs

    @api_tool_decorator()
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
        elif key == "syncGridScroll":
            return Globals.MATCH_SCROLL_POS
        elif key == "immediateChild":
            return Globals.GET_IMMEDIATE_SUBGROUPS
        elif key == "aliasDayDelta":
            return Globals.ALIAS_DAY_DELTA
        elif key == "fontSize":
            return Globals.FONT_SIZE
        elif key == "saveColVisibility":
            return Globals.SAVE_VISIBILITY
        else:
            return None

    def onResize(self, event):
        self.Refresh()
        event.Skip()

    def addPrefToPanel(
        self, sourcePanel, sourceSizer, label, inputObjType, toolTip="", choice=[]
    ):
        panel = wx.Panel(sourcePanel, wx.ID_ANY)
        if sourceSizer.GetEffectiveRowsCount() >= sourceSizer.GetRows():
            sourceSizer.SetRows(sourceSizer.GetRows() + 1)
        sourceSizer.Add(panel, 1, wx.ALL | wx.EXPAND, 5)

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(
            panel,
            wx.ID_ANY,
            label,
            style=wx.ST_ELLIPSIZE_END,
        )
        label.SetToolTip(toolTip)
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
        if inputObj:
            grid_sizer.Add(inputObj, 0, wx.ALIGN_RIGHT | wx.EXPAND, 0)

        panel.SetSizer(sizer)
        panel_2.SetSizer(grid_sizer)

        return panel, panel_2, inputObj
