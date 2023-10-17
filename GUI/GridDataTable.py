import Common.Globals as Globals
import pandas as pd

import wx
import wx.grid
from Common.decorator import api_tool_decorator

from Common.enum import Color
from Utility.Resource import acquireLocks, releaseLocks


class GridDataTable(wx.grid.GridTableBase):
    def __init__(self, data=None):
        wx.grid.GridTableBase.__init__(self)
        self.headerRows = 1
        if data is None:
            data = pd.DataFrame()
        self.data = data

    def GetNumberRows(self):
        return len(self.data)

    def GetNumberCols(self):
        return len(self.data.columns)  # + 1 # for index

    def GetValue(self, row, col):
        if col == 0:
            return self.data.index[row]
        return self.data.iloc[row, col - 1]

    def SetValue(self, row, col, value):
        self.data.iloc[row, col - 1] = value

    def GetColLabelValue(self, col):
        if col == 0:
            if self.data.index.name is None:
                return "Index"
            else:
                return self.data.index.name
        return str(self.data.columns[col - 1])

    def GetTypeName(self, row, col):
        return wx.grid.GRID_VALUE_STRING

    def GetAttr(self, row, col, prop):
        return super().GetAttr(row, col, prop)

    def AppendRows(self, numRows=1):
        beforeIndx = len(self.data.index)
        newRow = []
        for _ in range(len(self.data.columns)):
            newRow.append("")
        for _ in range(numRows):
            self.data.loc[len(self.data.index)] = newRow
        return beforeIndx + numRows == len(self.data.index)
