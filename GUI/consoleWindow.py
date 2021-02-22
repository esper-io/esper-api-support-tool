#!/usr/bin/env python

import wx
import Common.Globals as Globals
import platform
import Utility.wxThread as wxThread


class Console(wx.Frame):
    def __init__(self, parent=None):
        self.title = "Console"
        self.WINDOWS = True
        self.parent = parent
        if platform.system() == "Windows":
            self.WINDOWS = True
        else:
            self.WINDOWS = False

        no_sys_menu = (
            wx.MINIMIZE_BOX
            | wx.MAXIMIZE_BOX
            | wx.RESIZE_BORDER
            | wx.CAPTION
            | wx.CLIP_CHILDREN
            | wx.CLOSE_BOX
        )
        wx.Frame.__init__(
            self, title=self.title, parent=parent, size=(500, 700), style=no_sys_menu
        )
        panel = wx.Panel(self, -1)

        self.loggingList = wx.TextCtrl(
            panel,
            wx.ID_ANY,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_AUTO_URL | wx.TE_BESTWRAP,
        )

        self.loggingList.SetFont(
            wx.Font(
                11,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "",
            )
        )

        grid_sizer_2 = wx.GridSizer(1, 1, 0, 0)
        grid_sizer_2.Add(self.loggingList, 0, wx.EXPAND, 1)
        panel.SetSizer(grid_sizer_2)

        for entry in Globals.LOGLIST:
            self.loggingList.AppendText(entry)
            self.loggingList.AppendText("\n")
            if self.WINDOWS:
                self.loggingList.ShowPosition(self.loggingList.GetNumberOfLines() - 1)

        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.loggingList.Bind(wx.EVT_KEY_UP, self.onEscapePressed)
        self.Bind(wx.EVT_KEY_UP, self.onEscapePressed)

        self.SetBackgroundColour(wx.Colour(100, 100, 100))
        self.Centre()
        self.Show()

    def onEscapePressed(self, event):
        keycode = event.GetKeyCode()
        if (
            self.HasFocus() or self.loggingList.HasFocus()
        ) and keycode == wx.WXK_ESCAPE:
            self.onClose(event)

    def onClose(self, event):
        evt = wxThread.CustomEvent(wxThread.myEVT_UNCHECK_CONSOLE, -1, None)
        if Globals.frame:
            wx.PostEvent(Globals.frame, evt)
        if event.EventType != wx.EVT_CLOSE.typeId:
            self.Close()
        self.Destroy()

    def onClear(self, event=None):
        self.loggingList.Clear()
        Globals.LOGLIST.clear()

    def Logging(self, entry):
        """Logs Infromation To Frame UI"""
        self.loggingList.AppendText(entry)
        self.loggingList.AppendText("\n")
        if self.WINDOWS:
            self.loggingList.EnsureVisible(self.loggingList.GetCount() - 1)
        if entry:
            Globals.LOGLIST.append(entry.strip())
        return
