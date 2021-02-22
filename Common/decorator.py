#!/usr/bin/env python

import Common.Globals as Globals
import json
import sys
import time
import wx

from esperclient.rest import ApiException
from Utility.ApiToolLogging import ApiToolLog
from traceback import print_exc, extract_tb, format_list


def api_tool_decorator(func):
    def inner(*args, **kwargs):
        start = time.perf_counter()
        result = None
        excpt = None
        try:
            result = func(*args, **kwargs)
        except ApiException as e:
            excpt = e
            bodyMsg = json.loads(e.body)["message"]
            wx.MessageBox(
                "%s %s: %s" % (e.reason, e.status, bodyMsg), style=wx.OK | wx.ICON_ERROR
            )
            ApiToolLog().LogError(e)
        except Exception as e:
            excpt = e
            wx.MessageBox(
                "An Error has occured: \n\n%s" % e, style=wx.OK | wx.ICON_ERROR
            )
            print_exc()
            exc_type, exc_value, exc_traceback = sys.exc_info()
            exc_traceback = format_list(extract_tb(exc_traceback))
            ApiToolLog().LogError(e, exc_type, exc_value, exc_traceback)
        finally:
            if Globals.frame and excpt:
                Globals.frame.Logging(str(excpt), isError=True)
                Globals.frame.onComplete(None)
                Globals.frame.setCursorDefault()
                Globals.frame.setGaugeValue(100)
        end = time.perf_counter()
        duration = end - start
        if Globals.PRINT_FUNC_DURATION:
            print("%s executed in %s seconds." % (func.__name__, duration))
        return result

    return inner
