#!/usr/bin/env python

import os

import wx

import Common.Globals as Globals
from Common.decorator import api_tool_decorator
from Utility import EventUtility
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Resource import deleteFile, download, postEventToFrame
from Utility.Web.WebRequests import performPostRequestWithRetry


@api_tool_decorator()
def uploadWallpaper(link, key, enterprise_id, bg):
    json_resp = None
    files = None
    try:
        headers = {
            "Authorization": f"Bearer {key}",
        }
        download(bg["url"], "wallpaper.jpeg")
        ApiToolLog().LogApiRequestOccurrence(
            "download", bg["url"], Globals.PRINT_API_LOGS
        )
        if os.path.exists("wallpaper.jpeg"):
            payload = {
                "orientation": bg["orientation"],
                "enterprise": enterprise_id,
            }
            if not link.endswith("enterprise/"):
                if not link.endswith("/"):
                    link += "/enterprise/"
                else:
                    link += "enterprise/"
            if not link.endswith("/"):
                link += "/"
            url = (
                link
                + enterprise_id
                + "/wallpaper/"
                + "?limit={num}".format(num=Globals.limit)
            )
            files = {"image_file": open("wallpaper.jpeg", "rb")}
            postEventToFrame(
                EventUtility.myEVT_LOG, "Attempting to upload wallpaper..."
            )
            resp = performPostRequestWithRetry(
                url, headers=headers, data=payload, files=files
            )
            if resp.ok:
                postEventToFrame(EventUtility.myEVT_LOG, "Wallpaper upload Succeeded!")
                json_resp = resp.json()
            else:
                postEventToFrame(EventUtility.myEVT_LOG, "Wallpaper upload Failed!")
                wx.MessageBox(
                    "Wallpaper upload Failed! Source: %s" % bg["url"],
                    style=wx.OK | wx.ICON_ERROR,
                    parent=Globals.frame
                )
                resp.raise_for_status()
        else:
            wx.MessageBox(
                "Failed to download wallpaper for uploading",
                style=wx.OK | wx.ICON_ERROR,
                parent=Globals.frame
            )
    except Exception as e:
        raise e
    finally:
        if files:
            files["image_file"].close()
    deleteFile("wallpaper.jpeg")
    if json_resp:
        return json_resp
