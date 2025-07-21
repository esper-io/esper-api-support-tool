#!/usr/bin/env python

import platform
import re
from datetime import datetime

import wx
import wx.html as wxHtml

import Common.Globals as Globals
import Utility.EventUtility as eventUtil
from Common.decorator import api_tool_decorator
from Common.enum import Color, FontStyles
from Utility.Resource import (getFont, onDialogEscape, openWebLinkInBrowser,
                              postEventToFrame, resourcePath, setElmTheme)


class Console(wx.Frame):
    def __init__(self, parent=None):
        self.title = "Logs"
        self.WINDOWS = True
        self.parent = parent
        if platform.system() == "Windows":
            self.WINDOWS = True
        else:
            self.WINDOWS = False

        no_sys_menu = wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.RESIZE_BORDER | wx.CAPTION | wx.CLIP_CHILDREN | wx.CLOSE_BOX
        wx.Frame.__init__(self, title=self.title, parent=parent, size=(500, 700), style=no_sys_menu)
        self.SetThemeEnabled(False)
        icon = wx.Icon()
        icon.CopyFromBitmap(wx.Bitmap(resourcePath("Images/icon.png"), wx.BITMAP_TYPE_PNG))
        self.SetIcon(icon)

        panel = wx.Panel(self, wx.ID_ANY)
        panel.SetBackgroundColour(Color.grey.value)

        self.loggingList = wx.TextCtrl(
            panel,
            wx.ID_ANY,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_AUTO_URL | wx.TE_BESTWRAP,
        )

        self.loggingList.SetFont(getFont(FontStyles.NORMAL.value))

        grid_sizer_2 = wx.GridSizer(1, 1, 0, 0)
        grid_sizer_2.Add(self.loggingList, 0, wx.ALL | wx.EXPAND, 5)
        panel.SetSizer(grid_sizer_2)

        while len(Globals.LOGLIST) > Globals.MAX_LOG_LIST_SIZE:
            Globals.LOGLIST.pop(0)

        self.firstLine = True
        for entry in Globals.LOGLIST:
            self.Logging(entry.strip(), scrollToEnd=False)
            if self.firstLine:
                self.firstLine = False
        self.scrollToEnd()

        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.loggingList.Bind(wx.EVT_KEY_UP, self.onEscapePressed)

        self.loggingList.Bind(wxHtml.EVT_HTML_LINK_CLICKED, openWebLinkInBrowser)
        self.Bind(wx.EVT_KEY_UP, self.onEscapePressed)

        exitId = wx.NewId()
        self.Bind(wx.EVT_MENU, self.onClose, id=exitId)
        accel_table = wx.AcceleratorTable(
            [
                (wx.ACCEL_CTRL, ord("W"), exitId),
                (wx.ACCEL_CMD, ord("W"), exitId),
            ]
        )
        self.SetAcceleratorTable(accel_table)

        setElmTheme(self)
        self.Centre()
        self.Show()

    @api_tool_decorator()
    def onEscapePressed(self, event):
        onDialogEscape(self, event)

    @api_tool_decorator()
    def onClose(self, event):
        postEventToFrame(eventUtil.myEVT_UNCHECK_CONSOLE, None)
        if event.EventType != wx.EVT_CLOSE.typeId:
            self.Close()
        self.DestroyLater()

    @api_tool_decorator()
    def onClear(self, event=None):
        self.loggingList.Clear()
        Globals.LOGLIST.clear()

    def scrollToEnd(self):
        self.loggingList.SetInsertionPointEnd()
        wx.CallAfter(self.loggingList.ShowPosition, self.loggingList.GetInsertionPoint())

    @api_tool_decorator()
    def Logging(self, entry, scrollToEnd=True):
        """Logs Infromation To Frame UI"""
        pattern = r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}"

        if self.loggingList:
            if not entry.startswith("\n") and not self.firstLine:
                entry = "\n\n" + entry
            match = re.search(pattern, entry)
            if not match:
                entry = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " + entry
            self.loggingList.AppendText(entry)
        if scrollToEnd:
            self.scrollToEnd()
        if entry:
            while len(Globals.LOGLIST) > Globals.MAX_LOG_LIST_SIZE:
                Globals.LOGLIST.pop(0)
            if entry.strip() not in Globals.LOGLIST:
                Globals.LOGLIST.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " + entry.strip())
        return
