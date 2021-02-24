#!/usr/bin/env python

from Utility.Resource import resourcePath
from Common.decorator import api_tool_decorator
import Utility.wxThread as wxThread
import wx
import wx.adv as adv
import Common.Globals as Globals
import webbrowser
import platform


from Utility.ApiToolLogging import ApiToolLog

from Utility.Resource import (
    downloadFileFromUrl,
    checkForUpdate,
)


class ToolMenuBar(wx.MenuBar):
    def __init__(self, style=0):
        super().__init__(style=style)

        self.configMenuOptions = []

        self.isCheckingForUpdates = False
        self.WINDOWS = False

        if platform.system() == "Windows":
            self.WINDOWS = True

        fileMenu = wx.Menu()
        foa = wx.MenuItem(fileMenu, wx.ID_OPEN, "&Add New Endpoint\tCtrl+A")
        self.fileOpenAuth = fileMenu.Append(foa)

        foc = wx.MenuItem(fileMenu, wx.ID_APPLY, "&Open Device CSV\tCtrl+O")
        self.fileOpenConfig = fileMenu.Append(foc)

        self.recent = wx.Menu()

        fileMenu.Append(wx.ID_SEPARATOR)
        fs = wx.MenuItem(fileMenu, wx.ID_SAVE, "&Save Device and Network Info \tCtrl+S")
        self.fileSave = fileMenu.Append(fs)

        fileMenu.Append(wx.ID_SEPARATOR)
        fi = wx.MenuItem(fileMenu, wx.ID_EXIT, "&Quit\tCtrl+Q")
        self.fileItem = fileMenu.Append(fi)

        self.configMenu = wx.Menu()
        self.defaultConfigVal = self.configMenu.Append(
            wx.ID_NONE, "No Loaded Configurations", "No Loaded Configurations"
        )
        self.configMenuOptions.append(self.defaultConfigVal)

        editMenu = wx.Menu()
        pref = wx.MenuItem(editMenu, wx.ID_ANY, "&Preferences\tCtrl+Shift+P")
        self.pref = editMenu.Append(pref)

        runMenu = wx.Menu()
        runItem = wx.MenuItem(runMenu, wx.ID_RETRY, "&Run\tCtrl+R")
        self.run = runMenu.Append(runItem)
        runMenu.Append(wx.ID_SEPARATOR)
        commandItem = wx.MenuItem(runMenu, wx.ID_ANY, "&Execute Command\tCtrl+Shift+C")
        self.command = runMenu.Append(commandItem)
        runMenu.Append(wx.ID_SEPARATOR)
        cloneItem = wx.MenuItem(runMenu, wx.ID_ANY, "&Clone Template\tCtrl+Shift+T")
        self.clone = runMenu.Append(cloneItem)

        viewMenu = wx.Menu()
        self.deviceColumns = viewMenu.Append(
            wx.MenuItem(viewMenu, wx.ID_ANY, "Toggle Device Columns")
        )
        self.networkColumns = viewMenu.Append(
            wx.MenuItem(viewMenu, wx.ID_ANY, "Toggle Network Columns")
        )
        viewMenu.Append(wx.ID_SEPARATOR)
        self.consoleView = viewMenu.Append(
            wx.MenuItem(
                viewMenu, wx.ID_ANY, "&Show Console Log\tCtrl+L", kind=wx.ITEM_CHECK
            )
        )
        self.clearConsole = viewMenu.Append(
            wx.MenuItem(viewMenu, wx.ID_ANY, "Clear Console Log")
        )
        viewMenu.Append(wx.ID_SEPARATOR)
        self.refreshGrids = viewMenu.Append(
            wx.MenuItem(viewMenu, wx.ID_ANY, "Refresh Grids' Data")
        )

        self.clearGrids = viewMenu.Append(
            wx.MenuItem(viewMenu, wx.ID_ANY, "Clear Grids")
        )

        helpMenu = wx.Menu()

        helpItem = wx.MenuItem(helpMenu, wx.ID_ANY, "&Help\tF1")
        helpMenu.Append(helpItem)
        self.Bind(wx.EVT_MENU, self.onHelp, helpItem)

        helpMenu.Append(wx.ID_SEPARATOR)

        checkUpdate = wx.MenuItem(helpMenu, wx.ID_ANY, "&Check For Updates")
        helpMenu.Append(checkUpdate)
        self.Bind(wx.EVT_MENU, self.onUpdateCheck, checkUpdate)

        helpMenu.Append(wx.ID_SEPARATOR)

        about = helpMenu.Append(wx.ID_HELP, "About", "&About")
        self.Bind(wx.EVT_MENU, self.onAbout, about)

        self.Append(fileMenu, "&File")
        self.Append(editMenu, "&Edit")
        self.Append(viewMenu, "&View")
        self.Append(self.configMenu, "&Configurations")
        self.Append(runMenu, "&Run")
        self.Append(helpMenu, "&Help")

    @api_tool_decorator
    def onAbout(self, event):
        """ About Dialog """
        info = adv.AboutDialogInfo()

        info.SetIcon(wx.Icon(resourcePath("Images/logo.png"), wx.BITMAP_TYPE_PNG))
        info.SetName(Globals.TITLE)
        info.SetVersion(Globals.VERSION)
        info.SetDescription(Globals.DESCRIPTION)
        info.SetCopyright("(C) 2020 Esper - All Rights Reserved")
        info.SetWebSite(Globals.ESPER_LINK)

        adv.AboutBox(info)

    @api_tool_decorator
    def onHelp(self, event):
        webbrowser.open(Globals.HELP_LINK)

    @api_tool_decorator
    def onUpdateCheck(self, event):
        if not self.isCheckingForUpdates:
            update = wxThread.GUIThread(self, self.updateCheck, None)
            update.start()
            self.isCheckingForUpdates = True

    def updateCheck(self):
        icon = wx.ICON_INFORMATION
        msg = ""
        json = None
        try:
            json = checkForUpdate()
        except Exception as e:
            print(e)
            ApiToolLog().LogError(e)
        if json:
            tagVersion = json["tag_name"].replace("v", "")
            if float(tagVersion) > float(Globals.VERSION.replace("v", "")):
                downloadURL = ""
                name = ""
                assets = json["assets"]
                for asset in assets:
                    name = asset["name"]
                    if "win" in name.lower() and self.WINDOWS:
                        downloadURL = asset["browser_download_url"]
                        break
                    elif "mac" in name.lower() and not self.WINDOWS:
                        downloadURL = asset["browser_download_url"]
                        break
                if downloadURL:
                    result = None
                    try:
                        result = downloadFileFromUrl(downloadURL, name)
                    except Exception as e:
                        print(e)
                        ApiToolLog().LogError(e)
                    if result:
                        msg = (
                            "Download Succeeded! File should be located at:\n\n%s\nPlease open the executable from the download!"
                            % result
                        )
                    else:
                        icon = wx.ICON_ERROR
                        msg = "An error occured while downloading the update. Please try again later."
            else:
                msg = "You are up-to-date!"
        else:
            icon = wx.ICON_ERROR
            msg = (
                "An error occured while downloading the update. Please try again later."
            )
        wx.MessageBox(msg, style=icon)
        self.isCheckingForUpdates = False

    @api_tool_decorator
    def uncheckConsole(self, event):
        """ Uncheck Console menu item """
        self.consoleView.Check(False)