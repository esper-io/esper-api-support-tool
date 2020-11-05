from WXFrameLayoutNew import NewFrameLayout as FrameLayout
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import Globals
import wx
import ctypes
import sys
import os
import platform


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
