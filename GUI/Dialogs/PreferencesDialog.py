#!/usr/bin/env python

import Common.Globals as Globals
import wx


class PreferencesDialog(wx.Dialog):
    def __init__(self, prefDict, parent=None):
        super(PreferencesDialog, self).__init__(
            None,
            wx.ID_ANY,
            size=(500, 400),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.parent = parent
        self.prefs = prefDict
        self.prefKeys = [
            "enableDevice",
            "limit",
            "offset",
            "gridDialog",
            "updateRate",
        ]

        self.SetSize((500, 400))
        self.panel_1 = wx.ScrolledWindow(self, wx.ID_ANY, style=wx.TAB_TRAVERSAL)
        self.panel_3 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.checkbox_1 = wx.CheckBox(self.panel_3, wx.ID_ANY, "")
        self.panel_4 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.spin_ctrl_4 = wx.SpinCtrl(
            self.panel_4,
            id=wx.ID_ANY,
            min=Globals.MIN_LIMIT,
            max=Globals.MAX_LIMIT,
            initial=Globals.limit,
        )
        self.panel_7 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.spin_ctrl_1 = wx.SpinCtrl(
            self.panel_7, id=wx.ID_ANY, min=0, initial=Globals.offset
        )
        self.panel_6 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.spin_ctrl_3 = wx.SpinCtrl(
            self.panel_6, id=wx.ID_ANY, min=0, initial=Globals.COMMAND_TIMEOUT
        )
        self.panel_8 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.checkbox_2 = wx.CheckBox(self.panel_8, wx.ID_ANY, "")
        self.panel_5 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.spin_ctrl_2 = wx.SpinCtrl(
            self.panel_5,
            id=wx.ID_ANY,
            min=Globals.GRID_UPDATE_RATE,
            max=Globals.MAX_GRID_UPDATE_RATE,
            initial=Globals.GRID_UPDATE_RATE,
        )
        self.button_1 = wx.Button(self, wx.ID_ANY, "Apply")

        if prefDict and not prefDict["enableDevice"]:
            self.checkbox_1.Set3StateValue(wx.CHK_UNCHECKED)
        else:
            self.checkbox_1.Set3StateValue(wx.CHK_CHECKED)

        if prefDict and not prefDict["enableGridUpdate"]:
            self.checkbox_2.Set3StateValue(wx.CHK_UNCHECKED)
            Globals.ENABLE_GRID_UPDATE = False
        else:
            self.checkbox_2.Set3StateValue(wx.CHK_CHECKED)
            Globals.ENABLE_GRID_UPDATE = True
            if Globals.ENABLE_GRID_UPDATE and self.parent != None:
                self.parent.startUpdateThread()
        self.button_1.Bind(wx.EVT_BUTTON, self.OnApply)

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        # begin wxGlade: MyDialog.__set_properties
        self.SetTitle("Preferences")
        self.SetSize((500, 400))
        self.SetMinSize((500, 400))
        self.panel_1.SetScrollRate(10, 10)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MyDialog.__do_layout
        sizer_1 = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Preferences"), wx.VERTICAL
        )
        grid_sizer_1 = wx.GridSizer(1, 1, 0, 0)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_4 = wx.GridSizer(1, 2, 0, 0)
        grid_sizer_7 = wx.GridSizer(1, 2, 0, 0)
        grid_sizer_5 = wx.GridSizer(1, 2, 0, 0)
        grid_sizer_6 = wx.GridSizer(1, 2, 0, 0)
        grid_sizer_3 = wx.GridSizer(1, 2, 0, 0)
        grid_sizer_2 = wx.GridSizer(1, 2, 0, 0)
        label_1 = wx.StaticText(self.panel_3, wx.ID_ANY, "Enable Device Selection")
        label_1.SetToolTip(
            "Allow user to specify actions on a single device within a group"
        )
        grid_sizer_2.Add(label_1, 0, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0)
        grid_sizer_2.Add(self.checkbox_1, 0, wx.ALIGN_RIGHT, 0)
        self.panel_3.SetSizer(grid_sizer_2)
        sizer_2.Add(self.panel_3, 1, wx.ALL | wx.EXPAND, 5)
        label_2 = wx.StaticText(self.panel_4, wx.ID_ANY, "API Request Limit")
        grid_sizer_3.Add(label_2, 0, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0)
        grid_sizer_3.Add(
            self.spin_ctrl_4, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0
        )
        self.panel_4.SetSizer(grid_sizer_3)
        sizer_2.Add(self.panel_4, 1, wx.ALL | wx.EXPAND, 5)
        label_5 = wx.StaticText(self.panel_7, wx.ID_ANY, "API Request Offset")
        grid_sizer_6.Add(label_5, 0, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0)
        grid_sizer_6.Add(
            self.spin_ctrl_1, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0
        )
        self.panel_7.SetSizer(grid_sizer_6)
        sizer_2.Add(self.panel_7, 1, wx.ALL | wx.EXPAND, 5)
        label_4 = wx.StaticText(self.panel_6, wx.ID_ANY, "Command Timeout (seconds)")
        label_4.SetToolTip(
            "How long a command should wait on the status check before skipping."
        )
        grid_sizer_5.Add(label_4, 0, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0)
        grid_sizer_5.Add(self.spin_ctrl_3, 0, wx.ALIGN_RIGHT, 0)
        self.panel_6.SetSizer(grid_sizer_5)
        sizer_2.Add(self.panel_6, 1, wx.ALL | wx.EXPAND, 5)
        label_6 = wx.StaticText(self.panel_8, wx.ID_ANY, "Enable Grid Refresh")
        label_6.SetToolTip(
            "Allows the Grids to update cell data.\nOnly runs for datasets of %s or less."
            % Globals.MAX_UPDATE_COUNT
        )
        grid_sizer_7.Add(label_6, 0, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0)
        grid_sizer_7.Add(
            self.checkbox_2, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0
        )
        self.panel_8.SetSizer(grid_sizer_7)
        sizer_2.Add(self.panel_8, 1, wx.ALL | wx.EXPAND, 5)
        label_3 = wx.StaticText(self.panel_5, wx.ID_ANY, "Grid Refresh Rate (seconds)")
        label_3.SetToolTip("How often the Grid should update its cell data.")
        grid_sizer_4.Add(label_3, 0, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0)
        grid_sizer_4.Add(
            self.spin_ctrl_2, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0
        )
        self.panel_5.SetSizer(grid_sizer_4)
        sizer_2.Add(self.panel_5, 1, wx.ALL | wx.EXPAND, 5)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 1, wx.EXPAND, 0)
        grid_sizer_1.Add(self.button_1, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        sizer_1.Add(grid_sizer_1, 0, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        self.Layout()
        self.Centre()

    def OnApply(self, event):
        self.prefs = {
            "enableDevice": self.checkbox_1.IsChecked(),
            "limit": self.spin_ctrl_4.GetValue(),
            "offset": self.spin_ctrl_1.GetValue(),
            "gridDialog": Globals.SHOW_GRID_DIALOG,
            "templateDialog": Globals.SHOW_TEMPLATE_DIALOG,
            "templateUpdate": Globals.SHOW_TEMPLATE_UPDATE,
            "commandTimeout": self.spin_ctrl_3.GetValue(),
            "updateRate": self.spin_ctrl_2.GetValue(),
            "enableGridUpdate": self.checkbox_2.IsChecked(),
        }

        Globals.limit = self.prefs["limit"]
        Globals.offset = self.prefs["offset"]
        Globals.COMMAND_TIMEOUT = int(self.prefs["commandTimeout"])
        Globals.GRID_UPDATE_RATE = int(self.prefs["updateRate"])
        Globals.ENABLE_GRID_UPDATE = self.checkbox_2.IsChecked()

        if Globals.ENABLE_GRID_UPDATE and self.parent != None:
            self.parent.startUpdateThread()

        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        else:
            self.Close()

    def SetPrefs(self, prefs):
        self.prefs = prefs

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
        if "enableGridUpdate" in self.prefs and self.prefs["commandTimeout"]:
            self.checkbox_2.SetValue(self.prefs["enableGridUpdate"])
            Globals.ENABLE_GRID_UPDATE = self.checkbox_2.IsChecked()
            if Globals.ENABLE_GRID_UPDATE and self.parent != None:
                self.parent.startUpdateThread()

    def GetPrefs(self):
        if not self.prefs:
            self.prefs = {}
        for key in self.prefKeys:
            if key not in self.prefs.keys():
                self.prefs[key] = self.getDefaultKeyValue(key)
        self.prefs[
            "gridDialog"
        ] = Globals.SHOW_GRID_DIALOG  # update pref value to match global value
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
            return True
        else:
            return None
