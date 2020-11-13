import Common.Globals as Globals
import wx


class CheckboxMessageBox(wx.Dialog):
    def __init__(self, title, caption, *args, **kwds):
        # begin wxGlade: CheckboxMessageBox.__init__
        # kwds["style"] = kwds.get("style", 0) |
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
        # end wxGlade

    def __set_properties(self, title):
        # begin wxGlade: CheckboxMessageBox.__set_properties
        self.SetTitle(title)
        self.SetSize((400, 200))
        self.cancelBtn.SetFocus()
        # end wxGlade

    def __do_layout(self, caption):
        # begin wxGlade: CheckboxMessageBox.__do_layout
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
        sizer_4.Add(self.checkbox_1, 0, wx.ALL, 5)
        label_1 = wx.StaticText(
            self.panel_3, wx.ID_ANY, "Do not show again this session"
        )
        label_1.Bind(wx.EVT_LEFT_DOWN, self.toggleCheckbox)
        sizer_4.Add(label_1, 0, wx.BOTTOM | wx.RIGHT | wx.TOP, 5)
        sizer_2.Add(sizer_4, 1, wx.ALIGN_BOTTOM | wx.ALL, 5)
        sizer_5.Add(self.okBtn, 0, wx.ALL, 5)
        sizer_5.Add(self.cancelBtn, 0, wx.ALL, 5)
        sizer_2.Add(sizer_5, 1, wx.ALIGN_BOTTOM | wx.ALL, 5)
        self.panel_3.SetSizer(sizer_2)
        grid_sizer_1.Add(self.panel_3, 1, wx.ALIGN_RIGHT, 0)
        self.panel_1.SetSizer(grid_sizer_1)
        sizer_1.Add(self.panel_1, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        self.Layout()
        # end wxGlade

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


# end of class CheckboxMessageBox


class CommandDialog(wx.Dialog):
    def __init__(self, title, *args, **kwds):
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
            self.panel_2, wx.ID_ANY, "", style=wx.TE_MULTILINE
        )
        self.okBtn = wx.Button(self.panel_1, wx.ID_OK, "OK")
        self.cancelBtn = wx.Button(self.panel_1, wx.ID_CANCEL, "Cancel")

        self.okBtn.Bind(wx.EVT_BUTTON, self.OnClose)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.OnClose)

        self.__set_properties(title)
        self.__do_layout()
        # end wxGlade

    def __set_properties(self, title):
        # begin wxGlade: MyDialog.__set_properties
        self.SetTitle(title)
        self.SetSize((500, 400))
        self.text_ctrl_1.SetFocus()
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MyDialog.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
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
        # end wxGlade

    def GetValue(self):
        return self.text_ctrl_1.GetValue()

    def OnClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        else:
            self.Close()

    # end of class MyDialog
