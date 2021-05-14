#!/usr/bin/env python

from GUI.WXFrameLayoutNew import NewFrameLayout as FrameLayout
from Utility.ApiToolLogging import ApiToolLog

import Common.Globals as Globals
import sys
import wx

from Common.decorator import api_tool_decorator


class MyApp(wx.App):
    def OnInit(self):
        self.name = "EAST-%s" % wx.GetUserId()
        self.instance = wx.SingleInstanceChecker(self.name)

        if self.instance.IsAnotherRunning():
            return False

        Globals.frame = FrameLayout()
        self.SetTopWindow(Globals.frame)
        Globals.frame.Show()
        return True

    def MacPrintFile(self, file_path):
        Globals.frame.MacPrintFile(file_path)

    def MacNewFile(self):
        Globals.frame.MacNewFile()


@api_tool_decorator
def main():
    """Launches Main App"""
    sys.excepthook = ApiToolLog().excepthook
    try:
        Globals.app = MyApp(0)
        Globals.app.MainLoop()
    except Exception as e:
        ApiToolLog().LogError(e)


if __name__ == "__main__":
    main()
