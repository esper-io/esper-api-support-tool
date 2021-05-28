#!/usr/bin/env python3
from Utility.EsperAPICalls import getHeader
import os
from Common.decorator import api_tool_decorator
import Common.Globals as Globals
import Utility.wxThread as wxThread
from Utility.Resource import performPostRequestWithRetry, postEventToFrame
import csv
import wx
import wx.grid


class UserCreation(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, None, style=wx.DEFAULT_FRAME_STYLE)
        self.SetSize((671, 560))
        self.SetTitle("User Creation")
        self.users = []

        grid_sizer_2 = wx.GridSizer(1, 1, 0, 0)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        grid_sizer_2.Add(self.panel_1, 1, wx.EXPAND, 0)

        grid_sizer_3 = wx.GridSizer(1, 1, 0, 0)

        self.panel_2 = wx.Panel(self.panel_1, wx.ID_ANY)
        grid_sizer_3.Add(self.panel_2, 1, wx.ALL | wx.EXPAND, 5)

        sizer_1 = wx.FlexGridSizer(6, 1, 0, 0)

        label_1 = wx.StaticText(self.panel_2, wx.ID_ANY, "User Creation")
        label_1.SetFont(
            wx.Font(
                18,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        sizer_1.Add(label_1, 0, 0, 0)

        static_line_1 = wx.StaticLine(self.panel_2, wx.ID_ANY)
        sizer_1.Add(static_line_1, 0, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0)

        grid_sizer_1 = wx.FlexGridSizer(1, 2, 0, 0)
        sizer_1.Add(grid_sizer_1, 1, wx.EXPAND, 0)

        label_2 = wx.StaticText(self.panel_2, wx.ID_ANY, "Upload CSV:")
        grid_sizer_1.Add(label_2, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.button_1 = wx.Button(self.panel_2, wx.ID_ANY, "Upload")
        grid_sizer_1.Add(self.button_1, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

        label_3 = wx.StaticText(self.panel_2, wx.ID_ANY, "Preview:")
        sizer_1.Add(label_3, 0, wx.TOP, 5)

        self.grid_1 = wx.grid.Grid(self.panel_2, wx.ID_ANY, size=(1, 1))
        self.grid_1.CreateGrid(0, 6)
        self.grid_1.EnableEditing(0)
        self.grid_1.EnableDragColSize(0)
        self.grid_1.EnableDragRowSize(0)
        self.grid_1.SetColLabelValue(0, "First Name")
        self.grid_1.SetColLabelValue(1, "Last Name")
        self.grid_1.SetColLabelValue(2, "Email")
        self.grid_1.SetColLabelValue(3, "Username")
        self.grid_1.SetColLabelValue(4, "Password")
        self.grid_1.SetColLabelValue(5, "Role")
        self.grid_1.SetColLabelValue(6, "Groups")
        sizer_1.Add(self.grid_1, 1, wx.EXPAND, 0)

        grid_sizer_4 = wx.GridSizer(1, 2, 0, 0)
        sizer_1.Add(grid_sizer_4, 1, wx.EXPAND, 0)

        grid_sizer_4.Add((0, 0), 0, 0, 0)

        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_4.Add(sizer_3, 1, wx.ALIGN_RIGHT | wx.EXPAND, 0)

        self.button_6 = wx.Button(self.panel_2, wx.ID_ANY, "Create")
        sizer_3.Add(self.button_6, 0, wx.RIGHT, 5)

        self.button_7 = wx.Button(self.panel_2, wx.ID_ANY, "Cancel")
        sizer_3.Add(self.button_7, 0, wx.RIGHT, 5)

        grid_sizer_1.AddGrowableCol(1)

        sizer_1.AddGrowableRow(4)
        sizer_1.AddGrowableCol(0)
        self.panel_2.SetSizer(sizer_1)

        self.panel_1.SetSizer(grid_sizer_3)

        self.SetSizer(grid_sizer_2)

        self.Layout()
        self.Centre()

        self.button_1.Bind(wx.EVT_BUTTON, self.upload)
        self.button_6.Bind(wx.EVT_BUTTON, self.onCreate)
        self.button_7.Bind(wx.EVT_BUTTON, self.onClose)
        self.Bind(wx.EVT_DROP_FILES, self.onFileDrop)
        self.Bind(wx.EVT_KEY_UP, self.onEscapePressed)
        self.DragAcceptFiles(True)

    @api_tool_decorator
    def onEscapePressed(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_ESCAPE:
            self.onClose(event)

    @api_tool_decorator
    def onClose(self, event):
        evt = wxThread.CustomEvent(wxThread.myEVT_UNCHECK_CONSOLE, -1, None)
        if Globals.frame:
            wx.PostEvent(Globals.frame, evt)
        if event.EventType != wx.EVT_CLOSE.typeId:
            self.Close()
        self.DestroyLater()

    @api_tool_decorator
    def upload(self, event):
        with wx.FileDialog(
            self,
            "Open User CSV File",
            wildcard="CSV files (*.csv)|*.csv",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
            defaultDir=str(os.getcwd()),
        ) as fileDialog:
            result = fileDialog.ShowModal()
            if result == wx.ID_OK:
                self.processUpload(fileDialog.GetPath())

    @api_tool_decorator
    def onFileDrop(self, event):
        for file in event.Files:
            if file.endswith(".csv"):
                self.processUpload(file)

    @api_tool_decorator
    def processUpload(self, file):
        if self.grid_1.GetNumberRows() > 0:
            self.grid_1.DeleteRows(0, self.grid_1.GetNumberRows())
        data = None
        with open(file, "r") as csvFile:
            reader = csv.reader(
                csvFile, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True
            )
            data = list(reader)
        if data:
            headers = None
            for entry in data:
                if "Username" not in entry:
                    self.grid_1.AppendRows()
                    col = 0
                    user = {}
                    for field in entry:
                        self.grid_1.SetCellValue(
                            self.grid_1.GetNumberRows() - 1, col, str(field)
                        )
                        user[headers[col].lower()] = str(field)
                        col += 1
                    self.users.append(user)
                else:
                    headers = entry
        self.grid_1.AutoSize()

    @api_tool_decorator
    def onCreate(self, event):
        tenant = Globals.configuration.host.replace("https://", "").replace(
            "-api.esper.cloud/api", ""
        )
        url = "https://{tenant}-api.esper.cloud/api/user/".format(tenant=tenant)
        for user in self.users:
            body = {}
            userKeys = user.keys()
            body["first_name"] = user["first name"] if "first name" in userKeys else ""
            body["last_name"] = user["last name"] if "last name" in userKeys else ""
            body["username"] = (
                user["username"]
                if "username" in userKeys
                else (body["first_name"] + body["last_name"])
            )
            body["password"] = user["password"]
            body["profile"] = {}
            if "role" in userKeys:
                body["profile"]["role"] = user["role"]
            else:
                body["profile"]["role"] = "Group Viewer"
            body["profile"]["groups"] = user["groups"]
            if type(body["profile"]["groups"]) == str:
                body["profile"]["groups"] = list(body["profile"]["groups"])
            body["profile"]["enterprise"] = Globals.enterprise_id

            resp = performPostRequestWithRetry(url, headers=getHeader(), json=body)

            logMsg = ""
            if resp.status_code > 299:
                logMsg = "Successfully created user account: %s" % body["username"]
            else:
                logMsg = "ERROR: failed to create user account: %s" % body["username"]
            postEventToFrame(wxThread.myEVT_LOG, logMsg)
        self.onClose(event)
