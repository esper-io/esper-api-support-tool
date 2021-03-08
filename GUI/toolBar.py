from Utility.Resource import resourcePath, scale_bitmap
import wx


class ToolsToolBar(wx.ToolBar):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        close_icon = scale_bitmap(resourcePath("Images/exit.png"), 16, 16)
        self.qtool = self.AddTool(wx.ID_ANY, "Quit", close_icon, "Quit")
        self.AddSeparator()

        add_icon = scale_bitmap(resourcePath("Images/add.png"), 16, 16)
        self.atool = self.AddTool(
            wx.ID_ANY, "Add New Endpoint", add_icon, "Add New Endpoint"
        )
        self.AddSeparator()

        open_icon = scale_bitmap(resourcePath("Images/open.png"), 16, 16)
        self.otool = self.AddTool(
            wx.ID_ANY, "Open Device CSV", open_icon, "Open Device CSV"
        )
        self.AddSeparator()

        save_icon = scale_bitmap(resourcePath("Images/save.png"), 16, 16)
        self.stool = self.AddTool(
            wx.ID_ANY,
            "Save Device & Network Info",
            save_icon,
            "Save Device & Network Info",
        )
        self.AddSeparator()

        exe_icon = scale_bitmap(resourcePath("Images/run.png"), 16, 16)
        self.rtool = self.AddTool(wx.ID_ANY, "Run Action", exe_icon, "Run Action")
        self.AddSeparator()

        ref_icon = scale_bitmap(resourcePath("Images/refresh.png"), 16, 16)
        self.rftool = self.AddTool(
            wx.ID_ANY, "Refresh Grids", ref_icon, "Refresh Grids"
        )
        self.AddSeparator()

        cmd_icon = scale_bitmap(resourcePath("Images/command.png"), 16, 16)
        self.cmdtool = self.AddTool(wx.ID_ANY, "Run Command", cmd_icon, "Run Command")

        self.AddStretchableSpace()
        self.search = wx.SearchCtrl(self)
        self.AddControl(self.search)

        self.__set_properties()

    def __set_properties(self):
        size = self.search.GetSize()
        size.SetWidth(size.GetWidth() * 2)
        self.search.SetSize(size)
        self.search.SetDescriptiveText("Search Grids")
        self.search.ShowCancelButton(True)

        self.EnableTool(self.rtool.Id, False)
        self.EnableTool(self.cmdtool.Id, False)
        self.EnableTool(self.rftool.Id, False)

        self.Bind(wx.EVT_TOOL, self.Parent.OnQuit, self.qtool)
        self.Bind(wx.EVT_TOOL, self.Parent.AddEndpoint, self.atool)
        self.Bind(wx.EVT_TOOL, self.Parent.onUploadCSV, self.otool)
        self.Bind(wx.EVT_TOOL, self.Parent.onSaveBoth, self.stool)
        self.Bind(wx.EVT_TOOL, self.Parent.onRun, self.rtool)
        self.Bind(wx.EVT_TOOL, self.Parent.updateGrids, self.rftool)
        self.Bind(wx.EVT_TOOL, self.Parent.onCommand, self.cmdtool)
        self.search.Bind(wx.EVT_SEARCH, self.Parent.onSearch)
        self.search.Bind(wx.EVT_CHAR, self.onSearchChar)
        self.search.Bind(wx.EVT_SEARCH_CANCEL, self.Parent.onSearch)

    def onSearchChar(self, event):
        event.Skip()
        wx.CallAfter(self.Parent.onSearch, wx.EVT_CHAR.typeId)
