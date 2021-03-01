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
        size = self.search.GetSize()
        size.SetWidth(size.GetWidth() * 2)
        self.search.SetSize(size)
        self.search.SetDescriptiveText("Search Grids")
        self.AddControl(self.search)
        self.search.ShowCancelButton(True)