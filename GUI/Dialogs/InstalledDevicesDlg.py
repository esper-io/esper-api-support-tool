#!/usr/bin/env python3

import wx

import Common.Globals as Globals
from Common.decorator import api_tool_decorator
from Utility.API.AppUtilities import getAppVersions
from Utility.Resource import getStrRatioSimilarity


class InstalledDevicesDlg(wx.Dialog):
    def __init__(
        self,
        apps,
        hide_version=False,
        title="Get Installed Devices",
        showAllVersionsOption=True,
        showPkgTextInput=False,
        showBlueprintInput=False,
    ):
        super(InstalledDevicesDlg, self).__init__(
            Globals.frame,
            wx.ID_ANY,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )

        self.appNameList = []
        self.newBluePrintApp = []
        self.radio_box_2 = None
        self.otherPkgInput = None
        self.selectedAppName = None
        self.selectedVersion = None
        self.apps = apps
        for app in self.apps:
            self.appNameList.append(app["appPkgName"])
        self.versions = []
        self.showAllVersionsOption = showAllVersionsOption

        self.SetMinSize((400, 300))
        self.SetTitle(title)
        self.SetThemeEnabled(False)

        sizer_1 = wx.FlexGridSizer(3, 1, 0, 0)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_1, 1, wx.ALL | wx.EXPAND, 5)

        grid_sizer_1 = wx.GridSizer(1, 2 if not hide_version else 1, 0, 0)

        grid_sizer_3 = wx.FlexGridSizer(4, 1, 0, 0)
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
        grid_sizer_3.Add(label_1, 0, wx.LEFT, 3)

        sizer_3 = wx.FlexGridSizer(1, 2, 0, 0)
        grid_sizer_3.Add(sizer_3, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL | wx.EXPAND, 5)

        label_3 = wx.StaticText(self.panel_1, wx.ID_ANY, "App Search")
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

        if showPkgTextInput:
            sizer_4 = wx.FlexGridSizer(1, 2, 0, 0)
            grid_sizer_3.Add(sizer_4, 1, wx.ALL | wx.EXPAND, 5)

            label_4 = wx.StaticText(self.panel_1, wx.ID_ANY, "Other Package:")
            sizer_4.Add(label_4, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

            self.otherPkgInput = wx.TextCtrl(self.panel_1, wx.ID_ANY, "")
            sizer_4.Add(self.otherPkgInput, 0, wx.ALIGN_RIGHT | wx.EXPAND, 0)

            sizer_4.AddGrowableRow(0)
            sizer_4.AddGrowableCol(0)
            sizer_4.AddGrowableCol(1)

        self.list_box_2 = None
        if not hide_version:
            grid_sizer_2 = wx.FlexGridSizer(3, 1, 0, 0)
            grid_sizer_1.Add(grid_sizer_2, 1, wx.EXPAND, 0)

            label_2 = wx.StaticText(self.panel_1, wx.ID_ANY, "Available App Versions:")
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

            self.list_box_2 = wx.ListBox(
                self.panel_1,
                wx.ID_ANY,
                choices=[],
                style=wx.LB_SINGLE if showBlueprintInput else wx.LB_EXTENDED,
            )
            grid_sizer_2.Add(self.list_box_2, 0, wx.ALL | wx.EXPAND, 5)
            self.list_box_2.Bind(wx.EVT_LISTBOX, self.onVersionSelect)

            if showBlueprintInput:
                sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
                grid_sizer_2.Add(sizer_6, 1, wx.ALIGN_RIGHT | wx.EXPAND, 0)

                self.button_2 = wx.Button(self.panel_1, wx.ID_REMOVE, "")
                sizer_6.Add(self.button_2, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
                self.button_2.Bind(wx.EVT_BUTTON, self.RemoveBlueprintChangeList)

                self.button_1 = wx.Button(self.panel_1, wx.ID_ADD, "")
                sizer_6.Add(self.button_1, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
                self.button_1.Bind(wx.EVT_BUTTON, self.AddToBlueprintChangeList)

        if showBlueprintInput:
            self.panel_3 = wx.Panel(self, wx.ID_ANY)
            sizer_1.Add(self.panel_3, 1, wx.EXPAND | wx.TOP, 2)

            grid_sizer_4 = wx.GridSizer(1, 1, 0, 0)

            self.panel_5 = wx.Panel(self.panel_3, wx.ID_ANY)
            grid_sizer_4.Add(self.panel_5, 1, wx.ALL | wx.EXPAND, 5)

            grid_sizer_6 = wx.FlexGridSizer(3, 1, 0, 0)

            static_line_1 = wx.StaticLine(self.panel_5, wx.ID_ANY)
            grid_sizer_6.Add(static_line_1, 0, wx.BOTTOM | wx.EXPAND | wx.TOP, 5)

            sizer_5 = wx.FlexGridSizer(2, 1, 0, 0)
            grid_sizer_6.Add(sizer_5, 1, wx.EXPAND, 0)

            label_5 = wx.StaticText(self.panel_5, wx.ID_ANY, "Selected Apps:")
            label_5.SetFont(
                wx.Font(
                    11,
                    wx.FONTFAMILY_DEFAULT,
                    wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_BOLD,
                    0,
                    "",
                )
            )
            sizer_5.Add(label_5, 0, wx.LEFT, 5)

            self.text_ctrl_3 = wx.TextCtrl(
                self.panel_5,
                wx.ID_ANY,
                "",
                style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP,
            )
            sizer_5.Add(self.text_ctrl_3, 0, wx.ALL | wx.EXPAND, 5)

            self.radio_box_2 = wx.RadioBox(
                self.panel_5,
                wx.ID_ANY,
                "Do you want to push the selected App to all Blueprints or only updates Blueprints that already have this app?",
                choices=[
                    "Push to All Blueprints (if app is not defined it will be added)",
                    "Push ONLY to Blueprint that already have the app",
                ],
                majorDimension=1,
                style=wx.RA_SPECIFY_COLS,
            )
            self.radio_box_2.SetSelection(1)
            grid_sizer_6.Add(self.radio_box_2, 0, wx.ALL | wx.EXPAND, 5)

            sizer_5.AddGrowableRow(1)
            sizer_5.AddGrowableCol(0)

            grid_sizer_6.AddGrowableRow(1)
            grid_sizer_6.AddGrowableRow(2)
            grid_sizer_6.AddGrowableCol(0)
            self.panel_5.SetSizer(grid_sizer_6)

            self.panel_3.SetSizer(grid_sizer_4)

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

        sizer_1.AddGrowableRow(0)
        sizer_1.AddGrowableRow(1)
        sizer_1.AddGrowableCol(0)
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

        self.button_CANCEL.Bind(wx.EVT_BUTTON, self.onClose)
        self.search.Bind(wx.EVT_SEARCH, self.onSearch)
        self.search.Bind(wx.EVT_SEARCH_CANCEL, self.onSearch)
        self.search.Bind(wx.EVT_CHAR, self.onKey)
        if self.otherPkgInput:
            self.otherPkgInput.Bind(wx.EVT_CHAR, self.onOtherPkgInput)

    @api_tool_decorator()
    def onClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        elif self.IsShown():
            self.Close()

    def onAppSelect(self, event):
        self.selectedAppName = event.String
        event.Skip()
        wx.CallAfter(self.processAppSelect, self.selectedAppName)

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
        if self.showAllVersionsOption:
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
        selection = self.list_box_2.GetSelections() if self.list_box_2 else None
        if type(selection) is list and selection:
            if len(selection) == 1:
                version_id = self.list_box_2.GetClientData(selection[0])
                if version_id == -1:
                    # User selected All Versions
                    version_id = []
                    for version in self.versions:
                        if hasattr(version, "id"):
                            version_id.append(version.id)
                        elif type(version) == dict and "id" in version:
                            version_id.append(version["id"])
            else:
                version_id = []
                indx = 0
                for version in self.versions:
                    if indx in selection:
                        if hasattr(version, "id"):
                            version_id.append(version.id)
                        elif type(version) == dict and "id" in version:
                            version_id.append(version["id"])
                    indx += 1
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
        elif self.otherPkgInput:
            app_name = self.otherPkgInput.GetValue()
            packageName = self.otherPkgInput.GetValue()
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

        self.list_box_1.Freeze()
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
        self.list_box_1.Thaw()

    def onOtherPkgInput(self, event):
        input = self.otherPkgInput.GetValue()
        if input:
            self.list_box_1.SetSelection(-1)
        event.Skip()

    def onVersionSelect(self, event):
        self.selectedVersion = event.String
        event.Skip()
        wx.CallAfter(self.processVersionSelect, self.selectedVersion)

    def processVersionSelect(self, val):
        selections = self.list_box_2.GetSelections()
        if 0 in selections:
            for item in selections:
                if item != 0:
                    self.list_box_2.Deselect(item)

    def AddToBlueprintChangeList(self, event):
        versionSelection = self.list_box_2.GetSelection()
        if versionSelection >= 0:
            versionClientData = self.list_box_2.GetClientData(versionSelection)
            version = self.list_box_2.GetString(versionSelection)

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
            versionMatches = list(
                filter(
                    lambda x: x["id"] == versionClientData,
                    self.versions,
                )
            )
            app_id = matches[0]["id"]
            packageName = matches[0]["packageName"]
            app_name = None
            if Globals.SHOW_PKG_NAME:
                app_name = matches[0]["appPkgName"]
            else:
                app_name = matches[0]["app_name"]
            self.newBluePrintApp.append(
                {
                    "name": app_name,
                    "id": app_id,
                    "package": packageName,
                    "versionId": versionClientData,
                    "version": version,
                    "isPlayStore": versionMatches[0]["is_g_play"],
                    "codes": [versionMatches[0]["build_number"]],
                    "releaseName": versionMatches[0]["release_name"],
                }
            )

        self.updateBlueprintSelectedAppElm()

    def RemoveBlueprintChangeList(self, event):
        selection = self.list_box_2.GetSelection()
        versionClientData = self.list_box_2.GetClientData(selection)

        match = None
        for entry in self.newBluePrintApp:
            if entry["versionId"] == versionClientData:
                match = entry
                break
        if match:
            self.newBluePrintApp.remove(match)
        self.updateBlueprintSelectedAppElm()

    def updateBlueprintSelectedAppElm(self):
        selectedAppStr = ""
        for entry in self.newBluePrintApp:
            if Globals.SHOW_PKG_NAME:
                selectedAppStr += "%s (%s) - %s\n" % (
                    entry["name"],
                    entry["package"],
                    entry["version"],
                )
            else:
                selectedAppStr += "%s - %s\n" % (entry["name"], entry["version"])
        self.text_ctrl_3.SetValue(selectedAppStr)

    def getBlueprintInputs(self):
        if self.radio_box_2:
            return (
                True if self.radio_box_2.GetSelection() == 0 else False,
                self.newBluePrintApp,
            )
        else:
            return None
