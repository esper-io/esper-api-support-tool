#!/usr/bin/env python

from GUI.Dialogs.LargeTextEntryDialog import LargeTextEntryDialog
from Utility.EastUtility import processCollectionDevices
from Utility.API.CollectionsApi import checkCollectionIsEnabled, preformEqlSearch
from GUI.Dialogs.CollectionsDlg import CollectionsDialog
from Utility.Resource import openWebLinkInBrowser, resourcePath
from Common.decorator import api_tool_decorator
from GUI.UserCreation import UserCreation
import wx
import wx.adv as adv
import Common.Globals as Globals
import platform


from Utility.Logging.ApiToolLogging import ApiToolLog

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
        self.uc = None

        if platform.system() == "Windows":
            self.WINDOWS = True

        # File Menu
        fileMenu = wx.Menu()
        foa = wx.MenuItem(fileMenu, wx.ID_OPEN, "&Add New Tenant\tCtrl+A")
        addPng = wx.Bitmap(resourcePath("Images/Menu/add.png"))
        foa.SetBitmap(addPng)
        self.fileOpenAuth = fileMenu.Append(foa)

        fileMenu.Append(wx.ID_SEPARATOR)
        foc = wx.MenuItem(fileMenu, wx.ID_APPLY, "&Open Device CSV\tCtrl+O")
        foc.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/open.png")))
        self.fileOpenConfig = fileMenu.Append(foc)

        fileMenu.Append(wx.ID_SEPARATOR)
        fs = wx.MenuItem(fileMenu, wx.ID_SAVE, "&Save All Reports\tCtrl+S")
        fs.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/save.png")))
        self.fileSave = fileMenu.Append(fs)

        fileMenu.Append(wx.ID_SEPARATOR)
        fas = wx.MenuItem(
            fileMenu, wx.ID_SAVEAS, "&Fetch Selected and Save Device Info\tCtrl+Alt+S"
        )
        fas.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/fetchSave.png")))
        self.fileSaveAs = fileMenu.Append(fas)

        fileMenu.Append(wx.ID_SEPARATOR)
        fi = wx.MenuItem(fileMenu, wx.ID_EXIT, "&Quit\tCtrl+Q")
        fi.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/exit.png")))
        self.fileItem = fileMenu.Append(fi)

        # Tenant Menu
        self.configMenu = wx.Menu()
        self.defaultConfigVal = self.configMenu.Append(
            wx.ID_NONE, "No Loaded Tenants", "No Loaded Tenants"
        )
        self.configMenuOptions.append(self.defaultConfigVal)

        # Edit Menu
        editMenu = wx.Menu()
        pref = wx.MenuItem(editMenu, wx.ID_ANY, "&Preferences\tCtrl+Shift+P")
        pref.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/prefs.png")))
        self.pref = editMenu.Append(pref)

        # Run Menu
        runMenu = wx.Menu()
        runItem = wx.MenuItem(runMenu, wx.ID_RETRY, "&Run\tCtrl+R")
        runItem.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/run.png")))
        self.run = runMenu.Append(runItem)
        runMenu.Append(wx.ID_SEPARATOR)
        commandItem = wx.MenuItem(runMenu, wx.ID_ANY, "&Execute Command\tCtrl+Shift+C")
        commandItem.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/cmd.png")))
        self.command = runMenu.Append(commandItem)
        runMenu.Append(wx.ID_SEPARATOR)

        self.cloneSubMenu = wx.Menu()

        cloneItem = wx.MenuItem(
            self.cloneSubMenu, wx.ID_ANY, "&Clone Template\tCtrl+Shift+T"
        )
        self.clone = self.cloneSubMenu.Append(cloneItem)
        self.clone.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/clone.png")))

        cloneBlueprint = wx.MenuItem(
            self.cloneSubMenu,
            wx.ID_ANY,
            "&Clone Blueprint Across Tenants\tCtrl+Shift+B",
        )
        self.cloneBP = self.cloneSubMenu.Append(cloneBlueprint)
        self.cloneBP.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/clone.png")))
        self.toggleCloneMenuOptions(False)

        self.cloneSubMenu = runMenu.Append(wx.ID_ANY, "&Clone", self.cloneSubMenu)

        runMenu.Append(wx.ID_SEPARATOR)

        self.appSubMenu = wx.Menu()
        self.uploadApp = self.appSubMenu.Append(wx.ID_ANY, "Upload App (APK)")
        self.uploadApp.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/upload.png")))
        self.installApp = self.appSubMenu.Append(wx.ID_ANY, "Install App")
        self.uninstallApp = self.appSubMenu.Append(wx.ID_ANY, "Uninstall App")
        self.appSubMenu.Append(wx.ID_SEPARATOR)
        self.setKiosk = self.appSubMenu.Append(wx.ID_ANY, "Set Kiosk App")
        self.setMultiApp = self.appSubMenu.Append(wx.ID_ANY, "Set to Multi-App Mode")
        self.appSubMenu.Append(wx.ID_SEPARATOR)
        self.clearData = self.appSubMenu.Append(wx.ID_ANY, "Clear App Data")
        self.appSubMenu.Append(wx.ID_SEPARATOR)
        self.setAppState = self.appSubMenu.Append(wx.ID_ANY, "Set App State")
        self.appSubMenu.Append(wx.ID_SEPARATOR)
        self.installedDevices = self.appSubMenu.Append(
            wx.ID_ANY, "&Get Installed Devices\tCtrl+Shift+I"
        )
        self.appSubMenu = runMenu.Append(wx.ID_ANY, "&Applications", self.appSubMenu)
        self.appSubMenu.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/apps.png")))
        runMenu.Append(wx.ID_SEPARATOR)

        self.groupSubMenu = wx.Menu()
        self.moveGroup = self.groupSubMenu.Append(wx.ID_ANY, "&Move Device(s)\tCtrl+M")
        self.createGroup = self.groupSubMenu.Append(wx.ID_ANY, "&Manage Groups\tCtrl+G")
        self.groupSubMenu = runMenu.Append(wx.ID_ANY, "&Groups", self.groupSubMenu)
        self.groupSubMenu.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/groups.png")))
        runMenu.Append(wx.ID_SEPARATOR)

        self.collectionSubMenu = wx.Menu()
        collectionItem = wx.MenuItem(
            self.collectionSubMenu,
            wx.ID_ANY,
            "&Perform Collection Action (Preview)\tCtrl+Shift+F",
        )
        self.collection = self.collectionSubMenu.Append(collectionItem)
        self.collection.SetBitmap(
            wx.Bitmap(resourcePath("Images/Menu/collections.png"))
        )
        eqlQueryItem = wx.MenuItem(
            self.collectionSubMenu, wx.ID_ANY, "&EQL Search (Preview)\tCtrl+F"
        )
        self.eqlQuery = self.collectionSubMenu.Append(eqlQueryItem)
        self.eqlQuery.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/search.png")))
        self.collectionSubMenu = runMenu.Append(
            wx.ID_ANY, "&Collections", self.collectionSubMenu
        )
        self.collectionSubMenu.SetBitmap(
            wx.Bitmap(resourcePath("Images/Menu/collections.png"))
        )
        runMenu.Append(wx.ID_SEPARATOR)

        bulkReset = wx.MenuItem(runMenu, wx.ID_ANY, "&Bulk Factory Reset\t")
        self.bulkFactoryReset = runMenu.Append(bulkReset)
        runMenu.Append(wx.ID_SEPARATOR)

        geo = wx.MenuItem(runMenu, wx.ID_RETRY, "&Create Geofence")
        self.geoMenu = runMenu.Append(geo)
        runMenu.Append(wx.ID_SEPARATOR)

        self.userSubMenu = wx.Menu()
        fou = wx.MenuItem(self.userSubMenu, wx.ID_ADD, "&Manage Users\tCtrl+U")
        fou.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/addUser.png")))
        self.fileAddUser = self.userSubMenu.Append(fou)

        userReport = wx.MenuItem(
            self.userSubMenu, wx.ID_ANY, "&Get User Report\tCtrl+Shift+U"
        )
        self.userReportItem = self.userSubMenu.Append(userReport)

        # View Menu
        viewMenu = wx.Menu()
        self.deviceColumns = viewMenu.Append(
            wx.MenuItem(
                viewMenu, wx.ID_ANY, "&Toggle Grid Column Visibility\tCtrl+Shift+V"
            )
        )
        self.deviceColumns.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/view.png")))
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
        self.colSize = viewMenu.Append(
            wx.MenuItem(viewMenu, wx.ID_ANY, "Auto-Size Grids' Columns")
        )
        self.colSize.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/resize.png")))
        self.clearGrids = viewMenu.Append(
            wx.MenuItem(viewMenu, wx.ID_ANY, "Clear Grids")
        )
        self.clearGrids.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/clear.png")))
        viewMenu.Append(wx.ID_SEPARATOR)

        # Help Menu
        helpMenu = wx.Menu()

        helpItem = wx.MenuItem(helpMenu, wx.ID_ANY, "&Help\tF1")
        helpItem.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/help.png")))
        helpMenu.Append(helpItem)
        self.Bind(wx.EVT_MENU, self.onHelp, helpItem)

        helpMenu.Append(wx.ID_SEPARATOR)

        checkUpdate = wx.MenuItem(helpMenu, wx.ID_ANY, "&Check For Updates")
        checkUpdate.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/update.png")))
        helpMenu.Append(checkUpdate)
        self.Bind(wx.EVT_MENU, self.onUpdateCheck, checkUpdate)

        helpMenu.Append(wx.ID_SEPARATOR)

        about = helpMenu.Append(wx.ID_HELP, "About", "&About")
        about.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/info.png")))
        self.Bind(wx.EVT_MENU, self.onAbout, about)

        self.ConfigMenuPosition = 3
        self.Append(fileMenu, "&File")
        self.Append(editMenu, "&Edit")
        self.Append(viewMenu, "&View")
        self.Append(self.userSubMenu, "&Users")
        self.Append(self.configMenu, "&Tenants")
        self.Append(runMenu, "&Run")
        self.Append(helpMenu, "&Help")

        self.__set_properties()

    @api_tool_decorator()
    def __set_properties(self):
        self.run.Enable(False)
        self.command.Enable(False)
        self.clearConsole.Enable(False)
        self.collection.Enable(False)
        self.eqlQuery.Enable(False)
        self.collectionSubMenu.Enable(False)
        self.groupSubMenu.Enable(False)
        self.fileSave.Enable(False)
        self.fileSaveAs.Enable(False)

        self.Bind(wx.EVT_MENU, self.onEqlQuery, self.eqlQuery)
        self.Bind(wx.EVT_MENU, self.onCollection, self.collection)

        self.Bind(wx.EVT_MENU, self.parentFrame.showConsole, self.consoleView)
        self.Bind(wx.EVT_MENU, self.parentFrame.onClearGrids, self.clearGrids)
        self.Bind(wx.EVT_MENU, self.parentFrame.AddEndpoint, self.defaultConfigVal)
        self.Bind(wx.EVT_MENU, self.parentFrame.AddEndpoint, self.fileOpenAuth)
        self.Bind(wx.EVT_MENU, self.AddUser, self.fileAddUser)
        self.Bind(wx.EVT_MENU, self.parentFrame.onUploadCSV, self.fileOpenConfig)
        self.Bind(wx.EVT_MENU, self.parentFrame.OnQuit, self.fileItem)
        self.Bind(wx.EVT_MENU, self.parentFrame.onSaveBoth, self.fileSave)
        self.Bind(wx.EVT_MENU, self.parentFrame.onSaveBothAll, self.fileSaveAs)
        self.Bind(wx.EVT_MENU, self.parentFrame.onRun, self.run)
        self.Bind(wx.EVT_MENU, self.parentFrame.onCommand, self.command)
        self.Bind(wx.EVT_MENU, self.parentFrame.onClone, self.clone)
        self.Bind(wx.EVT_MENU, self.parentFrame.onCloneBP, self.cloneBP)
        self.Bind(wx.EVT_MENU, self.parentFrame.onPref, self.pref)
        self.Bind(
            wx.EVT_MENU, self.parentFrame.onInstalledDevices, self.installedDevices
        )
        self.Bind(
            wx.EVT_MENU, self.parentFrame.gridPanel.autoSizeGridsColumns, self.colSize
        )
        self.Bind(
            wx.EVT_MENU,
            self.parentFrame.gridPanel.onColumnVisibility,
            self.deviceColumns,
        )
        self.Bind(wx.EVT_MENU, self.parentFrame.moveGroup, self.moveGroup)
        self.Bind(wx.EVT_MENU, self.parentFrame.createGroup, self.createGroup)
        self.Bind(wx.EVT_MENU, self.parentFrame.installApp, self.installApp)
        self.Bind(wx.EVT_MENU, self.parentFrame.uninstallApp, self.uninstallApp)
        self.Bind(wx.EVT_MENU, self.onClearData, self.clearData)
        self.Bind(wx.EVT_MENU, self.onSetAppState, self.setAppState)
        self.Bind(wx.EVT_MENU, self.onSetMode, self.setKiosk)
        self.Bind(wx.EVT_MENU, self.onSetMode, self.setMultiApp)
        self.Bind(wx.EVT_MENU, self.parentFrame.uploadApplication, self.uploadApp)
        self.Bind(
            wx.EVT_MENU, self.parentFrame.onBulkFactoryReset, self.bulkFactoryReset
        )
        self.Bind(wx.EVT_MENU, self.parentFrame.onGeofence, self.geoMenu)
        self.Bind(wx.EVT_MENU, self.parentFrame.onUserReport, self.userReportItem)

    @api_tool_decorator()
    def onAbout(self, event):
        """ About Dialog """
        info = adv.AboutDialogInfo()

        info.SetIcon(wx.Icon(resourcePath("Images/logo.png"), wx.BITMAP_TYPE_PNG))
        info.SetName(Globals.TITLE)
        info.SetVersion(Globals.VERSION)
        info.SetDescription(Globals.DESCRIPTION)
        info.SetCopyright("No Copyright (C) 2021 Esper")
        info.SetWebSite(Globals.ESPER_LINK)

        adv.AboutBox(info)

    @api_tool_decorator()
    def onHelp(self, event):
        openWebLinkInBrowser(Globals.HELP_LINK)

    @api_tool_decorator()
    def onUpdateCheck(self, event=None, showDlg=True):
        if not self.isCheckingForUpdates:
            Globals.THREAD_POOL.enqueue(self.updateCheck, showDlg)
            self.isCheckingForUpdates = True

    @api_tool_decorator()
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

    @api_tool_decorator()
    def uncheckConsole(self, event):
        """ Uncheck Console menu item """
        self.consoleView.Check(False)

    @api_tool_decorator()
    def disableConfigMenu(self):
        self.EnableTop(self.ConfigMenuPosition, False)

    @api_tool_decorator()
    def enableConfigMenu(self):
        self.EnableTop(self.ConfigMenuPosition, True)

    @api_tool_decorator()
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
                    Globals.THREAD_POOL.enqueue(processCollectionDevices, deviceListResp)
            else:
                self.parentFrame.setCursorDefault()

    @api_tool_decorator()
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
                    Globals.THREAD_POOL.enqueue(processCollectionDevices, deviceListResp)
            else:
                self.parentFrame.setCursorDefault()
            dlg.DestroyLater()

    @api_tool_decorator()
    def checkCollectionEnabled(self):
        if not checkCollectionIsEnabled():
            if hasattr(self.collectionSubMenu, "Hide"):
                self.collectionSubMenu.Hide()
            else:
                self.collectionSubMenu.Enable(False)
        else:
            if hasattr(self.collectionSubMenu, "Show"):
                self.collectionSubMenu.Show()
            else:
                self.collectionSubMenu.Enable(True)

    @api_tool_decorator()
    def AddUser(self, event):
        if not self.uc:
            self.uc = UserCreation(self)
        self.parentFrame.toggleEnabledState(False)
        self.parentFrame.isRunning = True
        self.uc.Show()
        self.uc.tryToMakeActive()

    @api_tool_decorator()
    def onClearData(self, event):
        indx = self.parentFrame.sidePanel.actionChoice.GetItems().index(
            list(Globals.GENERAL_ACTIONS.keys())[4]
        )
        self.parentFrame.sidePanel.actionChoice.SetSelection(indx)
        self.parentFrame.onRun()

    @api_tool_decorator()
    def onSetMode(self, event):
        kioskIndx = self.parentFrame.sidePanel.actionChoice.GetItems().index(
            list(Globals.GENERAL_ACTIONS.keys())[2]
        )
        multiIndx = self.parentFrame.sidePanel.actionChoice.GetItems().index(
            list(Globals.GENERAL_ACTIONS.keys())[3]
        )
        menuItem = event.EventObject.FindItemById(event.Id)
        if "multi" in menuItem.GetItemLabelText().lower():
            self.parentFrame.sidePanel.actionChoice.SetSelection(multiIndx)
        else:
            self.parentFrame.sidePanel.actionChoice.SetSelection(kioskIndx)
        self.parentFrame.onRun()

    @api_tool_decorator()
    def onSetAppState(self, event):
        showIndx = self.parentFrame.sidePanel.actionChoice.GetItems().index(
            list(Globals.GENERAL_ACTIONS.keys())[5]
        )
        self.parentFrame.sidePanel.actionChoice.SetSelection(showIndx)
        self.parentFrame.onRun()

    def setSaveMenuOptionsEnableState(self, state):
        self.fileSave.Enable(state)
        self.fileSaveAs.Enable(state)

    def toggleCloneMenuOptions(self, showBlueprint, toggleBothSameState=False):
        if toggleBothSameState:
            self.clone.Enable(enable=showBlueprint)
            self.cloneBP.Enable(enable=showBlueprint)
        else:
            self.clone.Enable(enable=bool(not showBlueprint))
            self.cloneBP.Enable(enable=showBlueprint)
