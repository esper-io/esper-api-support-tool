#!/usr/bin/env python

from GUI.WXFrameLayoutNew import NewFrameLayout as FrameLayout
import Common.Globals as Globals
import wx


class MyApp(wx.App):
    def OnInit(self):
        Globals.frame = FrameLayout()
        self.SetTopWindow(Globals.frame)
        Globals.frame.Show()
        return True


if __name__ == "__main__":
    """Launches Main App"""
    Globals.app = MyApp(0)
    Globals.app.MainLoop()
