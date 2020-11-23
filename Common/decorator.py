import Common.Globals as Globals
import sys
import tempfile
import time
import wx

from Utility.ApiToolLogging import ApiToolLog
from traceback import print_exc, extract_tb, format_list


def api_tool_decorator(func):
    def inner(*args, **kwargs):
        start = time.perf_counter()
        result = None
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            wx.MessageBox(
                "An Error has occured: \n\n%s" % e, style=wx.OK | wx.ICON_ERROR
            )
            print_exc()
            exc_type, exc_value, exc_traceback = sys.exc_info()
            exc_traceback = format_list(extract_tb(exc_traceback))
            ApiToolLog().LogError(e, exc_type, exc_value, exc_traceback)

            Globals.frame.Logging(str(e), isError=True)
            Globals.frame.setCursorDefault()
            Globals.frame.setGaugeValue(100)
        end = time.perf_counter()
        duration = end - start
        if Globals.PRINT_FUNC_DURATION:
            print("%s executed in %s seconds." % (func.__name__, duration))
        return result

    return inner
