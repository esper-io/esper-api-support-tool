import wx
import wx.grid as gridlib
import esperclient
import time
import csv
import os.path
import logging
import Globals
import ctypes
import platform
import json
import wxThread

from consoleWindow import Console

from deviceInfo import getSecurityPatch, getWifiStatus, getCellularStatus, getDeviceName

from tkinter import Tk
from tkinter.filedialog import askopenfilename

from esperclient import EnterpriseApi, ApiClient
from esperclient.rest import ApiException
from EsperAPICalls import (
    TakeAction,
    iterateThroughGridRows,
    ApplyDeviceConfig,
    setKiosk,
    setMulti,
)

from CustomDialogs import CheckboxMessageBox, CommandDialog


class NewFrameLayout(wx.Frame):
    def __init__(self, *args, **kwds):
        self.configMenuOptions = []
        self.WINDOWS = True
        if platform.system() == "Windows":
            self.WINDOWS = True
        else:
            self.WINDOWS = False
        self.auth_csv_reader = None
        self.configChoice = {}
        self.consoleWin = None
        self.grid_1_contents = []
        self.grid_2_contents = []

        # begin wxGlade: MyFrame.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((1552, 840))

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.panel_5 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.panel_3 = wx.Panel(self.panel_5, wx.ID_ANY)
        self.configList = wx.TextCtrl(
            self.panel_3, wx.ID_ANY, style=wx.TE_MULTILINE | wx.TE_READONLY
        )
        self.panel_7 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.groupChoice = wx.ComboBox(
            self.panel_7, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY
        )
        self.actionChoice = wx.ComboBox(
            self.panel_7,
            wx.ID_ANY,
            style=wx.CB_DROPDOWN | wx.CB_READONLY,
            choices=Globals.GENERAL_ACTIONS,
        )
        self.deviceChoice = wx.ComboBox(
            self.panel_7, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY
        )
        self.appChoice = wx.ComboBox(
            self.panel_7, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY
        )
        self.gridActions = wx.ComboBox(
            self.panel_7,
            wx.ID_ANY,
            choices=Globals.GRID_ACTIONS,
            style=wx.CB_DROPDOWN | wx.CB_READONLY,
        )
        self.panel_6 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.panel_8 = wx.Panel(self.panel_6, wx.ID_ANY)
        self.runBtn = wx.Button(self.panel_8, wx.ID_ANY, "Run")
        self.panel_2 = wx.Panel(self, wx.ID_ANY)
        self.panel_4 = wx.Panel(self.panel_2, wx.ID_ANY)
        self.grid_2 = wx.grid.Grid(self.panel_4, wx.ID_ANY, size=(1, 1))
        self.panel_9 = wx.Panel(self.panel_2, wx.ID_ANY)
        self.grid_1 = wx.grid.Grid(self.panel_9, wx.ID_ANY, size=(1, 1))

        self.configList.SetFont(
            wx.Font(
                11,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "",
            )
        )

        self.Bind(wx.EVT_CLOSE, self.OnQuit)

        self.Bind(wx.EVT_COMBOBOX, self.onActionSelection, self.actionChoice)
        self.Bind(wx.EVT_COMBOBOX, self.onGridActionSelection, self.gridActions)
        self.Bind(wx.EVT_BUTTON, self.onRun, self.runBtn)
        self.grid_1.Bind(gridlib.EVT_GRID_CELL_CHANGING, self.onCellChange)
        # self.grid_1.Bind(gridlib.EVT_GRID_COL_SORT, self.onSort)
        self.grid_1.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.onDeviceGridSort)
        self.grid_2.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.onNetworkGridSort)
        self.grid_1.Bind(gridlib.EVT_GRID_LABEL_RIGHT_CLICK, self.toogleViewMenuItem)
        self.grid_2.Bind(gridlib.EVT_GRID_LABEL_RIGHT_CLICK, self.toogleViewMenuItem)

        # Menu Bar
        self.menubar = wx.MenuBar()

        fileMenu = wx.Menu()
        foa = wx.MenuItem(fileMenu, wx.ID_OPEN, "&Open Auth CSV\tCtrl+O")
        fileOpenAuth = fileMenu.Append(foa)

        foc = wx.MenuItem(fileMenu, wx.ID_APPLY, "&Open Device CSV\tCtrl+D")
        fileOpenConfig = fileMenu.Append(foc)

        fileMenu.Append(wx.ID_SEPARATOR)
        fs = wx.MenuItem(fileMenu, wx.ID_SAVE, "&Save Device Info As\tCtrl+S")
        fileSave = fileMenu.Append(fs)

        fsa = wx.MenuItem(fileMenu, wx.ID_SAVEAS, "&Save Network Info As\tCtrl+Shift+S")
        fileSaveAs = fileMenu.Append(fsa)

        fileMenu.Append(wx.ID_SEPARATOR)
        fi = wx.MenuItem(fileMenu, wx.ID_EXIT, "&Quit\tCtrl+Q")
        fileItem = fileMenu.Append(fi)

        self.configMenu = wx.Menu()
        defaultConfigVal = self.configMenu.Append(
            wx.ID_NONE, "No Loaded Configurations", "No Loaded Configurations"
        )
        self.configMenuOptions.append(defaultConfigVal)

        runMenu = wx.Menu()
        runItem = wx.MenuItem(runMenu, wx.ID_RETRY, "&Run\tCtrl+R")
        self.run = runMenu.Append(runItem)

        commandItem = wx.MenuItem(
            runMenu, wx.ID_ANY, "&Apply Device Config\tCtrl+Shift+C"
        )
        self.command = runMenu.Append(commandItem)

        viewMenu = wx.Menu()
        self.viewMenuOptions = {}
        colNum = 1
        for header in Globals.CSV_NETWORK_ATTR_NAME:
            if header == "Device Name":
                continue
            item = viewMenu.Append(
                wx.ID_ANY, "Show %s" % header, "Show %s" % header, kind=wx.ITEM_CHECK
            )
            item.Check(True)
            self.Bind(wx.EVT_MENU, self.toggleColVisibilityInGridTwo, item)
            self.viewMenuOptions[item.Id] = colNum
            colNum += 1
        colNum = 1
        viewMenu.Append(wx.ID_SEPARATOR)
        for header in Globals.CSV_TAG_ATTR_NAME.keys():
            if header == "Esper Name":
                continue
            item = viewMenu.Append(
                wx.ID_ANY, "Show %s" % header, "Show %s" % header, kind=wx.ITEM_CHECK
            )
            item.Check(True)
            self.Bind(wx.EVT_MENU, self.toggleColVisibilityInGridOne, item)
            self.viewMenuOptions[item.Id] = colNum
            colNum += 1
        viewMenu.Append(wx.ID_SEPARATOR)
        consoleView = viewMenu.Append(
            wx.MenuItem(viewMenu, wx.ID_ANY, "Show Console", kind=wx.ITEM_CHECK)
        )
        self.Bind(wx.EVT_MENU, self.showConsole, consoleView)
        self.clearConsole = viewMenu.Append(
            wx.MenuItem(viewMenu, wx.ID_ANY, "Clear Console")
        )

        # helpMenu = wx.Menu()
        # helpItem = helpMenu.Append(wx.ID_HELP, "Help", "Help")
        # self.Bind(wx.EVT_MENU, self.onHelp, helpItem)

        self.menubar.Append(fileMenu, "&File")
        self.menubar.Append(viewMenu, "&View")
        self.menubar.Append(self.configMenu, "&Configurations")
        self.menubar.Append(runMenu, "&Run")
        # self.menubar.Append(helpMenu, "&Help")
        self.SetMenuBar(self.menubar)

        self.Bind(wx.EVT_MENU, self.OnOpen, defaultConfigVal)
        self.Bind(wx.EVT_MENU, self.OnOpen, fileOpenAuth)
        self.Bind(wx.EVT_MENU, self.onUploadCSV, fileOpenConfig)
        self.Bind(wx.EVT_MENU, self.OnQuit, fileItem)
        self.Bind(wx.EVT_MENU, self.onSave, fileSave)
        self.Bind(wx.EVT_MENU, self.onSaveAs, fileSaveAs)
        self.Bind(wx.EVT_MENU, self.onRun, self.run)
        self.Bind(wx.EVT_MENU, self.onCommand, self.command)
        # Menu Bar end

        # Tool Bar
        # self.frame_toolbar = wx.ToolBar(self, -1)
        # self.SetToolBar(self.frame_toolbar)

        # qtool = self.frame_toolbar.AddTool(wx.ID_ANY, 'Quit', png)
        # otool = self.frame_toolbar.AddTool(wx.ID_ANY, 'Open Auth CSV',  wx.Bitmap('Images/openFile.png', wx.BITMAP_TYPE_ANY))
        # stool = self.frame_toolbar.AddTool(wx.ID_ANY, 'Save As',  wx.Bitmap('Images/save.png', wx.BITMAP_TYPE_ANY))
        # ctool = self.frame_toolbar.AddTool(wx.ID_ANY, 'Clear',  wx.Bitmap('Images/clear.png', wx.BITMAP_TYPE_ANY))

        # self.Bind(wx.EVT_TOOL, self.OnQuit, qtool)
        # self.Bind(wx.EVT_TOOL, self.OnOpen, otool)
        # self.Bind(wx.EVT_TOOL, self.onSave, stool)
        # self.Bind(wx.EVT_TOOL, self.onClear, ctool)
        # Tool Bar end

        self.Bind(wxThread.EVT_UPDATE, self.onUpdate)

        self.statusBar = self.CreateStatusBar()
        self.statusBar.SetStatusText("")

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MyFrame.__set_properties
        self.SetTitle(Globals.TITLE)
        self.SetBackgroundColour(wx.Colour(192, 192, 192))

        self.actionChoice.SetSelection(0)

        self.actionChoice.Enable(False)
        self.deviceChoice.Enable(False)
        self.groupChoice.Enable(False)
        self.appChoice.Enable(False)
        self.runBtn.Enable(False)
        self.run.Enable(False)
        self.command.Enable(False)
        self.clearConsole.Enable(False)

        self.grid_2.CreateGrid(0, len(Globals.CSV_NETWORK_ATTR_NAME))
        self.grid_1.CreateGrid(0, len(Globals.CSV_TAG_ATTR_NAME.keys()))
        self.grid_1.UseNativeColHeader()
        self.grid_2.UseNativeColHeader()
        self.fillDeviceGridHeaders()
        self.fillNetworkGridHeaders()

        # self.frame_toolbar.Realize()
        self.panel_1.SetMinSize((400, 900))
        self.panel_2.SetMinSize((2000, 800))
        self.Maximize(True)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MyFrame.__do_layout
        sizer_1 = wx.FlexGridSizer(1, 2, 0, 0)
        grid_sizer_2 = wx.GridSizer(2, 1, 0, 0)
        grid_sizer_8 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_4 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_5 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_7 = wx.GridSizer(2, 1, 0, 0)
        sizer_4 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_5 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_6 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_3 = wx.GridSizer(1, 1, 0, 0)
        label_1 = wx.StaticText(
            self.panel_5,
            wx.ID_ANY,
            "Loaded Configuration:",
            style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END,
        )
        label_1.SetFont(
            wx.Font(
                11,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        label_1.Wrap(200)
        grid_sizer_6.Add(label_1, 0, wx.EXPAND, 0)
        grid_sizer_3.Add(self.configList, 0, wx.EXPAND, 0)
        self.panel_3.SetSizer(grid_sizer_3)
        grid_sizer_6.Add(self.panel_3, 1, wx.EXPAND, 0)
        self.panel_5.SetSizer(grid_sizer_6)
        grid_sizer_1.Add(self.panel_5, 1, wx.EXPAND, 0)
        label_2 = wx.StaticText(
            self.panel_7,
            wx.ID_ANY,
            "Choose a Group :",
            style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END,
        )
        label_2.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        grid_sizer_5.Add(label_2, 0, wx.EXPAND, 0)
        grid_sizer_5.Add(self.groupChoice, 0, wx.ALL | wx.EXPAND, 0)
        grid_sizer_5.Add((20, 20), 0, wx.EXPAND, 0)
        label_3 = wx.StaticText(
            self.panel_7,
            wx.ID_ANY,
            "Choose a Specific Device (optional):",
            style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END,
        )
        label_3.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        grid_sizer_5.Add(label_3, 0, wx.EXPAND, 0)
        grid_sizer_5.Add(self.deviceChoice, 0, wx.EXPAND, 0)
        grid_sizer_5.Add((20, 20), 0, wx.EXPAND, 0)
        label_6 = wx.StaticText(
            self.panel_7,
            wx.ID_ANY,
            "Action to apply:",
            style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END,
        )
        label_6.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        grid_sizer_5.Add(label_6, 0, wx.EXPAND, 0)
        grid_sizer_5.Add(self.actionChoice, 0, wx.ALL | wx.EXPAND, 0)
        grid_sizer_5.Add((20, 20), 0, wx.EXPAND, 0)
        label_4 = wx.StaticText(
            self.panel_7,
            wx.ID_ANY,
            "Application for Kiosk Mode",
            style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END,
        )
        label_4.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        grid_sizer_5.Add(label_4, 0, wx.EXPAND, 0)
        grid_sizer_5.Add(self.appChoice, 0, wx.EXPAND, 0)
        grid_sizer_5.Add((20, 20), 0, wx.EXPAND, 0)
        label_5 = wx.StaticText(
            self.panel_7,
            wx.ID_ANY,
            "Device Grid Actions",
            style=wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END,
        )
        label_5.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        grid_sizer_5.Add(label_5, 0, wx.EXPAND, 0)
        grid_sizer_5.Add(self.gridActions, 0, wx.EXPAND, 0)
        sizer_4.Add(grid_sizer_5, 0, wx.EXPAND, 0)
        self.panel_7.SetSizer(sizer_4)
        grid_sizer_1.Add(self.panel_7, 1, wx.EXPAND, 0)
        grid_sizer_7.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_7.Add(self.runBtn, 0, wx.EXPAND, 0)
        self.panel_8.SetSizer(grid_sizer_7)
        sizer_5.Add(self.panel_8, 1, wx.EXPAND, 0)
        self.panel_6.SetSizer(sizer_5)
        grid_sizer_1.Add(self.panel_6, 1, wx.EXPAND, 0)
        self.panel_1.SetSizer(grid_sizer_1)
        sizer_1.Add(self.panel_1, 0, wx.ALL | wx.EXPAND, 5)
        network_grid = wx.StaticText(self.panel_4, wx.ID_ANY, "Network Information:")
        network_grid.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        grid_sizer_4.Add(network_grid, 0, wx.LEFT, 5)
        grid_sizer_4.Add(self.grid_2, 1, wx.ALL | wx.EXPAND, 5)
        self.panel_4.SetSizer(grid_sizer_4)
        grid_sizer_2.Add(self.panel_4, 1, wx.EXPAND, 0)
        label_8 = wx.StaticText(self.panel_9, wx.ID_ANY, "Device Information:")
        label_8.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        grid_sizer_8.Add(label_8, 0, wx.LEFT, 5)
        grid_sizer_8.Add(self.grid_1, 1, wx.ALL | wx.EXPAND, 5)
        self.panel_9.SetSizer(grid_sizer_8)
        grid_sizer_2.Add(self.panel_9, 1, wx.EXPAND, 0)
        self.panel_2.SetSizer(grid_sizer_2)
        sizer_1.Add(self.panel_2, 0, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(sizer_1)
        self.Layout()
        # end wxGlade

    def scaleBitmapImage(self, width, height, path):
        image = wx.Bitmap(path).ConvertToImage()
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        result = wx.Bitmap(image)
        return result

    # Frame UI Logging
    def Logging(self, entry):
        if self.consoleWin:
            self.consoleWin.Logging(entry)
        self.setTempStatus(entry)

    def OnOpen(self, event):
        # otherwise ask the user what new file to open
        with wx.FileDialog(
            self,
            "Open Auth CSV File",
            wildcard="CSV files (*.csv)|*.csv",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # Proceed loading the file chosen by the user
            Globals.csv_auth_path = fileDialog.GetPath()
            print(Globals.csv_auth_path)
            self.PopulateConfig()

    def OnQuit(self, e):
        if self.consoleWin:
            self.consoleWin.Close()
            self.consoleWin.Destroy()
            self.consoleWin = None
        if e.EventType != wx.EVT_CLOSE.typeId:
            self.Close()
        self.Destroy()

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

    def onSave(self, event=None):
        """Sends Device Info To Frame For Logging"""
        if self.grid_1.GetNumberRows() > 0:
            dlg = wx.FileDialog(
                self,
                "Save CSV as...",
                os.getcwd(),
                "",
                "*.csv",
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            )
            result = dlg.ShowModal()
            inFile = dlg.GetPath()
            dlg.Destroy()

            if result == wx.ID_OK:  # Save button was pressed
                self.save(inFile, self.grid_1, Globals.CSV_TAG_ATTR_NAME.keys())
                return True
            elif (
                result == wx.ID_CANCEL
            ):  # Either the cancel button was pressed or the window was closed
                return False

    def onSaveAs(self, event):
        if self.grid_2.GetNumberRows() > 0:
            dlg = wx.FileDialog(
                self,
                "Save CSV as...",
                os.getcwd(),
                "",
                "*.csv",
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            )
            result = dlg.ShowModal()
            inFile = dlg.GetPath()
            dlg.Destroy()

            if result == wx.ID_OK:  # Save button was pressed
                self.save(inFile, self.grid_2, Globals.CSV_NETWORK_ATTR_NAME)
                return True
            elif (
                result == wx.ID_CANCEL
            ):  # Either the cancel button was pressed or the window was closed
                return False

    def save(self, inFile, grid, header):
        numRows = grid.GetNumberRows()
        numCols = grid.GetNumberCols()
        gridData = []
        gridData.append(header.replace("\n", "").split(","))

        self.createNewFile(inFile)

        for row in range(numRows):
            rowValues = []
            for col in range(numCols):
                value = grid.GetCellValue(row, col)
                rowValues.append(value)
            gridData.append(rowValues)

        with open(Globals.csv_tag_path_clone, "w", newline="") as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerows(gridData)

        self.Logging("---> Info saved to csv file - " + Globals.csv_tag_path_clone)

    def createNewFile(self, filePath):
        Globals.csv_tag_path_clone = filePath
        if not os.path.exists(Globals.csv_tag_path_clone):
            with open(Globals.csv_tag_path_clone, "w"):
                pass

    def onUploadCSV(self, event=None):
        if not Globals.enterprise_id:
            self.loadConfigPrompt()
            return

        self.emptyDeviceGrid()
        self.emptyNetworkGrid()
        with wx.FileDialog(
            self,
            "Open Device CSV File",
            wildcard="CSV files (*.csv)|*.csv",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as fileDialog:
            result = fileDialog.ShowModal()
            if result == wx.ID_OK:
                # Proceed loading the file chosen by the user
                Globals.csv_auth_path = fileDialog.GetPath()
                self.Logging(
                    "--->Attempting to load device data from %s" % Globals.csv_auth_path
                )
                num = 0
                with open(Globals.csv_auth_path, "r") as csvFile:
                    reader = csv.reader(
                        csvFile, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True
                    )
                    header = None
                    grid_headers = list(Globals.CSV_TAG_ATTR_NAME.keys())
                    for row in reader:
                        if not all("" == val or val.isspace() for val in row):
                            if num == 0:
                                header = row
                                num += 1
                                continue
                            self.grid_1.AppendRows(1)
                            fileCol = 0
                            toolCol = 0
                            for colValue in row:
                                colName = (
                                    header[fileCol].replace(" ", "").lower()
                                    if len(header) > fileCol
                                    else ""
                                )
                                if (
                                    header[fileCol]
                                    in Globals.CSV_DEPRECATED_HEADER_LABEL
                                ):
                                    fileCol += 1
                                    continue
                                gridColName = (
                                    grid_headers[toolCol].replace(" ", "").lower()
                                )
                                val = str(colValue) if colName == gridColName else ""
                                self.grid_1.SetCellValue(
                                    self.grid_1.GetNumberRows() - 1,
                                    toolCol,
                                    str(colValue),
                                )
                                isEditable = True
                                if grid_headers[toolCol] in Globals.CSV_EDITABLE_COL:
                                    isEditable = False
                                self.grid_1.SetReadOnly(
                                    self.grid_1.GetNumberRows() - 1, toolCol, isEditable
                                )
                                toolCol += 1
                                fileCol += 1
                    self.grid_1.AutoSizeColumns()
            elif result == wx.ID_CANCEL:
                return  # the user changed their mind

    def PopulateConfig(self):
        """Populates Configuration From CSV"""
        self.Logging("--->Loading Configurations from %s" % Globals.csv_auth_path)
        configfile = Globals.csv_auth_path

        for item in self.configMenuOptions:
            try:
                self.configMenu.Delete(item)
            except:
                pass
        self.configMenuOptions = []

        if os.path.isfile(configfile):
            with open(configfile, newline="") as csvfile:
                self.auth_csv_reader = csv.DictReader(csvfile)
                num = 0
                for row in self.auth_csv_reader:
                    if "name" in row:
                        self.configChoice[row["name"]] = row
                        item = self.configMenu.Append(
                            wx.ID_ANY, row["name"], row["name"], kind=wx.ITEM_CHECK
                        )
                        self.Bind(wx.EVT_MENU, self.loadConfiguartion, item)
                        self.configMenuOptions.append(item)
                    else:
                        self.Logging(
                            "--->ERROR: Please check that the Auth CSV is set up correctly!"
                        )
                        defaultConfigVal = self.configMenu.Append(
                            wx.ID_NONE,
                            "No Loaded Configurations",
                            "No Loaded Configurations",
                        )
                        self.configMenuOptions.append(defaultConfigVal)
                        self.Bind(wx.EVT_MENU, self.OnOpen, defaultConfigVal)
                        return
            self.Logging(
                "--->**** Please Select an Endpoint From the Configuartion Menu (defaulting to first Config)"
            )
            defaultConfigItem = self.configMenuOptions[0]
            defaultConfigItem.Check(True)
            self.loadConfiguartion(defaultConfigItem)
        else:
            self.Logging(
                "--->****"
                + Globals.CONFIGFILE
                + " not found - PLEASE Quit and create configuration file"
            )
            defaultConfigVal = self.configMenu.Append(
                wx.ID_NONE, "No Loaded Configurations", "No Loaded Configurations"
            )
            self.configMenuOptions.append(defaultConfigVal)
            self.Bind(wx.EVT_MENU, self.OnOpen, defaultConfigVal)

    def LoadTagsAndAliases(self):
        return

    def setCursorDefault(self):
        myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
        self.SetCursor(myCursor)

    def setCursorBusy(self):
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)

    def loadConfiguartion(self, event, *args, **kwargs):
        """Populate Frame Layout With Device Configuration"""
        menuItem = self.configMenu.FindItemById(event.Id)
        try:
            self.Logging(
                "--->Attempting to load configuration: %s."
                % menuItem.GetItemLabelText()
            )
            selectedConfig = self.configChoice[menuItem.GetItemLabelText()]

            for item in menuItem.Menu.MenuItems:
                if item != menuItem:
                    item.Check(False)

            self.configList.Clear()
            self.configList.AppendText("API Host = " + selectedConfig["apiHost"] + "\n")
            self.configList.AppendText("API key = " + selectedConfig["apiKey"] + "\n")
            self.configList.AppendText(
                "API Prefix = " + selectedConfig["apiPrefix"] + "\n"
            )
            self.configList.AppendText("Enterprise = " + selectedConfig["enterprise"])

            if "https" in str(selectedConfig["apiHost"]):
                Globals.configuration.host = selectedConfig["apiHost"]
                Globals.configuration.api_key["Authorization"] = selectedConfig[
                    "apiKey"
                ]
                Globals.configuration.api_key_prefix["Authorization"] = selectedConfig[
                    "apiPrefix"
                ]
                Globals.enterprise_id = selectedConfig["enterprise"]

                self.PopulateGroups()
                self.PopulateApps()

            self.groupChoice.Enable(True)
            self.actionChoice.Enable(True)
        except Exception as e:
            self.Logging(
                "--->****An Error has occured while loading the configuration, please try again."
            )
            print(e)
            menuItem.Check(False)
        self.setCursorDefault()

    def PopulateGroups(self):
        """create an instance of the API class"""
        self.Logging("--->Attemptting to populate groups...")
        self.setCursorBusy()
        api_instance = esperclient.DeviceGroupApi(
            esperclient.ApiClient(Globals.configuration)
        )
        self.groupChoice.Clear()
        try:
            api_response = api_instance.get_all_groups(
                Globals.enterprise_id, limit=Globals.limit, offset=Globals.offset
            )
            if len(api_response.results):
                for group in api_response.results:
                    self.groupChoice.Append(group.name, group.id)
                self.groupChoice.SetValue("<Select Group>")
                self.Bind(wx.EVT_COMBOBOX, self.PopulateDevices, self.groupChoice)
            self.runBtn.Enable(True)
            self.run.Enable(True)
            self.command.Enable(True)
            self.groupChoice.SetSelection(0)
        except ApiException as e:
            self.Logging(
                "Exception when calling DeviceGroupApi->get_all_groups: %s\n" % e
            )
            print("Exception when calling DeviceGroupApi->get_all_groups: %s\n" % e)
        self.setCursorDefault()

    def PopulateDevices(self, event=None):
        self.Logging(
            "--->Attemptting to populate devices of selected group (%s)..."
            % event.String
        )
        self.setCursorBusy()
        self.deviceChoice.Clear()
        try:
            api_instance = esperclient.DeviceApi(
                esperclient.ApiClient(Globals.configuration)
            )
            api_response = api_instance.get_all_devices(
                Globals.enterprise_id,
                group=event.ClientData,
                limit=Globals.limit,
                offset=Globals.offset,
            )

            if len(api_response.results):
                self.deviceChoice.Enable(True)
                self.deviceChoice.Append("", "")
                for device in api_response.results:
                    name = "%s %s %s %s" % (
                        device.hardware_info["manufacturer"],
                        device.hardware_info["model"],
                        device.device_name,
                        device.software_info["androidVersion"],
                    )
                    self.deviceChoice.Append(name, device.id)
            else:
                self.deviceChoice.Append("No Devices Found", "")
                self.groupChoice.SetValue("No Devices Found")
                self.deviceChoice.Enable(False)
                self.Logging("No Devices found in group")
        except ApiException as e:
            self.Logging("Exception when calling DeviceApi->get_all_devices: %s\n" % e)
            print("Exception when calling DeviceApi->get_all_devices: %s\n" % e)
        self.setCursorDefault()

    def PopulateApps(self):
        """create an instance of the API class"""
        self.Logging("--->Attemptting to populate apps...")
        self.setCursorBusy()
        api_instance = esperclient.ApplicationApi(
            esperclient.ApiClient(Globals.configuration)
        )
        limit = 5000  # int | Number of results to return per page. (optional) (default to 20)
        offset = 0  # int | The initial index from which to return the results. (optional) (default to 0)
        self.appChoice.Clear()
        try:
            api_response = api_instance.get_all_applications(
                Globals.enterprise_id,
                limit=Globals.limit,
                offset=Globals.offset,
                is_hidden=False,
            )
            if len(api_response.results):
                for app in api_response.results:
                    self.appChoice.Append(app.application_name, app.package_name)
                self.appChoice.SetValue("<Select App>")
        except ApiException as e:
            self.Logging(
                "Exception when calling ApplicationApi->get_all_applications: %s\n" % e
            )
            print(
                "Exception when calling ApplicationApi->get_all_applications: %s\n" % e
            )
        self.setCursorDefault()

    def createLogString(self, deviceInfo, action):
        """Prepares Raw Data For UI"""
        logString = ""
        tagString = str(deviceInfo["Tags"])
        tagString = tagString.replace("'", "")
        tagString = tagString.replace("[", "")
        tagString = tagString.replace("]", "")
        tagString = tagString.replace(", ", ",")
        appString = str(deviceInfo["Apps"]).replace(",", "")
        if action == Globals.SHOW_ALL_AND_GENERATE_REPORT:
            logString = (
                # "{:>4}".format(str(deviceInfo["num"]))
                # + ","
                deviceInfo["EsperName"]
                + ","
                + deviceInfo["Alias"]
                + ","
                + deviceInfo["Status"]
                + ","
                + deviceInfo["Mode"]
                + ","
                + deviceInfo["Serial"]
                + ","
                + '"'
                + str(tagString)
                + '"'
                + ","
                + str(appString)
                + ","
                + str(deviceInfo["KioskApp"])
            )
            return logString
        logString = (
            # "{:>4}".format(str(deviceInfo["num"]))
            # + ","
            "{:13.13}".format(deviceInfo["EsperName"])
            + ","
            + "{:16.16}".format(str(deviceInfo["Alias"]))
            + ","
            + "{:10.10}".format(deviceInfo["Status"])
            + ","
            + "{:8.8}".format(deviceInfo["Mode"])
        )
        return logString

    def onRun(self, event=None):
        self.setCursorBusy()

        groupSelection = self.groupChoice.GetSelection()
        deviceSelection = self.deviceChoice.GetSelection()
        gridSelection = self.gridActions.GetSelection()
        appSelection = self.appChoice.GetSelection()
        actionSelection = self.actionChoice.GetSelection()

        groupLabel = (
            self.groupChoice.Items[groupSelection]
            if len(self.groupChoice.Items) > 0
            and self.groupChoice.Items[groupSelection]
            else ""
        )
        deviceLabel = (
            self.deviceChoice.Items[deviceSelection]
            if len(self.deviceChoice.Items) > 0
            and self.deviceChoice.Items[deviceSelection]
            else ""
        )
        appLabel = (
            self.appChoice.Items[appSelection]
            if len(self.appChoice.Items) > 0 and self.appChoice.Items[appSelection]
            else ""
        )
        gridLabel = (
            self.gridActions.Items[gridSelection]
            if len(self.gridActions.Items) > 0 and self.gridActions.Items[gridSelection]
            else ""
        )
        actionLabel = (
            self.actionChoice.Items[actionSelection]
            if len(self.actionChoice.Items) > 0
            and self.actionChoice.Items[actionSelection]
            else ""
        )

        if (
            groupSelection >= 0
            and deviceSelection <= 0
            and gridSelection < 0
            and actionSelection >= 0
        ):
            # run action on group
            if actionSelection == Globals.SET_KIOSK and appSelection < 0:
                wx.MessageBox(
                    "Please select an Application", style=wx.OK | wx.ICON_ERROR
                )
                return
            self.Logging(
                'Attempting to run action, "%s", on group, %s.'
                % (actionLabel, groupLabel)
            )
            self.runActionOnGroup(
                groupLabel=groupLabel, group=groupSelection, action=actionSelection
            )
        elif deviceSelection > 0 and gridSelection < 0 and actionSelection >= 0:
            # run action on device
            if actionSelection == Globals.SET_KIOSK and appSelection < 0:
                wx.MessageBox(
                    "Please select an Application", style=wx.OK | wx.ICON_ERROR
                )
                return
            self.Logging(
                'Attempting to run action, "%s", on device, %s.'
                % (actionLabel, deviceLabel)
            )
            self.runActionOnDevice(
                deviceLabel=deviceLabel, device=deviceSelection, action=actionSelection
            )
        elif gridSelection >= 0:
            # run grid action
            if self.grid_1.GetNumberRows() > 0:
                runAction = True
                if Globals.SHOW_GRID_DIALOG:
                    result = CheckboxMessageBox(
                        "Confirmation",
                        "The %s will attempt to process the action on all devices in the Device Info grid. \n\nContinue?"
                        % Globals.TITLE,
                    ).ShowModal()
                    if result != wx.ID_OK:
                        runAction = False
                if runAction:
                    self.Logging('Attempting to run grid action, "%s".' % gridLabel)
                    iterateThroughGridRows(self, gridSelection)
            else:
                wx.MessageBox(
                    "Make sure the grid has data to perform an action on",
                    style=wx.OK | wx.ICON_ERROR,
                )
        else:
            wx.MessageBox(
                "Please select an action to perform on a group or device!",
                style=wx.OK | wx.ICON_ERROR,
            )

        self.setCursorDefault()

    def runActionOnGroup(self, event=None, groupLabel=None, group=None, action=None):
        TakeAction(
            self,
            group,
            action,
            groupLabel,
        )

    def runActionOnDevice(self, event=None, deviceLabel=None, device=None, action=None):
        TakeAction(
            self,
            device,
            action,
            deviceLabel,
            isDevice=True,
        )

    def buttonYieldEvent(self):
        """Allows Button Press Action to Yield For Result"""
        if Globals.frame.WINDOWS:
            wx.Yield()
        else:
            Globals.app.SafeYield(None, True)

    def fillDeviceGridHeaders(self):
        num = 0
        headerLabels = Globals.CSV_TAG_ATTR_NAME.keys()
        for head in headerLabels:
            if head:
                if self.grid_1.GetNumberCols() < len(headerLabels):
                    self.grid_1.AppendCols(1)
                self.grid_1.SetColLabelValue(num, head)
                num += 1
        self.grid_1.AutoSizeColumns()

    def fillNetworkGridHeaders(self):
        num = 0
        headerLabels = Globals.CSV_NETWORK_ATTR_NAME
        for head in headerLabels:
            if head:
                if self.grid_2.GetNumberCols() < len(headerLabels):
                    self.grid_2.AppendCols(1)
                self.grid_2.SetColLabelValue(num, head)
                num += 1
        self.grid_2.AutoSizeColumns()

    def emptyDeviceGrid(self):
        self.grid_1.ClearGrid()
        if self.grid_1.GetNumberRows() > 0:
            self.grid_1.DeleteRows(0, self.grid_1.GetNumberRows())
        self.grid_1.SetScrollLineX(15)
        self.grid_1.SetScrollLineY(15)
        self.fillDeviceGridHeaders()

    def emptyNetworkGrid(self):
        self.grid_2.ClearGrid()
        if self.grid_2.GetNumberRows() > 0:
            self.grid_2.DeleteRows(0, self.grid_2.GetNumberRows())
        self.grid_2.SetScrollLineX(15)
        self.grid_2.SetScrollLineY(15)
        self.fillNetworkGridHeaders()

    def addDeviceToDeviceGrid(self, device_info):
        num = 0
        self.grid_1.AppendRows(1)
        device = {}

        for attribute in Globals.CSV_TAG_ATTR_NAME:
            value = (
                device_info[Globals.CSV_TAG_ATTR_NAME[attribute]]
                if Globals.CSV_TAG_ATTR_NAME[attribute] in device_info
                else ""
            )
            device[Globals.CSV_TAG_ATTR_NAME[attribute]] = str(value)
            self.grid_1.SetCellValue(self.grid_1.GetNumberRows() - 1, num, str(value))
            isEditable = True
            if attribute in Globals.CSV_EDITABLE_COL:
                isEditable = False
            self.grid_1.SetReadOnly(self.grid_1.GetNumberRows() - 1, num, isEditable)
            num += 1

        self.grid_1.AutoSizeColumns()
        if device not in self.grid_1_contents:
            self.grid_1_contents.append(device)

    def addDeviceToNetworkGrid(self, device, deviceInfo):
        networkInfo = {}
        networkInfo["Security Patch"] = getSecurityPatch(device)
        wifiStatus = getWifiStatus(deviceInfo).split(",")
        networkInfo["[WIFI ACCESS POINTS]"] = wifiStatus[0]
        networkInfo["[Current WIFI Connection]"] = wifiStatus[1]
        cellStatus = getCellularStatus(deviceInfo).split(",")
        networkInfo["[Cellular Access Point]"] = cellStatus[0]
        networkInfo["Active Connection"] = cellStatus[1]
        networkInfo["Device Name"] = getDeviceName(device)
        networkInfo["Bluetooth State"] = str(deviceInfo["bluetoothState"])
        self.addToNetworkGrid(networkInfo)

    def addToNetworkGrid(self, networkInfo):
        num = 0
        self.grid_2.AppendRows(1)

        for attribute in Globals.CSV_NETWORK_ATTR_NAME:
            value = networkInfo[attribute] if attribute in networkInfo else ""
            self.grid_2.SetCellValue(self.grid_2.GetNumberRows() - 1, num, str(value))
            isEditable = True
            if attribute in Globals.CSV_EDITABLE_COL:
                isEditable = False
            self.grid_2.SetReadOnly(self.grid_2.GetNumberRows() - 1, num, isEditable)
            num += 1

        self.grid_2.AutoSizeColumns()
        if networkInfo not in self.grid_2_contents:
            self.grid_2_contents.append(networkInfo)

    def toggleColVisibilityInGridOne(self, event):
        index = (
            self.viewMenuOptions[event.Id] if event.Id in self.viewMenuOptions else None
        )
        isShown = self.grid_1.IsColShown(index)
        if isShown:
            self.grid_1.HideCol(index)
        else:
            self.grid_1.ShowCol(index)

    def toggleColVisibilityInGridTwo(self, event):
        index = (
            self.viewMenuOptions[event.Id] if event.Id in self.viewMenuOptions else None
        )
        isShown = self.grid_2.IsColShown(index)
        if isShown:
            self.grid_2.HideCol(index)
        else:
            self.grid_2.ShowCol(index)

    def loadConfigPrompt(self):
        wx.MessageBox("Please load a configuration first!", style=wx.OK | wx.ICON_ERROR)

    def getDeviceTagsFromGrid(self):
        tagList = {}
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, 0)
                indx = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Tags")
                tags = self.grid_1.GetCellValue(rowNum, indx)
                tags = tags.split(",")
                properTagList = []
                for tag in tags:
                    properTagList.append(
                        tag.strip().replace("'", "").replace("[", "").replace("]", "")
                    )
                tagList[esperName] = properTagList
        return tagList

    def getDeviceAliasFromGrid(self):
        aliasList = {}
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, 0)
                indx = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Alias")
                alias = self.grid_1.GetCellValue(rowNum, indx)
                aliasList[esperName] = alias
        return aliasList

    def onGridActionSelection(self, event):
        if event and event.String:
            self.actionChoice.SetSelection(-1)
            self.appChoice.Enable(False)
            self.appChoice.SetSelection(-1)

    def onActionSelection(self, event):
        if event and event.String:
            self.gridActions.SetSelection(-1)

            if event and event.String == Globals.GENERAL_ACTIONS[Globals.SET_KIOSK]:
                self.appChoice.Enable(True)
            else:
                self.appChoice.SetSelection(-1)
                self.appChoice.Enable(False)

    def onCellChange(self, event=None):
        self.grid_1.AutoSizeColumns()

    def updateTagCell(self, name, tags):
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, 0)
                if name == esperName:
                    indx = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Tags")
                    self.grid_1.SetCellValue(rowNum, indx, str(tags))

    def showConsole(self, event):
        if not self.consoleWin:
            self.consoleWin = Console()
            self.clearConsole.Enable(True)
            self.Bind(wx.EVT_MENU, self.onClear, self.clearConsole)
        else:
            self.consoleWin.Destroy()
            self.consoleWin = None
            self.clearConsole.Enable(False)

    def onClear(self, event=None):
        if self.consoleWin:
            self.consoleWin.onClear()

    def onHelp(self, event=None):
        return

    def onCommand(self, event):
        self.setCursorBusy()
        try:
            groupSelection = self.groupChoice.GetSelection()
            if groupSelection >= 0:
                with CommandDialog("Enter JSON Command") as cmdDialog:
                    result = cmdDialog.ShowModal()
                    if result == wx.ID_OK:
                        cmd = json.loads(cmdDialog.GetValue())
                        if cmd:
                            result = ApplyDeviceConfig(self, cmd)
                            if hasattr(result, "state"):
                                wx.MessageBox(result.state, style=wx.OK)
            else:
                wx.MessageBox(
                    "Please select an group and or devices", style=wx.OK | wx.ICON_ERROR
                )
        except Exception as e:
            print(e)
            wx.MessageBox("EXCEPTION: \n%s" % str(e), style=wx.OK | wx.ICON_ERROR)
        self.setCursorDefault()

    def confirmCommand(self, cmd):
        deviceSelection = self.deviceChoice.GetSelection()
        groupSelection = self.groupChoice.GetSelection()
        groupToUse = self.groupChoice.GetClientData(groupSelection)
        deviceToUse = (
            self.deviceChoice.GetClientData(deviceSelection)
            if deviceSelection > 0
            else ""
        )
        groupLabel = (
            self.groupChoice.Items[groupSelection]
            if len(self.groupChoice.Items) > 0
            and self.groupChoice.Items[groupSelection]
            else ""
        )
        deviceLabel = (
            self.deviceChoice.Items[deviceSelection]
            if len(self.deviceChoice.Items) > 0
            and self.deviceChoice.Items[deviceSelection]
            else ""
        )
        modal = None
        isGroup = False
        cmd_format = (
            json.dumps(str(cmd).replace("\n", "").replace(" ", ""), indent=2)
            .replace(",", ",\n")
            .replace(":{", ":{\n")
        )
        if deviceSelection > 0 and deviceLabel:
            modal = wx.MessageBox(
                "About to try applying the command: \n\n%s\n\n on the device, %s, continue?"
                % (cmd_format, deviceLabel),
                style=wx.YES | wx.NO | wx.YES_DEFAULT,
            )
        elif groupSelection >= 0 and groupLabel:
            modal = wx.MessageBox(
                "About to try applying the command: \n%s\n\n on the group, %s, continue?"
                % (cmd_format, groupLabel),
                style=wx.YES | wx.NO | wx.YES_DEFAULT,
            )
            isGroup = True

        if modal == wx.YES:
            return True, isGroup
        else:
            return False, isGroup

    def setTempStatus(self, status):
        self.restoreStatus()
        self.statusBar.PushStatusText(status)

    def restoreStatus(self):
        text = self.statusBar.GetStatusText()
        if text and text != "\x00":
            self.statusBar.PopStatusText()

    def onDeviceGridSort(self, event):
        col = event.Col
        keyName = list(Globals.CSV_TAG_ATTR_NAME.values())[col]

        curSortCol = self.grid_1.GetSortingColumn()
        descending = False
        if curSortCol == col:
            descending = True
        self.grid_1.SetSortingColumn(col, bool(not descending))
        self.grid_1_contents = sorted(
            self.grid_1_contents, key=lambda i: i[keyName], reverse=descending
        )
        self.Logging("Sorting Device Grid on Column: %s" % keyName)
        self.emptyDeviceGrid()
        for device in self.grid_1_contents:
            self.addDeviceToDeviceGrid(device)

    def onNetworkGridSort(self, event):
        col = event.Col
        keyName = Globals.CSV_NETWORK_ATTR_NAME[col]

        curSortCol = self.grid_2.GetSortingColumn()
        descending = False
        if curSortCol == col:
            descending = True
        self.grid_2.SetSortingColumn(col, bool(not descending))
        self.grid_2_contents = sorted(
            self.grid_2_contents, key=lambda i: i[keyName], reverse=descending
        )
        self.Logging("Sorting Network Grid on Column: %s" % keyName)
        self.emptyNetworkGrid()
        for info in self.grid_2_contents:
            self.addToNetworkGrid(info)

    def toogleViewMenuItem(self, event):
        """
        Disable native headers ability to hide columns when clicking an entry from the context menu
        """
        return

    def onUpdate(self, event):
        evtValue = event.GetValue()
        action = evtValue[0]
        deviceList = evtValue[1]
        for entry in deviceList.values():
            device = entry[0]
            deviceInfo = entry[1]
            if action == Globals.SHOW_ALL_AND_GENERATE_REPORT:
                self.addDeviceToDeviceGrid(deviceInfo)
                self.addDeviceToNetworkGrid(device, deviceInfo)
            elif action == Globals.SET_KIOSK:
                setKiosk(self, device, deviceInfo)
            elif action == Globals.SET_MULTI:
                setMulti(self, device, deviceInfo)
