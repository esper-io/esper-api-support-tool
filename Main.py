from WXFrameLayoutNew import NewFrameLayout as FrameLayout
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import EsperAPICalls
import WXFrameLayout
import Globals
import wx
import ctypes
import sys
import os
import platform
import subprocess

def askForAuthCSV():
    # Windows, Standalone executable will allow user to select CSV
    if "Windows" in platform.system():
        answer = ctypes.windll.user32.MessageBoxW(
            0, "Please Select The Config CSV", "Esper Tool", 1
        )
        print(answer)
        if answer == 2:
            sys.exit("No CSV Selected")
        root = Tk()
        filename = askopenfilename()
        Globals.csv_auth_path = filename
        print(filename)
        root.destroy()
    # Mac, Debug mode, find csv file using system path
    else:
        currentpath = os.path.realpath(__file__)
        filename = os.path.dirname(currentpath) + os.path.sep + Globals.CONFIGFILE
        Globals.csv_auth_path = filename


def initFrameLayout():
    """Intializes Frame"""
    frame = FrameLayout(None)
    frame.Show()
    frame.PopulateConfig()
    frame.LoadTagsAndAliases()
    Globals.frame = frame


class MyApp(wx.App):
    def OnInit(self):
        self.frame = FrameLayout(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True

if __name__ == "__main__":
    """Launches Main App"""
    #askForAuthCSV()
    Globals.app = MyApp(0)
    Globals.app.MainLoop()
    
    #Globals.app = wx.App(False)
    #initFrameLayout()
    #Globals.app.MainLoop()
