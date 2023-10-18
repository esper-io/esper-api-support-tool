#!/usr/bin/env python

import re

import wx
import wx.grid as gridlib

import Common.Globals as Globals
from GUI.GridTable import GridTable
import Utility.EventUtility as eventUtil
from Common.decorator import api_tool_decorator
from Common.enum import Color
from GUI.Dialogs.ColumnVisibility import ColumnVisibility
from Utility.Resource import (
    acquireLocks,
    checkIfCurrentThreadStopped,
    determineDoHereorMainThread,
    postEventToFrame,
    releaseLocks,
    resourcePath,
    scale_bitmap,
)


class GridPanel(wx.Panel):
    def __init__(self, parentFrame, *args, **kw):
        super().__init__(*args, **kw)

        self.userEdited = []
        self.grid_1_contents = None
        self.grid_2_contents = None
        self.grid_3_contents = None
        self.disableProperties = False

        self.parentFrame = parentFrame
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
        self.notebook_2.SetThemeEnabled(False)
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

        self.grid_1 = GridTable(self.panel_14, headers=self.grid1HeaderLabels)
        sizer_6.Add(self.grid_1, 1, wx.EXPAND, 0)

        self.panel_15 = wx.Panel(self.notebook_2, wx.ID_ANY)
        self.notebook_2.AddPage(self.panel_15, "Network Information")

        sizer_7 = wx.BoxSizer(wx.VERTICAL)
        self.grid_2 = GridTable(self.panel_15, headers=self.grid2HeaderLabels)
        sizer_7.Add(self.grid_2, 1, wx.EXPAND, 0)

        self.panel_16 = wx.Panel(self.notebook_2, wx.ID_ANY)
        self.notebook_2.AddPage(self.panel_16, "Application Information")

        sizer_8 = wx.BoxSizer(wx.VERTICAL)

        self.grid_3 = GridTable(self.panel_16, headers=self.grid3HeaderLabels)
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
        self.SetThemeEnabled(False)
        self.grid_1.Bind(gridlib.EVT_GRID_CELL_CHANGED, self.onCellChange)

        self.grid_1.Bind(gridlib.EVT_GRID_SELECT_CELL, self.onSingleSelect)
        self.grid_2.Bind(gridlib.EVT_GRID_SELECT_CELL, self.onSingleSelect)
        self.grid_3.Bind(gridlib.EVT_GRID_SELECT_CELL, self.onSingleSelect)

        self.enableGridProperties()

    @api_tool_decorator(
        locks=[Globals.grid1_lock, Globals.grid2_lock, Globals.grid3_lock]
    )
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
            determineDoHereorMainThread(self.grid_1.AutoSizeColumns)
        self.onCellEdit(event)
        releaseLocks([Globals.grid1_lock])

    @api_tool_decorator()
    def onCellEdit(self, event):
        indx1 = self.grid1HeaderLabels.index("Tags")
        indx2 = self.grid1HeaderLabels.index("Alias")
        indx3 = self.grid1HeaderLabels.index("Group")
        x, y = self.grid_1.GetGridCursorCoords()
        esperName = self.grid_1.GetCellValue(x, 0)
        originalListing = self.grid_1_contents.loc[
            self.grid_1_contents["Esper Name"] == esperName
        ].values.tolist()
        deviceListing = self.grid_1.Table.data.loc[
            self.grid_1_contents["Esper Name"] == esperName
        ].values.tolist()
        if originalListing and deviceListing:
            self.onCellEditHelper(deviceListing[0], originalListing[0], indx1, x, y)
            self.onCellEditHelper(deviceListing[0], originalListing[0], indx2, x, y)
            self.onCellEditHelper(deviceListing[0], originalListing[0], indx3, x, y)
        event.Skip()

    def onCellEditHelper(self, deviceListing, originalListing, indx, x, y):
        deviceValue = deviceListing[indx]
        originalValue = originalListing[indx]
        if y == indx:
            if deviceValue == originalValue:
                self.grid_1.SetCellBackgroundColour(x, y, Color.white.value)
            else:
                self.grid_1.SetCellBackgroundColour(x, y, Color.lightBlue.value)

    @api_tool_decorator()
    def applyTextColorMatchingGridRow(self, grid, query, bgColor, applyAll=False):
        """ Apply a Text or Bg Color to a Grid Row """
        for rowNum in range(grid.GetNumberRows()):
            if checkIfCurrentThreadStopped():
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
            "Application": self.grid_3,
        }
        exemptedLabels = ["Esper Name", "Esper Id", "Device Name"]
        colLabelException = {
            "Device": exemptedLabels,
            "Network": exemptedLabels,
            "Application": exemptedLabels,
        }

        with ColumnVisibility(self, pageGridDict, colLabelException) as dialog:
            Globals.OPEN_DIALOGS.append(dialog)
            res = dialog.ShowModal()
            Globals.OPEN_DIALOGS.remove(dialog)
            if res == wx.ID_APPLY:
                selected = dialog.getSelected()
                for page in pageGridDict.keys():
                    for label, isChecked in selected[page].items():
                        if page == "Device":
                            indx = list(Globals.CSV_TAG_ATTR_NAME.keys()).index(label)
                            self.toggleColVisibilityInGrid(
                                indx,
                                self.grid_1,
                                Globals.grid1_lock,
                                showState=isChecked
                            )
                            self.grid1ColVisibility[label] = isChecked
                        elif page == "Network":
                            indx = list(Globals.CSV_NETWORK_ATTR_NAME.keys()).index(
                                label
                            )
                            self.toggleColVisibilityInGrid(
                                indx,
                                self.grid_2,
                                Globals.grid2_lock,
                                showState=isChecked
                            )
                            self.grid2ColVisibility[label] = isChecked
                        elif page == "Application":
                            indx = Globals.CSV_APP_ATTR_NAME.index(label)
                            self.toggleColVisibilityInGrid(
                                indx,
                                self.grid_3,
                                Globals.grid3_lock,
                                showState=isChecked
                            )
                            self.grid3ColVisibility[label] = isChecked

        self.parentFrame.prefDialog.colVisibilty = (
            self.grid1ColVisibility,
            self.grid2ColVisibility,
            self.grid3ColVisibility,
        )

    def setColVisibility(self):
        grid1Cols = self.grid1ColVisibility.keys()
        grid2Cols = self.grid2ColVisibility.keys()
        grid3Cols = self.grid3ColVisibility.keys()
        for col in grid1Cols:
            if col in self.grid1HeaderLabels:
                indx = self.grid1HeaderLabels.index(col)
                self.toggleColVisibilityInGrid(
                    indx,
                    self.grid_1,
                    Globals.grid1_lock,
                    showState=self.grid1ColVisibility[col]
                )
        for col in grid2Cols:
            if col in self.grid2HeaderLabels:
                indx = self.grid2HeaderLabels.index(col)
                self.toggleColVisibilityInGrid(
                    indx,
                    self.grid_2,
                    Globals.grid2_lock,
                    showState=self.grid2ColVisibility[col]
                )
        for col in grid3Cols:
            if col in self.grid3HeaderLabels:
                indx = self.grid3HeaderLabels.index(col)
                self.toggleColVisibilityInGrid(
                    indx,
                    self.grid_3,
                    Globals.grid3_lock,
                    showState=self.grid3ColVisibility[col]
                )

    @api_tool_decorator()
    def setAlteredCellColor(self, grid, device_info, rowNum, attribute, indx):
        if (
            attribute == "Alias"
            and "OriginalAlias" in device_info
            and device_info["Alias"] != device_info["OriginalAlias"]
        ) or (
            attribute == "Tags"
            and "OriginalTags" in device_info
            and device_info["Tags"] != device_info["OriginalTags"]
        ):
            postEventToFrame(
                eventUtil.myEVT_PROCESS_FUNCTION,
                (grid.SetCellBackgroundColour, (rowNum, indx, Color.lightBlue.value)),
            )

    @api_tool_decorator(locks=[Globals.grid1_lock])
    def applyTextColorToDevice(self, device, color, bgColor=None, applyAll=False):
        """ Apply a Text or Bg Color to a Grid Row """
        acquireLocks([Globals.grid1_lock])
        statusIndex = self.grid1HeaderLabels.index("Status")
        deviceName = ""
        if device:
            deviceName = (
                device.device_name
                if hasattr(device, "device_name")
                else device["device_name"]
                if type(device) is dict
                else ""
            )
        for rowNum in range(self.grid_1.GetNumberRows()):
            if rowNum < self.grid_1.GetNumberRows():
                esperName = self.grid_1.GetCellValue(rowNum, 0)
                id_index = self.grid1HeaderLabels.index("Esper Id")
                esperId = self.grid_1.GetCellValue(rowNum, id_index)
                if (
                    device and (esperName == deviceName or esperId == device)
                ) or applyAll:
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

    @api_tool_decorator()
    def getDeviceTagsFromGrid(self):
        """ Return the tags from Grid """
        if len(self.grid_1_contents) > 0:
            columns = [
                "Esper Name",
                "Tags",
                "Esper Id",
                "IMEI 1",
                "IMEI 2",
                "Serial Number",
                "Custom Serial Number"
            ]
            return self.getDeviceRowsSpecificCols(columns)
        return []

    @api_tool_decorator()
    def getDeviceAliasFromList(self):
        if len(self.grid_1_contents) > 0:
            columns = [
                "Esper Name",
                "Alias",
                "Esper Id",
                "IMEI 1",
                "IMEI 2",
                "Serial Number",
                "Custom Serial Number"
            ]
            return self.getDeviceRowsSpecificCols(columns)
        return []

    def getDeviceRowsSpecificCols(self, columns) -> list:
        returnList = []
        deviceName_identifers = self.grid_1.Table.data[columns].values.tolist()
        for row in deviceName_identifers:
            entry = {}
            for col in columns:
                if col == "Tags":
                    properTagList = []
                    for r in re.findall(
                        r"\".+?\"|\'.+?\'|\’.+?\’|[\w\d '-+\\/^%$#!@$%^&:.!?\-{}\<\>;]+",
                        row[columns.index(col)],
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
                            properTagList = properTagList[0 : Globals.MAX_TAGS]
                        entry[col] = properTagList
                else:
                    entry[col] = row[columns.index(col)]
            returnList.append(entry)
        return returnList

    @api_tool_decorator(locks=[Globals.grid1_lock, Globals.grid2_lock, Globals.grid3_lock])
    def toggleColVisibilityInGrid(self, event, grid, lock, showState=None):
        """ Toggle Column Visibility in Device Grid """
        acquireLocks([lock])
        index = None
        if isinstance(event, (int, float, complex)) and not isinstance(event, bool):
            index = event
        if index and index < grid.GetNumberCols():
            if type(showState) == bool:
                if not showState:
                    grid.HideCol(index)
                else:
                    grid.ShowCol(index)
            else:
                isShown = grid.IsColShown(index)
                if isShown:
                    grid.HideCol(index)
                else:
                    grid.ShowCol(index)
        releaseLocks([lock])

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
        self.grid_1.disableProperties = True
        self.grid_2.disableProperties = True
        self.grid_3.disableProperties = True
        releaseLocks([Globals.grid1_lock, Globals.grid2_lock])

    @api_tool_decorator(
        locks=[Globals.grid1_lock, Globals.grid2_lock, Globals.grid3_lock]
    )
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
        self.grid_1.disableProperties = self.disableProperties
        self.grid_2.disableProperties = self.disableProperties
        self.grid_3.disableProperties = self.disableProperties
        releaseLocks([Globals.grid1_lock, Globals.grid2_lock, Globals.grid3_lock])

    @api_tool_decorator()
    def getDeviceIdentifersFromGrid(self, tolerance=0):
        if len(self.grid_1_contents) > 0:
            columns = [
                "Esper Name",
                "Esper Id",
                "IMEI 1",
                "IMEI 2",
                "Serial Number",
                "Custom Serial Number"
            ]
            return self.getDeviceRowsSpecificCols(columns)
        return []

    def updateGridContent(self, event):
        evtVal = event.GetValue()
        if self.grid_1_contents:
            device = evtVal[0]
            modified = evtVal[1]
            deviceListing = list(
                filter(
                    lambda x: (
                        x[Globals.CSV_TAG_ATTR_NAME["Esper Name"]] == device.device_name
                        if hasattr(device, "device_name")
                        else device["device_name"]
                        if type(device) is dict
                        else device
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
            if self.parentFrame and hasattr(self.parentFrame, "fetchData"):
                self.parentFrame.fetchData(False)
        event.Skip()

    def incrementOffset(self, event):
        if not self.parentFrame.isRunning:
            Globals.offset = Globals.offset + Globals.limit
            if self.parentFrame and hasattr(self.parentFrame, "fetchData"):
                self.parentFrame.fetchData(False)
        event.Skip()

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
        if len(self.grid_1_contents) > 0:
            columns = [
                "Esper Name",
                "Esper Id",
                "Group",
                "IMEI 1",
                "IMEI 2",
                "Serial Number",
                "Custom Serial Number"
            ]
            return self.getDeviceRowsSpecificCols(columns)
        return []

    def thawGridsIfFrozen(self):
        if self.grid_1.IsFrozen():
            self.grid_1.Thaw()
        if self.grid_2.IsFrozen():
            self.grid_2.Thaw()
        if self.grid_3.IsFrozen():
            self.grid_3.Thaw()

    def freezeGrids(self):
        self.grid_1.Freeze()
        self.grid_2.Freeze()
        self.grid_3.Freeze()

    def EmptyGrids(self):
        Globals.frame.SpreadsheetUploaded = False
        self.grid_1.EmptyGrid()
        self.grid_2.EmptyGrid()
        self.grid_3.EmptyGrid()
        self.userEdited = []
        self.grid_1_contents = None
        self.grid_2_contents = None
        self.grid_3_contents = None

    def UnsetSortingColumns(self):
        self.grid_1.UnsetSortingColumn()
        self.grid_2.UnsetSortingColumn()
        self.grid_3.UnsetSortingColumn()
