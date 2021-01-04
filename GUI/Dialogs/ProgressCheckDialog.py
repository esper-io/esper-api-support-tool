#!/usr/bin/env python

import Common.Globals as Globals
import wx


class ProgressCheckDialog(wx.Dialog):
    def __init__(self):
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
