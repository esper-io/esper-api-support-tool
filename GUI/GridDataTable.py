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
        if hasattr(self, "data"):
            return len(self.data)
        return 0

    def GetNumberCols(self):
        if hasattr(self, "data"):
            return len(self.data.columns)
        return 0

    def GetValue(self, row, col):
        if hasattr(self, "data"):
            return self.data.iloc[row, col]
        return ""

    def SetValue(self, row, col, value):
        if hasattr(self, "data"):
            self.data.iloc[row, col] = value

    def GetColLabelValue(self, col):
        if hasattr(self, "data"):
            return str(self.data.columns[col])
        return ""

    def GetTypeName(self, row, col):
        return wx.grid.GRID_VALUE_STRING

    def GetAttr(self, row, col, prop):
        return super().GetAttr(row, col, prop)
