import pandas as pd

import wx
import wx.grid


class GridDataTable(wx.grid.GridTableBase):
    def __init__(self, data=None):
        wx.grid.GridTableBase.__init__(self)
        if data is None:
            data = pd.DataFrame()
        self.data = data

    def GetNumberRows(self):
        return len(self.data)

    def GetNumberCols(self):
        return len(self.data.columns)

    def GetValue(self, row, col):
        return self.data.iloc[row, col]

    def SetValue(self, row, col, value):
        self.data.iloc[row, col] = value

    def GetColLabelValue(self, col):
        return str(self.data.columns[col])

    def GetTypeName(self, row, col):
        if self.data[self.data.columns[0]].count() > 0:
            value = self.data.iloc[row, col]
            if type(value) is int:
                return wx.grid.GRID_VALUE_NUMBER
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
