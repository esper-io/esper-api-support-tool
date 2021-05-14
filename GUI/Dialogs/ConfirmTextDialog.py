#!/usr/bin/env python

from Utility.Resource import openWebLinkInBrowser
from Common.decorator import api_tool_decorator
import Common.Globals as Globals
import wx
import wx.html as wxHtml


class ConfirmTextDialog(wx.Dialog):
    def __init__(self, title, label, caption, detail):
        # begin wxGlade: MyDialog.__init__
        minSize = (500, 400)
        super(ConfirmTextDialog, self).__init__(
            None,
            wx.ID_ANY,
            size=minSize,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.SetMinSize(minSize)
        self.SetSize(minSize)
        self.SetTitle(title)

        sizer_7 = wx.FlexGridSizer(4, 1, 0, 0)

        self.panel_8 = wx.Panel(self, wx.ID_ANY)
        sizer_7.Add(self.panel_8, 0, wx.ALL | wx.EXPAND, 5)

        sizer_9 = wx.BoxSizer(wx.VERTICAL)

        label_2 = wx.StaticText(self.panel_8, wx.ID_ANY, caption)
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

        label_5 = wx.StaticText(self.panel_8, wx.ID_ANY, label, style=wx.ALIGN_LEFT)
        label_5.Wrap(500)
        sizer_9.Add(label_5, 0, wx.EXPAND | wx.LEFT | wx.TOP, 5)

        self.text_ctrl_1 = wx.TextCtrl(
            self,
            wx.ID_ANY,
            detail,
            style=wx.HSCROLL
            | wx.TE_LEFT
            | wx.TE_MULTILINE
            | wx.TE_READONLY
            | wx.TE_WORDWRAP
            | wx.TE_BESTWRAP
            | wx.TE_AUTO_URL,
        )
        sizer_7.Add(self.text_ctrl_1, 0, wx.ALL | wx.EXPAND, 5)

        static_line_3 = wx.StaticLine(self, wx.ID_ANY)
        sizer_7.Add(static_line_3, 0, wx.EXPAND, 0)

        sizer_1 = wx.StdDialogButtonSizer()
        sizer_7.Add(sizer_1, 0, wx.ALIGN_RIGHT, 5)

        self.button_2 = wx.Button(self, wx.ID_OK, "OK")
        self.button_2.SetFocus()
        sizer_1.Add(self.button_2, 0, wx.ALIGN_BOTTOM | wx.ALL, 5)

        self.button_1 = wx.Button(self, wx.ID_CANCEL, "Cancel")
        sizer_1.Add(self.button_1, 0, wx.ALIGN_BOTTOM | wx.ALL, 5)

        sizer_1.Realize()

        self.panel_8.SetSizer(sizer_9)

        sizer_7.AddGrowableRow(1)
        sizer_7.AddGrowableCol(0)
        self.SetSizer(sizer_7)

        self.SetAffirmativeId(self.button_2.GetId())
        self.SetEscapeId(self.button_1.GetId())

        self.Layout()
        self.Centre()

        self.text_ctrl_1.Bind(wxHtml.EVT_HTML_LINK_CLICKED, openWebLinkInBrowser)
        self.button_2.Bind(wx.EVT_BUTTON, self.OnClose)
        self.button_1.Bind(wx.EVT_BUTTON, self.OnClose)
        # end wxGlade

    @api_tool_decorator
    def OnClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        elif self.IsShown():
            self.Close()
        self.DestroyLater()
