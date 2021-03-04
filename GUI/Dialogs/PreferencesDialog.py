#!/usr/bin/env python

import Common.Globals as Globals
import wx


class PreferencesDialog(wx.Dialog):
    def __init__(self, prefDict, parent=None):
        super(PreferencesDialog, self).__init__(
            None,
            wx.ID_ANY,
            size=(500, 400),
            style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP,  # | wx.RESIZE_BORDER,
        )
        self.SetTitle("Preferences")
        self.SetSize((500, 400))
        self.SetMinSize((500, 400))

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

        self.general = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        self.general.Hide()
        sizer_5.Add(self.general, 1, wx.EXPAND, 0)

        sizer_6 = wx.FlexGridSizer(3, 1, 0, 0)

        self.panel_3 = wx.Panel(self.general, wx.ID_ANY)
        sizer_6.Add(self.panel_3, 1, wx.ALL | wx.EXPAND, 5)

        sizer_7 = wx.BoxSizer(wx.HORIZONTAL)

        label_1 = wx.StaticText(self.panel_3, wx.ID_ANY, "Enable Device Selection")
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

        label_2 = wx.StaticText(self.panel_5, wx.ID_ANY, "API Request Limit")
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

        label_4 = wx.StaticText(self.panel_9, wx.ID_ANY, "API Request Offset")
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

        self.command = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        self.command.Hide()
        sizer_5.Add(self.command, 1, wx.EXPAND, 0)

        sizer_14 = wx.FlexGridSizer(2, 1, 0, 0)

        self.panel_25 = wx.Panel(self.command, wx.ID_ANY)
        sizer_14.Add(self.panel_25, 1, wx.ALL | wx.EXPAND, 5)

        sizer_21 = wx.BoxSizer(wx.HORIZONTAL)

        label_12 = wx.StaticText(self.panel_25, wx.ID_ANY, "Command Timeout (seconds)")
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
            self.panel_27, wx.ID_ANY, "Reach Queued Command State Only"
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

        self.grid = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        self.grid.Hide()
        sizer_5.Add(self.grid, 1, wx.EXPAND, 0)

        sizer_16 = wx.FlexGridSizer(2, 1, 0, 0)

        self.panel_19 = wx.Panel(self.grid, wx.ID_ANY)
        sizer_16.Add(self.panel_19, 1, wx.ALL | wx.EXPAND, 5)

        sizer_17 = wx.BoxSizer(wx.HORIZONTAL)

        label_9 = wx.StaticText(self.panel_19, wx.ID_ANY, "Enable Grid Refresh")
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
            self.panel_21, wx.ID_ANY, "Grid Refresh Rate (seconds)"
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

        self.app = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        self.app.Hide()
        sizer_5.Add(self.app, 1, wx.EXPAND, 0)

        sizer_9 = wx.FlexGridSizer(3, 1, 0, 0)

        self.panel_7 = wx.Panel(self.app, wx.ID_ANY)
        sizer_9.Add(self.panel_7, 1, wx.ALL | wx.EXPAND, 5)

        sizer_12 = wx.BoxSizer(wx.HORIZONTAL)

        label_3 = wx.StaticText(
            self.panel_7, wx.ID_ANY, "Fetch All Installed Applications"
        )
        label_3.SetToolTip(
            "Fetches all installed applications, including those that are hidden."
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
            self.panel_13, wx.ID_ANY, "Show Application's Package Name"
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
            self.panel_15, wx.ID_ANY, "Get Applications for Each Device"
        )
        label_7.SetToolTip(
            "Fetch all applications for every device within a group.\nPerformance may be slower."
        )
        sizer_15.Add(label_7, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.panel_16 = wx.Panel(self.panel_15, wx.ID_ANY)
        sizer_15.Add(self.panel_16, 1, wx.EXPAND, 0)

        grid_sizer_7 = wx.GridSizer(1, 1, 0, 0)

        self.checkbox_6 = wx.CheckBox(self.panel_16, wx.ID_ANY, "")
        grid_sizer_7.Add(self.checkbox_6, 0, wx.ALIGN_RIGHT | wx.EXPAND, 0)

        self.prompts = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        self.prompts.Hide()
        sizer_5.Add(self.prompts, 1, wx.EXPAND, 0)

        sizer_19 = wx.FlexGridSizer(2, 1, 0, 0)

        self.panel_29 = wx.Panel(self.prompts, wx.ID_ANY)
        sizer_19.Add(self.panel_29, 1, wx.ALL | wx.EXPAND, 5)

        sizer_23 = wx.BoxSizer(wx.HORIZONTAL)

        label_14 = wx.StaticText(self.panel_29, wx.ID_ANY, "Grid Confirmation Prompt")
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
            self.panel_31, wx.ID_ANY, "Template Confirmation Prompt"
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
            self.checkbox_5.Set3StateValue(wx.CHK_UNCHECKED)
            Globals.SHOW_PKG_NAME = False
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
        }

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

        if self.prefs["getAllApps"]:
            Globals.USE_ENTERPRISE_APP = False
        else:
            Globals.USE_ENTERPRISE_APP = True

        if Globals.ENABLE_GRID_UPDATE and self.parent != None:
            self.parent.startUpdateThread()

        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        else:
            self.Close()

    def SetPrefs(self, prefs):
        self.prefs = prefs
        if not self.prefs:
            return

        if "enableDevice" in self.prefs:
            self.checkbox_1.SetValue(self.prefs["enableDevice"])
        if "limit" in self.prefs and self.prefs["limit"]:
            Globals.limit = self.prefs["limit"]
        if "offset" in self.prefs and self.prefs["offset"]:
            Globals.offset = self.prefs["offset"]
        if "gridDialog" in self.prefs and type(self.prefs["gridDialog"]) == bool:
            Globals.SHOW_GRID_DIALOG = self.prefs["gridDialog"]
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
        if "commandTimeout" in self.prefs and self.prefs["commandTimeout"]:
            Globals.COMMAND_TIMEOUT = int(self.prefs["commandTimeout"])
        if "updateRate" in self.prefs and self.prefs["updateRate"]:
            Globals.GRID_UPDATE_RATE = int(self.prefs["updateRate"])
        if "enableGridUpdate" in self.prefs and self.prefs["enableGridUpdate"]:
            self.checkbox_3.SetValue(self.prefs["enableGridUpdate"])
            Globals.ENABLE_GRID_UPDATE = self.checkbox_2.IsChecked()
            if Globals.ENABLE_GRID_UPDATE and self.parent != None:
                self.parent.startUpdateThread()
        if "windowSize" in self.prefs and self.prefs["windowSize"]:
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
        if "isMaximized" in self.prefs and self.prefs["isMaximized"]:
            if self.parent:
                self.parent.Maximize(self.prefs["isMaximized"])
        if "windowPosition" in self.prefs and self.prefs["windowPosition"]:
            if self.parent:
                if self.prefs["windowPosition"] == "1":
                    self.parent.Centre()
                else:
                    pos = tuple(self.prefs["windowPosition"])
                    self.parent.SetPosition(wx.Point(pos[0], pos[1]))
        if "getAllApps" in self.prefs and self.prefs["getAllApps"]:
            if (
                isinstance(self.prefs["getAllApps"], str)
                and self.prefs["getAllApps"].lower() == "false"
            ) or not self.prefs["getAllApps"]:
                Globals.USE_ENTERPRISE_APP = False
                self.checkbox_3.Set3StateValue(wx.CHK_CHECKED)
            elif (
                isinstance(self.prefs["getAllApps"], str)
                and self.prefs["getAllApps"].lower()
            ) == "true" or self.prefs["getAllApps"]:
                Globals.USE_ENTERPRISE_APP = True
                self.checkbox_3.Set3StateValue(wx.CHK_UNCHECKED)
            else:
                Globals.USE_ENTERPRISE_APP = True
                self.checkbox_3.Set3StateValue(wx.CHK_UNCHECKED)
        if "showPkg" in self.prefs and self.prefs["showPkg"]:
            if (
                isinstance(self.prefs["getAllApps"], str)
                and self.prefs["showPkg"].lower() == "false"
            ) or not self.prefs["showPkg"]:
                Globals.SHOW_PKG_NAME = False
                self.checkbox_4.Set3StateValue(wx.CHK_UNCHECKED)
            elif (
                isinstance(self.prefs["getAllApps"], str)
                and self.prefs["showPkg"].lower() == "true"
            ) or self.prefs["showPkg"]:
                Globals.SHOW_PKG_NAME = True
                self.checkbox_4.Set3StateValue(wx.CHK_CHECKED)
            else:
                Globals.SHOW_PKG_NAME = True
                self.checkbox_4.Set3StateValue(wx.CHK_CHECKED)

    def GetPrefs(self):
        if not self.prefs:
            self.prefs = {}
        for key in self.prefKeys:
            if key not in self.prefs.keys():
                self.prefs[key] = self.getDefaultKeyValue(key)

        self.prefs["reachQueueStateOnly"] = Globals.REACH_QUEUED_ONLY
        # self.prefs["getAppsForEachDevice"] = self.checkbox_5.IsChecked()
        self.prefs["getAllApps"] = Globals.USE_ENTERPRISE_APP
        self.prefs["showPkg"] = Globals.SHOW_PKG_NAME
        self.prefs[
            "gridDialog"
        ] = Globals.SHOW_GRID_DIALOG  # update pref value to match global value
        self.prefs["windowSize"] = (
            str(self.parent.GetSize()) if self.parent else Globals.MIN_SIZE
        )
        self.prefs["isMaximized"] = self.parent.IsMaximized() if self.parent else False
        self.prefs["templateDialog"] = Globals.SHOW_TEMPLATE_DIALOG
        self.prefs["templateUpdate"] = Globals.SHOW_TEMPLATE_UPDATE

        return self.prefs

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
        else:
            return None
