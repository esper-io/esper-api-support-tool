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
            print("Another instance is running")
            return False

        Globals.frame = FrameLayout()
        self.SetTopWindow(Globals.frame)
        Globals.frame.Show()
        return True

    def MacPrintFile(self, file_path):
        Globals.frame.MacPrintFile(file_path)

    def MacNewFile(self):
        Globals.frame.MacNewFile()


@api_tool_decorator()
def main():
    """Launches Main App"""
    sys.excepthook = ApiToolLog().excepthook
    try:
        Globals.app = MyApp(0)
        Globals.app.MainLoop()
    except Exception as e:
        ApiToolLog().LogError(e)


if __name__ == "__main__":
    command = " ".join(sys.argv)
    cmdList = command.split("--")
    for cmd in cmdList:
        parts = cmd.split(" ")
        if parts[0] == "record_place":
            if (
                parts[1].lower() == "true"
                or parts[1].lower() == "t"
                or parts[1].lower() == "y"
            ):
                Globals.RECORD_PLACE = True
            else:
                Globals.RECORD_PLACE = False
        if parts[0] == "print_res":
            if (
                parts[1].lower() == "true"
                or parts[1].lower() == "t"
                or parts[1].lower() == "y"
            ):
                Globals.PRINT_RESPONSES = True
            else:
                Globals.PRINT_RESPONSES = False
        if parts[0] == "print_duration":
            if (
                parts[1].lower() == "true"
                or parts[1].lower() == "t"
                or parts[1].lower() == "y"
            ):
                Globals.PRINT_FUNC_DURATION = True
            else:
                Globals.PRINT_FUNC_DURATION = False
        if parts[0] == "log_api":
            if (
                parts[1].lower() == "true"
                or parts[1].lower() == "t"
                or parts[1].lower() == "y"
            ):
                Globals.PRINT_API_LOGS = True
            else:
                Globals.PRINT_API_LOGS = False
    main()
