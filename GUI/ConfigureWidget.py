#!/usr/bin/env python3

import pandas as pd
import wx
import wx.grid

import Common.Globals as Globals
from Common.decorator import api_tool_decorator
from GUI.GridTable import GridTable
from Utility.FileUtility import read_csv_via_pandas, read_excel_via_openpyxl
from Utility.Resource import (determineKeyEventClose, displayFileDialog,
                              setElmTheme)


class WidgetPicker(wx.Dialog):
    def __init__(self, *args, **kwds):
        super(WidgetPicker, self).__init__(
            Globals.frame,
            wx.ID_ANY,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.SetSize((700, 500))
        self.SetTitle("Confgire Widgets")

        self.deviceList = []
        self.gridHeader = [
            "Device/Group Identifier",
        ]

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        label_5 = wx.StaticText(self, wx.ID_ANY, "Configure Widget")
        sizer_1.Add(label_5, 0, wx.LEFT | wx.TOP, 5)

        self.panel_2 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_2, 1, wx.ALL | wx.EXPAND, 5)

        sizer_3 = wx.StaticBoxSizer(
            wx.StaticBox(self.panel_2, wx.ID_ANY, ""), wx.HORIZONTAL
        )

        self.window_1 = wx.SplitterWindow(self.panel_2, wx.ID_ANY, style=0)
        self.window_1.SetMinimumPaneSize(200)
        self.window_1.SetSashGravity(0.5)
        sizer_3.Add(self.window_1, 1, wx.EXPAND, 0)

        self.panel_1 = wx.ScrolledWindow(
            self.window_1, wx.ID_ANY, style=wx.TAB_TRAVERSAL
        )
        self.panel_1.SetScrollRate(10, 10)

        grid_sizer_1 = wx.FlexGridSizer(4, 1, 0, 0)

        label_1 = wx.StaticText(self.panel_1, wx.ID_ANY, "Widget State:")
        grid_sizer_1.Add(label_1, 0, wx.ALL, 5)

        self.radio_box_1 = wx.RadioBox(
            self.panel_1,
            wx.ID_ANY,
            "",
            choices=["Enable", "Disable"],
            majorDimension=1,
            style=wx.RA_SPECIFY_ROWS,
        )
        self.radio_box_1.SetToolTip(
            "Select whether a the Widget feature should be Enabled or Disabled on a device."
        )
        self.radio_box_1.SetSelection(1)
        grid_sizer_1.Add(
            self.radio_box_1, 0, wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.RIGHT, 10
        )

        label_2 = wx.StaticText(self.panel_1, wx.ID_ANY, "Widget Class Name:")
        grid_sizer_1.Add(label_2, 0, wx.ALL, 5)

        grid_sizer_4 = wx.GridSizer(1, 1, 0, 0)
        grid_sizer_1.Add(grid_sizer_4, 1, wx.EXPAND, 0)

        self.default_text = (
            "Example: com.android.alarmclock.AnalogAppWidgetProvider"
        )
        self.text_ctrl_1 = wx.TextCtrl(
            self.panel_1,
            wx.ID_ANY,
            self.default_text,
            style=wx.TE_MULTILINE | wx.TE_WORDWRAP,
        )
        self.text_ctrl_1.SetToolTip(
            "Widget Package Name. %s" % self.default_text
        )
        grid_sizer_4.Add(
            self.text_ctrl_1, 0, wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.RIGHT, 10
        )
        self.text_ctrl_1.Enable(False)

        self.panel_3 = wx.Panel(self.window_1, wx.ID_ANY)

        grid_sizer_5 = wx.FlexGridSizer(2, 1, 0, 0)

        grid_sizer_3 = wx.FlexGridSizer(2, 2, 0, 0)
        grid_sizer_5.Add(grid_sizer_3, 0, wx.EXPAND, 0)

        label_4 = wx.StaticText(self.panel_3, wx.ID_ANY, "Apply To:")
        grid_sizer_3.Add(label_4, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.radio_box_2 = wx.RadioBox(
            self.panel_3,
            wx.ID_ANY,
            "",
            choices=["Device(s)", "Group(s)"],
            majorDimension=1,
            style=wx.RA_SPECIFY_ROWS,
        )
        self.radio_box_2.SetSelection(0)
        grid_sizer_3.Add(
            self.radio_box_2,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.EXPAND | wx.LEFT,
            10,
        )
        self.radio_box_2.SetToolTip(
            "Apply Command to the uploaded identifers that represent Devices or Groups.\n\nWARNING: If the ID is not provided we will attempt to search and apply the command to the closest match."
        )

        self.button_1 = wx.Button(self.panel_3, wx.ID_ANY, "Upload")
        self.button_1.SetToolTip(
            "Upload Identifers that should be targetted for the Widget Command."
        )
        grid_sizer_3.Add(
            self.button_1,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.BOTTOM | wx.LEFT,
            10,
        )

        grid_sizer_3.Add((0, 0), 0, 0, 0)

        grid_sizer_6 = wx.FlexGridSizer(2, 1, 0, 0)
        grid_sizer_5.Add(grid_sizer_6, 1, wx.EXPAND, 0)

        label_3 = wx.StaticText(self.panel_3, wx.ID_ANY, "Upload Preview:")
        grid_sizer_6.Add(label_3, 0, wx.ALL, 5)

        self.widget_grid = GridTable(self.panel_3, headers=self.gridHeader)
        self.widget_grid.AutoSizeColumns()
        grid_sizer_6.Add(self.widget_grid, 1, wx.ALL | wx.EXPAND, 10)

        sizer_2 = wx.StdDialogButtonSizer()
        sizer_1.Add(sizer_2, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

        self.button_CANCEL = wx.Button(self, wx.ID_CANCEL, "")
        sizer_2.AddButton(self.button_CANCEL)

        self.button_APPLY = wx.Button(self, wx.ID_APPLY, "")
        sizer_2.AddButton(self.button_APPLY)

        sizer_2.Realize()

        grid_sizer_6.AddGrowableRow(1)
        grid_sizer_6.AddGrowableCol(0)

        grid_sizer_3.AddGrowableRow(0)
        grid_sizer_3.AddGrowableCol(1)

        grid_sizer_5.AddGrowableRow(1)
        grid_sizer_5.AddGrowableCol(0)
        self.panel_3.SetSizer(grid_sizer_5)

        grid_sizer_1.AddGrowableCol(0)
        self.panel_1.SetSizer(grid_sizer_1)

        self.window_1.SplitVertically(self.panel_1, self.panel_3)

        self.panel_2.SetSizer(sizer_3)

        self.SetSizer(sizer_1)

        self.SetEscapeId(self.button_CANCEL.GetId())

        self.applyFontSize()
        setElmTheme(self)
        self.Layout()

        self.button_1.Bind(wx.EVT_BUTTON, self.onUpload)
        self.radio_box_1.Bind(wx.EVT_RADIOBOX, self.onRadioSelection)
        self.text_ctrl_1.Bind(wx.EVT_CHAR_HOOK, self.checkInput)
        self.button_APPLY.Bind(wx.EVT_BUTTON, self.onClose)
        self.button_CANCEL.Bind(wx.EVT_BUTTON, self.onClose)

        accel_table = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord('W'), self.button_CANCEL.GetId()),
            (wx.ACCEL_CMD, ord('W'), self.button_CANCEL.GetId()),
        ])
        self.SetAcceleratorTable(accel_table)

        self.Bind(wx.EVT_SYS_COLOUR_CHANGED, Globals.frame.onThemeChange)
        self.Bind(wx.EVT_KEY_UP, self.onEscapePressed)

    @api_tool_decorator()
    def onEscapePressed(self, event):
        if determineKeyEventClose(event):
            self.onClose(event)
        event.Skip()

    @api_tool_decorator()
    def onClose(self, event):
        if Globals.frame:
            Globals.frame.isRunning = False
            Globals.frame.toggleEnabledState(
                not Globals.frame.isRunning and not Globals.frame.isSavingPrefs
            )
        if event.EventType != wx.EVT_CLOSE.typeId:
            self.Close()
        self.EndModal(wx.EVT_CLOSE.typeId)
        self.DestroyLater()

    def checkInput(self, event=None):
        selection = self.radio_box_1.GetSelection()
        numRows = self.widget_grid.GetNumberRows() - 1
        textValue = self.text_ctrl_1.GetValue()
        if (
            selection == 0
            and textValue
            and textValue != self.default_text
            and numRows > 0
        ) or (selection == 1 and numRows > 0):
            self.button_APPLY.Enable(True)
        else:
            self.button_APPLY.Enable(False)
        if event:
            event.Skip()

    @api_tool_decorator()
    def onRadioSelection(self, event):
        selection = self.radio_box_1.GetSelection()
        if selection == 0:
            self.text_ctrl_1.Enable(True)
        else:
            self.text_ctrl_1.Clear()
            self.text_ctrl_1.Enable(False)

        self.checkInput(event)

    @api_tool_decorator()
    def onUpload(self, event):
        inFile = displayFileDialog(
            "Open Idenifier Spreadsheet",
            "Spreadsheet Files (*.csv;*.xlsx)|*.csv;*.xlsx|CSV Files (*.csv)|*.csv|Microsoft Excel Open XML Spreadsheet (*.xlsx)|*.xlsx",
            styles=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )

        if inFile:
            if self.widget_grid.GetNumberRows() > 0:
                df = pd.DataFrame(columns=self.gridHeader)
                self.widget_grid.applyNewDataFrame(df, resetPosition=True)
            self.button_1.Enable(False)
            Globals.THREAD_POOL.enqueue(self.onUploadHelper, inFile)

        if event:
            event.Skip()

    @api_tool_decorator()
    def onUploadHelper(self, inFile):
        self.deviceList = []
        dfs = None
        try:
            if inFile.endswith(".csv"):
                dfs = read_csv_via_pandas(inFile)
            elif inFile.endswith(".xlsx"):
                try:
                    dfs = read_excel_via_openpyxl(inFile, readAnySheet=True)
                except:
                    pass
            if dfs is not None and len(dfs) > 0:
                gridTableData = {
                    self.gridHeader[0]: [],
                }
                identifers = dfs[dfs.columns.values.tolist()[0]].tolist()
                self.addIdToDeviceList(identifers, gridTableData)
                df = pd.DataFrame(gridTableData, columns=self.gridHeader)
                self.widget_grid.applyNewDataFrame(df, resetPosition=True)
        except Exception as e:
            raise e
        finally:
            self.button_1.Enable(True)
            self.checkInput()

    def addIdToDeviceList(self, identifers, gridTableData):
        for id in identifers:
            if id and id not in self.deviceList:
                gridTableData[self.gridHeader[0]].append(id)
                self.deviceList.append(str(id))

    def getInputs(self):
        return (
            self.radio_box_1.GetSelection(),
            self.text_ctrl_1.GetValue(),
            self.radio_box_2.GetSelection(),
            self.deviceList,
        )

    def applyFontSize(self):
        normalFont = wx.Font(
            Globals.FONT_SIZE,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL,
            0,
            "Normal",
        )
        normalBoldFont = wx.Font(
            Globals.FONT_SIZE,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD,
            0,
            "NormalBold",
        )

        self.applyFontHelper(self, normalFont, normalBoldFont)

    def applyFontHelper(self, elm, font, normalBoldFont):
        if self:
            childen = elm.GetChildren()
            for child in childen:
                if hasattr(child, "SetFont"):
                    if isinstance(child, wx.StaticText):
                        child.SetFont(normalBoldFont)
                    else:
                        child.SetFont(font)
                self.applyFontHelper(child, font, normalBoldFont)
