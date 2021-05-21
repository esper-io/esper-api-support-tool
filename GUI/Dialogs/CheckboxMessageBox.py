#!/usr/bin/env python

from Common.decorator import api_tool_decorator
import Common.Globals as Globals
import wx


class CheckboxMessageBox(wx.Dialog):
    def __init__(self, title, caption):
        super(CheckboxMessageBox, self).__init__(
            None,
            wx.ID_ANY,
            size=(400, 200),
            style=wx.DEFAULT_DIALOG_STYLE | wx.OK | wx.CANCEL,
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

    @api_tool_decorator
    def __set_properties(self, title):
        self.SetTitle(title)
        self.SetSize((400, 200))
        self.cancelBtn.SetFocus()

    @api_tool_decorator
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
        self.Centre()

    @api_tool_decorator
    def toggleCheckbox(self, event):
        if self.checkbox_1.IsChecked():
            self.checkbox_1.SetValue(False)
        else:
            self.checkbox_1.SetValue(True)
        event.Skip()

    @api_tool_decorator
    def getCheckBoxValue(self):
        return self.checkbox_1.GetValue()

    @api_tool_decorator
    def OnClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        elif self.IsShown():
            self.Close()
        self.DestroyLater()
