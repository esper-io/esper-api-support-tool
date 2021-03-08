#!/usr/bin/env python

import Common.Globals as Globals
import re
import threading
import wx
import wx.grid as gridlib


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

        sizer_6 = wx.BoxSizer(wx.VERTICAL)

        label_7 = wx.StaticText(self, wx.ID_ANY, "Network Info:")
        label_7.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        sizer_6.Add(label_7, 0, wx.EXPAND, 0)

        self.grid_2 = wx.grid.Grid(self, wx.ID_ANY, size=(1, 1))
        sizer_6.Add(self.grid_2, 1, wx.EXPAND, 0)

        label_8 = wx.StaticText(self, wx.ID_ANY, "Device Info:")
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
        sizer_6.Add(label_8, 0, wx.EXPAND, 0)

        self.grid_1 = wx.grid.Grid(self, wx.ID_ANY, size=(1, 1))
        sizer_6.Add(self.grid_1, 1, wx.EXPAND, 0)

        self.SetSizer(sizer_6)

        self.__set_properties()

    def __set_properties(self):
        self.grid_1.Bind(gridlib.EVT_GRID_CELL_CHANGED, self.onCellChange)
        self.grid_1.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.onDeviceGridSort)
        self.grid_2.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.onNetworkGridSort)
        self.grid_1.Bind(gridlib.EVT_GRID_LABEL_RIGHT_CLICK, self.toogleViewMenuItem)
        self.grid_2.Bind(gridlib.EVT_GRID_LABEL_RIGHT_CLICK, self.toogleViewMenuItem)

        self.grid_1.GetGridWindow().Bind(wx.EVT_MOTION, self.onGridMotion)

        self.grid_2.CreateGrid(0, len(Globals.CSV_NETWORK_ATTR_NAME.keys()))
        self.grid_1.CreateGrid(0, len(Globals.CSV_TAG_ATTR_NAME.keys()))
        self.grid_1.UseNativeColHeader()
        self.grid_2.UseNativeColHeader()
        self.grid_1.DisableDragRowSize()
        self.grid_2.DisableDragRowSize()
        self.fillDeviceGridHeaders()
        self.fillNetworkGridHeaders()

    @api_tool_decorator
    def fillDeviceGridHeaders(self):
        """ Populate Device Grid Headers """
        num = 0
        headerLabels = Globals.CSV_TAG_ATTR_NAME.keys()
        try:
            for head in headerLabels:
                if head:
                    if self.grid_1.GetNumberCols() < len(headerLabels):
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
        headerLabels = Globals.CSV_NETWORK_ATTR_NAME.keys()
        try:
            for head in headerLabels:
                if head:
                    if self.grid_2.GetNumberCols() < len(headerLabels):
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
        self.grid_1.ClearGrid()
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
        self.grid_2.ClearGrid()
        if self.grid_2.GetNumberRows() > 0:
            self.grid_2.DeleteRows(0, self.grid_2.GetNumberRows())
        self.grid_2.SetScrollLineX(15)
        self.grid_2.SetScrollLineY(15)
        self.fillNetworkGridHeaders()
        Globals.grid2_lock.release()

    @api_tool_decorator
    def autoSizeGridsColumns(self):
        if not Globals.grid1_lock.locked():
            Globals.grid1_lock.acquire()
        if not Globals.grid2_lock.locked:
            Globals.grid2_lock.acquire()
        self.grid_1.AutoSizeColumns()
        self.grid_2.AutoSizeColumns()
        if Globals.grid1_lock.locked():
            Globals.grid1_lock.release()
        if Globals.grid2_lock.locked():
            Globals.grid2_lock.release()

    def onCellChange(self, event):
        """ Try to Auto size Columns on change """
        Globals.grid1_lock.acquire()
        self.userEdited.append((event.Row, event.Col))
        editor = self.grid_1.GetCellEditor(event.Row, event.Col)
        if not editor.IsCreated():
            self.grid_1.AutoSizeColumns()
        self.onCellEdit(event)
        Globals.grid1_lock.release()

    def onCellEdit(self, event):
        indx1 = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Tags")
        indx2 = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Alias")
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
                    key=lambda i: i[keyName],
                    reverse=self.deviceDescending,
                )
        self.parentFrame.Logging(
            "---> Sorting Device Grid on Column: %s Order: %s"
            % (keyName, "Descending" if self.deviceDescending else "Ascending")
        )
        self.parentFrame.setGaugeValue(0)
        self.emptyDeviceGrid(emptyContents=False)
        num = 1
        for device in self.grid_1_contents:
            self.addDeviceToDeviceGrid(device)
            self.parentFrame.setGaugeValue(int(num / len(self.grid_1_contents) * 100))
            num += 1
        self.grid_1.AutoSizeColumns()
        self.grid_1.MakeCellVisible(0, col)
        self.parentFrame.onSearch(self.parentFrame.frame_toolbar.search.GetValue())
        wx.CallLater(3000, self.parentFrame.setGaugeValue, 0)

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
                key=lambda i: i[keyName],
                reverse=self.networkDescending,
            )
        self.parentFrame.Logging(
            "---> Sorting Network Grid on Column: %s Order: %s"
            % (keyName, "Descending" if self.networkDescending else "Ascending")
        )
        self.parentFrame.setGaugeValue(0)
        self.emptyNetworkGrid(emptyContents=False)
        num = 1
        for info in self.grid_2_contents:
            self.addToNetworkGrid(info)
            self.parentFrame.setGaugeValue(int(num / len(self.grid_2_contents) * 100))
            num += 1
        self.grid_2.AutoSizeColumns()
        self.grid_2.MakeCellVisible(0, col)
        self.parentFrame.onSearch(self.parentFrame.frame_toolbar.search.GetValue())
        wx.CallLater(3000, self.parentFrame.setGaugeValue, 0)

    def toogleViewMenuItem(self, event):
        """
        Disable native headers ability to hide columns when clicking an entry from the context menu
        """
        return

    def onGridMotion(self, event):
        indx1 = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Tags")
        indx2 = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Alias")
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

    def applyTextColorMatchingGridRow(self, grid, query, bgColor, applyAll=False):
        """ Apply a Text or Bg Color to a Grid Row """
        statusIndex = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Status")
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

    def onDeviceColumn(self, event):
        headerLabels = list(Globals.CSV_TAG_ATTR_NAME.keys())
        if "Esper Name" in headerLabels:
            headerLabels.remove("Esper Name")
        if "Device Name" in headerLabels:
            headerLabels.remove("Device Name")

        with ColumnVisibilityDialog(self.grid_1, choiceData=headerLabels) as dialog:
            if dialog.ShowModal() == wx.ID_APPLY:
                colNum = 0
                for _ in headerLabels:
                    self.toggleColVisibilityInGridOne(
                        colNum + 1, showState=dialog.isChecked(colNum)
                    )
                    colNum += 1

    def onNetworkColumn(self, event):
        headerLabels = list(Globals.CSV_NETWORK_ATTR_NAME.keys())
        if "Esper Name" in headerLabels:
            headerLabels.remove("Esper Name")
        if "Device Name" in headerLabels:
            headerLabels.remove("Device Name")

        with ColumnVisibilityDialog(self.grid_2, choiceData=headerLabels) as dialog:
            if dialog.ShowModal() == wx.ID_APPLY:
                colNum = 0
                for _ in headerLabels:
                    self.toggleColVisibilityInGridTwo(
                        colNum + 1, showState=dialog.isChecked(colNum)
                    )
                    colNum += 1

    @api_tool_decorator
    def addDeviceToDeviceGrid(self, device_info, isUpdate=False):
        """ Add device info to Device Grid """
        Globals.grid1_lock.acquire()
        self.grid_1.Enable(False)
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
                            indx = list(Globals.CSV_TAG_ATTR_NAME.keys()).index(
                                attribute
                            )
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
        self.grid_1.Enable(True)
        Globals.grid1_lock.release()

    def setStatusCellColor(self, value, rowNum, colNum):
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

    def setAlteredCellColor(self, grid, device_info, rowNum, attribute, indx):
        if attribute == "Alias" and "OriginalAlias" in device_info:
            grid.SetCellBackgroundColour(rowNum, indx, Color.lightBlue.value)
            pass
        if attribute == "Tags" and "OriginalTags" in device_info:
            grid.SetCellBackgroundColour(rowNum, indx, Color.lightBlue.value)
            pass

    @api_tool_decorator
    def addDeviceToNetworkGrid(self, device, deviceInfo, isUpdate=False):
        """ Construct network info and add to grid """
        Globals.grid2_lock.acquire()
        networkInfo = constructNetworkInfo(device, deviceInfo)
        self.addToNetworkGrid(networkInfo, isUpdate, device_info=deviceInfo)
        Globals.grid2_lock.release()

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
                            indx = list(Globals.CSV_NETWORK_ATTR_NAME.keys()).index(
                                attribute
                            )
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
        # self.grid_2.AutoSizeColumns()

    def applyTextColorToDevice(self, device, color, bgColor=None, applyAll=False):
        """ Apply a Text or Bg Color to a Grid Row """
        Globals.grid1_lock.acquire()
        statusIndex = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Status")
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
        en_indx = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Esper Name")
        sn_indx = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Serial Number")
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, en_indx)
                serialNum = self.grid_1.GetCellValue(rowNum, sn_indx)
                indx = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Tags")
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
                elif serialNum:
                    tagList[serialNum] = properTagList
        Globals.grid1_lock.release()
        return tagList

    @api_tool_decorator
    def getDeviceAliasFromGrid(self):
        """ Return a list of Aliases from the Grid """
        Globals.grid1_lock.acquire()
        aliasList = {}
        indx = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Alias")
        en_indx = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Esper Name")
        sn_indx = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Serial Number")
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, en_indx)
                serialNum = self.grid_1.GetCellValue(rowNum, sn_indx)
                alias = self.grid_1.GetCellValue(rowNum, indx)
                if esperName and esperName not in aliasList.keys():
                    aliasList[esperName] = alias
                elif serialNum and serialNum not in aliasList.keys():
                    aliasList[serialNum] = alias
        Globals.grid1_lock.release()
        return aliasList

    def getDeviceAliasFromList(self):
        aliasList = {}
        if self.grid_1_contents:
            for device in self.grid_1_contents:
                if device["EsperName"] not in aliasList:
                    aliasList[device["EsperName"]] = device["Alias"]
        else:
            aliasList = self.getDeviceAliasFromGrid()
        return aliasList

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
        Globals.grid1_lock.acquire()
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
                        indx = list(Globals.CSV_TAG_ATTR_NAME.keys()).index("Tags")
                        if not all("" == s or s.isspace() for s in tags):
                            self.grid_1.SetCellValue(rowNum, indx, str(tags))
                        else:
                            self.grid_1.SetCellValue(rowNum, indx, "")
        Globals.grid1_lock.release()
