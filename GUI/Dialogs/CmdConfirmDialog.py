#!/usr/bin/env python

import Common.Globals as Globals
import wx


class CmdConfirmDialog(wx.Dialog):
    def __init__(self, commandType, cmdFormatted, applyToType, applyTo):
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
        label_5.Wrap(475)
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
