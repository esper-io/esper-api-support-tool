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
        emptyJson = "{\n\n}"

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_1, 1, wx.EXPAND, 0)

        sizer_2 = wx.BoxSizer(wx.VERTICAL)

        grid_sizer_1 = wx.GridSizer(2, 1, 0, 0)
        sizer_2.Add(grid_sizer_1, 1, wx.EXPAND, 0)

        self.window_1 = wx.SplitterWindow(self.panel_1, wx.ID_ANY)
        self.window_1.SetMinimumPaneSize(20)
        grid_sizer_1.Add(self.window_1, 1, wx.ALL | wx.EXPAND, 5)

        self.window_1_pane_1 = wx.Panel(self.window_1, wx.ID_ANY)

        sizer_7 = wx.BoxSizer(wx.VERTICAL)

        label_1 = wx.StaticText(self.window_1_pane_1, wx.ID_ANY, "Enter Cmd Args JSON:")
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
        sizer_7.Add(label_1, 0, wx.ALL, 5)

        self.panel_2 = wx.Panel(self.window_1_pane_1, wx.ID_ANY)
        sizer_7.Add(self.panel_2, 1, wx.ALL | wx.EXPAND, 5)

        sizer_3 = wx.GridSizer(1, 1, 0, 0)

        self.text_ctrl_1 = wx.TextCtrl(
            self.panel_2, wx.ID_ANY, "{\n\n}", style=wx.TE_MULTILINE
        )
        self.text_ctrl_1.SetFocus()
        sizer_3.Add(self.text_ctrl_1, 0, wx.EXPAND, 0)

        self.window_1_pane_2 = wx.Panel(self.window_1, wx.ID_ANY)

        sizer_8 = wx.BoxSizer(wx.VERTICAL)

        label_3 = wx.StaticText(
            self.window_1_pane_2, wx.ID_ANY, "Enter Schedule Args JSON:"
        )
        label_3.SetFont(
            wx.Font(
                11,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_LIGHT,
                0,
                "",
            )
        )
        sizer_8.Add(label_3, 0, wx.ALL, 5)

        self.panel_4 = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        sizer_8.Add(self.panel_4, 1, wx.ALL | wx.EXPAND, 5)

        sizer_9 = wx.GridSizer(1, 1, 0, 0)

        self.text_ctrl_2 = wx.TextCtrl(
            self.panel_4, wx.ID_ANY, "{\n\n}\n", style=wx.TE_MULTILINE
        )
        sizer_9.Add(self.text_ctrl_2, 0, wx.EXPAND, 0)

        self.panel_3 = wx.Panel(self.panel_1, wx.ID_ANY)
        grid_sizer_1.Add(self.panel_3, 1, wx.ALL | wx.EXPAND, 5)

        sizer_5 = wx.BoxSizer(wx.VERTICAL)

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
        sizer_5.Add(label_2, 0, wx.ALL, 5)

        self.cmdTypeBox = wx.ComboBox(
            self.panel_3,
            wx.ID_ANY,
            choices=Globals.COMMAND_TYPES,
            style=wx.CB_DROPDOWN | wx.CB_READONLY | wx.CB_SIMPLE | wx.CB_SORT,
        )
        sizer_5.Add(self.cmdTypeBox, 0, wx.ALL | wx.SHAPED, 5)

        static_line_1 = wx.StaticLine(self.panel_1, wx.ID_ANY)
        sizer_2.Add(static_line_1, 0, wx.EXPAND, 0)

        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2.Add(sizer_4, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        self.okBtn = wx.Button(self.panel_1, wx.ID_OK, "OK")
        sizer_4.Add(self.okBtn, 0, wx.ALL, 5)

        sizer_4.Add((20, 20), 0, wx.ALL, 5)

        self.cancelBtn = wx.Button(self.panel_1, wx.ID_CANCEL, "Cancel")
        sizer_4.Add(self.cancelBtn, 0, wx.ALL, 5)

        self.panel_3.SetSizer(sizer_5)

        self.panel_4.SetSizer(sizer_9)

        self.window_1_pane_2.SetSizer(sizer_8)

        self.panel_2.SetSizer(sizer_3)

        self.window_1_pane_1.SetSizer(sizer_7)

        self.window_1.SplitVertically(self.window_1_pane_1, self.window_1_pane_2)

        self.panel_1.SetSizer(sizer_2)

        self.okBtn.Bind(wx.EVT_BUTTON, self.OnClose)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.OnClose)

        self.SetSizer(sizer_1)

        self.Layout()
        self.Centre()

    def GetValue(self):
        return (
            self.text_ctrl_1.GetValue() + "_-_" + self.text_ctrl_2.GetValue(),
            self.cmdTypeBox.GetValue(),
        )

    def OnClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        else:
            self.Close()
