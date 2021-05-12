#!/usr/bin/env python3
from Common.decorator import api_tool_decorator
from Utility.EsperAPICalls import getAppVersions
import wx


class InstalledDevicesDlg(wx.Dialog):
    def __init__(self, apps):
        super(InstalledDevicesDlg, self).__init__(
            None,
            wx.ID_ANY,
            style=wx.DEFAULT_DIALOG_STYLE,
        )
        self.SetTitle("Get Installed Devices")

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_1, 1, wx.ALL | wx.EXPAND, 5)

        grid_sizer_1 = wx.FlexGridSizer(4, 1, 0, 0)

        label_1 = wx.StaticText(self.panel_1, wx.ID_ANY, "Select Application:")
        grid_sizer_1.Add(label_1, 0, 0, 0)

        self.appNameList = []
        self.apps = apps
        self.appNameList = [a_dict["app_name"] for a_dict in apps]
        self.combo_box_1 = wx.ComboBox(
            self.panel_1,
            wx.ID_ANY,
            choices=self.appNameList,
            style=wx.CB_DROPDOWN | wx.CB_READONLY,
        )
        self.combo_box_1.Bind(wx.EVT_COMBOBOX, self.onAppSelect)
        grid_sizer_1.Add(self.combo_box_1, 0, wx.EXPAND, 0)

        label_2 = wx.StaticText(self.panel_1, wx.ID_ANY, "Select Application Version:")
        grid_sizer_1.Add(label_2, 0, 0, 0)

        self.combo_box_2 = wx.ComboBox(
            self.panel_1, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY
        )
        self.combo_box_2.Enable(False)
        grid_sizer_1.Add(self.combo_box_2, 0, wx.EXPAND, 0)

        sizer_2 = wx.StdDialogButtonSizer()
        sizer_1.Add(sizer_2, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

        self.button_OK = wx.Button(self, wx.ID_OK, "Get Installed Devices")
        self.button_OK.SetDefault()
        sizer_2.Add(self.button_OK, 0, 0, 0)

        sizer_2.Realize()

        grid_sizer_1.AddGrowableRow(1)
        grid_sizer_1.AddGrowableRow(3)
        grid_sizer_1.AddGrowableCol(0)
        self.panel_1.SetSizer(grid_sizer_1)

        self.SetSizer(sizer_1)
        sizer_1.Fit(self)

        self.SetAffirmativeId(self.button_OK.GetId())

        self.Layout()

        self.Bind(wx.EVT_CLOSE, self.onClose)

    @api_tool_decorator
    def onClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        elif self.IsShown():
            self.Close()
        self.DestroyLater()

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
        self.combo_box_2.Clear()
        for match in matches:
            id = match["id"]
            versions = getAppVersions(id)
            for version in versions.results:
                self.combo_box_2.Append(version.version_code, version.id)
        if matches:
            self.combo_box_2.Enable(True)
        else:
            self.combo_box_2.Enable(False)
        self.SetCursor(wx.Cursor(wx.CURSOR_DEFAULT))

    def getAppValues(self):
        app_id = None
        version_id = None
        selection = self.combo_box_2.GetSelection()
        if selection >= 0:
            version_id = self.combo_box_2.GetClientData(selection)
            matches = list(
                filter(
                    lambda x: x["app_name"]
                    == self.combo_box_1.GetString(self.combo_box_1.GetSelection()),
                    self.apps,
                )
            )
            if matches:
                app_id = matches[0]["id"]
        return app_id, version_id
