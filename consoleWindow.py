import wx
import Globals
import platform

class Console(wx.Frame):
    def __init__(self, parent=None):
        self.title = "Console"
        self.WINDOWS = True
        if platform.system() == "Windows":
            self.WINDOWS = True
        else:
            self.WINDOWS = False

        wx.Frame.__init__(self, title=self.title, parent=parent, size=(500,700))
        panel = wx.Panel(self, -1)

        self.loggingList = wx.ListBox(panel, wx.ID_ANY, choices=[], style=wx.LB_NEEDED_SB | wx.LB_HSCROLL)

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

        self.SetBackgroundColour(wx.Colour(100,100,100))
        self.Centre()
        self.Show()

    def Logging(self, entry):
        """Logs Infromation To Frame UI"""
        self.loggingList.Append(entry)
        if self.WINDOWS:
            self.loggingList.EnsureVisible(self.loggingList.GetCount() - 1)
        if "--->" not in entry:
            Globals.LOGLIST.append(entry)
        return