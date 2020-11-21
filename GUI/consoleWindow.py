import wx
import Common.Globals as Globals
import platform


class Console(wx.Frame):
    def __init__(self, parent=None):
        self.title = "Console"
        self.WINDOWS = True
        if platform.system() == "Windows":
            self.WINDOWS = True
        else:
            self.WINDOWS = False

        no_sys_menu = wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.RESIZE_BORDER | wx.CAPTION | wx.CLIP_CHILDREN | wx.CLOSE_BOX
        wx.Frame.__init__(self, title=self.title, parent=parent, size=(500, 700), style=no_sys_menu)
        panel = wx.Panel(self, -1)

        self.loggingList = wx.ListBox(
            panel, wx.ID_ANY, choices=[], style=wx.LB_NEEDED_SB | wx.LB_HSCROLL
        )

        self.loggingList.SetFont(
            wx.Font(
                11,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "",
            )
        )

        grid_sizer_2 = wx.GridSizer(1, 1, 0, 0)
        grid_sizer_2.Add(self.loggingList, 0, wx.EXPAND, 1)
        panel.SetSizer(grid_sizer_2)

        for entry in Globals.LOGLIST:
            self.loggingList.Append(entry)
            if self.WINDOWS:
                self.loggingList.EnsureVisible(self.loggingList.GetCount() - 1)

        self.SetBackgroundColour(wx.Colour(100, 100, 100))
        self.Centre()
        self.Show()

    def onClear(self, event=None):
        self.loggingList.Clear()
        Globals.LOGLIST.clear()

    def Logging(self, entry):
        """Logs Infromation To Frame UI"""
        self.loggingList.Append(entry)
        if self.WINDOWS:
            self.loggingList.EnsureVisible(self.loggingList.GetCount() - 1)
        Globals.LOGLIST.append(entry)
        return
