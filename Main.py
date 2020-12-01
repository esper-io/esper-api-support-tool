from GUI.WXFrameLayoutNew import NewFrameLayout as FrameLayout
import Common.Globals as Globals
import wx
import sys
import os
import platform


class MyApp(wx.App):
    def OnInit(self):
        Globals.frame = FrameLayout(None, wx.ID_ANY, "")
        self.SetTopWindow(Globals.frame)
        Globals.frame.Show()
        return True


if __name__ == "__main__":
    """Launches Main App"""
    Globals.app = MyApp(0)
    Globals.app.MainLoop()
