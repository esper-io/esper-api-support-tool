import Globals
import time
import wx

from traceback import print_exc


def api_tool_decorator(func):
    def inner(*args, **kwargs):
        start = time.perf_counter()
        try:
            func(*args, **kwargs)
        except Exception as e:
            wx.MessageBox(
                    "An Error has occured: \n\n%s" % e, style=wx.OK | wx.ICON_ERROR
                )
            print_exc()
        end = time.perf_counter()
        duration = end - start
        if Globals.PRINT_FUNC_DURATION:
            print("%s executed in %s seconds." % (func.__name__, duration))
    return inner
