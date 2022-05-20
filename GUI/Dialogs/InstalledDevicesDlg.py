#!/usr/bin/env python3

import wx
import Common.Globals as Globals
from Utility.API.AppUtilities import getAppVersions

from Utility.Resource import getStrRatioSimilarity
from Common.decorator import api_tool_decorator


class InstalledDevicesDlg(wx.Dialog):
    def __init__(self, apps, hide_version=False, title="Get Installed Devices"):
        super(InstalledDevicesDlg, self).__init__(
            None,
            wx.ID_ANY,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )

        self.appNameList = []
        self.apps = apps
        for app in self.apps:
            self.appNameList.append(app["appPkgName"])
        self.versions = []

        self.SetMinSize((400, 300))
        self.SetTitle(title)

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_1, 1, wx.ALL | wx.EXPAND, 5)

        grid_sizer_1 = wx.GridSizer(1, 2, 0, 0)

        grid_sizer_3 = wx.FlexGridSizer(3, 1, 0, 0)
        grid_sizer_1.Add(grid_sizer_3, 1, wx.EXPAND, 0)

        label_1 = wx.StaticText(self.panel_1, wx.ID_ANY, "Applications:")
        label_1.SetFont(
            wx.Font(
                Globals.FONT_SIZE,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "NormalBold",
            )
        )
        grid_sizer_3.Add(label_1, 0, wx.LEFT, 5)

        sizer_3 = wx.FlexGridSizer(1, 2, 0, 0)
        grid_sizer_3.Add(sizer_3, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL | wx.EXPAND, 5)

        label_3 = wx.StaticText(self.panel_1, wx.ID_ANY, "Search")
        sizer_3.Add(label_3, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.search = wx.SearchCtrl(self.panel_1, wx.ID_ANY, "")
        self.search.ShowCancelButton(True)
        sizer_3.Add(
            self.search, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.LEFT, 5
        )

        self.list_box_1 = wx.ListBox(
            self.panel_1,
            wx.ID_ANY,
            choices=self.appNameList,
            style=wx.LB_HSCROLL | wx.LB_NEEDED_SB,
        )
        grid_sizer_3.Add(self.list_box_1, 0, wx.ALL | wx.EXPAND, 5)

        self.list_box_2 = None
        if not hide_version:
            grid_sizer_2 = wx.FlexGridSizer(2, 1, 0, 0)
            grid_sizer_1.Add(grid_sizer_2, 1, wx.EXPAND, 0)

            label_2 = wx.StaticText(self.panel_1, wx.ID_ANY, "Versions:")
            label_2.SetFont(
                wx.Font(
                    Globals.FONT_SIZE,
                    wx.FONTFAMILY_DEFAULT,
                    wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_BOLD,
                    0,
                    "NormalBold",
                )
            )
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

        if not hide_version:
            grid_sizer_2.AddGrowableRow(1)
            grid_sizer_2.AddGrowableCol(0)

        sizer_3.AddGrowableRow(0)
        sizer_3.AddGrowableCol(0)
        sizer_3.AddGrowableCol(1)

        grid_sizer_3.AddGrowableRow(2)
        grid_sizer_3.AddGrowableCol(0)

        self.panel_1.SetSizer(grid_sizer_1)

        self.SetSizer(sizer_1)

        self.SetAffirmativeId(self.button_OK.GetId())
        self.SetEscapeId(self.button_CANCEL.GetId())

        size = wx.DisplaySize()
        self.SetMaxSize(wx.Size(int(size[0] * 0.75), int(size[1] * 0.75)))

        self.Layout()
        self.Fit()
        self.Centre()

        if not hide_version:
            self.list_box_1.Bind(wx.EVT_LISTBOX, self.onAppSelect)
        self.Bind(wx.EVT_CLOSE, self.onClose)

        self.search.Bind(wx.EVT_SEARCH, self.onSearch)
        self.search.Bind(wx.EVT_SEARCH_CANCEL, self.onSearch)
        self.search.Bind(wx.EVT_CHAR, self.onKey)

    @api_tool_decorator()
    def onClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        elif self.IsShown():
            self.Close()

    def onAppSelect(self, event):
        val = event.String
        event.Skip()
        wx.CallAfter(self.processAppSelect, val)

    def processAppSelect(self, val):
        self.list_box_1.Enable(False)
        self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
        matches = list(
            filter(
                lambda x: x["app_name"] == val or val in x.keys(),
                self.apps,
            )
        )
        self.list_box_2.Clear()
        self.list_box_2.Append("All Enterprise Versions", -1)
        for match in matches:
            if "id" in match:
                id = match["id"]
                versions = getAppVersions(id, getPlayStore=True)
                self.versions = (
                    versions.results
                    if not type(versions) == dict
                    else versions["results"]
                )
                for version in self.versions:
                    if hasattr(version, "version_code"):
                        self.list_box_2.Append(version.version_code, version.id)
                    elif type(versions) == dict:
                        self.list_box_2.Append(version["version_code"], version["id"])
        if matches:
            self.list_box_2.Enable(True)
        else:
            self.list_box_2.Enable(False)
        self.SetCursor(wx.Cursor(wx.CURSOR_DEFAULT))
        self.list_box_1.Enable(True)

    def getAppValues(self, returnPkgName=False, returnAppName=False):
        app_id = None
        packageName = None
        version_id = None
        app_name = None
        selection = self.list_box_2.GetSelection() if self.list_box_2 else None
        if type(selection) == int and selection >= 0:
            version_id = self.list_box_2.GetClientData(self.list_box_2.GetSelection())
            if version_id == -1:
                # User selected All Versions
                version_id = []
                for version in self.versions:
                    if hasattr(version, "id"):
                        version_id.append(version.id)
                    elif type(version) == dict and "id" in version:
                        version_id.append(version["id"])
        if self.list_box_1.GetSelection() >= 0:
            matches = list(
                filter(
                    lambda x: x["app_name"]
                    == self.list_box_1.GetString(self.list_box_1.GetSelection())
                    or (
                        "appPkgName" in x
                        and x["appPkgName"]
                        == self.list_box_1.GetString(self.list_box_1.GetSelection())
                    ),
                    self.apps,
                )
            )
            if matches:
                app_id = matches[0]["id"]
                packageName = matches[0]["packageName"]
                if Globals.SHOW_PKG_NAME:
                    app_name = matches[0]["appPkgName"]
                else:
                    app_name = matches[0]["app_name"]
        if returnPkgName and not returnAppName:
            return app_id, version_id, packageName
        elif returnAppName and returnPkgName:
            return app_id, version_id, packageName, app_name
        elif returnAppName and not returnPkgName:
            return app_id, version_id, app_name
        else:
            return app_id, version_id

    @api_tool_decorator()
    def onKey(self, event):
        keycode = event.GetKeyCode()
        # CTRL + C or CTRL + Insert
        if event.ControlDown() and keycode in [67, 322]:
            self.on_copy(event)
        # CTRL + V
        elif event.ControlDown() and keycode == 86:
            self.on_paste(event)
        elif keycode == wx.WXK_ESCAPE:
            self.onClose(event)
        else:
            self.onChar(event)

    @api_tool_decorator()
    def on_copy(self, event):
        widget = self.FindFocus()
        data = wx.TextDataObject()
        data.SetText(widget.GetStringSelection())
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()

    @api_tool_decorator()
    def on_paste(self, event):
        widget = self.FindFocus()
        success = False
        data = wx.TextDataObject()
        if wx.TheClipboard.Open():
            success = wx.TheClipboard.GetData(data)
            wx.TheClipboard.Close()
        if success:
            widget.WriteText(data.GetText())

    @api_tool_decorator()
    def onChar(self, event):
        event.Skip()
        wx.CallAfter(self.onSearch, event)

    @api_tool_decorator()
    def onSearch(self, event=None):
        if event:
            event.Skip()
        queryString = ""
        if hasattr(event, "GetString"):
            queryString = event.GetString()
        else:
            queryString = self.search.GetValue()
        self.list_box_1.Clear()

        if queryString:
            sortedList = list(
                filter(
                    lambda i: queryString.lower() in i.lower()
                    or getStrRatioSimilarity(i.lower(), queryString) > 90,
                    self.appNameList,
                )
            )
            for item in sortedList:
                self.list_box_1.Append(item)
            self.isFiltered = True
        else:
            for item in self.appNameList:
                self.list_box_1.Append(item)
            self.isFiltered = False
