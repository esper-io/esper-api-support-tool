#!/usr/bin/env python

from GUI.WXFrameLayoutNew import NewFrameLayout as FrameLayout
from Utility.ApiToolLogging import ApiToolLog

import argparse
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


def parseArgs():
    parser = argparse.ArgumentParser(description=Globals.DESCRIPTION)
    parser.add_argument(
        "--print_responses",
        dest="print_res",
        action="store",
        nargs="?",
        default=False,
        help="Print Responses",
        required=False,
    )
    parser.add_argument(
        "--print_duration",
        dest="print_duration",
        action="store",
        nargs="?",
        default=False,
        help="Print Duration of Methods",
        required=False,
    )
    parser.add_argument(
        "--record_place",
        dest="record_place",
        action="store",
        nargs="?",
        default=False,
        help="Record Execution Pathing",
        required=False,
    )
    args = parser.parse_args()
    if hasattr(args, "record_place"):
        Globals.RECORD_PLACE = args.record_place
    if hasattr(args, "print_res"):
        Globals.PRINT_RESPONSES = args.print_res
    if hasattr(args, "print_duration"):
        Globals.PRINT_FUNC_DURATION = args.print_duration


if __name__ == "__main__":
    parseArgs()
    main()
