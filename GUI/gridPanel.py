#!/usr/bin/env python

import time
from Utility.Resource import postEventToFrame, resourcePath, scale_bitmap
import Common.Globals as Globals
import re
import threading
import wx
import wx.grid as gridlib
import Utility.wxThread as wxThread


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

        self.deviceDescending = False
        self.networkDescending = False

        self.parentFrame = parentFrame
        self.disableProperties = False
        self.currentlySelectedCell = (-1, -1)

        self.grid1HeaderLabels = list(Globals.CSV_TAG_ATTR_NAME.keys())
        self.grid2HeaderLabels = list(Globals.CSV_NETWORK_ATTR_NAME.keys())

        grid_sizer_2 = wx.FlexGridSizer(2, 1, 0, 0)

        self.panel_4 = wx.Panel(self, wx.ID_ANY)
        grid_sizer_2.Add(self.panel_4, 1, wx.EXPAND | wx.TOP, 5)

        grid_sizer_4 = wx.FlexGridSizer(2, 1, 0, 0)

        self.panel_1 = wx.Panel(self.panel_4, wx.ID_ANY)
        grid_sizer_4.Add(self.panel_1, 1, wx.EXPAND, 0)

        grid_sizer_1 = wx.GridSizer(1, 2, 0, 0)

        network_grid = wx.StaticText(self.panel_1, wx.ID_ANY, "Network Information:")
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
        grid_sizer_1.Add(network_grid, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)

        self.panel_3 = wx.Panel(self.panel_1, wx.ID_ANY)
        grid_sizer_1.Add(
            self.panel_3, 1, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5
        )

        grid_sizer_3 = wx.GridSizer(1, 3, 0, 0)

        prev_icon = scale_bitmap(resourcePath("Images/prev.png"), 18, 18)
        self.button_1 = wx.BitmapButton(
            self.panel_3,
            wx.ID_BACKWARD,
            prev_icon,
        )
        self.button_1.SetToolTip("Load previous page of devices.")
        grid_sizer_3.Add(self.button_1, 0, 0, 0)

        grid_sizer_3.Add((20, 20), 0, wx.EXPAND, 0)

        next_icon = scale_bitmap(resourcePath("Images/next.png"), 18, 18)
        self.button_2 = wx.BitmapButton(
            self.panel_3,
            wx.ID_FORWARD,
            next_icon,
        )
        self.button_2.SetToolTip("Load next page of devices.")
        grid_sizer_3.Add(self.button_2, 0, 0, 0)

        self.grid_2 = wx.grid.Grid(self.panel_4, wx.ID_ANY, size=(1, 1))
        grid_sizer_4.Add(self.grid_2, 1, wx.ALL | wx.EXPAND, 5)

        self.panel_9 = wx.Panel(self, wx.ID_ANY)
        grid_sizer_2.Add(self.panel_9, 1, wx.EXPAND, 0)

        grid_sizer_8 = wx.BoxSizer(wx.VERTICAL)

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

        self.grid_1 = wx.grid.Grid(self.panel_9, wx.ID_ANY, size=(1, 1))
        grid_sizer_8.Add(self.grid_1, 1, wx.ALL | wx.EXPAND, 5)

        self.panel_9.SetSizer(grid_sizer_8)

        self.panel_3.SetSizer(grid_sizer_3)

        self.panel_1.SetSizer(grid_sizer_1)

        grid_sizer_4.AddGrowableRow(1)
        grid_sizer_4.AddGrowableCol(0)
        self.panel_4.SetSizer(grid_sizer_4)

        grid_sizer_2.AddGrowableRow(0)
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

    @api_tool_decorator
    def __set_properties(self):
        self.grid_1.Bind(gridlib.EVT_GRID_CELL_CHANGED, self.onCellChange)
        self.grid_1.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.onDeviceGridSort)
        self.grid_2.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.onNetworkGridSort)
        self.grid_1.Bind(gridlib.EVT_GRID_LABEL_RIGHT_CLICK, self.toogleViewMenuItem)
        self.grid_2.Bind(gridlib.EVT_GRID_LABEL_RIGHT_CLICK, self.toogleViewMenuItem)

        self.grid_1.GetGridWindow().Bind(wx.EVT_MOTION, self.onGridMotion)
        self.grid_1.Bind(wx.EVT_SCROLLWIN, self.onGrid1Scroll)
        self.grid_2.Bind(wx.EVT_SCROLLWIN, self.onGrid2Scroll)
        self.grid_1.Bind(gridlib.EVT_GRID_SELECT_CELL, self.onSingleSelect)
        self.grid_2.Bind(gridlib.EVT_GRID_SELECT_CELL, self.onSingleSelect)
        self.grid_1.GetGridWindow().Bind(wx.EVT_KEY_DOWN, self.onKey)
        self.grid_2.GetGridWindow().Bind(wx.EVT_KEY_DOWN, self.onKey)

        self.grid_2.CreateGrid(0, len(Globals.CSV_NETWORK_ATTR_NAME.keys()))
        self.grid_1.CreateGrid(0, len(Globals.CSV_TAG_ATTR_NAME.keys()))
        self.grid_1.UseNativeColHeader()
        self.grid_2.UseNativeColHeader()
        self.grid_1.DisableDragRowSize()
        self.grid_2.DisableDragRowSize()
        self.grid_1.EnableDragColMove(True)
        self.grid_2.EnableDragColMove(True)
        self.enableGridProperties()
        self.fillDeviceGridHeaders()
        self.fillNetworkGridHeaders()

    @api_tool_decorator
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

    @api_tool_decorator
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

    @api_tool_decorator
    def emptyDeviceGrid(self, emptyContents=True):
        """ Empty Device Grid """
        Globals.grid1_lock.acquire()
        if emptyContents:
            self.grid_1_contents = []
        if self.grid_1.GetNumberRows() > 0:
            self.grid_1.DeleteRows(0, self.grid_1.GetNumberRows())
        self.grid_1.SetScrollLineX(15)
        self.grid_1.SetScrollLineY(15)
        self.fillDeviceGridHeaders()
        Globals.grid1_lock.release()

    @api_tool_decorator
    def emptyNetworkGrid(self, emptyContents=True):
        """ Empty Network Grid """
        Globals.grid2_lock.acquire()
        if emptyContents:
            self.grid_2_contents = []
        if self.grid_2.GetNumberRows() > 0:
            self.grid_2.DeleteRows(0, self.grid_2.GetNumberRows())
        self.grid_2.SetScrollLineX(15)
        self.grid_2.SetScrollLineY(15)
        self.fillNetworkGridHeaders()
        Globals.grid2_lock.release()

    @api_tool_decorator
    def autoSizeGridsColumns(self, event=None):
        Globals.grid1_lock.acquire()
        Globals.grid2_lock.acquire()
        self.grid_1.AutoSizeColumns()
        self.grid_2.AutoSizeColumns()
        self.grid_1.ForceRefresh()
        self.grid_2.ForceRefresh()
        Globals.grid1_lock.release()
        Globals.grid2_lock.release()

    @api_tool_decorator
    def onCellChange(self, event):
        """ Try to Auto size Columns on change """
        Globals.grid1_lock.acquire()
        self.userEdited.append((event.Row, event.Col))
        editor = self.grid_1.GetCellEditor(event.Row, event.Col)
        if not editor.IsCreated():
            self.grid_1.AutoSizeColumns()
        self.onCellEdit(event)
        Globals.grid1_lock.release()

    @api_tool_decorator
    def onCellEdit(self, event):
        indx1 = self.grid1HeaderLabels.index("Tags")
        indx2 = self.grid1HeaderLabels.index("Alias")
        x, y = self.grid_1.GetGridCursorCoords()
        esperName = self.grid_1.GetCellValue(x, 0)
        deviceListing = list(
            filter(
                lambda x: (x[Globals.CSV_TAG_ATTR_NAME["Esper Name"]] == esperName),
                self.grid_1_contents,
            )
        )
        if deviceListing:
            if (
                (
                    y == indx2
                    and not "OriginalAlias" in deviceListing[0]
                    and deviceListing[0][Globals.CSV_TAG_ATTR_NAME["Alias"]]
                    != self.grid_1.GetCellValue(x, y)
                )
                or (
                    y == indx2
                    and "OriginalAlias" in deviceListing[0]
                    and deviceListing[0]["OriginalAlias"]
                    != self.grid_1.GetCellValue(x, y)
                )
                or (
                    y == indx1
                    and not "OriginalTags" in deviceListing[0]
                    and deviceListing[0][Globals.CSV_TAG_ATTR_NAME["Tags"]]
                    != self.grid_1.GetCellValue(x, y)
                )
                or (
                    y == indx1
                    and "OriginalTags" in deviceListing[0]
                    and deviceListing[0]["OriginalTags"]
                    != self.grid_1.GetCellValue(x, y)
                )
            ):
                self.grid_1.SetCellBackgroundColour(x, y, Color.lightBlue.value)
                if y == indx2:
                    deviceListing[0][
                        Globals.CSV_TAG_ATTR_NAME["Alias"]
                    ] = self.grid_1.GetCellValue(x, y)
                if y == indx1:
                    deviceListing[0][
                        Globals.CSV_TAG_ATTR_NAME["Tags"]
                    ] = self.grid_1.GetCellValue(x, y)
                if y == indx2 and not "OriginalAlias" in deviceListing[0]:
                    deviceListing[0]["OriginalAlias"] = event.GetString()
                if y == indx1 and not "OriginalTags" in deviceListing[0]:
                    deviceListing[0]["OriginalTags"] = event.GetString()
            else:
                if (
                    y == indx1
                    and "OriginalTags" in deviceListing[0]
                    and deviceListing[0]["OriginalTags"]
                    == self.grid_1.GetCellValue(x, y)
                ):
                    deviceListing[0][
                        Globals.CSV_TAG_ATTR_NAME["Tags"]
                    ] = self.grid_1.GetCellValue(x, y)
                if (
                    y == indx2
                    and "OriginalAlias" in deviceListing[0]
                    and deviceListing[0]["OriginalAlias"]
                    == self.grid_1.GetCellValue(x, y)
                ):
                    deviceListing[0][
                        Globals.CSV_TAG_ATTR_NAME["Alias"]
                    ] = self.grid_1.GetCellValue(x, y)
                self.grid_1.SetCellBackgroundColour(x, y, Color.white.value)
        event.Skip()

    @api_tool_decorator
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
        thread = wxThread.GUIThread(
            self.parentFrame, self.repopulateGrid, (self.grid_1_contents, col)
        )
        thread.start()

    @api_tool_decorator
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
        thread = wxThread.GUIThread(
            self.parentFrame,
            self.repopulateGrid,
            (self.grid_2_contents, col, "Network"),
        )
        thread.start()

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
        if action == "Device":
            self.grid_1.AutoSizeColumns()
            self.grid_1.MakeCellVisible(0, col)
            self.grid_1.Thaw()
        elif action == "Network":
            self.grid_2.AutoSizeColumns()
            self.grid_2.MakeCellVisible(0, col)
            self.grid_2.Thaw()
        self.parentFrame.onSearch(self.parentFrame.frame_toolbar.search.GetValue())
        time.sleep(3)
        postEventToFrame(wxThread.myEVT_UPDATE_GAUGE, (0))

    @api_tool_decorator
    def toogleViewMenuItem(self, event):
        """
        Disable native headers ability to hide columns when clicking an entry from the context menu
        """
        return

    @api_tool_decorator
    def onGridMotion(self, event):
        if self.disableProperties:
            event.Skip()
            return
        indx1 = self.grid1HeaderLabels.index("Tags")
        indx2 = self.grid1HeaderLabels.index("Alias")
        grid_win = self.grid_1.GetTargetWindow()
        grid_win2 = self.grid_2.GetTargetWindow()

        x, y = self.grid_1.CalcUnscrolledPosition(event.GetX(), event.GetY())
        coords = self.grid_1.XYToCell(x, y)
        col = coords[1]

        if col == indx1 or col == indx2:
            grid_win.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        elif self.parentFrame.isBusy:
            grid_win.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
            grid_win2.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
        else:
            grid_win.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
            grid_win2.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        event.Skip()

    @api_tool_decorator
    def applyTextColorMatchingGridRow(self, grid, query, bgColor, applyAll=False):
        """ Apply a Text or Bg Color to a Grid Row """
        statusIndex = self.grid1HeaderLabels.index("Status")
        if grid != self.grid_1:
            statusIndex = -1
        for rowNum in range(grid.GetNumberRows()):
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

    @api_tool_decorator
    def onDeviceColumn(self, event):
        headerLabels = list(Globals.CSV_TAG_ATTR_NAME.keys())
        if "Esper Name" in headerLabels:
            headerLabels.remove("Esper Name")
        if "Device Name" in headerLabels:
            headerLabels.remove("Device Name")

        with ColumnVisibilityDialog(
            self, self.grid_1, choiceData=headerLabels
        ) as dialog:
            if dialog.ShowModal() == wx.ID_APPLY:
                colNum = 0
                for _ in headerLabels:
                    self.toggleColVisibilityInGridOne(
                        colNum + 1, showState=dialog.isChecked(colNum)
                    )
                    colNum += 1
            dialog.DestroyLater()

    @api_tool_decorator
    def onNetworkColumn(self, event):
        headerLabels = list(Globals.CSV_NETWORK_ATTR_NAME.keys())
        if "Esper Name" in headerLabels:
            headerLabels.remove("Esper Name")
        if "Device Name" in headerLabels:
            headerLabels.remove("Device Name")

        with ColumnVisibilityDialog(
            self, self.grid_2, choiceData=headerLabels
        ) as dialog:
            if dialog.ShowModal() == wx.ID_APPLY:
                colNum = 0
                for _ in headerLabels:
                    self.toggleColVisibilityInGridTwo(
                        colNum + 1, showState=dialog.isChecked(colNum)
                    )
                    colNum += 1
            dialog.DestroyLater()

    @api_tool_decorator
    def addDeviceToDeviceGrid(self, device_info, isUpdate=False):
        """ Add device info to Device Grid """
        Globals.grid1_lock.acquire()
        num = 0
        device = {}
        if isUpdate:
            deviceName = device_info[Globals.CSV_TAG_ATTR_NAME["Esper Name"]]
            for rowNum in range(self.grid_1.GetNumberRows()):
                if rowNum < self.grid_1.GetNumberRows():
                    esperName = self.grid_1.GetCellValue(rowNum, 0)
                    if deviceName == esperName:
                        deviceListing = list(
                            filter(
                                lambda x: (
                                    x[Globals.CSV_TAG_ATTR_NAME["Esper Name"]]
                                    == esperName
                                ),
                                self.grid_1_contents,
                            )
                        )
                        if deviceListing:
                            deviceListing = deviceListing[0]
                        else:
                            if hasattr(threading.current_thread(), "isStopped"):
                                if threading.current_thread().isStopped():
                                    Globals.grid1_lock.release()
                                    return
                            Globals.grid1_lock.release()
                            self.addDeviceToDeviceGrid(device_info, isUpdate=False)
                            break
                        deviceListing.update(device)
                        for attribute in Globals.CSV_TAG_ATTR_NAME:
                            indx = self.grid1HeaderLabels.index(attribute)
                            cellValue = self.grid_1.GetCellValue(rowNum, indx)
                            fecthValue = (
                                device_info[Globals.CSV_TAG_ATTR_NAME[attribute]]
                                if Globals.CSV_TAG_ATTR_NAME[attribute] in device_info
                                else ""
                            )
                            if (
                                not (
                                    rowNum,
                                    indx,
                                )
                                in self.userEdited
                                and cellValue != str(fecthValue)
                            ):
                                if hasattr(threading.current_thread(), "isStopped"):
                                    if threading.current_thread().isStopped():
                                        Globals.grid1_lock.release()
                                        return
                                self.grid_1.SetCellValue(rowNum, indx, str(fecthValue))
                                self.setStatusCellColor(fecthValue, rowNum, indx)
                                self.setAlteredCellColor(
                                    self.grid_1,
                                    device_info,
                                    rowNum,
                                    attribute,
                                    indx,
                                )
                                device[Globals.CSV_TAG_ATTR_NAME[attribute]] = str(
                                    fecthValue
                                )
                            else:
                                device[Globals.CSV_TAG_ATTR_NAME[attribute]] = str(
                                    cellValue
                                )
                        break
            # Don't add if not found as potential Endpoint swap could have occurred
        else:
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
                        Globals.grid1_lock.release()
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
        Globals.grid1_lock.release()

    @api_tool_decorator
    def setStatusCellColor(self, value, rowNum, colNum):
        Globals.grid1_status_lock.acquire()
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
        Globals.grid1_status_lock.release()

    @api_tool_decorator
    def setAlteredCellColor(self, grid, device_info, rowNum, attribute, indx):
        Globals.grid_color_lock.acquire()
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
        Globals.grid_color_lock.release()

    @api_tool_decorator
    def addDeviceToNetworkGrid(self, device, deviceInfo, isUpdate=False):
        """ Construct network info and add to grid """
        Globals.grid2_lock.acquire()
        networkInfo = constructNetworkInfo(device, deviceInfo)
        self.addToNetworkGrid(networkInfo, isUpdate, device_info=deviceInfo)
        Globals.grid2_lock.release()

    @api_tool_decorator
    def addToNetworkGrid(self, networkInfo, isUpdate=False, device_info=None):
        """ Add info to the network grid """
        num = 0
        if isUpdate:
            deviceName = device_info[Globals.CSV_NETWORK_ATTR_NAME["Device Name"]]
            found = False
            for rowNum in range(self.grid_2.GetNumberRows()):
                if rowNum < self.grid_2.GetNumberRows():
                    esperName = self.grid_2.GetCellValue(rowNum, 0)
                    if deviceName == esperName:
                        found = True
                        deviceListing = list(
                            filter(
                                lambda x: (x["Device Name"] == esperName),
                                self.grid_2_contents,
                            )
                        )
                        if deviceListing:
                            deviceListing = deviceListing[0]
                        else:
                            self.addToNetworkGrid(
                                networkInfo, device_info=device_info, isUpdate=False
                            )
                            break
                        for attribute in Globals.CSV_NETWORK_ATTR_NAME.keys():
                            indx = self.grid2HeaderLabels.index(attribute)
                            cellValue = self.grid_2.GetCellValue(rowNum, indx)
                            fecthValue = (
                                networkInfo[attribute]
                                if attribute in networkInfo
                                else ""
                            )
                            if (
                                not (
                                    rowNum,
                                    indx,
                                )
                                in self.userEdited
                                and cellValue != str(fecthValue)
                            ):
                                self.grid_2.SetCellValue(rowNum, indx, str(fecthValue))
                            deviceListing.update(networkInfo)
                        break
            if not found:
                self.addToNetworkGrid(
                    networkInfo, device_info=device_info, isUpdate=False
                )
        else:
            self.grid_2.AppendRows(1)
            for attribute in Globals.CSV_NETWORK_ATTR_NAME.keys():
                value = networkInfo[attribute] if attribute in networkInfo else ""
                self.grid_2.SetCellValue(
                    self.grid_2.GetNumberRows() - 1, num, str(value)
                )
                isEditable = True
                if attribute in Globals.CSV_EDITABLE_COL:
                    isEditable = False
                self.grid_2.SetReadOnly(
                    self.grid_2.GetNumberRows() - 1, num, isEditable
                )
                num += 1
            if networkInfo not in self.grid_2_contents:
                self.grid_2_contents.append(networkInfo)

    @api_tool_decorator
    def applyTextColorToDevice(self, device, color, bgColor=None, applyAll=False):
        """ Apply a Text or Bg Color to a Grid Row """
        Globals.grid1_lock.acquire()
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
        Globals.grid1_lock.release()

    @api_tool_decorator
    def getDeviceTagsFromGrid(self):
        """ Return the tags from Grid """
        Globals.grid1_lock.acquire()
        tagList = {}
        en_indx = self.grid1HeaderLabels.index("Esper Name")
        sn_indx = self.grid1HeaderLabels.index("Serial Number")
        csn_indx = self.grid1HeaderLabels.index("Custom Serial Number")
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, en_indx)
                serialNum = self.grid_1.GetCellValue(rowNum, sn_indx)
                cusSerialNum = self.grid_1.GetCellValue(rowNum, csn_indx)
                indx = self.grid1HeaderLabels.index("Tags")
                tags = self.grid_1.GetCellValue(rowNum, indx)
                properTagList = []
                for r in re.findall(r"\".+?\"|[\w\d '-+\\/^%$#!@$%^&]+", tags):
                    processedTag = r.strip()
                    while processedTag.startswith('"') or processedTag.startswith("'"):
                        processedTag = processedTag[1 : len(processedTag)]
                    while processedTag.endswith('"') or processedTag.endswith("'"):
                        processedTag = processedTag[0 : len(processedTag) - 1]
                    if processedTag:
                        properTagList.append(processedTag.strip())
                if esperName:
                    tagList[esperName] = properTagList
                if serialNum:
                    tagList[serialNum] = properTagList
                if cusSerialNum:
                    tagList[cusSerialNum] = properTagList
        Globals.grid1_lock.release()
        return tagList

    @api_tool_decorator
    def getDeviceAliasFromGrid(self):
        """ Return a list of Aliases from the Grid """
        Globals.grid1_lock.acquire()
        aliasList = {}
        indx = self.grid1HeaderLabels.index("Alias")
        en_indx = self.grid1HeaderLabels.index("Esper Name")
        sn_indx = self.grid1HeaderLabels.index("Serial Number")
        csn_indx = self.grid1HeaderLabels.index("Custom Serial Number")
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, en_indx)
                serialNum = self.grid_1.GetCellValue(rowNum, sn_indx)
                cusSerialNum = self.grid_1.GetCellValue(rowNum, csn_indx)
                alias = self.grid_1.GetCellValue(rowNum, indx)
                if esperName and esperName not in aliasList.keys():
                    aliasList[esperName] = alias
                if serialNum and serialNum not in aliasList.keys():
                    aliasList[serialNum] = alias
                if cusSerialNum and cusSerialNum not in aliasList.keys():
                    aliasList[cusSerialNum] = alias
        Globals.grid1_lock.release()
        return aliasList

    @api_tool_decorator
    def getDeviceAliasFromList(self):
        aliasList = {}
        if self.grid_1_contents:
            for device in self.grid_1_contents:
                if device["EsperName"] not in aliasList:
                    aliasList[device["EsperName"]] = device["Alias"]
        else:
            aliasList = self.getDeviceAliasFromGrid()
        return aliasList

    @api_tool_decorator
    def toggleColVisibilityInGridOne(self, event, showState=None):
        """ Toggle Column Visibility in Device Grid """
        Globals.grid1_lock.acquire()
        index = None
        if isinstance(event, (int, float, complex)) and not isinstance(event, bool):
            index = event
        if index:
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
        Globals.grid1_lock.release()

    @api_tool_decorator
    def toggleColVisibilityInGridTwo(self, event, showState):
        """ Toggle Column Visibility in Network Grid """
        Globals.grid2_lock.acquire()
        index = None
        if isinstance(event, (int, float, complex)) and not isinstance(event, bool):
            index = event
        if index:
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
        Globals.grid2_lock.release()

    @api_tool_decorator
    def updateTagCell(self, name, tags=None):
        """ Update the Tag Column in the Device Grid """
        wxThread.GUIThread(
            self.parentFrame,
            self.processUpdateTagCell,
            (name, tags),
            name="UpdateTagCell",
        )

    def processUpdateTagCell(self, name, tags=None):
        Globals.grid1_lock.acquire()
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
        Globals.grid1_lock.release()

    @api_tool_decorator
    def disableGridProperties(
        self, disableGrid=True, disableColSize=True, disableColMove=True
    ):
        Globals.grid1_lock.acquire()
        Globals.grid2_lock.acquire()
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
        Globals.grid1_lock.release()
        Globals.grid2_lock.release()

    @api_tool_decorator
    def enableGridProperties(
        self, enableGrid=True, enableColSize=True, enableColMove=True
    ):
        Globals.grid1_lock.acquire()
        Globals.grid2_lock.acquire()
        if enableGrid:
            self.grid_1.Enable(True)
            self.grid_2.Enable(True)
        if enableColSize:
            self.grid_1.EnableDragColSize()
            self.grid_2.EnableDragColSize()
        if enableColMove:
            self.grid_1.EnableDragColMove()
            self.grid_2.EnableDragColMove()
        self.disableProperties = False
        Globals.grid1_lock.release()
        Globals.grid2_lock.release()

    def getDeviceIdentifersFromGrid(self):
        Globals.grid1_lock.acquire()
        identifers = []
        en_indx = self.grid1HeaderLabels.index("Esper Name")
        sn_indx = self.grid1HeaderLabels.index("Serial Number")
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, en_indx)
                serialNum = self.grid_1.GetCellValue(rowNum, sn_indx)
                if esperName or serialNum:
                    identifers.append((esperName, serialNum))
        Globals.grid1_lock.release()
        return identifers

    def getDeviceAppFromGrid(self):
        Globals.grid1_lock.acquire()
        appList = {}
        indx = self.grid1HeaderLabels.index("Applications")
        en_indx = self.grid1HeaderLabels.index("Esper Name")
        sn_indx = self.grid1HeaderLabels.index("Serial Number")
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, en_indx)
                serialNum = self.grid_1.GetCellValue(rowNum, sn_indx)
                apps = self.grid_1.GetCellValue(rowNum, indx)
                if esperName and esperName not in appList.keys():
                    appList[esperName] = apps
                elif serialNum and serialNum not in appList.keys():
                    appList[serialNum] = apps
        Globals.grid1_lock.release()
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
        wx.CallAfter(self.setBothGridVSCrollPositions, self.grid_1, self.grid_2)

    def onGrid2Scroll(self, event):
        event.Skip()
        wx.CallAfter(self.setBothGridVSCrollPositions, self.grid_2, self.grid_1)

    def setBothGridVSCrollPositions(self, gridOne, gridTwo):
        if Globals.MATCH_SCROLL_POS:
            gridTwo.Scroll(
                gridTwo.GetScrollPos(wx.HORIZONTAL), gridOne.GetScrollPos(wx.VERTICAL)
            )

    @api_tool_decorator
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

    @api_tool_decorator
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

    @api_tool_decorator
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
