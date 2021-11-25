#!/usr/bin/env python

import platform
import time
from GUI.Dialogs.ColumnVisibility import ColumnVisibility
from Utility.Resource import acquireLocks, postEventToFrame, releaseLocks, resourcePath, scale_bitmap
import Common.Globals as Globals
import re
import threading
import wx
import wx.grid as gridlib
import Utility.wxThread as wxThread
import Utility.EventUtility as eventUtil

from Common.decorator import api_tool_decorator
from Common.enum import Color
from Utility.deviceInfo import constructNetworkInfo
from GUI.Dialogs.ColumnVisibilityDialog import ColumnVisibilityDialog


class GridPanel(wx.Panel):
    def __init__(self, parentFrame, *args, **kw):
        super().__init__(*args, **kw)

        self.userEdited = []
        self.grid_1_contents = []
        self.grid_2_contents = []
        self.grid_3_contents = []

        self.deviceDescending = False
        self.networkDescending = False

        self.parentFrame = parentFrame
        self.disableProperties = False
        self.currentlySelectedCell = (-1, -1)

        self.grid1HeaderLabels = list(Globals.CSV_TAG_ATTR_NAME.keys())
        self.grid2HeaderLabels = list(Globals.CSV_NETWORK_ATTR_NAME.keys())
        self.grid3HeaderLabels = Globals.CSV_APP_ATTR_NAME
        self.grid1ColVisibility = {}
        self.grid2ColVisibility = {}
        self.grid3ColVisibility = {}

        grid_sizer_2 = wx.FlexGridSizer(2, 1, 0, 0)

        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_2.Add(sizer_3, 1, wx.ALIGN_RIGHT | wx.BOTTOM | wx.EXPAND, 5)

        prev_icon = scale_bitmap(resourcePath("Images/prev.png"), 20, 20)
        self.button_1 = wx.BitmapButton(
            self,
            wx.ID_BACKWARD,
            prev_icon,
        )
        self.button_1.SetToolTip("Load previous page of devices.")
        sizer_3.Add(self.button_1, 0, wx.RIGHT, 5)

        next_icon = scale_bitmap(resourcePath("Images/next.png"), 20, 20)
        self.button_2 = wx.BitmapButton(
            self,
            wx.ID_FORWARD,
            next_icon,
        )
        self.button_2.SetToolTip("Load next page of devices.")
        sizer_3.Add(self.button_2, 0, wx.LEFT, 5)

        self.notebook_2 = wx.Notebook(self, wx.ID_ANY)
        grid_sizer_2.Add(self.notebook_2, 1, wx.EXPAND, 0)

        self.notebook_2.SetFont(
            wx.Font(
                Globals.FONT_SIZE,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "GridNotebook",
            )
        )

        self.panel_14 = wx.Panel(self.notebook_2, wx.ID_ANY)
        self.notebook_2.AddPage(self.panel_14, "Device Information")

        sizer_6 = wx.BoxSizer(wx.VERTICAL)

        self.grid_1 = wx.grid.Grid(self.panel_14, wx.ID_ANY, size=(1, 1))
        sizer_6.Add(self.grid_1, 1, wx.EXPAND, 0)

        self.panel_15 = wx.Panel(self.notebook_2, wx.ID_ANY)
        self.notebook_2.AddPage(self.panel_15, "Network Information")

        sizer_7 = wx.BoxSizer(wx.VERTICAL)

        self.grid_2 = wx.grid.Grid(self.panel_15, wx.ID_ANY, size=(1, 1))
        sizer_7.Add(self.grid_2, 1, wx.EXPAND, 0)


        self.panel_16 = wx.Panel(self.notebook_2, wx.ID_ANY)
        self.notebook_2.AddPage(self.panel_16, "Application Information")

        sizer_8 = wx.BoxSizer(wx.VERTICAL)

        self.grid_3 = wx.grid.Grid(self.panel_16, wx.ID_ANY, size=(1, 1))
        sizer_8.Add(self.grid_3, 1, wx.EXPAND, 0)

        self.panel_16.SetSizer(sizer_8)

        self.panel_15.SetSizer(sizer_7)

        self.panel_14.SetSizer(sizer_6)

        grid_sizer_2.AddGrowableRow(1)
        grid_sizer_2.AddGrowableCol(0)
        self.SetSizer(grid_sizer_2)

        self.Layout()

        self.button_1.Bind(wx.EVT_BUTTON, self.decrementOffset)
        self.button_2.Bind(wx.EVT_BUTTON, self.incrementOffset)
        self.button_1.Enable(False)
        self.button_2.Enable(False)

        self.Layout()

        self.__set_properties()

    @api_tool_decorator()
    def __set_properties(self):
        self.grid_1.Bind(gridlib.EVT_GRID_CELL_CHANGED, self.onCellChange)

        self.grid_1.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.onDeviceGridSort)
        self.grid_2.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.onNetworkGridSort)
        self.grid_3.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.onAppGridSort)

        self.grid_1.Bind(gridlib.EVT_GRID_LABEL_RIGHT_CLICK, self.toogleViewMenuItem)
        self.grid_2.Bind(gridlib.EVT_GRID_LABEL_RIGHT_CLICK, self.toogleViewMenuItem)
        self.grid_3.Bind(gridlib.EVT_GRID_LABEL_RIGHT_CLICK, self.toogleViewMenuItem)

        self.grid_1.GetGridWindow().Bind(wx.EVT_MOTION, self.onGridMotion)
        self.grid_1.Bind(wx.EVT_SCROLLWIN, self.onGrid1Scroll)
        self.grid_2.Bind(wx.EVT_SCROLLWIN, self.onGrid2Scroll)
        self.grid_3.Bind(wx.EVT_SCROLLWIN, self.onGrid3Scroll)
        self.grid_1.Bind(gridlib.EVT_GRID_SELECT_CELL, self.onSingleSelect)
        self.grid_2.Bind(gridlib.EVT_GRID_SELECT_CELL, self.onSingleSelect)
        self.grid_1.GetGridWindow().Bind(wx.EVT_KEY_DOWN, self.onKey)
        self.grid_2.GetGridWindow().Bind(wx.EVT_KEY_DOWN, self.onKey)

        self.grid_3.CreateGrid(0, len(Globals.CSV_APP_ATTR_NAME))
        self.grid_2.CreateGrid(0, len(Globals.CSV_NETWORK_ATTR_NAME.keys()))
        self.grid_1.CreateGrid(0, len(Globals.CSV_TAG_ATTR_NAME.keys()))
        self.setupGrid(self.grid_1)
        self.setupGrid(self.grid_2)
        self.setupGrid(self.grid_3)
        self.enableGridProperties()
        self.fillDeviceGridHeaders()
        self.fillNetworkGridHeaders()
        self.fillAppGridHeaders()
    
    def setupGrid(self, grid):
        grid.UseNativeColHeader()
        grid.DisableDragRowSize()
        grid.EnableDragColMove(True)
        grid.SetLabelFont(
            wx.Font(
                Globals.FONT_SIZE,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "NormalBold",
            )
        )
        grid.SetDefaultCellFont(
            wx.Font(
                Globals.FONT_SIZE,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "Normal",
            )
        )


    @api_tool_decorator()
    def fillDeviceGridHeaders(self):
        """ Populate Device Grid Headers """
        num = 0
        try:
            for head in self.grid1HeaderLabels:
                if head:
                    if self.grid_1.GetNumberCols() < len(self.grid1HeaderLabels):
                        self.grid_1.AppendCols(1)
                    self.grid_1.SetColLabelValue(num, head)
                    num += 1
        except:
            pass
        self.grid_1.AutoSizeColumns()

    @api_tool_decorator()
    def fillNetworkGridHeaders(self):
        """ Populate Network Grid Headers """
        num = 0
        try:
            for head in self.grid2HeaderLabels:
                if head:
                    if self.grid_2.GetNumberCols() < len(self.grid2HeaderLabels):
                        self.grid_2.AppendCols(1)
                    self.grid_2.SetColLabelValue(num, head)
                    num += 1
        except:
            pass
        self.grid_2.AutoSizeColumns()

    @api_tool_decorator()
    def fillAppGridHeaders(self):
        """ Populate Device Grid Headers """
        num = 0
        try:
            for head in self.grid3HeaderLabels:
                if head:
                    if self.grid_3.GetNumberCols() < len(self.grid3HeaderLabels):
                        self.grid_3.AppendCols(1)
                    self.grid_3.SetColLabelValue(num, head)
                    num += 1
        except:
            pass
        self.grid_3.AutoSizeColumns()

    @api_tool_decorator(locks=[Globals.grid1_lock])
    def emptyDeviceGrid(self, emptyContents=True):
        """ Empty Device Grid """
        acquireLocks([Globals.grid1_lock])
        if emptyContents:
            self.grid_1_contents = []
        if self.grid_1.GetNumberRows() > 0:
            self.grid_1.DeleteRows(0, self.grid_1.GetNumberRows())
        self.grid_1.SetScrollLineX(15)
        self.grid_1.SetScrollLineY(15)
        self.fillDeviceGridHeaders()
        releaseLocks([Globals.grid1_lock])

    @api_tool_decorator(locks=[Globals.grid2_lock])
    def emptyNetworkGrid(self, emptyContents=True):
        """ Empty Network Grid """
        acquireLocks([Globals.grid2_lock])
        if emptyContents:
            self.grid_2_contents = []
        if self.grid_2.GetNumberRows() > 0:
            self.grid_2.DeleteRows(0, self.grid_2.GetNumberRows())
        self.grid_2.SetScrollLineX(15)
        self.grid_2.SetScrollLineY(15)
        self.fillNetworkGridHeaders()
        releaseLocks([Globals.grid2_lock])

    @api_tool_decorator(locks=[Globals.grid3_lock])
    def emptyAppGrid(self, emptyContents=True):
        acquireLocks([Globals.grid3_lock])
        if emptyContents:
            self.grid_3_contents = []
        if self.grid_3.GetNumberRows() > 0:
            self.grid_3.DeleteRows(0, self.grid_3.GetNumberRows())
        self.grid_3.SetScrollLineX(15)
        self.grid_3.SetScrollLineY(15)
        self.fillAppGridHeaders()
        releaseLocks([Globals.grid3_lock])

    @api_tool_decorator(locks=[Globals.grid1_lock, Globals.grid2_lock, Globals.grid3_lock])
    def autoSizeGridsColumns(self, event=None):
        acquireLocks([Globals.grid1_lock, Globals.grid2_lock, Globals.grid3_lock])
        self.grid_1.AutoSizeColumns()
        self.grid_2.AutoSizeColumns()
        self.grid_3.AutoSizeColumns()
        self.grid_1.ForceRefresh()
        self.grid_2.ForceRefresh()
        self.grid_3.ForceRefresh()
        releaseLocks([Globals.grid1_lock, Globals.grid2_lock, Globals.grid3_lock])

    @api_tool_decorator(locks=[Globals.grid1_lock])
    def onCellChange(self, event):
        """ Try to Auto size Columns on change """
        acquireLocks([Globals.grid1_lock])
        self.userEdited.append((event.Row, event.Col))
        editor = self.grid_1.GetCellEditor(event.Row, event.Col)
        if not editor.IsCreated():
            self.grid_1.AutoSizeColumns()
        self.onCellEdit(event)
        releaseLocks([Globals.grid1_lock])

    @api_tool_decorator()
    def onCellEdit(self, event):
        indx1 = self.grid1HeaderLabels.index("Tags")
        indx2 = self.grid1HeaderLabels.index("Alias")
        indx3 = self.grid1HeaderLabels.index("Group")
        x, y = self.grid_1.GetGridCursorCoords()
        esperName = self.grid_1.GetCellValue(x, 0)
        deviceListing = list(
            filter(
                lambda x: (x[Globals.CSV_TAG_ATTR_NAME["Esper Name"]] == esperName),
                self.grid_1_contents,
            )
        )
        if deviceListing:
            self.onCellEditHelper(
                deviceListing, event, indx1, "OriginalTags", "Tags", x, y
            )
            self.onCellEditHelper(
                deviceListing, event, indx2, "OriginalAlias", "Alias", x, y
            )
            self.onCellEditHelper(
                deviceListing, event, indx3, "OriginalGroup", "Group", x, y
            )
        event.Skip()

    def onCellEditHelper(
        self, deviceListing, event, indx, orginalFieldName, AlteredfieldName, x, y
    ):
        if (
            y == indx
            and not orginalFieldName in deviceListing[0]
            and deviceListing[0][Globals.CSV_TAG_ATTR_NAME[AlteredfieldName]]
            != self.grid_1.GetCellValue(x, y)
        ) or (
            y == indx
            and orginalFieldName in deviceListing[0]
            and deviceListing[0][orginalFieldName] != self.grid_1.GetCellValue(x, y)
        ):
            self.grid_1.SetCellBackgroundColour(x, y, Color.lightBlue.value)
            if y == indx:
                deviceListing[0][
                    Globals.CSV_TAG_ATTR_NAME[AlteredfieldName]
                ] = self.grid_1.GetCellValue(x, y)
            if y == indx and not orginalFieldName in deviceListing[0]:
                deviceListing[0][orginalFieldName] = event.GetString()
        else:
            if (
                y == indx
                and orginalFieldName in deviceListing[0]
                and deviceListing[0][orginalFieldName] == self.grid_1.GetCellValue(x, y)
            ):
                deviceListing[0][
                    Globals.CSV_TAG_ATTR_NAME[AlteredfieldName]
                ] = self.grid_1.GetCellValue(x, y)
            if y == indx:
                self.grid_1.SetCellBackgroundColour(x, y, Color.white.value)

    @api_tool_decorator()
    def onDeviceGridSort(self, event):
        """ Sort Device Grid """
        if (
            self.parentFrame.isRunning
            or (
                self.parentFrame.gauge.GetValue() != self.parentFrame.gauge.GetRange()
                and self.parentFrame.gauge.GetValue() != 0
            )
            or self.parentFrame.CSVUploaded
            or self.disableProperties
        ):
            return
        if hasattr(event, "Col"):
            col = event.Col
        else:
            col = event
        keyName = list(Globals.CSV_TAG_ATTR_NAME.values())[col]

        curSortCol = self.grid_1.GetSortingColumn()
        if curSortCol == col and hasattr(event, "Col"):
            self.deviceDescending = not self.deviceDescending
        self.grid_1.SetSortingColumn(col, bool(not self.deviceDescending))

        if keyName == "androidVersion":
            self.grid_1_contents = sorted(
                self.grid_1_contents,
                key=lambda i: list(map(int, i[keyName].split("."))),
                reverse=self.deviceDescending,
            )
        else:
            if self.grid_1_contents and all(
                s[keyName].isdigit() for s in self.grid_1_contents
            ):
                self.grid_1_contents = sorted(
                    self.grid_1_contents,
                    key=lambda i: i[keyName] and int(i[keyName]),
                    reverse=self.deviceDescending,
                )
            else:
                self.grid_1_contents = sorted(
                    self.grid_1_contents,
                    key=lambda i: i[keyName].lower(),
                    reverse=self.deviceDescending,
                )
        self.parentFrame.Logging(
            "---> Sorting Device Grid on Column: %s Order: %s"
            % (keyName, "Descending" if self.deviceDescending else "Ascending")
        )
        self.parentFrame.setGaugeValue(0)
        self.emptyDeviceGrid(emptyContents=False)
        self.grid_1.Freeze()
        if platform.system() == "Windows":
            thread = wxThread.GUIThread(
                self.parentFrame, self.repopulateGrid, (self.grid_1_contents, col)
            )
            thread.start()
        else:
            self.repopulateGrid(self.grid_1_contents, col)

    @api_tool_decorator()
    def onNetworkGridSort(self, event):
        """ Sort the network grid """
        if (
            self.parentFrame.isRunning
            or (
                self.parentFrame.gauge.GetValue() != self.parentFrame.gauge.GetRange()
                and self.parentFrame.gauge.GetValue() != 0
            )
            or self.parentFrame.CSVUploaded
            or self.disableProperties
        ):
            return
        if hasattr(event, "Col"):
            col = event.Col
        else:
            col = event
        keyName = list(Globals.CSV_NETWORK_ATTR_NAME.keys())[col]

        curSortCol = self.grid_2.GetSortingColumn()
        if curSortCol == col and hasattr(event, "Col"):
            self.networkDescending = not self.networkDescending
        self.grid_2.SetSortingColumn(col, bool(not self.networkDescending))
        if self.grid_2_contents and all(
            s[keyName].isdigit() for s in self.grid_2_contents
        ):
            self.grid_2_contents = sorted(
                self.grid_2_contents,
                key=lambda i: i[keyName] and int(i[keyName]),
                reverse=self.networkDescending,
            )
        else:
            self.grid_2_contents = sorted(
                self.grid_2_contents,
                key=lambda i: i[keyName].lower(),
                reverse=self.networkDescending,
            )
        self.parentFrame.Logging(
            "---> Sorting Network Grid on Column: %s Order: %s"
            % (keyName, "Descending" if self.networkDescending else "Ascending")
        )
        self.parentFrame.setGaugeValue(0)
        self.emptyNetworkGrid(emptyContents=False)
        self.grid_2.Freeze()
        if platform.system() == "Windows":
            thread = wxThread.GUIThread(
                self.parentFrame,
                self.repopulateGrid,
                (self.grid_2_contents, col, "Network"),
            )
            thread.start()
        else:
            self.repopulateGrid(self.grid_2_contents, col, "Network")

    @api_tool_decorator()
    def onAppGridSort(self, event):
        if (
            self.parentFrame.isRunning
            or (
                self.parentFrame.gauge.GetValue() != self.parentFrame.gauge.GetRange()
                and self.parentFrame.gauge.GetValue() != 0
            )
            or self.parentFrame.CSVUploaded
            or self.disableProperties
        ):
            return
        if hasattr(event, "Col"):
            col = event.Col
        else:
            col = event
        keyName = Globals.CSV_APP_ATTR_NAME[col]

        curSortCol = self.grid_3.GetSortingColumn()
        if curSortCol == col and hasattr(event, "Col"):
            self.networkDescending = not self.networkDescending
        self.grid_3.SetSortingColumn(col, bool(not self.networkDescending))
        if self.grid_3_contents and all(
            s[keyName].isdigit() if type(s) == str else False for s in self.grid_3_contents
        ):
            self.grid_3_contents = sorted(
                self.grid_3_contents,
                key=lambda i: i[keyName] and int(i[keyName]),
                reverse=self.networkDescending,
            )
        else:
            self.grid_3_contents = sorted(
                self.grid_3_contents,
                key=lambda i: i[keyName].lower(),
                reverse=self.networkDescending,
            )
        self.parentFrame.Logging(
            "---> Sorting App Grid on Column: %s Order: %s"
            % (keyName, "Descending" if self.networkDescending else "Ascending")
        )
        self.parentFrame.setGaugeValue(0)
        self.emptyAppGrid(emptyContents=False)
        self.grid_3.Freeze()
        if platform.system() == "Windows":
            thread = wxThread.GUIThread(
                self.parentFrame,
                self.repopulateGrid,
                (self.grid_3_contents, col, "App"),
            )
            thread.start()
        else:
            self.repopulateGrid(self.grid_3_contents, col, "App"),

    def repopulateGrid(self, content, col, action="Device"):
        num = 1
        for info in content:
            if action == "Device":
                self.addDeviceToDeviceGrid(info)
                self.parentFrame.setGaugeValue(
                    int(num / len(self.grid_1_contents) * 100)
                )
                num += 1
            elif action == "Network":
                self.addToNetworkGrid(info)
                self.parentFrame.setGaugeValue(
                    int(num / len(self.grid_2_contents) * 100)
                )
                num += 1
            elif action == "App":
                self.addApptoAppGrid(info)
                self.parentFrame.setGaugeValue(
                    int(num / len(self.grid_3_contents) * 100)
                )
                num += 1
        if action == "Device":
            self.grid_1.AutoSizeColumns()
            self.grid_1.MakeCellVisible(0, col)
            self.grid_1.Thaw()
        elif action == "Network":
            self.grid_2.AutoSizeColumns()
            self.grid_2.MakeCellVisible(0, col)
            self.grid_2.Thaw()
        elif action == "App":
            self.grid_3.AutoSizeColumns()
            self.grid_3.MakeCellVisible(0, col)
            self.grid_3.Thaw()
        self.parentFrame.onSearch(self.parentFrame.frame_toolbar.search.GetValue())
        time.sleep(3)
        postEventToFrame(eventUtil.myEVT_UPDATE_GAUGE, (0))

    @api_tool_decorator()
    def toogleViewMenuItem(self, event):
        """
        Disable native headers ability to hide columns when clicking an entry from the context menu
        """
        return

    @api_tool_decorator()
    def onGridMotion(self, event):
        if self.disableProperties:
            event.Skip()
            return
        validIndexes = [
            self.grid1HeaderLabels.index(col)
            for col in Globals.CSV_EDITABLE_COL
            if col in self.grid1HeaderLabels
        ]

        grid_win = self.grid_1.GetTargetWindow()
        grid_win2 = self.grid_2.GetTargetWindow()

        x, y = self.grid_1.CalcUnscrolledPosition(event.GetX(), event.GetY())
        coords = self.grid_1.XYToCell(x, y)
        col = coords[1]

        if col in validIndexes:
            grid_win.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        elif self.parentFrame.isBusy:
            self.setGridsCursor(wx.Cursor(wx.CURSOR_WAIT))
        else:
            self.setGridsCursor(wx.Cursor(wx.CURSOR_ARROW))
        event.Skip()

    def setGridsCursor(self, icon):
        grid_win = self.grid_1.GetTargetWindow()
        grid_win2 = self.grid_2.GetTargetWindow()
        grid_win.SetCursor(icon)
        grid_win2.SetCursor(icon)

    @api_tool_decorator()
    def applyTextColorMatchingGridRow(self, grid, query, bgColor, applyAll=False):
        """ Apply a Text or Bg Color to a Grid Row """
        statusIndex = self.grid1HeaderLabels.index("Status")
        if grid != self.grid_1:
            statusIndex = -1
        for rowNum in range(grid.GetNumberRows()):
            if hasattr(threading.current_thread(), "isStopped"):
                if threading.current_thread().isStopped():
                    return
            if rowNum < grid.GetNumberRows():
                match = []
                [
                    match.append(grid.GetCellValue(rowNum, colNum))
                    if query.lower() in grid.GetCellValue(rowNum, colNum).lower()
                    else None
                    for colNum in range(grid.GetNumberCols())
                ]
                if match or applyAll:
                    for colNum in range(grid.GetNumberCols()):
                        if (
                            colNum < grid.GetNumberCols()
                            and colNum != statusIndex
                            and (
                                grid.GetCellBackgroundColour(rowNum, colNum)
                                == Color.white.value
                                or (
                                    applyAll
                                    and grid.GetCellBackgroundColour(rowNum, colNum)
                                    == Color.lightYellow.value
                                )
                            )
                        ):
                            grid.SetCellBackgroundColour(rowNum, colNum, bgColor)
        grid.ForceRefresh()

    @api_tool_decorator()
    def onColumnVisibility(self, event):
        pageGridDict = {
            "Device": self.grid_1,
            "Network": self.grid_2,
            "Application": self.grid_3
        }
        exemptedLabels = [
            "Esper Name",
            "Esper Id",
            "Device Name"
        ]
        colLabelException = {
            "Device": exemptedLabels,
            "Network": exemptedLabels,
            "Application": exemptedLabels
        }

        with ColumnVisibility(self, pageGridDict, colLabelException) as dialog:
            res = dialog.ShowModal()
            if res == wx.ID_APPLY:
                selected = dialog.getSelected()
                for page in pageGridDict.keys():
                    # checkbox = dialog.getCheckBox(page)
                    for label, isChecked in selected[page].items():
                        if page == "Device":
                            indx = list(Globals.CSV_TAG_ATTR_NAME.keys()).index(label)
                            self.toggleColVisibilityInGridOne(
                                indx, showState=isChecked
                            )
                            self.grid1ColVisibility[label] = isChecked
                        elif page == "Network":
                            indx = list(Globals.CSV_NETWORK_ATTR_NAME.keys()).index(label)
                            self.toggleColVisibilityInGridTwo(
                                indx, showState=isChecked
                            )
                            self.grid2ColVisibility[label] = isChecked
                        elif page == "Application":
                            indx = Globals.CSV_APP_ATTR_NAME.index(label)
                            self.toggleColVisibilityInGridThree(
                                indx, showState=isChecked
                            )
                            self.grid2ColVisibility[label] = isChecked
                # self.parentFrame.savePrefs(self.parentFrame.prefDialog)

        self.parentFrame.prefDialog.colVisibilty = (
            self.grid1ColVisibility,
            self.grid2ColVisibility,
            self.grid3ColVisibility
        )

    def setColVisibility(self):
        grid1Cols = self.grid1ColVisibility.keys()
        grid2Cols = self.grid2ColVisibility.keys()
        grid3Cols = self.grid3ColVisibility.keys()
        for col in grid1Cols:
            if col in self.grid1HeaderLabels:
                indx = self.grid1HeaderLabels.index(col)
                self.toggleColVisibilityInGridOne(
                    indx, showState=self.grid1ColVisibility[col]
                )
        for col in grid2Cols:
            if col in self.grid2HeaderLabels:
                indx = self.grid2HeaderLabels.index(col)
                self.toggleColVisibilityInGridTwo(
                    indx, showState=self.grid2ColVisibility[col]
                )
        for col in grid3Cols:
            if col in self.grid3HeaderLabels:
                indx = self.grid3HeaderLabels.index(col)
                self.toggleColVisibilityInGridThree(
                    indx, showState=self.grid3ColVisibility[col]
                )

    @api_tool_decorator(locks=[Globals.grid1_lock])
    def addDeviceToDeviceGrid(self, device_info, isUpdate=False):
        """ Add device info to Device Grid """
        acquireLocks([Globals.grid1_lock])
        num = 0
        device = {}
        self.grid_1.AppendRows(1)
        esperName = ""
        for attribute in Globals.CSV_TAG_ATTR_NAME:
            value = (
                device_info[Globals.CSV_TAG_ATTR_NAME[attribute]]
                if Globals.CSV_TAG_ATTR_NAME[attribute] in device_info
                else ""
            )
            if "Esper Name" == attribute:
                esperName = value
            device[Globals.CSV_TAG_ATTR_NAME[attribute]] = str(value)
            if hasattr(threading.current_thread(), "isStopped"):
                if threading.current_thread().isStopped():
                    releaseLocks([Globals.grid1_lock])
                    return
            self.grid_1.SetCellValue(
                self.grid_1.GetNumberRows() - 1, num, str(value)
            )
            isEditable = True
            if attribute in Globals.CSV_EDITABLE_COL:
                isEditable = False
            self.grid_1.SetReadOnly(
                self.grid_1.GetNumberRows() - 1, num, isEditable
            )
            self.setStatusCellColor(value, self.grid_1.GetNumberRows() - 1, num)
            self.setAlteredCellColor(
                self.grid_1,
                device_info,
                self.grid_1.GetNumberRows() - 1,
                attribute,
                num,
            )
            num += 1
        deviceListing = list(
            filter(
                lambda x: (x[Globals.CSV_TAG_ATTR_NAME["Esper Name"]] == esperName),
                self.grid_1_contents,
            )
        )
        if device not in self.grid_1_contents and not deviceListing:
            self.grid_1_contents.append(device)
        releaseLocks([Globals.grid1_lock])

    def constructDeviceGridContent(self, device_info):
        device = {}
        for attribute in Globals.CSV_TAG_ATTR_NAME:
            value = (
                device_info[Globals.CSV_TAG_ATTR_NAME[attribute]]
                if Globals.CSV_TAG_ATTR_NAME[attribute] in device_info
                else ""
            )
            if "Esper Name" == attribute:
                esperName = value
            device[Globals.CSV_TAG_ATTR_NAME[attribute]] = str(value)
        deviceListing = list(
                filter(
                    lambda x: (x[Globals.CSV_TAG_ATTR_NAME["Esper Name"]] == esperName),
                    self.grid_1_contents,
                )
            )
        if device not in self.grid_1_contents and not deviceListing:
            self.grid_1_contents.append(device)
        return device

    def getDeviceNetworkInfoListing(self, device, device_info):
        device = {}
        for attribute in Globals.CSV_TAG_ATTR_NAME.keys():
            value = (
                device_info[Globals.CSV_TAG_ATTR_NAME[attribute]]
                if Globals.CSV_TAG_ATTR_NAME[attribute] in device_info
                else ""
            )
            device[Globals.CSV_TAG_ATTR_NAME[attribute]] = str(value)
        networkInfo = constructNetworkInfo(device, device_info)
        for attribute in Globals.CSV_NETWORK_ATTR_NAME.keys():
            value = networkInfo[attribute] if attribute in networkInfo else ""
            device[Globals.CSV_NETWORK_ATTR_NAME[attribute]] = str(value)
        return device

    @api_tool_decorator(locks=[Globals.grid1_status_lock])
    def setStatusCellColor(self, value, rowNum, colNum):
        acquireLocks(Globals.grid1_status_lock)
        if value == "Offline":
            self.grid_1.SetCellTextColour(rowNum, colNum, Color.red.value)
            self.grid_1.SetCellBackgroundColour(rowNum, colNum, Color.lightRed.value)
        elif value == "Online":
            self.grid_1.SetCellTextColour(rowNum, colNum, Color.green.value)
            self.grid_1.SetCellBackgroundColour(rowNum, colNum, Color.lightGreen.value)
        elif value == "Unspecified":
            self.grid_1.SetCellTextColour(rowNum, colNum, Color.darkGrey.value)
            self.grid_1.SetCellBackgroundColour(rowNum, colNum, Color.grey.value)
        elif value == "Provisioning":
            self.grid_1.SetCellTextColour(rowNum, colNum, Color.orange.value)
            self.grid_1.SetCellBackgroundColour(rowNum, colNum, Color.lightOrange.value)
        elif value == "Wipe In-Progress":
            self.grid_1.SetCellTextColour(rowNum, colNum, Color.purple.value)
            self.grid_1.SetCellBackgroundColour(rowNum, colNum, Color.lightPurple.value)
        elif value == "Unkown":
            self.grid_1.SetCellTextColour(rowNum, colNum, Color.black.value)
            self.grid_1.SetCellBackgroundColour(rowNum, colNum, Color.white.value)
        releaseLocks([Globals.grid1_status_lock])

    @api_tool_decorator(locks=[Globals.grid_color_lock])
    def setAlteredCellColor(self, grid, device_info, rowNum, attribute, indx):
        acquireLocks([Globals.grid_color_lock])
        if (
            attribute == "Alias"
            and "OriginalAlias" in device_info
            and device_info["Alias"] != device_info["OriginalAlias"]
        ):
            grid.SetCellBackgroundColour(rowNum, indx, Color.lightBlue.value)
        if (
            attribute == "Tags"
            and "OriginalTags" in device_info
            and device_info["Tags"] != device_info["OriginalTags"]
        ):
            grid.SetCellBackgroundColour(rowNum, indx, Color.lightBlue.value)
        releaseLocks([Globals.grid_color_lock])

    @api_tool_decorator(locks=[Globals.grid2_lock])
    def addDeviceToNetworkGrid(self, device, deviceInfo, isUpdate=False):
        """ Construct network info and add to grid """
        acquireLocks([Globals.grid2_lock])
        networkInfo = constructNetworkInfo(device, deviceInfo)
        self.addToNetworkGrid(networkInfo, isUpdate, device_info=deviceInfo)
        releaseLocks([Globals.grid2_lock])

    @api_tool_decorator()
    def addToNetworkGrid(self, networkInfo, isUpdate=False, device_info=None):
        """ Add info to the network grid """
        num = 0
        self.grid_2.AppendRows(1)
        for attribute in Globals.CSV_NETWORK_ATTR_NAME.keys():
            value = networkInfo[attribute] if attribute in networkInfo else ""
            self.grid_2.SetCellValue(
                self.grid_2.GetNumberRows() - 1, num, str(value)
            )
            self.grid_2.SetReadOnly(self.grid_2.GetNumberRows() - 1, num, True)
            num += 1
        if networkInfo not in self.grid_2_contents:
            self.grid_2_contents.append(networkInfo)

    def constructNetworkGridContent(self, device, deviceInfo):
        networkInfo = constructNetworkInfo(device, deviceInfo)
        for attribute in Globals.CSV_NETWORK_ATTR_NAME.keys():
            value = networkInfo[attribute] if attribute in networkInfo else ""
        if networkInfo not in self.grid_2_contents:
            self.grid_2_contents.append(networkInfo)

    @api_tool_decorator(locks=[Globals.grid1_lock])
    def applyTextColorToDevice(self, device, color, bgColor=None, applyAll=False):
        """ Apply a Text or Bg Color to a Grid Row """
        acquireLocks([Globals.grid1_lock])
        statusIndex = self.grid1HeaderLabels.index("Status")
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, 0)
                if (device and esperName == device.device_name) or applyAll:
                    for colNum in range(self.grid_1.GetNumberCols()):
                        if (
                            colNum < self.grid_1.GetNumberCols()
                            and colNum != statusIndex
                        ):
                            self.grid_1.SetCellTextColour(rowNum, colNum, color)
                            if bgColor:
                                self.grid_1.SetCellBackgroundColour(
                                    rowNum, colNum, bgColor
                                )
        self.grid_1.ForceRefresh()
        releaseLocks([Globals.grid1_lock])

    @api_tool_decorator(locks=[Globals.grid1_lock])
    def getDeviceTagsFromGrid(self):
        """ Return the tags from Grid """
        acquireLocks([Globals.grid1_lock])
        tagList = {}
        rowTagList = {}
        en_indx = self.grid1HeaderLabels.index("Esper Name")
        sn_indx = self.grid1HeaderLabels.index("Serial Number")
        csn_indx = self.grid1HeaderLabels.index("Custom Serial Number")
        imei1_indx = self.grid1HeaderLabels.index("IMEI 1")
        imei2_indx = self.grid1HeaderLabels.index("IMEI 2")
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, en_indx)
                serialNum = self.grid_1.GetCellValue(rowNum, sn_indx)
                cusSerialNum = self.grid_1.GetCellValue(rowNum, csn_indx)
                imei1 = self.grid_1.GetCellValue(rowNum, imei1_indx)
                imei2 = self.grid_1.GetCellValue(rowNum, imei2_indx)
                indx = self.grid1HeaderLabels.index("Tags")
                tags = self.grid_1.GetCellValue(rowNum, indx)
                properTagList = []
                for r in re.findall(
                    r"\".+?\"|\'.+?\'|\’.+?\’|[\w\d '-+\\/^%$#!@$%^&:.!?\-{}\<\>;]+",
                    tags,
                ):
                    processedTag = r.strip()
                    while (
                        processedTag.startswith('"')
                        or processedTag.startswith("'")
                        or processedTag.startswith("[")
                        or processedTag.startswith("’")
                    ):
                        processedTag = processedTag[1 : len(processedTag)]
                    while (
                        processedTag.endswith('"')
                        or processedTag.endswith("'")
                        or processedTag.endswith("]")
                        or processedTag.endswith("’")
                    ):
                        processedTag = processedTag[0 : len(processedTag) - 1]
                    if processedTag:
                        properTagList.append(processedTag.strip())
                    if len(properTagList) >= Globals.MAX_TAGS:
                        break
                if esperName:
                    if len(properTagList) <= 5:
                        tagList[esperName] = properTagList
                    else:
                        tagList[esperName] = properTagList[: Globals.MAX_TAGS]
                    rowTagList[rowNum] = {"esperName": esperName, "tags": properTagList}
                if serialNum:
                    if len(properTagList) <= 5:
                        tagList[serialNum] = properTagList
                    else:
                        tagList[serialNum] = properTagList[: Globals.MAX_TAGS]
                    if rowNum in rowTagList.keys():
                        rowTagList[rowNum]["sn"] = serialNum
                    else:
                        rowTagList[rowNum] = {"sn": serialNum, "tags": properTagList}
                if cusSerialNum:
                    if len(properTagList) <= 5:
                        tagList[cusSerialNum] = properTagList
                    else:
                        tagList[cusSerialNum] = properTagList[: Globals.MAX_TAGS]
                    if rowNum in rowTagList.keys():
                        rowTagList[rowNum]["csn"] = cusSerialNum
                    else:
                        rowTagList[rowNum] = {
                            "csn": cusSerialNum,
                            "tags": properTagList,
                        }
                if imei1:
                    if len(properTagList) <= 5:
                        tagList[imei1] = properTagList
                    else:
                        tagList[imei1] = properTagList[: Globals.MAX_TAGS]
                    if rowNum in rowTagList.keys():
                        rowTagList[rowNum]["imei1"] = imei1
                    else:
                        rowTagList[rowNum] = {
                            "imei1": imei1,
                            "tags": properTagList,
                        }
                if imei2:
                    if len(properTagList) <= 5:
                        tagList[imei2] = properTagList
                    else:
                        tagList[imei2] = properTagList[: Globals.MAX_TAGS]
                    if rowNum in rowTagList.keys():
                        rowTagList[rowNum]["imei2"] = imei2
                    else:
                        rowTagList[rowNum] = {
                            "imei2": imei2,
                            "tags": properTagList,
                        }
        releaseLocks([Globals.grid1_lock])
        return tagList, rowTagList

    @api_tool_decorator(locks=[Globals.grid1_lock])
    def getAppsFromGrid(self):
        """ Return the tags from Grid """
        acquireLocks([Globals.grid1_lock])
        appList = {}
        rowAppList = {}
        en_indx = self.grid1HeaderLabels.index("Esper Name")
        sn_indx = self.grid1HeaderLabels.index("Serial Number")
        csn_indx = self.grid1HeaderLabels.index("Custom Serial Number")
        imei1_indx = self.grid1HeaderLabels.index("IMEI 1")
        imei2_indx = self.grid1HeaderLabels.index("IMEI 2")
        indx = self.grid1HeaderLabels.index("Applications")
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, en_indx)
                serialNum = self.grid_1.GetCellValue(rowNum, sn_indx)
                cusSerialNum = self.grid_1.GetCellValue(rowNum, csn_indx)
                imei1 = self.grid_1.GetCellValue(rowNum, imei1_indx)
                imei2 = self.grid_1.GetCellValue(rowNum, imei2_indx)
                apps = self.grid_1.GetCellValue(rowNum, indx)

                properAppList = []
                for r in re.findall(
                    r"\".+?\"|\'.+?\'|\’.+?\’|[\w\d '-+\\/^%$#!@$%^&:.!?\-{}\<\>;]+",
                    apps,
                ):
                    processedTag = r.strip()
                    while (
                        processedTag.startswith('"')
                        or processedTag.startswith("'")
                        or processedTag.startswith("[")
                        or processedTag.startswith("’")
                    ):
                        processedTag = processedTag[1 : len(processedTag)]
                    while (
                        processedTag.endswith('"')
                        or processedTag.endswith("'")
                        or processedTag.endswith("]")
                        or processedTag.endswith("’")
                    ):
                        processedTag = processedTag[0 : len(processedTag) - 1]
                    if processedTag:
                        properAppList.append(processedTag.strip())
                if esperName:
                    appList[esperName] = properAppList
                    rowAppList[rowNum] = {"esperName": esperName, "tags": properAppList}
                if serialNum:
                    appList[serialNum] = properAppList
                    if rowNum in rowAppList.keys():
                        rowAppList[rowNum]["sn"] = serialNum
                    else:
                        rowAppList[rowNum] = {"sn": serialNum, "tags": properAppList}
                if cusSerialNum:
                    appList[cusSerialNum] = properAppList
                    if rowNum in rowAppList.keys():
                        rowAppList[rowNum]["csn"] = cusSerialNum
                    else:
                        rowAppList[rowNum] = {
                            "csn": cusSerialNum,
                            "tags": properAppList,
                        }
                if imei1:
                    appList[imei1] = properAppList
                    if rowNum in rowAppList.keys():
                        rowAppList[rowNum]["imei1"] = imei1
                    else:
                        rowAppList[rowNum] = {"imei1": imei1, "tags": properAppList}
                if imei2:
                    appList[imei2] = properAppList
                    if rowNum in rowAppList.keys():
                        rowAppList[rowNum]["imei2"] = imei2
                    else:
                        rowAppList[rowNum] = {"imei2": imei2, "tags": properAppList}
        releaseLocks([Globals.grid1_lock])
        return appList, rowAppList

    @api_tool_decorator(locks=[Globals.grid1_lock])
    def getDeviceAliasFromGrid(self):
        """ Return a list of Aliases from the Grid """
        acquireLocks([Globals.grid1_lock])
        aliasList = {}
        indx = self.grid1HeaderLabels.index("Alias")
        en_indx = self.grid1HeaderLabels.index("Esper Name")
        sn_indx = self.grid1HeaderLabels.index("Serial Number")
        csn_indx = self.grid1HeaderLabels.index("Custom Serial Number")
        imei1_indx = self.grid1HeaderLabels.index("IMEI 1")
        imei2_indx = self.grid1HeaderLabels.index("IMEI 2")
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, en_indx)
                serialNum = self.grid_1.GetCellValue(rowNum, sn_indx)
                cusSerialNum = self.grid_1.GetCellValue(rowNum, csn_indx)
                imei1 = self.grid_1.GetCellValue(rowNum, imei1_indx)
                imei2 = self.grid_1.GetCellValue(rowNum, imei2_indx)
                alias = self.grid_1.GetCellValue(rowNum, indx)
                if esperName and esperName not in aliasList.keys():
                    aliasList[esperName] = alias
                if serialNum and serialNum not in aliasList.keys():
                    aliasList[serialNum] = alias
                if cusSerialNum and cusSerialNum not in aliasList.keys():
                    aliasList[cusSerialNum] = alias
                if imei1 and imei1 not in aliasList.keys():
                    aliasList[imei1] = alias
                if imei2 and imei2 not in aliasList.keys():
                    aliasList[imei2] = alias
        releaseLocks([Globals.grid1_lock])
        return aliasList

    @api_tool_decorator()
    def getDeviceAliasFromList(self):
        aliasList = {}
        if self.grid_1_contents:
            for device in self.grid_1_contents:
                if device["EsperName"] not in aliasList:
                    aliasList[device["EsperName"]] = device["Alias"]
        else:
            aliasList = self.getDeviceAliasFromGrid()
        return aliasList

    @api_tool_decorator(locks=[Globals.grid1_lock])
    def toggleColVisibilityInGridOne(self, event, showState=None):
        """ Toggle Column Visibility in Device Grid """
        acquireLocks([Globals.grid1_lock])
        index = None
        if isinstance(event, (int, float, complex)) and not isinstance(event, bool):
            index = event
        if index and index < self.grid_1.GetNumberCols():
            if type(showState) == bool:
                if not showState:
                    self.grid_1.HideCol(index)
                else:
                    self.grid_1.ShowCol(index)
            else:
                isShown = self.grid_1.IsColShown(index)
                if isShown:
                    self.grid_1.HideCol(index)
                else:
                    self.grid_1.ShowCol(index)
        releaseLocks([Globals.grid1_lock])

    @api_tool_decorator(locks=[Globals.grid2_lock])
    def toggleColVisibilityInGridTwo(self, event, showState):
        """ Toggle Column Visibility in Network Grid """
        acquireLocks([Globals.grid2_lock])
        index = None
        if isinstance(event, (int, float, complex)) and not isinstance(event, bool):
            index = event
        if index and index < self.grid_2.GetNumberCols():
            if type(showState) == bool:
                if not showState:
                    self.grid_2.HideCol(index)
                else:
                    self.grid_2.ShowCol(index)
            else:
                isShown = self.grid_2.IsColShown(index)
                if isShown:
                    self.grid_2.HideCol(index)
                else:
                    self.grid_2.ShowCol(index)
        releaseLocks([Globals.grid2_lock])

    @api_tool_decorator(locks=[Globals.grid3_lock])
    def toggleColVisibilityInGridThree(self, event, showState):
        """ Toggle Column Visibility in Network Grid """
        acquireLocks([Globals.grid3_lock])
        index = None
        if isinstance(event, (int, float, complex)) and not isinstance(event, bool):
            index = event
        if index and index < self.grid_3.GetNumberCols():
            if type(showState) == bool:
                if not showState:
                    self.grid_3.HideCol(index)
                else:
                    self.grid_3.ShowCol(index)
            else:
                isShown = self.grid_3.IsColShown(index)
                if isShown:
                    self.grid_3.HideCol(index)
                else:
                    self.grid_3.ShowCol(index)
        releaseLocks([Globals.grid3_lock])

    @api_tool_decorator()
    def updateTagCell(self, name, tags=None):
        """ Update the Tag Column in the Device Grid """
        if platform.system() == "Windows":
            wxThread.GUIThread(
                self.parentFrame,
                self.processUpdateTagCell,
                (name, tags),
                name="UpdateTagCell",
            )
        else:
            self.processUpdateTagCell(name, tags)

    @api_tool_decorator(locks=[Globals.grid1_lock])
    def processUpdateTagCell(self, name, tags=None):
        acquireLocks([Globals.grid1_lock])
        self.disableGridProperties()
        name = tags = None
        if hasattr(name, "GetValue"):
            tple = name.GetValue()
            name = tple[0]
            tags = tple[1]
        if name and tags:
            for rowNum in range(self.grid_1.GetNumberRows()):
                if rowNum < self.grid_1.GetNumberRows():
                    esperName = self.grid_1.GetCellValue(rowNum, 0)
                    if name == esperName:
                        indx = self.grid1HeaderLabels.index("Tags")
                        if not all("" == s or s.isspace() for s in tags):
                            self.grid_1.SetCellValue(rowNum, indx, str(tags))
                        else:
                            self.grid_1.SetCellValue(rowNum, indx, "")
        self.enableGridProperties()
        releaseLocks([Globals.grid1_lock])

    @api_tool_decorator(locks=[Globals.grid1_lock, Globals.grid2_lock])
    def disableGridProperties(
        self, disableGrid=True, disableColSize=True, disableColMove=True
    ):
        acquireLocks([Globals.grid1_lock, Globals.grid2_lock])
        if disableGrid:
            self.grid_1.Enable(False)
            self.grid_2.Enable(False)
        if disableColSize:
            self.grid_1.DisableDragColSize()
            self.grid_2.DisableDragColSize()
        if disableColMove:
            self.grid_1.DisableDragColMove()
            self.grid_2.DisableDragColMove()
        self.disableProperties = True
        releaseLocks([Globals.grid1_lock, Globals.grid2_lock])

    @api_tool_decorator(locks=[Globals.grid1_lock, Globals.grid2_lock, Globals.grid3_lock])
    def enableGridProperties(
        self, enableGrid=True, enableColSize=True, enableColMove=True
    ):
        acquireLocks([Globals.grid1_lock, Globals.grid2_lock, Globals.grid3_lock])
        if enableGrid:
            self.grid_1.Enable(True)
            self.grid_2.Enable(True)
            self.grid_3.Enable(True)
        if enableColSize:
            self.grid_1.EnableDragColSize()
            self.grid_2.EnableDragColSize()
            self.grid_3.EnableDragColSize()
        if enableColMove:
            self.grid_1.EnableDragColMove()
            self.grid_2.EnableDragColMove()
            self.grid_3.EnableDragColMove()
        self.disableProperties = False
        releaseLocks([Globals.grid1_lock, Globals.grid2_lock, Globals.grid3_lock])

    @api_tool_decorator(locks=[Globals.grid1_lock])
    def getDeviceIdentifersFromGrid(self):
        acquireLocks([Globals.grid1_lock])
        identifers = []
        en_indx = self.grid1HeaderLabels.index("Esper Name")
        sn_indx = self.grid1HeaderLabels.index("Serial Number")
        csn_indx = self.grid1HeaderLabels.index("Custom Serial Number")
        imei1_indx = self.grid1HeaderLabels.index("IMEI 1")
        imei2_indx = self.grid1HeaderLabels.index("IMEI 2")
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, en_indx)
                serialNum = self.grid_1.GetCellValue(rowNum, sn_indx)
                cusSerialNum = self.grid_1.GetCellValue(rowNum, csn_indx)
                imei1 = self.grid_1.GetCellValue(rowNum, imei1_indx)
                imei2 = self.grid_1.GetCellValue(rowNum, imei2_indx)
                identifers.append((esperName, serialNum, cusSerialNum, imei1, imei2))
        releaseLocks([Globals.grid1_lock])
        return identifers

    @api_tool_decorator(locks=[Globals.grid1_lock])
    def getDeviceAppFromGrid(self):
        acquireLocks([Globals.grid1_lock])
        appList = {}
        indx = self.grid1HeaderLabels.index("Applications")
        en_indx = self.grid1HeaderLabels.index("Esper Name")
        sn_indx = self.grid1HeaderLabels.index("Serial Number")
        csn_indx = self.grid1HeaderLabels.index("Custom Serial Number")
        imei1_indx = self.grid1HeaderLabels.index("IMEI 1")
        imei2_indx = self.grid1HeaderLabels.index("IMEI 2")
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, en_indx)
                serialNum = self.grid_1.GetCellValue(rowNum, sn_indx)
                cusSerialNum = self.grid_1.GetCellValue(rowNum, csn_indx)
                imei1 = self.grid_1.GetCellValue(rowNum, imei1_indx)
                imei2 = self.grid_1.GetCellValue(rowNum, imei2_indx)
                apps = self.grid_1.GetCellValue(rowNum, indx)
                appListKeys = appList.keys()
                if esperName and esperName not in appListKeys:
                    appList[esperName] = apps
                elif serialNum and serialNum not in appListKeys:
                    appList[serialNum] = apps
                elif cusSerialNum and cusSerialNum not in appListKeys:
                    appList[cusSerialNum] = apps
                elif imei1 and imei1 not in appListKeys:
                    appList[imei1] = apps
                elif imei2 and imei2 not in appListKeys:
                    appList[imei2] = apps
        releaseLocks([Globals.grid1_lock])
        return appList

    def updateGridContent(self, event):
        evtVal = event.GetValue()
        if self.grid_1_contents:
            device = evtVal[0]
            modified = evtVal[1]
            deviceListing = list(
                filter(
                    lambda x: (
                        x[Globals.CSV_TAG_ATTR_NAME["Esper Name"]] == device.device_name
                    ),
                    self.grid_1_contents,
                )
            )
            for listing in deviceListing:
                indx = self.grid_1_contents.index(listing)
                if modified == "alias":
                    listing["OriginalAlias"] = listing["Alias"]
                elif modified == "tags":
                    listing["OriginalTags"] = listing["Tags"]
                self.grid_1_contents[indx] = listing

    def decrementOffset(self, event):
        if not self.parentFrame.isRunning:
            Globals.offset = Globals.offset - Globals.limit
            self.parentFrame.fetchData(False)
        event.Skip()

    def incrementOffset(self, event):
        if not self.parentFrame.isRunning:
            Globals.offset = Globals.offset + Globals.limit
            self.parentFrame.fetchData(False)
        event.Skip()

    def onGrid1Scroll(self, event):
        event.Skip()
        wx.CallAfter(self.setBothGridPositionsAndLoad, self.grid_1, self.grid_2)

    def onGrid2Scroll(self, event):
        event.Skip()
        wx.CallAfter(self.setBothGridPositionsAndLoad, self.grid_2, self.grid_1)

    def onGrid3Scroll(self, event):
        event.Skip()
        wx.CallAfter(self.onScroll, None)

    def setBothGridPositionsAndLoad(self, gridOne, gridTwo):
        self.onScroll(None)
        self.setBothGridVSCrollPositions(gridOne, gridTwo)

    def setBothGridVSCrollPositions(self, gridOne, gridTwo):
        if (
            Globals.MATCH_SCROLL_POS
            and gridOne.GetSortingColumn() < 0
            and gridTwo.GetSortingColumn() < 0
        ):
            gridTwo.Scroll(
                gridTwo.GetScrollPos(wx.HORIZONTAL), gridOne.GetScrollPos(wx.VERTICAL)
            )

    @api_tool_decorator()
    def onKey(self, event):
        keycode = event.GetKeyCode()
        # CTRL + C or CTRL + Insert
        if event.ControlDown() and keycode in [67, 322]:
            self.on_copy(event)
        # CTRL + V
        elif event.ControlDown() and keycode == 86:
            self.on_paste(event)
        else:
            event.Skip()

    @api_tool_decorator()
    def on_copy(self, event):
        widget = self.FindFocus()
        if self.currentlySelectedCell[0] >= 0 and self.currentlySelectedCell[1] >= 0:
            data = wx.TextDataObject()
            data.SetText(
                widget.GetCellValue(
                    self.currentlySelectedCell[0], self.currentlySelectedCell[1]
                )
            )
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(data)
                wx.TheClipboard.Close()
            widget.SetFocus()

    @api_tool_decorator()
    def on_paste(self, event):
        widget = self.FindFocus()
        success = False
        data = wx.TextDataObject()
        if wx.TheClipboard.Open():
            success = wx.TheClipboard.GetData(data)
            wx.TheClipboard.Close()
        if (
            success
            and self.currentlySelectedCell[0] >= 0
            and self.currentlySelectedCell[1] >= 0
            and not widget.IsReadOnly(
                self.currentlySelectedCell[0], self.currentlySelectedCell[1]
            )
        ):
            widget.SetCellValue(
                self.currentlySelectedCell[0],
                self.currentlySelectedCell[1],
                data.GetText(),
            )
        widget.SetFocus()

    def onSingleSelect(self, event):
        """
        Get the selection of a single cell by clicking or
        moving the selection with the arrow keys
        """
        self.currentlySelectedCell = (event.GetRow(), event.GetCol())
        event.Skip()

    def getColVisibility(self):
        if not self.grid1ColVisibility and not self.grid2ColVisibility:
            headerLabels = list(Globals.CSV_TAG_ATTR_NAME.keys())
            headerLabels2 = list(Globals.CSV_NETWORK_ATTR_NAME.keys())
            colNum = 0
            grid1Sizes = self.grid_1.GetColSizes()
            grid2Sizes = self.grid_2.GetColSizes()
            for header in headerLabels2:
                if grid2Sizes.GetSize(colNum) > 0:
                    self.grid2ColVisibility[str(header)] = True
                else:
                    self.grid2ColVisibility[str(header)] = False
                colNum += 1
            colNum = 0
            for header in headerLabels:
                if grid1Sizes.GetSize(colNum) > 0:
                    self.grid1ColVisibility[str(header)] = True
                else:
                    self.grid1ColVisibility[str(header)] = False
                colNum += 1
        return (self.grid1ColVisibility, self.grid2ColVisibility)

    @api_tool_decorator(locks=[Globals.grid1_lock])
    def getDeviceGroupFromGrid(self):
        acquireLocks([Globals.grid1_lock])
        groupList = {}
        en_indx = self.grid1HeaderLabels.index("Esper Name")
        sn_indx = self.grid1HeaderLabels.index("Serial Number")
        csn_indx = self.grid1HeaderLabels.index("Custom Serial Number")
        imei1_indx = self.grid1HeaderLabels.index("IMEI 1")
        imei2_indx = self.grid1HeaderLabels.index("IMEI 2")
        indx = self.grid1HeaderLabels.index("Group")
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, en_indx)
                serialNum = self.grid_1.GetCellValue(rowNum, sn_indx)
                cusSerialNum = self.grid_1.GetCellValue(rowNum, csn_indx)
                imei1 = self.grid_1.GetCellValue(rowNum, imei1_indx)
                imei2 = self.grid_1.GetCellValue(rowNum, imei2_indx)
                group = self.grid_1.GetCellValue(rowNum, indx)
                if esperName:
                    groupList[esperName] = group
                if serialNum:
                    groupList[serialNum] = group
                if cusSerialNum:
                    groupList[cusSerialNum] = group
                if imei1:
                    groupList[imei1] = group
                if imei2:
                    groupList[imei2] = group
        releaseLocks([Globals.grid1_lock])
        return groupList

    @api_tool_decorator(locks=[Globals.grid3_lock])
    def populateAppGrid(self, device, deviceInfo, apps):
        acquireLocks([Globals.grid3_lock])
        if apps and type(apps) == dict and "results" in apps:
            for app in apps["results"]:
                if app["package_name"] not in Globals.BLACKLIST_PACKAGE_NAME:
                    info = {
                        "Esper Name": device.device_name,
                        "Group": deviceInfo["groups"],
                        "Application Name": app["app_name"],
                        "Application Type": app["app_type"],
                        "Application Version Code": app["version_code"],
                        "Application Version Name": app["version_name"],
                        "Package Name": app["package_name"],
                        "State": app["state"],
                        "Whitelisted": app["whitelisted"],
                        "Can Clear Data": app["is_data_clearable"],
                        "Can Uninstall": app["is_uninstallable"]
                    }
                    self.addApptoAppGrid(info)
        releaseLocks([Globals.grid3_lock])

    @api_tool_decorator()
    def addApptoAppGrid(self, info):
        num = 0
        self.grid_3.AppendRows(1)
        for attribute in Globals.CSV_APP_ATTR_NAME:
            value = (
                info[attribute]
                if attribute in info
                else ""
            )
            if hasattr(threading.current_thread(), "isStopped"):
                if threading.current_thread().isStopped():
                    releaseLocks([Globals.grid3_lock])
                    return
            self.grid_3.SetCellValue(
                self.grid_3.GetNumberRows() - 1, num, str(value)
            )
            isEditable = True
            if attribute in Globals.CSV_EDITABLE_COL:
                isEditable = False
            self.grid_3.SetReadOnly(
                self.grid_3.GetNumberRows() - 1, num, isEditable
            )
            num += 1
            if info and info not in self.grid_3_contents:
                self.grid_3_contents.append(info)

    def constructAppGridContent(self, device, deviceInfo, apps):
        info = {}
        for app in apps["results"]:
            if app["package_name"] not in Globals.BLACKLIST_PACKAGE_NAME:
                info = {
                    "Esper Name": device.device_name,
                    "Group": deviceInfo["groups"],
                    "Application Name": app["app_name"],
                    "Application Type": app["app_type"],
                    "Application Version Code": app["version_code"],
                    "Application Version Name": app["version_name"],
                    "Package Name": app["package_name"],
                    "State": app["state"],
                    "Whitelisted": app["whitelisted"],
                    "Can Clear Data": app["is_data_clearable"],
                    "Can Uninstall": app["is_uninstallable"]
                }
        if info and info not in self.grid_3_contents:
            self.grid_3_contents.append(info)

    def onScroll(self, event):
        scrollPosPercentage = self.getScrollpercentage(self.grid_1)
        if scrollPosPercentage >= 90:
            self.populateGridRows(self.grid_1, self.grid_1_contents, Globals.CSV_TAG_ATTR_NAME)
        
        scrollPosPercentage = self.getScrollpercentage(self.grid_2)
        if scrollPosPercentage >= 90:
            self.populateGridRows(self.grid_2, self.grid_2_contents, Globals.CSV_NETWORK_ATTR_NAME)
        
        scrollPosPercentage = self.getScrollpercentage(self.grid_3)
        if scrollPosPercentage >= 90:
            self.populateGridRows(self.grid_3, self.grid_3_contents, Globals.CSV_APP_ATTR_NAME)
        if event:
            event.Skip()

    def getScrollpercentage(self, grid):
        numerator = (grid.GetScrollThumb(wx.VERTICAL) + grid.GetScrollPos(wx.VERTICAL))
        denominator = grid.GetScrollRange(wx.VERTICAL)
        scrollPosPercentage = 0
        if denominator > 0:
            scrollPosPercentage = numerator / denominator * 100
        return scrollPosPercentage

    def populateGridRows(self, grid, content, fields):
        if content:
            curNumRow = grid.GetNumberRows()
            num = curNumRow
            limit = curNumRow + Globals.MAX_GRID_LOAD
            if curNumRow < len(content) and num != limit:
                grid.Freeze()
                Globals.frame.setCursorBusy()
            while curNumRow < len(content) and num != limit:
                grid.AppendRows(1)
                entry = content[num]
                col = 0
                for attr in fields:
                    value = None
                    if type(fields) == dict:
                        value = (
                            entry[fields[attr]]
                            if fields[attr] in entry
                            else ""
                        )
                    if type(fields) == list or not value:
                        value = (
                            entry[attr]
                            if attr in entry
                            else ""
                        )
                    grid.SetCellValue(
                        grid.GetNumberRows() - 1, col, str(value)
                    )
                    isEditable = True
                    if attr in Globals.CSV_EDITABLE_COL:
                        isEditable = False
                    grid.SetReadOnly(
                        grid.GetNumberRows() - 1, col, isEditable
                    )
                    self.setStatusCellColor(value, grid.GetNumberRows() - 1, col)
                    self.setAlteredCellColor(
                        grid,
                        entry,
                        grid.GetNumberRows() - 1,
                        attr,
                        col,
                    )
                    col += 1
                num += 1
                curNumRow = grid.GetNumberRows()
        if grid.IsFrozen():
            grid.Thaw()
        Globals.frame.setCursorDefault()
