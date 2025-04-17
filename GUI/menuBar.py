#!/usr/bin/env python

import atexit
import os
import platform
import shutil
import sys

import wx
import wx.adv as adv

import Common.Globals as Globals
import Utility.Threading.wxThread as wxThread
from Common.decorator import api_tool_decorator
from GUI.Dialogs.HtmlDialog import HtmlDialog
from Utility import EventUtility
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Resource import (
    checkForUpdate,
    downloadFileFromUrl,
    openWebLinkInBrowser,
    postEventToFrame,
    resourcePath,
)


class ToolMenuBar(wx.MenuBar):
    def __init__(self, parent, style=0):
        super().__init__(style=style)

        self.configMenuOptions = []
        self.parentFrame = parent

        self.isCheckingForUpdates = False
        self.WINDOWS = False
        self.uc = None

        self.SetThemeEnabled(False)
        if platform.system() == "Windows":
            self.WINDOWS = True

        # File Menu
        fileMenu = wx.Menu()
        foa = wx.MenuItem(fileMenu, wx.ID_OPEN, "&Add New Tenant\tCtrl+A")
        addPng = wx.Bitmap(resourcePath("Images/Menu/add.png"))
        foa.SetBitmap(addPng)
        self.fileOpenAuth = fileMenu.Append(foa)

        fileMenu.Append(wx.ID_SEPARATOR)
        foc = wx.MenuItem(fileMenu, wx.ID_APPLY, "&Open Device Spreadsheet\tCtrl+O")
        foc.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/open.png")))
        self.fileOpenConfig = fileMenu.Append(foc)

        fileMenu.Append(wx.ID_SEPARATOR)
        fs = wx.MenuItem(fileMenu, wx.ID_SAVE, "&Save All Reports\tCtrl+S")
        fs.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/save.png")))
        self.fileSave = fileMenu.Append(fs)

        fileMenu.Append(wx.ID_SEPARATOR)
        fas = wx.MenuItem(
            fileMenu,
            wx.ID_SAVEAS,
            "&Fetch Selected and Save Device Info\tCtrl+Alt+S",
        )
        fas.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/fetchSave.png")))
        self.fileSaveAs = fileMenu.Append(fas)

        fileMenu.Append(wx.ID_SEPARATOR)
        fi = wx.MenuItem(fileMenu, wx.ID_EXIT, "&Quit\tCtrl+Q")
        fi.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/exit.png")))
        self.fileItem = fileMenu.Append(fi)

        # Tenant Menu
        self.configMenu = wx.Menu()
        self.defaultConfigVal = self.configMenu.Append(wx.ID_NONE, "No Loaded Tenants", "No Loaded Tenants")
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
        powerDownItem = wx.MenuItem(runMenu, wx.ID_ANY, "&Power Down Devices (Knox Only)")
        self.powerDown = runMenu.Append(powerDownItem)
        runMenu.Append(wx.ID_SEPARATOR)

        self.cloneSubMenu = wx.Menu()

        cloneItem = wx.MenuItem(self.cloneSubMenu, wx.ID_ANY, "&Clone Template\tCtrl+Shift+T")
        self.clone = self.cloneSubMenu.Append(cloneItem)
        self.clone.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/clone.png")))

        cloneBlueprint = wx.MenuItem(
            self.cloneSubMenu,
            wx.ID_ANY,
            "&Clone Blueprint Across Tenants\tCtrl+Shift+B",
        )
        self.cloneBP = self.cloneSubMenu.Append(cloneBlueprint)
        self.cloneBP.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/clone.png")))

        self.cloneSubMenu.Append(wx.ID_SEPARATOR)

        convertTemplate = wx.MenuItem(self.cloneSubMenu, wx.ID_ANY, "&Convert Template to Blueprint")
        self.convert = self.cloneSubMenu.Append(convertTemplate)

        self.cloneSubMenu = runMenu.Append(wx.ID_ANY, "&Clone", self.cloneSubMenu)

        runMenu.Append(wx.ID_SEPARATOR)

        self.appSubMenu = wx.Menu()
        self.installedDevices = self.appSubMenu.Append(wx.ID_ANY, "&Get Installed Devices\tCtrl+Shift+I")
        self.appSubMenu.Append(wx.ID_SEPARATOR)
        self.newBlueprintApp = self.appSubMenu.Append(wx.ID_ANY, "&Push new app to Blueprints")
        self.appSubMenu = runMenu.Append(wx.ID_ANY, "&Applications", self.appSubMenu)
        self.appSubMenu.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/apps.png")))
        runMenu.Append(wx.ID_SEPARATOR)

        self.groupSubMenu = wx.Menu()
        self.moveGroup = self.groupSubMenu.Append(wx.ID_ANY, "&Move Device(s)\tCtrl+M")
        self.downloadGroups = self.groupSubMenu.Append(wx.ID_ANY, "&Download CSV of Groups\tCtrl+Shift+G")
        self.groupSubMenu = runMenu.Append(wx.ID_ANY, "&Groups", self.groupSubMenu)
        self.groupSubMenu.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/groups.png")))
        runMenu.Append(wx.ID_SEPARATOR)

        geo = wx.MenuItem(runMenu, wx.ID_ANY, "&Create Geofence")
        self.geoMenu = runMenu.Append(geo)
        runMenu.Append(wx.ID_SEPARATOR)

        widgetMenu = wx.MenuItem(runMenu, wx.ID_ANY, "&Configure Widgets\tCtrl+Shift+W")
        self.configureWidgets = runMenu.Append(widgetMenu)

        runMenu.Append(wx.ID_SEPARATOR)

        self.userSubMenu = wx.Menu()

        userReport = wx.MenuItem(self.userSubMenu, wx.ID_ANY, "&Get User Report\tCtrl+Shift+U")
        self.userReportItem = self.userSubMenu.Append(userReport)

        pendingUserReport = wx.MenuItem(self.userSubMenu, wx.ID_ANY, "&Get Pending User Report\tCtrl+Alt+U")
        self.pendingUserReportItem = self.userSubMenu.Append(pendingUserReport)

        # View Menu
        viewMenu = wx.Menu()
        self.deviceColumns = viewMenu.Append(
            wx.MenuItem(
                viewMenu,
                wx.ID_ANY,
                "&Toggle Grid Column Visibility\tCtrl+Shift+V",
            )
        )
        self.fullscreen = viewMenu.Append(
            wx.MenuItem(
                viewMenu,
                wx.ID_ANY,
                "&Toggle Fullscreen\tF11",
            )
        )
        self.deviceColumns.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/view.png")))
        viewMenu.Append(wx.ID_SEPARATOR)
        self.consoleView = viewMenu.Append(
            wx.MenuItem(
                viewMenu,
                wx.ID_ANY,
                "&Show Console Log\tCtrl+L",
                kind=wx.ITEM_CHECK,
            )
        )
        self.clearConsole = viewMenu.Append(wx.MenuItem(viewMenu, wx.ID_ANY, "Clear Console Log"))
        viewMenu.Append(wx.ID_SEPARATOR)
        self.colSize = viewMenu.Append(wx.MenuItem(viewMenu, wx.ID_ANY, "Auto-Size Grids' Columns"))
        self.colSize.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/resize.png")))
        self.gridRefresh = viewMenu.Append(wx.MenuItem(viewMenu, wx.ID_ANY, "Refresh Grids"))
        self.gridRefresh.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/refresh.png")))
        self.clearGrids = viewMenu.Append(wx.MenuItem(viewMenu, wx.ID_ANY, "Clear Grids"))
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

        tnc = helpMenu.Append(wx.ID_ANY, "Terms and Conditions", "&Terms and Conditions")
        self.Bind(wx.EVT_MENU, self.onDisclaimer, tnc)

        about = helpMenu.Append(wx.ID_HELP, "About", "&About")
        about.SetBitmap(wx.Bitmap(resourcePath("Images/Menu/info.png")))
        self.Bind(wx.EVT_MENU, self.onAbout, about)

        self.sensitiveMenuOptions = [0, 1, 2, 3, 4, 5]
        self.ConfigMenuPosition = 4
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
        self.groupSubMenu.Enable(False)
        self.fileSave.Enable(False)
        self.fileSaveAs.Enable(False)

        self.Bind(wx.EVT_MENU, self.parentFrame.showConsole, self.consoleView)
        self.Bind(wx.EVT_MENU, self.parentFrame.onClearGrids, self.clearGrids)
        self.Bind(wx.EVT_MENU, self.parentFrame.AddEndpoint, self.defaultConfigVal)
        self.Bind(wx.EVT_MENU, self.parentFrame.AddEndpoint, self.fileOpenAuth)
        self.Bind(
            wx.EVT_MENU,
            self.parentFrame.onUploadSpreadsheet,
            self.fileOpenConfig,
        )
        self.Bind(wx.EVT_MENU, self.parentFrame.OnQuit, self.fileItem)
        self.Bind(wx.EVT_MENU, self.parentFrame.onSaveBoth, self.fileSave)
        self.Bind(wx.EVT_MENU, self.parentFrame.onSaveBothAll, self.fileSaveAs)
        self.Bind(wx.EVT_MENU, self.parentFrame.onRun, self.run)
        self.Bind(wx.EVT_MENU, self.parentFrame.onCommand, self.command)
        self.Bind(wx.EVT_MENU, self.parentFrame.onClone, self.clone)
        self.Bind(wx.EVT_MENU, self.parentFrame.onCloneBP, self.cloneBP)
        self.Bind(wx.EVT_MENU, self.parentFrame.onConvertTemplate, self.convert)
        self.Bind(wx.EVT_MENU, self.parentFrame.onPref, self.pref)
        self.Bind(
            wx.EVT_MENU,
            self.parentFrame.onInstalledDevices,
            self.installedDevices,
        )
        self.Bind(
            wx.EVT_MENU,
            self.parentFrame.onNewBlueprintApp,
            self.newBlueprintApp,
        )
        self.Bind(
            wx.EVT_MENU,
            self.parentFrame.gridPanel.autoSizeGridsColumns,
            self.colSize,
        )
        self.Bind(
            wx.EVT_MENU,
            self.parentFrame.gridPanel.forceRefreshGrids,
            self.gridRefresh,
        )
        self.Bind(
            wx.EVT_MENU,
            self.parentFrame.gridPanel.onColumnVisibility,
            self.deviceColumns,
        )
        self.Bind(wx.EVT_MENU, self.parentFrame.onFullscreen, self.fullscreen)
        self.Bind(wx.EVT_MENU, self.parentFrame.moveGroup, self.moveGroup)
        self.Bind(wx.EVT_MENU, self.parentFrame.downloadGroups, self.downloadGroups)
        self.Bind(wx.EVT_MENU, self.parentFrame.onGeofence, self.geoMenu)
        self.Bind(wx.EVT_MENU, self.parentFrame.onUserReport, self.userReportItem)
        self.Bind(
            wx.EVT_MENU,
            self.parentFrame.onPendingUserReport,
            self.pendingUserReportItem,
        )
        self.Bind(
            wx.EVT_MENU,
            self.parentFrame.onConfigureWidgets,
            self.configureWidgets,
        )
        self.Bind(wx.EVT_MENU, self.parentFrame.onPowerDown, self.powerDown)

    @api_tool_decorator()
    def onAbout(self, event):
        """About Dialog"""
        info = adv.AboutDialogInfo()

        info.SetIcon(wx.Icon(resourcePath("Images/logo.png"), wx.BITMAP_TYPE_PNG))
        info.SetName(Globals.TITLE)
        info.SetVersion(Globals.VERSION)
        info.SetDescription(Globals.DESCRIPTION)
        info.SetCopyright("No Copyright (C) 2022 Esper")
        info.SetWebSite(Globals.ESPER_LINK)

        adv.AboutBox(info)

    @api_tool_decorator()
    def onDisclaimer(self, event=None, showCheckBox=False):
        showDisclaimer = True
        with HtmlDialog(showCheckbox=showCheckBox) as dialog:
            Globals.OPEN_DIALOGS.append(dialog)
            dialog.ShowModal()
            Globals.OPEN_DIALOGS.remove(dialog)

            showDisclaimer = bool(not dialog.isCheckboxChecked())
        if Globals.frame:
            Globals.frame.savePrefs(Globals.frame.prefDialog)
        return showDisclaimer

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
        msg = ""
        json = None
        try:
            json = checkForUpdate()
        except Exception as e:
            print(e)
            ApiToolLog().LogError(e)
        if json:
            tagVersion = json["tag_name"].split("-")[0].replace("v", "")
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
                    postEventToFrame(
                        EventUtility.myEVT_PROCESS_FUNCTION,
                        (
                            self.displayUpdateOnMain,
                            (downloadURL, name, showDlg),
                        ),
                    )
            else:
                msg = "You are up-to-date!"
        else:
            msg = "An error occurred while downloading the update. Please try again later."
        if msg:
            self.parentFrame.Logging(msg, isError=True if "error" in msg.lower() else False)
        self.isCheckingForUpdates = False

    def displayUpdateOnMain(self, downloadURL, name, showDlg):
        dlg = wx.MessageBox(
            "Update found! Do you want to update?",
            "Update",
            wx.YES_NO | wx.ICON_QUESTION,
            parent=Globals.frame,
        )
        if dlg == wx.ID_YES or dlg == wx.YES:
            self.parentFrame.statusBar.gauge.Pulse()
            thread = wxThread.GUIThread(None, downloadFileFromUrl, (downloadURL, name))
            thread.startWithRetry()
            Globals.THREAD_POOL.enqueue(self.processUpdateResult, thread, showDlg)

    def processUpdateResult(self, thread, showDlg):
        icon = wx.ICON_INFORMATION
        msg = ""
        thread.join()
        result = thread.result
        if result:
            msg = (
                "Download Succeeded!\n\nFile should be located at:\n%s\n\nPlease open the executable from the download!" % result
            )
        else:
            icon = wx.ICON_ERROR
            msg = "An error occurred while downloading the update. Please try again later."

        if msg and showDlg:
            postEventToFrame(
                EventUtility.myEVT_MESSAGE_BOX,
                (msg, icon),
            )
            if result:
                openWebLinkInBrowser(result, isfile=True)
                atexit.register(lambda file=__file__: self.deleteFile(file))
                Globals.frame.OnQuit(None)
        elif msg:
            self.parentFrame.Logging(msg, isError=True if "error" in msg.lower() else False)
        self.isCheckingForUpdates = False

    def deleteFile(self, file_path):
        application_path = ""
        if getattr(sys, "frozen", False):
            # If the application is run as a bundle, the PyInstaller bootloader
            # extends the sys module by a flag frozen=True and sets the app
            # path into variable _MEIPASS'.
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))

        files = os.listdir(application_path)
        try:
            version = Globals.VERSION.replace(".", "-")
            extention = "exe" if platform.system() == "Windows" else "app"
            versionExtention = "%s_EsperApiSupportTool.%s" % (
                version,
                extention,
            )
            for file in files:
                ApiToolLog().Log(file)
                if file.endswith(".exe") and file.endswith(versionExtention):
                    exe_path = os.path.join(application_path, file)
                    shutil.rmtree(exe_path, ignore_errors=True)
                    break
        except Exception as e:
            ApiToolLog().LogError(e)

    @api_tool_decorator()
    def uncheckConsole(self, event):
        """Uncheck Console menu item"""
        self.consoleView.Check(False)

    @api_tool_decorator()
    def disableConfigMenu(self):
        self.EnableTop(self.ConfigMenuPosition, False)

    @api_tool_decorator()
    def enableConfigMenu(self):
        self.EnableTop(self.ConfigMenuPosition, True)

    def setSaveMenuOptionsEnableState(self, state):
        self.fileSave.Enable(state)
        self.fileSaveAs.Enable(state)
