#!/usr/bin/env python

import atexit
import locale
import os
import signal
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
            atexit.register(OnExit)

            # Register signal handlers for common termination signals (optional, but recommended)
            signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
            signal.signal(signal.SIGTERM, signal_handler) # Termination signal
            # On Windows, also handle these signals:
            if os.name == 'nt':
                signal.signal(signal.SIGBREAK, signal_handler)

            Globals.frame = FrameLayout()
            self.SetTopWindow(Globals.frame)
            # Globals.frame.Show()
        except Exception as e:
            ApiToolLog().LogError(e)
            raise e
        return True

    def MacPrintFile(self, file_path):
        Globals.frame.MacPrintFile(file_path)

    def MacNewFile(self):
        Globals.frame.MacNewFile()

def OnExit():
    if Globals.frame:
        Globals.frame.OnQuit(None)

def signal_handler(signal, frame):
    OnExit()

@api_tool_decorator(displayPrompt=False)
def main():
    """Launches Main App"""
    logger = ApiToolLog()
    try:
        SentryUtils()
    except Exception as e:
        ApiToolLog().LogError(e)
    sys.excepthook = logger.excepthook

    logger.limitLogFileSizes()
    try:
        Globals.app = MyApp(0)
        Globals.app.MainLoop()
    except Exception as e:
        ApiToolLog().LogError(e)

def is_arg_enabled(val):
    val = val.lower() if hasattr(val, "lower") else val
    return (val == "true" or val == "t" or val == "y")

if __name__ == "__main__":
    command = " ".join(sys.argv)
    cmdList = command.split("--")
    for cmd in cmdList:
        parts = cmd.split(" ")
        if parts[0] == "record_place":
            if is_arg_enabled(parts[1]):
                Globals.RECORD_PLACE = True
            else:
                Globals.RECORD_PLACE = False
        if parts[0] == "print_res":
            if is_arg_enabled(parts[1]):
                Globals.PRINT_RESPONSES = True
            else:
                Globals.PRINT_RESPONSES = False
        if parts[0] == "print_duration":
            if is_arg_enabled(parts[1]):
                Globals.PRINT_FUNC_DURATION = True
            else:
                Globals.PRINT_FUNC_DURATION = False
        if parts[0] == "log_api":
            if is_arg_enabled(parts[1]):
                Globals.PRINT_API_LOGS = True
            else:
                Globals.PRINT_API_LOGS = False
        if parts[0] == "debug":
            if is_arg_enabled(parts[1]):
                Globals.IS_DEBUG = True
            else:
                Globals.IS_DEBUG = False
        if parts[0] == "do_extra_logging":
            if not is_arg_enabled(parts[1]):
                Globals.DO_EXTRA_LOGGING = False
            else:
                Globals.DO_EXTRA_LOGGING = True
    main()
