import Common.Globals as Globals
import wx


class CheckboxMessageBox(wx.Dialog):
    def __init__(self, title, caption, *args, **kwds):
        super(CheckboxMessageBox, self).__init__(
            None,
            wx.ID_ANY,
            size=(400, 200),
            style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP | wx.OK | wx.CANCEL,
        )
        self.SetSize((400, 200))
        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.panel_2 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.panel_3 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.checkbox_1 = wx.CheckBox(self.panel_3, wx.ID_ANY, "")
        self.okBtn = wx.Button(self.panel_3, wx.ID_OK, "OK")
        self.cancelBtn = wx.Button(self.panel_3, wx.ID_CANCEL, "Cancel")

        self.okBtn.Bind(wx.EVT_BUTTON, self.OnClose)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.OnClose)

        self.__set_properties(title)
        self.__do_layout(caption)

    def __set_properties(self, title):
        self.SetTitle(title)
        self.SetSize((400, 200))
        self.cancelBtn.SetFocus()

    def __do_layout(self, caption):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self.panel_2, wx.ID_ANY, caption)
        title.Wrap(375)
        sizer_3.Add(title, 0, wx.ALL | wx.EXPAND, 5)
        self.panel_2.SetSizer(sizer_3)
        grid_sizer_1.Add(self.panel_2, 1, wx.ALL | wx.EXPAND, 5)
        sizer_4.Add(self.checkbox_1, 0, wx.BOTTOM | wx.RIGHT | wx.TOP, 5)
        label_1 = wx.StaticText(self.panel_3, wx.ID_ANY, "Do not show again")
        label_1.Bind(wx.EVT_LEFT_DOWN, self.toggleCheckbox)
        sizer_4.Add(label_1, 0, wx.BOTTOM | wx.RIGHT | wx.TOP, 5)
        sizer_2.Add(sizer_4, 1, wx.ALIGN_BOTTOM | wx.BOTTOM | wx.RIGHT | wx.TOP, 5)
        sizer_5.Add(self.okBtn, 0, wx.ALL, 5)
        sizer_5.Add(self.cancelBtn, 0, wx.ALL, 5)
        sizer_2.Add(sizer_5, 1, wx.ALIGN_BOTTOM | wx.ALL, 5)
        self.panel_3.SetSizer(sizer_2)
        grid_sizer_1.Add(self.panel_3, 1, wx.ALIGN_RIGHT, 0)
        self.panel_1.SetSizer(grid_sizer_1)
        sizer_1.Add(self.panel_1, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        self.Layout()

    def toggleCheckbox(self, event):
        if self.checkbox_1.IsChecked():
            self.checkbox_1.SetValue(False)
        else:
            self.checkbox_1.SetValue(True)
        event.Skip()

    def OnClose(self, event):
        if self.checkbox_1.GetValue():
            Globals.SHOW_GRID_DIALOG = False
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        else:
            self.Close()
        self.Destroy()


class CommandDialog(wx.Dialog):
    def __init__(self, title, value="{\n\n}", *args, **kwds):
        super(CommandDialog, self).__init__(
            None,
            wx.ID_ANY,
            size=(400, 200),
            style=wx.DEFAULT_DIALOG_STYLE
            | wx.STAY_ON_TOP
            | wx.OK
            | wx.CANCEL
            | wx.RESIZE_BORDER,
        )
        self.SetSize((500, 400))
        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.panel_2 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.text_ctrl_1 = wx.TextCtrl(
            self.panel_2, wx.ID_ANY, value, style=wx.TE_MULTILINE
        )
        self.text_ctrl_1.SetValue(value)
        self.panel_3 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.cmdTypeBox = wx.ComboBox(
            self.panel_3,
            wx.ID_ANY,
            choices=Globals.COMMAND_TYPES,
            style=wx.CB_DROPDOWN | wx.CB_READONLY | wx.CB_SIMPLE | wx.CB_SORT,
        )
        self.okBtn = wx.Button(self.panel_1, wx.ID_OK, "OK")
        self.cancelBtn = wx.Button(self.panel_1, wx.ID_CANCEL, "Cancel")

        self.okBtn.Bind(wx.EVT_BUTTON, self.OnClose)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.OnClose)

        self.__set_properties(title)
        self.__do_layout()

    def __set_properties(self, title):
        self.SetTitle(title)
        self.SetSize((500, 400))
        self.text_ctrl_1.SetFocus()

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.GridSizer(1, 1, 0, 0)
        label_1 = wx.StaticText(
            self.panel_1, wx.ID_ANY, "Please Enter Device Config JSON below:"
        )
        label_1.SetFont(
            wx.Font(
                11,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_LIGHT,
                0,
                "",
            )
        )
        sizer_2.Add(label_1, 0, wx.ALL, 5)
        sizer_2.Add((20, 20), 0, wx.EXPAND, 0)
        sizer_3.Add(self.text_ctrl_1, 0, wx.EXPAND, 0)
        self.panel_2.SetSizer(sizer_3)
        sizer_2.Add(self.panel_2, 1, wx.ALL | wx.EXPAND, 5)
        sizer_2.Add((20, 20), 0, wx.EXPAND, 0)
        label_2 = wx.StaticText(self.panel_3, wx.ID_ANY, "Command Type")
        label_2.SetFont(
            wx.Font(
                11,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_LIGHT,
                0,
                "",
            )
        )
        sizer_5.Add(label_2, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        sizer_5.Add(
            self.cmdTypeBox, 0, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND | wx.SHAPED, 0
        )
        self.panel_3.SetSizer(sizer_5)
        sizer_2.Add(self.panel_3, 1, wx.EXPAND, 0)
        static_line_1 = wx.StaticLine(self.panel_1, wx.ID_ANY)
        sizer_2.Add(static_line_1, 0, wx.EXPAND, 0)
        sizer_2.Add((20, 20), 0, wx.EXPAND, 0)
        sizer_4.Add(self.okBtn, 0, wx.ALL, 5)
        sizer_4.Add((20, 20), 0, wx.ALL, 5)
        sizer_4.Add(self.cancelBtn, 0, wx.ALL, 5)
        sizer_2.Add(sizer_4, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        self.Layout()

    def GetValue(self):
        return self.text_ctrl_1.GetValue(), self.cmdTypeBox.GetValue()

    def OnClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        else:
            self.Close()


class ProgressCheckDialog(wx.Dialog):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MyDialog.__init__
        super(ProgressCheckDialog, self).__init__(
            None,
            wx.ID_ANY,
            size=(375, 250),
            style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP | wx.OK,
        )
        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.panel_2 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.okBtn = wx.Button(self.panel_1, wx.ID_ANY, "OK")

        self.okBtn.Bind(wx.EVT_BUTTON, self.OnClose)

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MyDialog.__set_properties
        self.SetTitle("Progress Check")
        self.SetSize((375, 250))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MyDialog.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.StaticBoxSizer(
            wx.StaticBox(self.panel_1, wx.ID_ANY, ""), wx.VERTICAL
        )
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        label_2 = wx.StaticText(self.panel_2, wx.ID_ANY, "Progress Check:")
        label_2.SetFont(
            wx.Font(
                11,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        sizer_2.Add(label_2, 0, 0, 0)
        sizer_2.Add((20, 20), 0, wx.EXPAND, 0)
        label_1 = wx.StaticText(
            self.panel_2,
            wx.ID_ANY,
            "Please check the Esper Console for detailed results for the action taken.\nThe action may take some time to be reflected on each device.",
        )
        label_1.Wrap(300)
        sizer_2.Add(label_1, 0, 0, 0)
        self.panel_2.SetSizer(sizer_2)
        grid_sizer_1.Add(self.panel_2, 1, wx.ALL | wx.EXPAND, 10)
        grid_sizer_1.Add(self.okBtn, 0, wx.ALIGN_RIGHT | wx.ALL, 15)
        self.panel_1.SetSizer(grid_sizer_1)
        sizer_1.Add(self.panel_1, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        self.Layout()
        # end wxGlade

    def OnClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        else:
            self.Close()
        self.Destroy()


class CmdConfirmDialog(wx.Dialog):
    def __init__(self, commandType, cmdFormatted, applyToType, applyTo, *args, **kwds):
        # begin wxGlade: MyDialog.__init__
        super(CmdConfirmDialog, self).__init__(
            None,
            wx.ID_ANY,
            size=(500, 300),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.SetSize((500, 300))
        self.panel_8 = wx.Panel(self, wx.ID_ANY)
        self.panel_7 = wx.Panel(self, wx.ID_ANY)
        self.window_1_pane_1 = wx.Panel(self.panel_7, wx.ID_ANY)
        self.text_ctrl_1 = wx.TextCtrl(
            self.window_1_pane_1,
            wx.ID_ANY,
            cmdFormatted,
            style=wx.HSCROLL
            | wx.TE_LEFT
            | wx.TE_MULTILINE
            | wx.TE_READONLY
            | wx.TE_WORDWRAP,
        )
        self.panel_6 = wx.Panel(self, wx.ID_ANY)
        self.panel_2 = wx.Panel(self.panel_6, wx.ID_ANY)
        self.button_2 = wx.Button(self.panel_2, wx.ID_OK, "OK")
        self.button_1 = wx.Button(self.panel_2, wx.ID_CANCEL, "Cancel")

        self.button_2.Bind(wx.EVT_BUTTON, self.OnClose)
        self.button_1.Bind(wx.EVT_BUTTON, self.OnClose)

        self.__set_properties()
        self.__do_layout(commandType, applyToType, applyTo)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MyDialog.__set_properties
        self.SetTitle("Command Confirmation")
        self.SetSize((500, 300))
        self.text_ctrl_1.SetMinSize((400, 200))
        self.window_1_pane_1.SetMinSize((400, 200))
        self.button_2.SetFocus()
        # end wxGlade

    def __do_layout(self, commandType, applyToType, applyTo):
        # begin wxGlade: MyDialog.__do_layout
        sizer_7 = wx.BoxSizer(wx.VERTICAL)
        sizer_6 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.GridSizer(1, 1, 0, 0)
        sizer_4 = wx.BoxSizer(wx.VERTICAL)
        sizer_9 = wx.BoxSizer(wx.VERTICAL)
        label_2 = wx.StaticText(self.panel_8, wx.ID_ANY, "Commnd Confirmation")
        label_2.SetFont(
            wx.Font(
                12,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        sizer_9.Add(label_2, 0, wx.EXPAND, 0)
        static_line_2 = wx.StaticLine(self.panel_8, wx.ID_ANY)
        sizer_9.Add(static_line_2, 0, wx.EXPAND, 0)
        label_5 = wx.StaticText(
            self.panel_8,
            wx.ID_ANY,
            "About to try applying the %s command on the %s, %s, continue?"
            % (commandType, applyToType, applyTo),
            style=wx.ALIGN_LEFT,
        )
        label_5.Wrap(500)
        sizer_9.Add(label_5, 0, wx.EXPAND | wx.LEFT | wx.TOP, 5)
        self.panel_8.SetSizer(sizer_9)
        sizer_7.Add(self.panel_8, 0, wx.ALL | wx.EXPAND, 5)
        sizer_4.Add(self.text_ctrl_1, 0, wx.ALL | wx.EXPAND, 5)
        self.window_1_pane_1.SetSizer(sizer_4)
        sizer_3.Add(self.window_1_pane_1, 0, wx.ALL | wx.EXPAND | wx.FIXED_MINSIZE, 5)
        self.panel_7.SetSizer(sizer_3)
        sizer_7.Add(self.panel_7, 1, wx.ALL | wx.EXPAND, 5)
        sizer_2.Add(self.button_2, 0, wx.ALIGN_BOTTOM | wx.ALL, 10)
        sizer_2.Add(self.button_1, 0, wx.ALIGN_BOTTOM | wx.ALL, 10)
        self.panel_2.SetSizer(sizer_2)
        sizer_6.Add(self.panel_2, 1, wx.ALIGN_RIGHT, 0)
        self.panel_6.SetSizer(sizer_6)
        sizer_7.Add(self.panel_6, 0, wx.ALIGN_RIGHT, 0)
        self.SetSizer(sizer_7)
        self.Layout()
        # end wxGlade

    def OnClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        else:
            self.Close()
        self.Destroy()


class PreferencesDialog(wx.Dialog):
    def __init__(self, prefDict, parent=None, *args, **kwds):
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
            "recentAuth",
            "lastAuth",
        ]

        self.SetSize((500, 400))
        self.window_1_pane_1 = wx.ScrolledWindow(
            self, wx.ID_ANY, style=wx.TAB_TRAVERSAL
        )
        self.panel_4 = wx.Panel(self.window_1_pane_1, wx.ID_ANY)
        self.checkbox_2 = wx.CheckBox(self.panel_4, wx.ID_ANY, "")

        self.panel_5 = wx.Panel(self.window_1_pane_1, wx.ID_ANY)
        self.panel_3 = wx.Panel(self.panel_5, wx.ID_ANY)
        self.text_ctrl_3 = wx.TextCtrl(self.panel_3, wx.ID_ANY, str(Globals.limit))

        self.panel_6 = wx.Panel(self.window_1_pane_1, wx.ID_ANY)
        self.panel_2 = wx.Panel(self.panel_6, wx.ID_ANY)
        self.text_ctrl_2 = wx.TextCtrl(self.panel_2, wx.ID_ANY, str(Globals.offset))

        self.panel_7 = wx.Panel(self.window_1_pane_1, wx.ID_ANY)
        self.panel_8 = wx.Panel(self.panel_7, wx.ID_ANY)
        self.text_ctrl_4 = wx.TextCtrl(
            self.panel_8, wx.ID_ANY, str(Globals.COMMAND_TIMEOUT)
        )

        self.button_1 = wx.Button(self, wx.ID_APPLY, "Apply")

        if prefDict and not prefDict["enableDevice"]:
            self.checkbox_2.Set3StateValue(wx.CHK_UNCHECKED)
        else:
            self.checkbox_2.Set3StateValue(wx.CHK_CHECKED)
        self.button_1.Bind(wx.EVT_BUTTON, self.OnApply)

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.SetTitle("Preferences")
        self.SetSize((500, 400))
        self.window_1_pane_1.SetMinSize((437, 271))
        self.window_1_pane_1.SetScrollRate(10, 10)

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.GridSizer(1, 1, 0, 0)
        grid_sizer_4 = wx.GridSizer(5, 1, 0, 0)
        sizer_7 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_8 = wx.GridSizer(1, 1, 0, 0)
        sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_6 = wx.GridSizer(1, 1, 0, 0)
        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_7 = wx.GridSizer(1, 1, 0, 0)
        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_3 = wx.GridSizer(1, 1, 0, 0)
        label_2 = wx.StaticText(self, wx.ID_ANY, "Preferences:")
        sizer_1.Add(label_2, 0, wx.ALL, 5)
        label_3 = wx.StaticText(self.panel_4, wx.ID_ANY, "Enable Device Selection")
        sizer_4.Add(label_3, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        grid_sizer_3.Add(
            self.checkbox_2, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0
        )
        sizer_4.Add(grid_sizer_3, 1, wx.EXPAND, 0)
        self.panel_4.SetSizer(sizer_4)
        grid_sizer_4.Add(self.panel_4, 1, wx.EXPAND, 0)
        label_4 = wx.StaticText(self.panel_5, wx.ID_ANY, "API Request Limit")
        sizer_5.Add(label_4, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        grid_sizer_7.Add(
            self.text_ctrl_3, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0
        )
        self.panel_3.SetSizer(grid_sizer_7)
        sizer_5.Add(self.panel_3, 1, wx.EXPAND, 0)
        self.panel_5.SetSizer(sizer_5)
        grid_sizer_4.Add(self.panel_5, 1, wx.EXPAND, 0)
        label_5 = wx.StaticText(self.panel_6, wx.ID_ANY, "API Request Offset")
        sizer_6.Add(label_5, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        grid_sizer_6.Add(
            self.text_ctrl_2, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0
        )
        self.panel_2.SetSizer(grid_sizer_6)
        sizer_6.Add(self.panel_2, 1, wx.EXPAND, 0)
        self.panel_6.SetSizer(sizer_6)
        grid_sizer_4.Add(self.panel_6, 1, wx.EXPAND, 0)
        label_6 = wx.StaticText(self.panel_7, wx.ID_ANY, "Command Timeout (seconds)")
        sizer_7.Add(label_6, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        grid_sizer_8.Add(
            self.text_ctrl_4, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0
        )
        self.panel_8.SetSizer(grid_sizer_8)
        sizer_7.Add(self.panel_8, 1, wx.EXPAND, 0)
        self.panel_7.SetSizer(sizer_7)
        grid_sizer_4.Add(self.panel_7, 1, wx.EXPAND, 0)
        grid_sizer_4.Add((0, 0), 0, 0, 0)
        self.window_1_pane_1.SetSizer(grid_sizer_4)
        sizer_1.Add(self.window_1_pane_1, 0, wx.ALL | wx.EXPAND, 10)
        sizer_2.Add(self.button_1, 0, wx.ALIGN_BOTTOM | wx.ALIGN_RIGHT | wx.ALL, 10)
        sizer_1.Add(sizer_2, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        self.Layout()

    def OnApply(self, event):
        self.prefs = {
            "enableDevice": self.checkbox_2.IsChecked(),
            "limit": self.text_ctrl_3.GetValue(),
            "offset": self.text_ctrl_2.GetValue(),
            "recentAuth": self.prefs["recentAuth"]
            if self.prefs and self.prefs["recentAuth"]
            else [Globals.csv_auth_path],
            "lastAuth": Globals.csv_auth_path,
            "gridDialog": Globals.SHOW_GRID_DIALOG,
            "commandTimeout": self.text_ctrl_2.GetValue(),
        }

        Globals.limit = self.prefs["limit"]
        Globals.offset = self.prefs["offset"]
        Globals.COMMAND_TIMEOUT = int(self.prefs["commandTimeout"])

        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        else:
            self.Close()

    def SetPrefs(self, prefs):
        self.prefs = prefs

        if "enableDevice" in self.prefs:
            self.checkbox_2.SetValue(self.prefs["enableDevice"])
        if "limit" in self.prefs and self.prefs["limit"]:
            Globals.limit = self.prefs["limit"]
        if "offset" in self.prefs and self.prefs["offset"]:
            Globals.offset = self.prefs["offset"]
        if "gridDialog" in self.prefs and type(self.prefs["gridDialog"]) == bool:
            Globals.SHOW_GRID_DIALOG = self.prefs["gridDialog"]
        if "commandTimeout" in self.prefs and self.prefs["commandTimeout"]:
            Globals.COMMAND_TIMEOUT = int(self.prefs["commandTimeout"])

    def GetPrefs(self):
        if not self.prefs:
            self.prefs = {}
        for key in self.prefKeys:
            if key not in self.prefs.keys():
                self.prefs[key] = self.getDefaultKeyValue(key)
        self.prefs[
            "gridDialog"
        ] = Globals.SHOW_GRID_DIALOG  # update pref value to match global value
        self.prefs["recentAuth"] = list(dict.fromkeys(self.prefs["recentAuth"]))
        if len(self.prefs["recentAuth"]) > Globals.MAX_RECENT_ITEMS:
            self.prefs["recentAuth"] = self.prefs["recentAuth"][
                len(self.prefs["recentAuth"])
                - Globals.MAX_RECENT_ITEMS : len(self.prefs["recentAuth"])
            ]

        return self.prefs

    def getDefaultKeyValue(self, key):
        if key == "enableDevice":
            return True
        elif key == "limit":
            return Globals.limit
        elif key == "offset":
            return Globals.offset
        elif key == "gridDialog":
            return Globals.SHOW_GRID_DIALOG
        elif key == "recentAuth":
            return [Globals.csv_auth_path] if Globals.csv_auth_path else []
        elif key == "lastAuth":
            return Globals.csv_auth_path
        elif key == "commandTimeout":
            return Globals.COMMAND_TIMEOUT
        else:
            return None
