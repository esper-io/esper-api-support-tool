#!/usr/bin/env python

import platform

import wx

from Common.decorator import api_tool_decorator
from Utility.Resource import resourcePath, scale_bitmap


class ToolsToolBar(wx.ToolBar):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.AddSeparator()

        size = (16, 16)
        if platform.system() != "Windows":
            size = (24, 24)
        self.SetToolBitmapSize(size)

        self.SetThemeEnabled(False)

        close_icon = scale_bitmap(resourcePath("Images/exit.png"), *size)
        self.qtool = self.AddTool(wx.ID_ANY, "Quit", close_icon, "Quit")
        self.AddSeparator()

        add_icon = scale_bitmap(resourcePath("Images/add.png"), *size)
        self.atool = self.AddTool(
            wx.ID_ANY, "Add New Tenant", add_icon, "Add New Tenant"
        )
        self.AddSeparator()

        open_icon = scale_bitmap(resourcePath("Images/open.png"), *size)
        self.otool = self.AddTool(
            wx.ID_ANY, "Open Device Spreadsheet", open_icon, "Open Device Spreadsheet"
        )
        self.AddSeparator()

        save_icon = scale_bitmap(resourcePath("Images/save.png"), *size)
        self.stool = self.AddTool(
            wx.ID_ANY,
            "Save All Reports",
            save_icon,
            "Save All Reports",
        )
        self.AddSeparator()

        exe_icon = scale_bitmap(resourcePath("Images/run.png"), *size)
        self.rtool = self.AddTool(wx.ID_ANY, "Run Action", exe_icon, "Run Action")
        self.AddSeparator()

        cmd_icon = scale_bitmap(resourcePath("Images/command.png"), *size)
        self.cmdtool = self.AddTool(wx.ID_ANY, "Run Command", cmd_icon, "Run Command")

        self.AddSeparator()

        uploadIcon = scale_bitmap(resourcePath("Images/upload.png"), *size)
        self.uploadApp = self.AddTool(
            wx.ID_ANY, "Upload App (APK)", uploadIcon, "Upload App (APK)"
        )

        self.AddSeparator()

        self.AddStretchableSpace()
        self.search = wx.SearchCtrl(self)
        self.AddControl(self.search)

        self.__set_properties()

    @api_tool_decorator()
    def __set_properties(self):
        size = self.search.GetSize()
        size.SetWidth(size.GetWidth() * 2)
        self.search.SetSize(size)
        self.search.SetDescriptiveText("Search Grids")
        self.search.ShowCancelButton(True)

        self.EnableTool(self.rtool.Id, False)
        self.EnableTool(self.cmdtool.Id, False)

        self.Bind(wx.EVT_TOOL, self.Parent.OnQuit, self.qtool)
        self.Bind(wx.EVT_TOOL, self.Parent.AddEndpoint, self.atool)
        self.Bind(wx.EVT_TOOL, self.Parent.onUploadSpreadsheet, self.otool)
        self.Bind(wx.EVT_TOOL, self.Parent.onSaveBoth, self.stool)
        self.Bind(wx.EVT_TOOL, self.Parent.onRun, self.rtool)
        self.Bind(wx.EVT_TOOL, self.Parent.onCommand, self.cmdtool)
        self.Bind(wx.EVT_TOOL, self.Parent.uploadApplication, self.uploadApp)

        self.search.Bind(wx.EVT_SEARCH, self.Parent.onSearch)
        self.search.Bind(wx.EVT_SEARCH_CANCEL, self.Parent.onSearch)

    @api_tool_decorator()
    def onSearchChar(self, event):
        event.Skip()
        wx.CallAfter(self.Parent.onSearch, wx.EVT_CHAR.typeId)

    @api_tool_decorator()
    def onKey(self, event):
        keycode = event.GetKeyCode()
        # CTRL + C or CTRL + Insert
        if event.ControlDown() and keycode in [67, 322]:
            self.on_copy(event)
        # CTRL + V
        elif event.ControlDown() and keycode == 86:
            self.on_paste(event)
        else:
            event.Skip()

    @api_tool_decorator()
    def on_copy(self, event):
        widget = self.FindFocus()
        data = wx.TextDataObject()
        data.SetText(widget.GetStringSelection())
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()
        widget.SetFocus()

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
        widget.SetFocus()
