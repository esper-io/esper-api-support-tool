#!/usr/bin/env python3
from Common.decorator import api_tool_decorator
from Utility.EsperAPICalls import getAppVersions
import wx


class InstalledDevicesDlg(wx.Dialog):
    def __init__(self, apps):
        super(InstalledDevicesDlg, self).__init__(
            None,
            wx.ID_ANY,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )

        self.appNameList = []
        self.apps = apps
        self.appNameList = [a_dict["app_name"] for a_dict in apps]
        self.versions = []

        self.SetMinSize((400, 300))
        self.SetTitle("Get Installed Devices")

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_1, 1, wx.EXPAND, 0)

        grid_sizer_1 = wx.BoxSizer(wx.HORIZONTAL)

        grid_sizer_3 = wx.FlexGridSizer(2, 1, 0, 0)
        grid_sizer_1.Add(grid_sizer_3, 1, wx.EXPAND, 0)

        label_1 = wx.StaticText(self.panel_1, wx.ID_ANY, "Applications:")
        grid_sizer_3.Add(label_1, 0, wx.LEFT, 5)

        self.list_box_1 = wx.ListBox(self.panel_1, wx.ID_ANY, choices=self.appNameList)
        grid_sizer_3.Add(self.list_box_1, 0, wx.ALL | wx.EXPAND, 5)

        grid_sizer_2 = wx.FlexGridSizer(2, 1, 0, 0)
        grid_sizer_1.Add(grid_sizer_2, 1, wx.EXPAND, 0)

        label_2 = wx.StaticText(self.panel_1, wx.ID_ANY, "Versions:")
        grid_sizer_2.Add(label_2, 0, wx.LEFT, 5)

        self.list_box_2 = wx.ListBox(self.panel_1, wx.ID_ANY, choices=[])
        grid_sizer_2.Add(self.list_box_2, 0, wx.ALL | wx.EXPAND, 5)

        sizer_2 = wx.StdDialogButtonSizer()
        sizer_1.Add(sizer_2, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

        self.button_OK = wx.Button(self, wx.ID_OK, "")
        self.button_OK.SetDefault()
        sizer_2.AddButton(self.button_OK)

        self.button_CANCEL = wx.Button(self, wx.ID_CANCEL, "")
        sizer_2.AddButton(self.button_CANCEL)

        sizer_2.Realize()

        grid_sizer_2.AddGrowableRow(1)
        grid_sizer_2.AddGrowableCol(0)

        grid_sizer_3.AddGrowableRow(1)
        grid_sizer_3.AddGrowableCol(0)
        self.panel_1.SetSizer(grid_sizer_1)

        self.panel_1.SetSizer(grid_sizer_1)

        self.SetSizer(sizer_1)

        self.SetAffirmativeId(self.button_OK.GetId())
        self.SetEscapeId(self.button_CANCEL.GetId())

        self.Layout()
        self.Centre()

        self.list_box_1.Bind(wx.EVT_LISTBOX, self.onAppSelect)
        self.Bind(wx.EVT_CLOSE, self.onClose)

    @api_tool_decorator
    def onClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        elif self.IsShown():
            self.Close()
        # self.DestroyLater()

    def onAppSelect(self, event):
        val = event.String
        event.Skip()
        wx.CallAfter(self.processAppSelect, val)

    def processAppSelect(self, val):
        self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
        matches = list(
            filter(
                lambda x: x["app_name"] == val,
                self.apps,
            )
        )
        self.list_box_2.Clear()
        for match in matches:
            id = match["id"]
            versions = getAppVersions(id)
            self.versions = versions.results
            for version in versions.results:
                # self.list_box_2.Append(version.version_code, version.id)
                self.list_box_2.Append(version.version_code)
        if matches:
            self.list_box_2.Enable(True)
        else:
            self.list_box_2.Enable(False)
        self.SetCursor(wx.Cursor(wx.CURSOR_DEFAULT))

    def getAppValues(self):
        app_id = None
        version_id = None
        selection = self.list_box_2.GetSelection()
        if selection >= 0:
            matches = list(
                filter(
                    lambda x: x["app_name"]
                    == self.list_box_1.GetString(self.list_box_1.GetSelection()),
                    self.apps,
                )
            )
            verMatches = list(
                filter(
                    lambda x: x.version_code
                    == self.list_box_2.GetString(self.list_box_2.GetSelection()),
                    self.versions,
                )
            )
            if matches:
                app_id = matches[0]["id"]
            if verMatches:
                version_id = verMatches[0].id
        return app_id, version_id
