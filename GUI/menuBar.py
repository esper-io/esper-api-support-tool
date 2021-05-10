#!/usr/bin/env python

from GUI.Dialogs.LargeTextEntryDialog import LargeTextEntryDialog
from Utility.EastUtility import processCollectionDevices
from Utility.CollectionsApi import checkCollectionIsEnabled, preformEqlSearch
from GUI.Dialogs.CollectionsDlg import CollectionsDialog
from Utility.Resource import openWebLinkInBrowser, resourcePath
from Common.decorator import api_tool_decorator
import Utility.wxThread as wxThread
import wx
import wx.adv as adv
import Common.Globals as Globals
import platform


from Utility.ApiToolLogging import ApiToolLog

from Utility.Resource import (
    downloadFileFromUrl,
    checkForUpdate,
)


class ToolMenuBar(wx.MenuBar):
    def __init__(self, parent, style=0):
        super().__init__(style=style)

        self.configMenuOptions = []
        self.parentFrame = parent

        self.isCheckingForUpdates = False
        self.WINDOWS = False

        if platform.system() == "Windows":
            self.WINDOWS = True

        fileMenu = wx.Menu()
        foa = wx.MenuItem(fileMenu, wx.ID_OPEN, "&Add New Endpoint\tCtrl+A")
        self.fileOpenAuth = fileMenu.Append(foa)

        foc = wx.MenuItem(fileMenu, wx.ID_APPLY, "&Open Device CSV\tCtrl+O")
        self.fileOpenConfig = fileMenu.Append(foc)

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
        runMenu.Append(wx.ID_SEPARATOR)
        installedDevices = wx.MenuItem(
            runMenu, wx.ID_ANY, "&Get Installed Devices\tCtrl+Shift+I"
        )
        self.installedDevices = runMenu.Append(installedDevices)
        runMenu.Append(wx.ID_SEPARATOR)
        collectionItem = wx.MenuItem(
            runMenu, wx.ID_ANY, "&Perform Collection Action (Preview)\tCtrl+Shift+F"
        )
        self.collection = runMenu.Append(collectionItem)
        eqlQueryItem = wx.MenuItem(runMenu, wx.ID_ANY, "&EQL Search (Preview)\tCtrl+F")
        self.eqlQuery = runMenu.Append(eqlQueryItem)

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
        self.colSize = viewMenu.Append(
            wx.MenuItem(viewMenu, wx.ID_ANY, "Auto-Size Grids' Columns")
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

        self.ConfigMenuPosition = 3
        self.Append(fileMenu, "&File")
        self.Append(editMenu, "&Edit")
        self.Append(viewMenu, "&View")
        self.Append(self.configMenu, "&Configurations")
        self.Append(runMenu, "&Run")
        self.Append(helpMenu, "&Help")

        self.__set_properties()

    @api_tool_decorator
    def __set_properties(self):
        self.run.Enable(False)
        self.clone.Enable(False)
        self.command.Enable(False)
        self.clearConsole.Enable(False)
        self.collection.Enable(False)
        self.eqlQuery.Enable(False)

        self.Bind(wx.EVT_MENU, self.onEqlQuery, self.eqlQuery)
        self.Bind(wx.EVT_MENU, self.onCollection, self.collection)

        self.Bind(wx.EVT_MENU, self.parentFrame.showConsole, self.consoleView)
        self.Bind(wx.EVT_MENU, self.parentFrame.updateGrids, self.refreshGrids)
        self.Bind(wx.EVT_MENU, self.parentFrame.onClearGrids, self.clearGrids)
        self.Bind(wx.EVT_MENU, self.parentFrame.AddEndpoint, self.defaultConfigVal)
        self.Bind(wx.EVT_MENU, self.parentFrame.AddEndpoint, self.fileOpenAuth)
        self.Bind(wx.EVT_MENU, self.parentFrame.onUploadCSV, self.fileOpenConfig)
        self.Bind(wx.EVT_MENU, self.parentFrame.OnQuit, self.fileItem)
        self.Bind(wx.EVT_MENU, self.parentFrame.onSaveBoth, self.fileSave)
        self.Bind(wx.EVT_MENU, self.parentFrame.onRun, self.run)
        self.Bind(wx.EVT_MENU, self.parentFrame.onCommand, self.command)
        self.Bind(wx.EVT_MENU, self.parentFrame.onClone, self.clone)
        self.Bind(wx.EVT_MENU, self.parentFrame.onPref, self.pref)
        self.Bind(
            wx.EVT_MENU, self.parentFrame.onInstalledDevices, self.installedDevices
        )
        self.Bind(
            wx.EVT_MENU, self.parentFrame.gridPanel.autoSizeGridsColumns, self.colSize
        )
        self.Bind(
            wx.EVT_MENU, self.parentFrame.gridPanel.onDeviceColumn, self.deviceColumns
        )
        self.Bind(
            wx.EVT_MENU, self.parentFrame.gridPanel.onNetworkColumn, self.networkColumns
        )

    @api_tool_decorator
    def onAbout(self, event):
        """ About Dialog """
        info = adv.AboutDialogInfo()

        info.SetIcon(wx.Icon(resourcePath("Images/logo.png"), wx.BITMAP_TYPE_PNG))
        info.SetName(Globals.TITLE)
        info.SetVersion(Globals.VERSION)
        info.SetDescription(Globals.DESCRIPTION)
        info.SetCopyright("(C) 2021 Esper - All Rights Reserved")
        info.SetWebSite(Globals.ESPER_LINK)

        adv.AboutBox(info)

    @api_tool_decorator
    def onHelp(self, event):
        openWebLinkInBrowser(Globals.HELP_LINK)

    @api_tool_decorator
    def onUpdateCheck(self, event=None, showDlg=True):
        if not self.isCheckingForUpdates:
            update = wxThread.GUIThread(
                self, self.updateCheck, showDlg, name="UpdateCheck"
            )
            update.start()
            self.isCheckingForUpdates = True

    @api_tool_decorator
    def updateCheck(self, showDlg=False):
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
                    dlg = wx.MessageDialog(
                        None,
                        "Update found! Do you want to update?",
                        "Update",
                        wx.YES_NO | wx.ICON_QUESTION,
                    )
                    if dlg.ShowModal() == wx.ID_YES:
                        result = None
                        try:
                            result = downloadFileFromUrl(downloadURL, name)
                        except Exception as e:
                            print(e)
                            ApiToolLog().LogError(e)
                        if result:
                            showDlg = True
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
        if msg and showDlg:
            wx.MessageBox(msg, style=icon)
        elif msg:
            self.parentFrame.Logging(
                msg, isError=True if "error" in msg.lower() else False
            )
        self.isCheckingForUpdates = False

    @api_tool_decorator
    def uncheckConsole(self, event):
        """ Uncheck Console menu item """
        self.consoleView.Check(False)

    @api_tool_decorator
    def disableConfigMenu(self):
        self.EnableTop(self.ConfigMenuPosition, False)

    @api_tool_decorator
    def enableConfigMenu(self):
        self.EnableTop(self.ConfigMenuPosition, True)

    @api_tool_decorator
    def onEqlQuery(self, event):
        self.parentFrame.setGaugeValue(0)
        self.parentFrame.setCursorBusy()
        self.parentFrame.onClearGrids(None)
        with LargeTextEntryDialog(
            self.parentFrame, "Enter EQL Query:", "EQL Query"
        ) as textDialog:
            if textDialog.ShowModal() == wx.ID_OK:
                eql = textDialog.GetValue()
                if eql:
                    self.parentFrame.toggleEnabledState(False)
                    self.parentFrame.gauge.Pulse()
                    self.parentFrame.Logging("---> Performing EQL Query")
                    deviceListResp = preformEqlSearch(eql, None, returnJson=True)
                    self.parentFrame.Logging(
                        "---> Finsihed Performing EQL Query, processing results..."
                    )
                    wxThread.doAPICallInThread(
                        self,
                        processCollectionDevices,
                        args=(deviceListResp),
                        eventType=None,
                        waitForJoin=False,
                        name="eqlIterateThroughDeviceList",
                    )
            else:
                self.parentFrame.setCursorDefault()

    @api_tool_decorator
    def onCollection(self, event):
        self.parentFrame.setGaugeValue(0)
        self.parentFrame.setCursorBusy()
        self.parentFrame.onClearGrids(None)
        with CollectionsDialog(self.parentFrame) as dlg:
            if dlg.ShowModal() == wx.ID_EXECUTE:
                eql = dlg.getSelectionEql()
                if eql:
                    self.parentFrame.gauge.Pulse()
                    self.parentFrame.toggleEnabledState(False)
                    self.parentFrame.Logging("---> Performing EQL Query")
                    deviceListResp = preformEqlSearch(eql, None, returnJson=True)
                    self.parentFrame.Logging(
                        "---> Finsihed Performing EQL Query, processing results..."
                    )
                    wxThread.doAPICallInThread(
                        self,
                        processCollectionDevices,
                        args=(deviceListResp),
                        eventType=None,
                        waitForJoin=False,
                        name="collectionIterateThroughDeviceList",
                    )
            else:
                self.parentFrame.setCursorDefault()

    @api_tool_decorator
    def checkCollectionEnabled(self):
        if not checkCollectionIsEnabled():
            self.collection.Hide()
            self.eqlQuery.Hide()
