import pandas as pd
import wx
import wx.grid as gridlib
import Common.Globals as Globals
from Common.decorator import api_tool_decorator

from GUI.GridDataTable import GridDataTable
from Utility.Resource import determineDoHereorMainThread, getStrRatioSimilarity


class GridTable(gridlib.Grid):
    def __init__(self, parent, data=None, headers=[]):
        gridlib.Grid.__init__(self, parent, wx.ID_ANY, size=(1, 1))

        self.headersLabels = headers

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
        self.HideCol(0)
        self.AutoSizeColumns()

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
            self.SetColAttr(self.headersLabels.index(header) + 1, attr)

        self.ApplyGridStyle()

    @api_tool_decorator()
    def fillGridHeaders(self):
        """ Populate Grid Headers """
        num = 0
        try:
            for head in self.headersLabels:
                if head:
                    if self.GetNumberCols() < len(self.grid1HeaderLabels):
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

        if col:
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
