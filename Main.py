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
    parser.add_argument(
        "--log_api",
        dest="log_api",
        action="store",
        nargs="?",
        default=False,
        help="Record What API Requests Are Made",
        required=False,
    )
    args = parser.parse_args()
    if hasattr(args, "record_place"):
        if args.record_place.lower() == "false" or args.record_place.lower() == "f":
            Globals.RECORD_PLACE = False
        elif args.record_place.lower() == "true" or args.record_place.lower() == "t":
            Globals.RECORD_PLACE = True
    if hasattr(args, "print_res"):
        if args.print_res.lower() == "false" or args.print_res.lower() == "f":
            Globals.PRINT_RESPONSES = False
        elif args.print_res.lower() == "true" or args.print_res.lower() == "t":
            Globals.PRINT_RESPONSES = True
    if hasattr(args, "print_duration"):
        if args.print_duration.lower() == "false" or args.print_duration.lower() == "f":
            Globals.PRINT_FUNC_DURATION = False
        elif (
            args.print_duration.lower() == "true" or args.print_duration.lower() == "t"
        ):
            Globals.PRINT_FUNC_DURATION = True
    if hasattr(args, "log_api"):
        if args.log_api.lower() == "false" or args.log_api.lower() == "f":
            Globals.PRINT_API_LOGS = False
        elif args.log_api.lower() == "true" or args.log_api.lower() == "t":
            Globals.PRINT_API_LOGS = True


if __name__ == "__main__":
    parseArgs()
    main()
