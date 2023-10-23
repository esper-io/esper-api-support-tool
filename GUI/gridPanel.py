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
from Utility.GridUtilities import areDataFramesTheSame
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
        self.device_grid_contents = None
        self.network_grid_contents = None
        self.app_grid_contents = None
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

        self.device_grid = GridTable(self.panel_14, headers=self.grid1HeaderLabels)
        sizer_6.Add(self.device_grid, 1, wx.EXPAND, 0)

        self.panel_15 = wx.Panel(self.notebook_2, wx.ID_ANY)
        self.notebook_2.AddPage(self.panel_15, "Network Information")

        sizer_7 = wx.BoxSizer(wx.VERTICAL)
        self.network_grid = GridTable(self.panel_15, headers=self.grid2HeaderLabels)
        sizer_7.Add(self.network_grid, 1, wx.EXPAND, 0)

        self.panel_16 = wx.Panel(self.notebook_2, wx.ID_ANY)
        self.notebook_2.AddPage(self.panel_16, "Application Information")

        sizer_8 = wx.BoxSizer(wx.VERTICAL)

        self.app_grid = GridTable(self.panel_16, headers=self.grid3HeaderLabels)
        sizer_8.Add(self.app_grid, 1, wx.EXPAND, 0)

        self.panel_16.SetSizer(sizer_8)

        self.panel_15.SetSizer(sizer_7)

        self.panel_14.SetSizer(sizer_6)

        grid_sizer_2.AddGrowableRow(1)
        grid_sizer_2.AddGrowableCol(0)
        self.SetSizer(grid_sizer_2)

        self.Layout()

        self.__set_properties()

    @api_tool_decorator()
    def __set_properties(self):
        self.SetThemeEnabled(False)
        self.device_grid.Bind(gridlib.EVT_GRID_CELL_CHANGED, self.onCellChange)

        self.device_grid.Bind(gridlib.EVT_GRID_SELECT_CELL, self.onSingleSelect)
        self.network_grid.Bind(gridlib.EVT_GRID_SELECT_CELL, self.onSingleSelect)
        self.app_grid.Bind(gridlib.EVT_GRID_SELECT_CELL, self.onSingleSelect)

        self.enableGridProperties()

    @api_tool_decorator(
        locks=[Globals.grid1_lock, Globals.grid2_lock, Globals.grid3_lock]
    )
    def autoSizeGridsColumns(self, event=None):
        acquireLocks([Globals.grid1_lock, Globals.grid2_lock, Globals.grid3_lock])
        self.device_grid.AutoSizeColumns()
        self.network_grid.AutoSizeColumns()
        self.app_grid.AutoSizeColumns()
        self.device_grid.ForceRefresh()
        self.network_grid.ForceRefresh()
        self.app_grid.ForceRefresh()
        releaseLocks([Globals.grid1_lock, Globals.grid2_lock, Globals.grid3_lock])

    @api_tool_decorator(locks=[Globals.grid1_lock])
    def onCellChange(self, event):
        """ Try to Auto size Columns on change """
        acquireLocks([Globals.grid1_lock])
        self.userEdited.append((event.Row, event.Col))
        editor = self.device_grid.GetCellEditor(event.Row, event.Col)
        if not editor.IsCreated():
            determineDoHereorMainThread(self.device_grid.AutoSizeColumns)
        self.onCellEdit(event)
        releaseLocks([Globals.grid1_lock])

    @api_tool_decorator()
    def onCellEdit(self, event):
        indx1 = self.grid1HeaderLabels.index("Tags")
        indx2 = self.grid1HeaderLabels.index("Alias")
        indx3 = self.grid1HeaderLabels.index("Group")
        x, y = self.device_grid.GetGridCursorCoords()
        esperName = self.device_grid.GetCellValue(x, 0)
        originalListing = self.device_grid_contents.loc[
            self.device_grid_contents["Esper Name"] == esperName
        ].values.tolist()
        deviceListing = self.device_grid.Table.data.loc[
            self.device_grid_contents["Esper Name"] == esperName
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
                self.device_grid.SetCellBackgroundColour(x, y, Color.white.value)
            else:
                self.device_grid.SetCellBackgroundColour(x, y, Color.lightBlue.value)

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
                        if colNum < grid.GetNumberCols() and (
                            grid.GetCellBackgroundColour(rowNum, colNum)
                            == Color.white.value
                            or (
                                applyAll
                                and grid.GetCellBackgroundColour(rowNum, colNum)
                                == Color.lightYellow.value
                            )
                        ):
                            grid.SetCellBackgroundColour(rowNum, colNum, bgColor)
        grid.ForceRefresh()

    @api_tool_decorator()
    def onColumnVisibility(self, event):
        pageGridDict = {
            "Device": self.device_grid,
            "Network": self.network_grid,
            "Application": self.app_grid,
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
                                self.device_grid,
                                Globals.grid1_lock,
                                showState=isChecked,
                            )
                            self.grid1ColVisibility[label] = isChecked
                        elif page == "Network":
                            indx = list(Globals.CSV_NETWORK_ATTR_NAME.keys()).index(
                                label
                            )
                            self.toggleColVisibilityInGrid(
                                indx,
                                self.network_grid,
                                Globals.grid2_lock,
                                showState=isChecked,
                            )
                            self.grid2ColVisibility[label] = isChecked
                        elif page == "Application":
                            indx = Globals.CSV_APP_ATTR_NAME.index(label)
                            self.toggleColVisibilityInGrid(
                                indx,
                                self.app_grid,
                                Globals.grid3_lock,
                                showState=isChecked,
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
                    self.device_grid,
                    Globals.grid1_lock,
                    showState=self.grid1ColVisibility[col],
                )
        for col in grid2Cols:
            if col in self.grid2HeaderLabels:
                indx = self.grid2HeaderLabels.index(col)
                self.toggleColVisibilityInGrid(
                    indx,
                    self.network_grid,
                    Globals.grid2_lock,
                    showState=self.grid2ColVisibility[col],
                )
        for col in grid3Cols:
            if col in self.grid3HeaderLabels:
                indx = self.grid3HeaderLabels.index(col)
                self.toggleColVisibilityInGrid(
                    indx,
                    self.app_grid,
                    Globals.grid3_lock,
                    showState=self.grid3ColVisibility[col],
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
        for rowNum in range(self.device_grid.GetNumberRows()):
            if rowNum < self.device_grid.GetNumberRows():
                esperName = self.device_grid.GetCellValue(rowNum, 0)
                id_index = self.grid1HeaderLabels.index("Esper Id")
                esperId = self.device_grid.GetCellValue(rowNum, id_index)
                if (
                    device and (esperName == deviceName or esperId == device)
                ) or applyAll:
                    for colNum in range(self.device_grid.GetNumberCols()):
                        if (
                            colNum < self.device_grid.GetNumberCols()
                            and colNum != statusIndex
                        ):
                            self.device_grid.SetCellTextColour(rowNum, colNum, color)
                            if bgColor:
                                self.device_grid.SetCellBackgroundColour(
                                    rowNum, colNum, bgColor
                                )
        self.device_grid.ForceRefresh()
        releaseLocks([Globals.grid1_lock])

    @api_tool_decorator()
    def getDeviceTagsFromGrid(self):
        """ Return the tags from Grid """
        if len(self.device_grid_contents) > 0:
            columns = [
                "Esper Name",
                "Tags",
                "Esper Id",
                "IMEI 1",
                "IMEI 2",
                "Serial Number",
                "Custom Serial Number",
            ]
            return self.getDeviceRowsSpecificCols(columns)
        return []

    @api_tool_decorator()
    def getDeviceAliasFromList(self):
        if len(self.device_grid_contents) > 0:
            columns = [
                "Esper Name",
                "Alias",
                "Esper Id",
                "IMEI 1",
                "IMEI 2",
                "Serial Number",
                "Custom Serial Number",
            ]
            return self.getDeviceRowsSpecificCols(columns)
        return []

    def getDeviceRowsSpecificCols(self, columns) -> list:
        returnList = []
        deviceName_identifers = self.device_grid.Table.data[columns].values.tolist()
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
                    entry[col] = row[columns.index(col)].strip()
            returnList.append(entry)
        return returnList

    @api_tool_decorator(
        locks=[Globals.grid1_lock, Globals.grid2_lock, Globals.grid3_lock]
    )
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
            self.device_grid.Enable(False)
            self.network_grid.Enable(False)
        if disableColSize:
            self.device_grid.DisableDragColSize()
            self.network_grid.DisableDragColSize()
        if disableColMove:
            self.device_grid.DisableDragColMove()
            self.network_grid.DisableDragColMove()
        self.disableProperties = True
        self.device_grid.disableProperties = True
        self.network_grid.disableProperties = True
        self.app_grid.disableProperties = True
        releaseLocks([Globals.grid1_lock, Globals.grid2_lock])

    @api_tool_decorator(
        locks=[Globals.grid1_lock, Globals.grid2_lock, Globals.grid3_lock]
    )
    def enableGridProperties(
        self, enableGrid=True, enableColSize=True, enableColMove=True
    ):
        acquireLocks([Globals.grid1_lock, Globals.grid2_lock, Globals.grid3_lock])
        if enableGrid:
            self.device_grid.Enable(True)
            self.network_grid.Enable(True)
            self.app_grid.Enable(True)
        if enableColSize:
            self.device_grid.EnableDragColSize()
            self.network_grid.EnableDragColSize()
            self.app_grid.EnableDragColSize()
        if enableColMove:
            self.device_grid.EnableDragColMove()
            self.network_grid.EnableDragColMove()
            self.app_grid.EnableDragColMove()
        self.disableProperties = False
        self.device_grid.disableProperties = self.disableProperties
        self.network_grid.disableProperties = self.disableProperties
        self.app_grid.disableProperties = self.disableProperties
        releaseLocks([Globals.grid1_lock, Globals.grid2_lock, Globals.grid3_lock])

    @api_tool_decorator()
    def getDeviceIdentifersFromGrid(self, tolerance=0):
        if len(self.device_grid_contents) > 0:
            columns = [
                "Esper Name",
                "Esper Id",
                "IMEI 1",
                "IMEI 2",
                "Serial Number",
                "Custom Serial Number",
            ]
            return self.getDeviceRowsSpecificCols(columns)
        return []

    def updateGridContent(self, event):
        evtVal = event.GetValue()
        if self.device_grid_contents:
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
                    self.device_grid_contents,
                )
            )
            for listing in deviceListing:
                indx = self.device_grid_contents.index(listing)
                if modified == "alias":
                    listing["OriginalAlias"] = listing["Alias"]
                elif modified == "tags":
                    listing["OriginalTags"] = listing["Tags"]
                self.device_grid_contents[indx] = listing

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
            grid1Sizes = self.device_grid.GetColSizes()
            grid2Sizes = self.network_grid.GetColSizes()
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
        if len(self.device_grid_contents) > 0:
            columns = [
                "Esper Name",
                "Esper Id",
                "Group",
                "IMEI 1",
                "IMEI 2",
                "Serial Number",
                "Custom Serial Number",
            ]
            return self.getDeviceRowsSpecificCols(columns)
        return []

    def thawGridsIfFrozen(self):
        if self.device_grid.IsFrozen():
            self.device_grid.Thaw()
        if self.network_grid.IsFrozen():
            self.network_grid.Thaw()
        if self.app_grid.IsFrozen():
            self.app_grid.Thaw()

    def freezeGrids(self):
        self.device_grid.Freeze()
        self.network_grid.Freeze()
        self.app_grid.Freeze()

    def EmptyGrids(self):
        Globals.frame.SpreadsheetUploaded = False
        self.device_grid.EmptyGrid()
        self.network_grid.EmptyGrid()
        self.app_grid.EmptyGrid()
        self.userEdited = []
        self.device_grid_contents = None
        self.network_grid_contents = None
        self.app_grid_contents = None

    def UnsetSortingColumns(self):
        self.device_grid.UnsetSortingColumn()
        self.network_grid.UnsetSortingColumn()
        self.app_grid.UnsetSortingColumn()

    def setGridsCursor(self, cursorType):
        self.device_grid.SetCursor(cursorType)
        self.network_grid.SetCursor(cursorType)
        self.app_grid.SetCursor(cursorType)

    def getGridDataForSave(self):
        deviceData = networkData = appData = None
        deviceData = self.__getGridDataForSaveHelper__(self.device_grid, self.device_grid_contents)
        networkData = self.__getGridDataForSaveHelper__(self.network_grid, self.network_grid_contents)
        appData = self.__getGridDataForSaveHelper__(self.app_grid, self.app_grid_contents)
        return deviceData, networkData, appData

    def __getGridDataForSaveHelper__(self, grid, content):
        data = None
        if ((content is not None 
            and grid.Table.data is not None
            and areDataFramesTheSame(content, grid.Table.data))
            or (content is not None 
                and (grid.Table.data is None
                     or len(grid.Table.data) == 0))):
            data = content
        elif ((content is None 
               or len(content) == 0)
            and grid.Table.data is not None):
            data = grid.Table.data
        return data
    
    def forceRefreshGrids(self):
        self.device_grid.ForceRefresh()
        self.network_grid.ForceRefresh()
        self.app_grid.ForceRefresh()
