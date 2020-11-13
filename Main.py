from WXFrameLayoutNew import NewFrameLayout as FrameLayout
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import Globals
import wx
import ctypes
import sys
import os
import platform


class MyApp(wx.App):
    def OnInit(self):
        Globals.frame = FrameLayout(None, wx.ID_ANY, "")
        self.SetTopWindow(Globals.frame)
        Globals.frame.Show()
        return True


if __name__ == "__main__":
    """Launches Main App"""
    Globals.app = MyApp(0)
    Globals.app.MainLoop()
