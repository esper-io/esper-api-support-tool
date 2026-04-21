#!/usr/bin/env python

import platform

import wx

from Common.decorator import api_tool_decorator
from Utility.Resource import resourcePath, scale_bitmap
from Utility.widgetUtils import safeBind, safeEnable


class ToolsToolBar(wx.ToolBar):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.AddSeparator()

        size = (16, 16)
        if platform.system() != "Windows":
            size = (24, 24)
        self.SetToolBitmapSize(size)

        self.SetThemeEnabled(False)

        self.qtool = self.addToolBarItem("Images/exit.png", size, "Quit", "Quit")
        self.atool = self.addToolBarItem("Images/add.png", size, "Add New Tenant", "Add New Tenant")
        self.otool = self.addToolBarItem(
            "Images/open.png",
            size,
            "Open Device Spreadsheet",
            "Open Device Spreadsheet",
        )
        self.stool = self.addToolBarItem("Images/save.png", size, "Save All Reports", "Save All Reports")
        self.rtool = self.addToolBarItem("Images/run.png", size, "Run Action", "Run Action")
        self.cmdtool = self.addToolBarItem("Images/command.png", size, "Run Command", "Run Command")

        self.AddStretchableSpace()
        self.search = wx.SearchCtrl(self)
        self.AddControl(self.search)

        self.__set_properties()

    def addToolBarItem(
        self,
        bitmap_path,
        size,
        label,
        shortHelp,
        id=wx.ID_ANY,
        addSeparator=True,
    ):
        icon = scale_bitmap(resourcePath(bitmap_path), *size)
        tool = self.AddTool(id, label, icon, shortHelp)

        if addSeparator:
            self.AddSeparator()
        return tool

    @api_tool_decorator()
    def __set_properties(self):
        size = self.search.GetSize()
        size.SetWidth(size.GetWidth() * 2)
        self.search.SetSize(size)
        self.search.SetDescriptiveText("Search Grids")
        self.search.ShowCancelButton(True)

        self.EnableTool(self.rtool.Id, False)
        self.EnableTool(self.cmdtool.Id, False)

        
        safeBind(self, wx.EVT_TOOL, self.Parent.OnQuit, self.qtool)
        safeBind(self, wx.EVT_TOOL, self.Parent.AddEndpoint, self.atool)
        safeBind(self, wx.EVT_TOOL, self.Parent.onUploadSpreadsheet, self.otool)
        safeBind(self, wx.EVT_TOOL, self.Parent.onSaveBoth, self.stool)
        safeBind(self, wx.EVT_TOOL, self.Parent.onRun, self.rtool)
        safeBind(self, wx.EVT_TOOL, self.Parent.onCommand, self.cmdtool)

        safeBind(self.search, wx.EVT_SEARCH, self.Parent.onSearch)
        safeBind(self.search, wx.EVT_SEARCH_CANCEL, self.Parent.onSearch)

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

    def toggleMajorityToolsState(self, state):
        # self.EnableTool(self.qtool.Id, state)  # Quit
        self.EnableTool(self.rtool.Id, state)  # Run
        self.EnableTool(self.cmdtool.Id, state)  # Command
        self.EnableTool(self.atool.Id, state)  # Add Tenant
        self.EnableTool(self.otool.Id, state)  # Open Spreadsheet
        self.EnableTool(self.stool.Id, state)  # Save
        safeEnable(self.search, state)
