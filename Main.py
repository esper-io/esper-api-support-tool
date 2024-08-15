#!/usr/bin/env python

import locale
import sys

import wx

import Common.Globals as Globals
from Common.decorator import api_tool_decorator
from GUI.WXFrameLayoutNew import NewFrameLayout as FrameLayout
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Logging.SentryUtils import SentryUtils


class MyApp(wx.App):
    def OnInit(self):
        try:
            self.locale = wx.Locale(wx.LANGUAGE_ENGLISH_US)
            locale.setlocale(locale.LC_ALL, "en_US")
            self.name = "EAST-%s" % wx.GetUserId()
            self.instance = wx.SingleInstanceChecker(self.name)

            if self.instance.IsAnotherRunning() and not Globals.IS_DEBUG:
                wx.MessageBox(
                    "Another instance is running!", style=wx.ICON_ERROR
                )
                return False

            Globals.frame = FrameLayout()
            self.SetTopWindow(Globals.frame)
            Globals.frame.Show()
        except Exception as e:
            ApiToolLog().LogError(e)
            raise e
        return True

    def MacPrintFile(self, file_path):
        Globals.frame.MacPrintFile(file_path)

    def MacNewFile(self):
        Globals.frame.MacNewFile()


@api_tool_decorator(displayPrompt=False)
def main():
    """Launches Main App"""
    logger = ApiToolLog()
    SentryUtils()
    sys.excepthook = logger.excepthook

    logger.limitLogFileSizes()
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
        if parts[0] == "debug":
            if (
                parts[1].lower() == "true"
                or parts[1].lower() == "t"
                or parts[1].lower() == "y"
            ):
                Globals.IS_DEBUG = True
            else:
                Globals.IS_DEBUG = False
    main()
