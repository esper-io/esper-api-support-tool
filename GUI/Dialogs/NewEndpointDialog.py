#!/usr/bin/env python3

import re
import wx
import wx.html as wxHtml

from Common.decorator import api_tool_decorator
from Utility.Resource import openWebLinkInBrowser


class NewEndpointDialog(wx.Dialog):
    def __init__(self, errorMsg=None, name=None, host=None, entId=None, key=None):
        super(NewEndpointDialog, self).__init__(
            None,
            wx.ID_ANY,
            size=(400, 200),
            style=wx.DEFAULT_DIALOG_STYLE,
        )
        self.SetSize((500, 400))
        self.SetTitle("Add New Endpoint")

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_1, 1, wx.EXPAND, 0)

        sizer_3 = wx.StaticBoxSizer(
            wx.StaticBox(self.panel_1, wx.ID_ANY, "Add New Endpoint"), wx.VERTICAL
        )

        label_1 = wx.StaticText(self.panel_1, wx.ID_ANY, "Endpoint Name")
        sizer_3.Add(label_1, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)

        self.text_ctrl_1 = wx.TextCtrl(self.panel_1, wx.ID_ANY, "")
        self.text_ctrl_1.SetFocus()
        if name:
            self.text_ctrl_1.SetValue(str(name))
        self.text_ctrl_1.Bind(wx.EVT_TEXT, self.checkInputs)
        sizer_3.Add(self.text_ctrl_1, 0, wx.ALL | wx.EXPAND, 5)

        label_2 = wx.StaticText(
            self.panel_1,
            wx.ID_ANY,
            "Endpoint Host Name (e.g., The host in https://<host>.esper.cloud/)",
        )
        sizer_3.Add(label_2, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)

        self.text_ctrl_2 = wx.TextCtrl(self.panel_1, wx.ID_ANY, "")
        if host:
            self.text_ctrl_2.SetValue(str(host))
        self.text_ctrl_2.Bind(wx.EVT_TEXT, self.checkInputs)
        sizer_3.Add(self.text_ctrl_2, 0, wx.ALL | wx.EXPAND, 5)

        label_3 = wx.StaticText(self.panel_1, wx.ID_ANY, "Enterprise Id")
        sizer_3.Add(label_3, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)

        self.text_ctrl_3 = wx.TextCtrl(self.panel_1, wx.ID_ANY, "")
        if entId:
            self.text_ctrl_3.SetValue(str(entId))
        self.text_ctrl_3.Bind(wx.EVT_TEXT, self.checkInputs)
        sizer_3.Add(self.text_ctrl_3, 0, wx.ALL | wx.EXPAND, 5)

        label_4 = wx.StaticText(self.panel_1, wx.ID_ANY, "API Key (Bearer Token)")
        sizer_3.Add(label_4, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)

        self.text_ctrl_4 = wx.TextCtrl(self.panel_1, wx.ID_ANY, "")
        if key:
            self.text_ctrl_4.SetValue(str(key))
        self.text_ctrl_4.Bind(wx.EVT_TEXT, self.checkInputs)
        sizer_3.Add(self.text_ctrl_4, 0, wx.ALL | wx.EXPAND, 5)

        self.panel_2 = wx.Panel(self.panel_1, wx.ID_ANY)
        sizer_3.Add(self.panel_2, 1, wx.EXPAND, 0)

        grid_sizer_1 = wx.GridSizer(1, 1, 0, 0)

        self.text_ctrl_5 = wx.TextCtrl(
            self.panel_2,
            wx.ID_ANY,
            "",
            style=wx.TE_AUTO_URL | wx.TE_MULTILINE | wx.TE_READONLY,
        )
        self.text_ctrl_5.Bind(wxHtml.EVT_HTML_LINK_CLICKED, openWebLinkInBrowser)
        self.text_ctrl_5.SetForegroundColour(wx.Colour(255, 0, 0))
        if errorMsg:
            self.text_ctrl_5.SetValue(str(errorMsg))
        else:
            self.text_ctrl_5.Hide()
        grid_sizer_1.Add(self.text_ctrl_5, 0, wx.ALL | wx.EXPAND, 5)

        sizer_2 = wx.StdDialogButtonSizer()
        sizer_1.Add(sizer_2, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

        self.button_APPLY = wx.Button(self, wx.ID_ADD, "")
        self.button_APPLY.Enable(False)
        sizer_2.Add(self.button_APPLY, 0, 0, 0)
        self.button_APPLY.Bind(wx.EVT_BUTTON, self.onClose)

        sizer_2.Realize()

        self.panel_2.SetSizer(grid_sizer_1)

        self.panel_1.SetSizer(sizer_3)

        self.SetSizer(sizer_1)

        self.Layout()
        self.Centre()

    @api_tool_decorator
    def onClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        elif self.IsShown():
            self.Close()

    @api_tool_decorator
    def getInputValues(self):
        name = str(self.text_ctrl_1.GetValue().strip())
        hostname = self.text_ctrl_2.GetValue().strip()
        if hostname:
            match = re.search(
                "[https://|http://]*[a-zA-Z]+[-api]*\.esper\.cloud[\S]*", hostname
            )
            if match:
                hostname = re.sub("[-api]*\.esper\.cloud[\S]*", "", hostname)
                hostname = hostname.replace("https://", "")
                hostname = hostname.replace("http://", "")

        host = "https://%s-api.esper.cloud/api" % str(hostname)
        entId = str(self.text_ctrl_3.GetValue().strip())
        key = str(self.text_ctrl_4.GetValue().strip())
        prefix = "Bearer"
        return name, host, entId, key, prefix

    @api_tool_decorator
    def getCSVRowEntry(self):
        name = str(self.text_ctrl_1.GetValue().strip())
        hostname = self.text_ctrl_2.GetValue().strip()
        if hostname:
            match = re.search(
                "[https://|http://]*[a-zA-Z]+[-api]*\.esper\.cloud[\S]*", hostname
            )
            if match:
                hostname = re.sub("[-api]*\.esper\.cloud[\S]*", "", hostname)
                hostname = hostname.replace("https://", "")
                hostname = hostname.replace("http://", "")

        host = "https://%s-api.esper.cloud/api" % str(hostname)
        entId = str(self.text_ctrl_3.GetValue().strip())
        key = str(self.text_ctrl_4.GetValue().strip())
        prefix = "Bearer"
        return [name, host, entId, key, prefix]

    @api_tool_decorator
    def checkInputs(self, event):
        hostname = self.text_ctrl_2.GetValue().strip()
        if hostname:
            match = re.search(
                "[https://|http://]*[a-zA-Z]+[-api]*\.esper\.cloud[\S]*", hostname
            )
            if match:
                hostname = re.sub("[-api]*\.esper\.cloud[\S]*", "", hostname)
                hostname = hostname.replace("https://", "")
                hostname = hostname.replace("http://", "")
                self.text_ctrl_2.SetValue(hostname)
        if (
            self.text_ctrl_4.GetValue()
            and self.text_ctrl_3.GetValue()
            and self.text_ctrl_2.GetValue()
            and self.text_ctrl_1.GetValue()
        ):
            self.button_APPLY.Enable(True)
        else:
            self.button_APPLY.Enable(False)
