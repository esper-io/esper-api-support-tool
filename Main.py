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


@api_tool_decorator()
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
        if (
            args.record_place.lower() == "true"
            or args.record_place.lower() == "t"
            or args.record_place.lower() == "y"
        ):
            Globals.RECORD_PLACE = True
        else:
            Globals.RECORD_PLACE = False
    if hasattr(args, "print_res"):
        if (
            args.print_res.lower() == "true"
            or args.print_res.lower() == "t"
            or args.print_res.lower() == "y"
        ):
            Globals.PRINT_RESPONSES = True
        else:
            Globals.PRINT_RESPONSES = False
    if hasattr(args, "print_duration"):
        if (
            args.print_duration.lower() == "true"
            or args.print_duration.lower() == "t"
            or args.print_duration.lower() == "y"
        ):
            Globals.PRINT_FUNC_DURATION = True
        else:
            Globals.PRINT_FUNC_DURATION = False
    if hasattr(args, "log_api"):
        if (
            args.log_api.lower() == "true"
            or args.log_api.lower() == "t"
            or args.log_api.lower() == "y"
        ):
            Globals.PRINT_API_LOGS = True
        else:
            Globals.PRINT_API_LOGS = False


if __name__ == "__main__":
    # parseArgs()
    main()
