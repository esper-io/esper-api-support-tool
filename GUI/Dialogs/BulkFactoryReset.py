#!/usr/bin/env python3

import csv
import wx
import wx.grid
from Common.decorator import api_tool_decorator

import Utility.wxThread as wxThread


class BulkFactoryReset(wx.Dialog):
    def __init__(self):
        super(BulkFactoryReset, self).__init__(
            None,
            wx.ID_ANY,
            style=wx.DEFAULT_DIALOG_STYLE,
        )
        self.SetSize((555, 400))
        self.SetMinSize((555, 400))
        self.SetTitle("Bulk Factory Reset")

        self.identifers = []
        self.expectedHeaders = ["Device Identifiers"]

        sizer_1 = wx.FlexGridSizer(2, 1, 0, 0)

        grid_sizer_4 = wx.FlexGridSizer(5, 1, 0, 0)
        sizer_1.Add(grid_sizer_4, 0, wx.EXPAND, 0)

        label_4 = wx.StaticText(self, wx.ID_ANY, "Bulk Factory Reset")
        label_4.SetFont(
            wx.Font(
                11,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        grid_sizer_4.Add(label_4, 0, wx.ALL, 5)

        label_3 = wx.StaticText(
            self,
            wx.ID_ANY,
            "Upload a CSV containing device idenifers that you wish to Factory Reset:",
            style=wx.ST_ELLIPSIZE_END,
        )
        label_3.Wrap(1)
        grid_sizer_4.Add(label_3, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        label_5 = wx.StaticText(
            self,
            wx.ID_ANY,
            "Device idenifers include: Serial Number, Custom Serial Number, IMEI, Device Name, Device Id",
            style=wx.ST_ELLIPSIZE_END,
        )
        label_5.Wrap(1)
        grid_sizer_4.Add(label_5, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_4.Add(sizer_4, 1, wx.ALIGN_RIGHT | wx.ALL | wx.EXPAND, 5)

        self.button_7 = wx.Button(self, wx.ID_ANY, "Download Template")
        self.button_7.SetToolTip("Upload CSV file")
        sizer_4.Add(self.button_7, 0, wx.BOTTOM | wx.RIGHT, 5)

        self.button_6 = wx.Button(self, wx.ID_ANY, "Upload CSV")
        self.button_6.SetToolTip("Upload CSV file")
        sizer_4.Add(self.button_6, 0, wx.BOTTOM | wx.RIGHT, 5)

        self.grid_1 = wx.grid.Grid(self, wx.ID_ANY, size=(1, 1))
        self.grid_1.CreateGrid(10, 1)
        self.grid_1.EnableDragGridSize(0)
        self.grid_1.SetColLabelValue(0, "Device Identifiers")
        self.grid_1.SetColSize(0, 132)
        grid_sizer_4.Add(self.grid_1, 1, wx.ALL | wx.EXPAND, 5)

        sizer_2 = wx.StdDialogButtonSizer()
        sizer_1.Add(sizer_2, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

        self.button_OK = wx.Button(self, wx.ID_OK, "RESET")
        self.button_OK.SetDefault()
        sizer_2.AddButton(self.button_OK)

        self.button_CANCEL = wx.Button(self, wx.ID_CANCEL, "")
        sizer_2.AddButton(self.button_CANCEL)

        sizer_2.Realize()

        grid_sizer_4.AddGrowableRow(4)
        grid_sizer_4.AddGrowableCol(0)

        sizer_1.AddGrowableRow(0)
        sizer_1.AddGrowableCol(0)
        self.SetSizer(sizer_1)

        self.SetAffirmativeId(self.button_OK.GetId())
        self.SetEscapeId(self.button_CANCEL.GetId())

        self.Layout()
        self.Centre()

        self.button_OK.Enable(False)

        self.button_7.Bind(wx.EVT_BUTTON, self.downloadCSV)
        self.button_6.Bind(wx.EVT_BUTTON, self.openCSV)
        self.button_CANCEL.Bind(wx.EVT_BUTTON, self.onClose)
        self.button_OK.Bind(wx.EVT_BUTTON, self.onReset)

        self.Fit()

    @api_tool_decorator()
    def onClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        elif self.IsShown():
            self.Close()
        self.DestroyLater()
        if event:
            event.Skip()

    def onReset(self, event):
        self.onClose(event)

    def downloadCSV(self, event):
        dlg = wx.FileDialog(
            self,
            message="Save Bulk Factory Reset CSV as...",
            defaultFile="",
            wildcard="*.csv",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )
        result = dlg.ShowModal()
        inFile = dlg.GetPath()
        dlg.DestroyLater()

        if result == wx.ID_OK:
            self.setCursorBusy()
            self.button_OK.Enable(False)
            thread = wxThread.GUIThread(None, self.saveGroupCSV, (inFile))
            thread.startWithRetry()

    def saveGroupCSV(self, inFile):
        gridData = []
        gridData.append(self.expectedHeaders)
        gridData.append(["serial_number"])
        gridData.append(["custom_serial_number"])
        gridData.append(["imei"])
        gridData.append(["esper_device_name"])
        gridData.append(["esper_device_id"])

        with open(inFile, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerows(gridData)
        self.button_OK.Enable(True)
        self.setCursorDefault()

    def openCSV(self, event):
        filePath = None
        with wx.FileDialog(
            self,
            "Open CSV File",
            wildcard="CSV files (*.csv)|*.csv",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as fileDialog:
            result = fileDialog.ShowModal()
            if result == wx.ID_OK:
                # Proceed loading the file chosen by the user
                filePath = fileDialog.GetPath()
        if filePath:
            self.uploadCSV(filePath)

    def uploadCSV(self, filePath):
        self.setCursorBusy()
        if self.grid_1.GetNumberRows() > 0:
            self.grid_1.DeleteRows(0, self.grid_1.GetNumberRows())
        data = None
        try:
            with open(filePath, "r", encoding="utf-8-sig") as csvFile:
                reader = csv.reader(
                    csvFile, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True
                )
                data = list(reader)
        except:
            with open(filePath, "r") as csvFile:
                reader = csv.reader(
                    csvFile, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True
                )
                data = list(reader)
        for row in data:
            colNum = 0
            for col in row:
                if colNum > 0:
                    break
                if col in self.expectedHeaders:
                    break
                else:
                    self.grid_1.AppendRows(1)
                    self.grid_1.SetCellValue(
                        self.grid_1.GetNumberRows() - 1, colNum, col
                    )
                    self.identifers.append(col)
                colNum += 1
        self.grid_1.AutoSizeColumns()
        self.checkActions()
        self.setCursorDefault()

    def checkActions(self):
        if self.grid_1.GetNumberRows() > 0:
            self.button_OK.Enable(True)
        else:
            self.button_OK.Enable(False)

    @api_tool_decorator()
    def setCursorDefault(self):
        """ Set cursor icon to default state """
        try:
            self.isBusy = False
            myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
            self.SetCursor(myCursor)
            self.grid_1.GetGridWindow().SetCursor(myCursor)
            self.grid_1.GetTargetWindow().SetCursor(myCursor)
        except:
            pass

    @api_tool_decorator()
    def setCursorBusy(self):
        """ Set cursor icon to busy state """
        self.isBusy = True
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)
        self.grid_1.GetGridWindow().SetCursor(myCursor)
        self.grid_1.GetTargetWindow().SetCursor(myCursor)

    def getIdentifiers(self):
        return self.identifers
