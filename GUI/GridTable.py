import pandas as pd
import wx
import wx.grid as gridlib
import Common.Globals as Globals
from Common.decorator import api_tool_decorator

from GUI.GridDataTable import GridDataTable
from Utility.Resource import determineDoHereorMainThread, getStrRatioSimilarity
from Common.decorator import api_tool_decorator

from Common.enum import Color


class GridTable(gridlib.Grid):
    def __init__(self, parent, data=None, headers=[]):
        gridlib.Grid.__init__(self, parent, wx.ID_ANY, size=(1, 1))

        self.headersLabels = headers
        self.disableProperties = False

        if data is None:
            data = pd.DataFrame(columns=self.headersLabels)
        self.CreateGrid(len(data), len(data.columns))
        self.applyNewDataFrame(data)

        self.sortedColumn = None
        self.sortAcesnding = True

    def ApplyGridStyle(self):
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
        self.fillGridHeaders()
        self.AutoSizeColumns()

        self.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.SortColumn)
        self.Bind(gridlib.EVT_GRID_LABEL_RIGHT_CLICK, self.toogleViewMenuItem)
        self.GetGridWindow().Bind(wx.EVT_KEY_DOWN, self.onKey)
        self.GetGridWindow().Bind(wx.EVT_MOTION, self.onGridMotion)

        self.SetStatusCellColor()
        self.ForceRefresh()

    def applyNewDataFrame(self, data):
        if data is None:
            data = pd.DataFrame(columns=self.headersLabels)
        else:
            dropColumns = []
            renameColumns = {}
            matchingColumns = []
            for column in data.columns:
                matchFound = False
                for expectedCol in self.headersLabels:
                    if getStrRatioSimilarity(column, expectedCol) >= 95:
                        renameColumns[column] = expectedCol
                        matchingColumns.append(expectedCol)
                        matchFound = True
                        break
                if not matchFound:
                    dropColumns.append(column)
            missingColumns = list(set(self.headersLabels) - set(matchingColumns))
            for missingColumn in missingColumns:
                data[missingColumn] = ""
            data = data.drop(columns=dropColumns, axis=1)
            data = data.rename(columns=renameColumns)

        for header in Globals.NUMERIC_COLUMNS:
            if header in data.columns:
                data[header] = data[header].astype(int)

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

        self.ApplyGridStyle()

    @api_tool_decorator()
    def fillGridHeaders(self):
        """ Populate Grid Headers """
        num = 0
        try:
            for head in self.headersLabels:
                if head:
                    if self.GetNumberCols() < len(self.headersLabels):
                        self.AppendCols(1)
                    self.SetColLabelValue(num, head)
                    num += 1
        except:
            pass
        determineDoHereorMainThread(self.AutoSizeColumns)

    def AppendRows(self, numRows=1, updateLabels=True):
        return self.table.AppendRows(numRows)

    def SetCellValue(self, *args, **kw):
        return self.table.SetValue(*args, **kw)

    def EmptyGrid(self):
        data = pd.DataFrame(columns=self.headersLabels)
        self.applyNewDataFrame(data)

    def SortColumn(self, event):
        col = None
        if hasattr(event, "Col"):
            col = event.Col
        else:
            col = event

        if col and col > 0:
            if self.sortedColumn != col:
                self.sortAcesnding = True
            else:
                self.sortAcesnding = not self.sortAcesnding
            self.sortedColumn = col
            self.SetSortingColumn(self.sortedColumn, self.sortAcesnding)
            df = self.table.data.sort_values(
                self.GetColLabelValue(col), ascending=self.sortAcesnding
            )
            self.applyNewDataFrame(df)

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
            and "Status" in self.headersLabels
            and not Globals.frame.SpreadsheetUploaded
        ):
            colNum = self.headersLabels.index("Status")
            for rowNum in range(numRows):
                value = self.GetCellValue(rowNum, colNum)
                if value == "Offline":
                    self.SetCellTextColour(rowNum, colNum, Color.red.value)
                    self.SetCellBackgroundColour(rowNum, colNum, Color.lightRed.value)
                elif value == "Online":
                    self.SetCellTextColour(rowNum, colNum, Color.green.value)
                    self.SetCellBackgroundColour(rowNum, colNum, Color.lightGreen.value)
                elif value == "Unspecified":
                    self.SetCellTextColour(rowNum, colNum, Color.darkGrey.value)
                    self.SetCellBackgroundColour(rowNum, colNum, Color.grey.value)
                elif value == "Provisioning" or value == "Onboarding":
                    self.SetCellTextColour(rowNum, colNum, Color.orange.value)
                    self.SetCellBackgroundColour(
                        rowNum, colNum, Color.lightOrange.value
                    )
                elif value == "Wipe In-Progress":
                    self.SetCellTextColour(rowNum, colNum, Color.purple.value)
                    self.SetCellBackgroundColour(
                        rowNum, colNum, Color.lightPurple.value
                    )
                elif value == "Unknown":
                    self.SetCellTextColour(rowNum, colNum, Color.black.value)
                    self.SetCellBackgroundColour(rowNum, colNum, Color.white.value)
