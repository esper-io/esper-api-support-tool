#!/usr/bin/env python

import Common.Globals as Globals
import wx


class CommandDialog(wx.Dialog):
    def __init__(self, title, value="{\n\n}"):
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
            self.panel_1, wx.ID_ANY, "Please Enter Command JSON below:"
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
