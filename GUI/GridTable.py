import platform
import threading
from datetime import datetime
from distutils.version import LooseVersion

import pandas as pd
import wx
import wx.grid as gridlib
from pandas.api.types import is_bool_dtype, is_string_dtype

import Common.Globals as Globals
from Common.decorator import api_tool_decorator
from Common.enum import Color
from GUI.GridDataTable import GridDataTable
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Resource import determineDoHereorMainThread, getStrRatioSimilarity


class GridTable(gridlib.Grid):
    def __init__(self, parent, data=None, headers=[]):
        gridlib.Grid.__init__(self, parent, wx.ID_ANY, size=(1, 1))

        self.headersLabels = headers
        self.disableProperties = False

        if data is None:
            data = self.createEmptyDataFrame()
        self.CreateGrid(len(data), len(data.columns))
        self.applyNewDataFrame(
            data, checkColumns=False, autosize=True, resetPosition=True
        )

        self.sortedColumn = None
        self.sortAcesnding = True
        self.currentlySelectedCell = []

    def createEmptyDataFrame(self):
        df = pd.DataFrame(columns=self.headersLabels)
        for col in self.headersLabels:
            df[col] = df[col].astype("string")
        df.index = pd.RangeIndex(start=0, stop=len(df.index) * 1 - 1, step=1)
        return df

    def convertColumnTypes(self, data):
        for col in self.headersLabels:
            if len(data[col]) > 0:
                if col in Globals.DATE_COL:
                    data[col] = pd.to_datetime(data[col], exact=False, errors="coerce")
                    data[col] = data[col].dt.strftime(Globals.DATE_COL[col])
                    data[col].fillna("No Data Available", inplace=True)
                elif is_bool_dtype(data[col]):
                    data[col] = data[col].astype("bool")
                elif is_string_dtype(data[col]) and all(data[col].str.isnumeric()):
                    data[col] = data[col].astype("int64")
                else:
                    data[col] = data[col].astype("string")
        return data

    def ApplyGridStyle(self, autosize=False, resetPosition=False):
        if platform.system() == "Darwin" and "main" not in threading.current_thread().name.lower():
            determineDoHereorMainThread(self.ApplyGridStyle, autosize, resetPosition)
            return
        self.SetThemeEnabled(False)
        self.GetGridWindow().SetThemeEnabled(False)

        self.UseNativeColHeader()
        self.DisableDragRowSize()
        self.EnableDragColMove(True)
        self.SetLabelFont(
            wx.Font(
                Globals.FONT_SIZE,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "NormalBold",
            )
        )
        self.SetDefaultCellFont(
            wx.Font(
                Globals.FONT_SIZE,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "Normal",
            )
        )

        self.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.SortColumn)
        self.Bind(gridlib.EVT_GRID_LABEL_RIGHT_CLICK, self.toogleViewMenuItem)
        self.Bind(gridlib.EVT_GRID_SELECT_CELL, self.onSingleSelect)
        self.GetGridWindow().Bind(wx.EVT_KEY_DOWN, self.onKey)
        self.GetGridWindow().Bind(wx.EVT_MOTION, self.onGridMotion)

        self.SetStatusCellColor()
        if resetPosition:
            self.GoToCell(0, 0)
        if autosize:
            self.AutoSizeColumns()
            self.ForceRefresh()

    def applyNewDataFrame(
        self, data, checkColumns=True, autosize=False, resetPosition=False
    ):
        if platform.system() == "Darwin" and "main" not in threading.current_thread().name.lower():
            determineDoHereorMainThread(self.applyNewDataFrame, data, checkColumns, autosize, resetPosition)
            return

        try:
            self.SetCursor(wx.Cursor(wx.CURSOR_ARROWWAIT))
            self.Freeze()
            self.logToParentFrame("Loading Grid Data...")
            if data is None:
                data = self.createEmptyDataFrame()
            else:
                if checkColumns:
                    renameColumns = {}
                    matchingColumns = []
                    for column in data.columns:
                        for expectedCol in self.headersLabels:
                            if getStrRatioSimilarity(column, expectedCol) >= 95:
                                renameColumns[column] = expectedCol
                                matchingColumns.append(expectedCol)
                                break
                    missingColumns = list(
                        set(self.headersLabels) - set(matchingColumns)
                    )
                    for missingColumn in missingColumns:
                        data[missingColumn] = ""
                    data = data[list(self.headersLabels)]
                    data = data.rename(columns=renameColumns)

            self.convertColumnTypes(data)
            data.fillna("", inplace=True)
            self.table = GridDataTable(data)

            # The second parameter means that the grid is to take ownership of the
            # table and will destroy it when done.  Otherwise you would need to keep
            # a reference to it and call it's Destroy method later.
            self.SetTable(self.table, True)

            for header in self.headersLabels:
                isReadOnly = True
                if header in Globals.CSV_EDITABLE_COL:
                    isReadOnly = False
                editor = self.GetCellEditor(0, self.headersLabels.index(header))
                attr = gridlib.GridCellAttr()
                attr.SetReadOnly(isReadOnly)
                self.SetColAttr(self.headersLabels.index(header), attr)

            self.ApplyGridStyle(autosize=autosize, resetPosition=resetPosition)
        except Exception as e:
            ApiToolLog().LogError(e)
        finally:
            if self.IsFrozen():
                self.Thaw()
            self.SetCursor(wx.Cursor(wx.CURSOR_DEFAULT))
            self.logToParentFrame("Finished Loading Grid Data...")

    def SetCellValue(self, *args, **kw):
        return self.table.SetValue(*args, **kw)

    def EmptyGrid(self):
        data = self.createEmptyDataFrame()
        self.applyNewDataFrame(
            data, checkColumns=False, autosize=True, resetPosition=True
        )

    def SortColumn(self, event):
        col = None
        if hasattr(event, "Col"):
            col = event.Col
        else:
            col = event

        if col is not None and col >= 0:
            if self.sortedColumn != col:
                self.sortAcesnding = True
            else:
                self.sortAcesnding = not self.sortAcesnding
            self.sortedColumn = col
            self.SetSortingColumn(self.sortedColumn, self.sortAcesnding)
            colName = self.GetColLabelValue(col)
            self.logToParentFrame(
                'Sorting Grid on Column: "%s" Order: %s'
                % (colName, "Ascending" if self.sortAcesnding else "Descending")
            )
            if colName in Globals.SEMANTIC_VERSION_COL:
                try:
                    df = self.table.data.iloc[
                        self.table.data[colName].apply(LooseVersion).argsort()
                    ].reset_index(drop=True)

                    if not self.sortAcesnding:
                        df = df.iloc[::-1]
                except:
                    df = self.table.data.sort_values(colName, ascending=self.sortAcesnding)
            else:
                df = self.table.data.sort_values(colName, ascending=self.sortAcesnding)
            Globals.THREAD_POOL.enqueue(
                self.applyNewDataFrame, df, checkColumns=False, autosize=True
            )
            self.GoToCell(0, col)

    @api_tool_decorator()
    def toogleViewMenuItem(self, event):
        """
        Disable native headers ability to hide columns when clicking an entry from the context menu
        """
        return

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
        if (self.currentlySelectedCell 
            and self.currentlySelectedCell[0] >= 0 
            and self.currentlySelectedCell[1] >= 0):
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

    @api_tool_decorator()
    def onGridMotion(self, event):
        if self.disableProperties:
            event.Skip()
            return
        validIndexes = [
            self.headersLabels.index(col)
            for col in Globals.CSV_EDITABLE_COL
            if col in self.headersLabels
        ]

        grid_win = self.GetTargetWindow()

        x, y = self.CalcUnscrolledPosition(event.GetX(), event.GetY())
        coords = self.XYToCell(x, y)
        col = coords[1]

        if col in validIndexes:
            grid_win.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        elif Globals.frame.isBusy:
            self.setGridsCursor(wx.Cursor(wx.CURSOR_WAIT))
        else:
            self.setGridsCursor(wx.Cursor(wx.CURSOR_ARROW))
        event.Skip()

    def setGridsCursor(self, icon):
        grid_win = self.GetTargetWindow()
        grid_win.SetCursor(icon)

    @api_tool_decorator()
    def SetStatusCellColor(self):
        # Check to see if rows exsist
        numRows = self.GetNumberRows()
        if (
            numRows > 0
            and "Last Seen" in self.headersLabels
            and not Globals.frame.SpreadsheetUploaded
        ):
            colNum = self.headersLabels.index("Last Seen")
            currentDate = datetime.now()
            for rowNum in range(numRows):
                value = self.GetCellValue(rowNum, colNum)
                datePattern = "%Y-%m-%dT%H:%M:%S.%fZ" if "." in value else "%Y-%m-%dT%H:%MZ"
                parsedDateTime = None
                differenceInMinutes = None
                try:
                    parsedDateTime = datetime.strptime(value, datePattern) if "ago" not in value else None
                except:
                    pass
                if parsedDateTime:
                    differenceInMinutes = (currentDate - parsedDateTime).total_seconds() / 60
                if value == "Less than 1 minute ago":
                    self.SetCellTextColour(rowNum, colNum, Color.green.value)
                    self.SetCellBackgroundColour(rowNum, colNum, Color.lightGreen.value)
                elif " minutes ago" in value:
                    minutes = int(value.split(" ")[0])
                    if minutes < 30:
                        self.SetCellTextColour(rowNum, colNum, Color.green.value)
                        self.SetCellBackgroundColour(rowNum, colNum, Color.lightGreen.value)
                    else:
                        self.SetCellTextColour(rowNum, colNum, Color.orange.value)
                        self.SetCellBackgroundColour(rowNum, colNum, Color.lightYellow.value)
                elif " days ago" in value:
                    self.SetCellTextColour(rowNum, colNum, Color.red.value)
                    self.SetCellBackgroundColour(rowNum, colNum, Color.lightRed.value)
                elif differenceInMinutes and differenceInMinutes < 30:
                    self.SetCellTextColour(rowNum, colNum, Color.green.value)
                    self.SetCellBackgroundColour(rowNum, colNum, Color.lightGreen.value)
                elif differenceInMinutes and differenceInMinutes < 1440:
                    self.SetCellTextColour(rowNum, colNum, Color.orange.value)
                    self.SetCellBackgroundColour(rowNum, colNum, Color.lightYellow.value)
                elif differenceInMinutes and differenceInMinutes > 1440:
                    self.SetCellTextColour(rowNum, colNum, Color.red.value)
                    self.SetCellBackgroundColour(rowNum, colNum, Color.lightRed.value)

    def logToParentFrame(self, msg, isError=False):
        if Globals.frame and hasattr(Globals.frame, "Logging"):
            Globals.frame.Logging(msg, isError=isError)

    def onSingleSelect(self, event):
        """
        Get the selection of a single cell by clicking or
        moving the selection with the arrow keys
        """
        self.currentlySelectedCell = (event.GetRow(), event.GetCol())
        event.Skip()

    @api_tool_decorator()
    def SetCellTextColour(self, rowNum, colNum, color):
        if platform.system() == "Darwin" and "main" not in threading.current_thread().name.lower():
            determineDoHereorMainThread(super().SetCellTextColour, rowNum, colNum, color)
            return
        super().SetCellTextColour(rowNum, colNum, color)

    @api_tool_decorator()
    def SetCellBackgroundColour(self, rowNum, colNum, color):
        if platform.system() == "Darwin" and "main" not in threading.current_thread().name.lower():
            determineDoHereorMainThread(super().SetCellBackgroundColour, rowNum, colNum, color)
            return
        super().SetCellBackgroundColour(rowNum, colNum, color)

    @api_tool_decorator()
    def ForceRefresh(self):
        if platform.system() == "Darwin" and "main" not in threading.current_thread().name.lower():
            determineDoHereorMainThread(super().ForceRefresh)
            return
        return super().ForceRefresh()

    @api_tool_decorator()
    def AutoSizeColumns(self, setAsMin=True):
        if platform.system() == "Darwin" and "main" not in threading.current_thread().name.lower():
            determineDoHereorMainThread(super().AutoSizeColumns, setAsMin)
            return
        return super().AutoSizeColumns(setAsMin)