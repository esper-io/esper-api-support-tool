#!/usr/bin/env python3

import csv

import pandas as pd
import wx
import wx.grid

import Common.Globals as Globals
from Common.decorator import api_tool_decorator


class WidgetPicker(wx.Dialog):
    def __init__(self, *args, **kwds):
        super(WidgetPicker, self).__init__(
            None,
            wx.ID_ANY,
            style=wx.DEFAULT_DIALOG_STYLE
            | wx.RESIZE_BORDER,
        )
        self.SetSize((700, 500))
        self.SetTitle("Confgire Widgets")

        self.deviceList = []

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        label_5 = wx.StaticText(self, wx.ID_ANY, "Configure Widget")
        label_5.SetFont(
            wx.Font(
                14,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
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
        label_1.SetFont(
            wx.Font(
                11,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        grid_sizer_1.Add(label_1, 0, wx.ALL, 5)

        self.radio_box_1 = wx.RadioBox(
            self.panel_1,
            wx.ID_ANY,
            "",
            choices=["Enable", "Disable"],
            majorDimension=1,
            style=wx.RA_SPECIFY_ROWS,
        )
        self.radio_box_1.SetToolTip("Select whether a the Widget feature should be Enabled or Disabled on a device.")
        self.radio_box_1.SetSelection(1)
        grid_sizer_1.Add(
            self.radio_box_1, 0, wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.RIGHT, 10
        )

        label_2 = wx.StaticText(self.panel_1, wx.ID_ANY, "Widget Class Name:")
        label_2.SetFont(
            wx.Font(
                11,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        grid_sizer_1.Add(label_2, 0, wx.ALL, 5)

        grid_sizer_4 = wx.GridSizer(1, 1, 0, 0)
        grid_sizer_1.Add(grid_sizer_4, 1, wx.EXPAND, 0)

        self.default_text = "Example: com.android.alarmclock.AnalogAppWidgetProvider"
        self.text_ctrl_1 = wx.TextCtrl(
            self.panel_1,
            wx.ID_ANY,
            self.default_text,
            style=wx.TE_MULTILINE | wx.TE_WORDWRAP,
        )
        self.text_ctrl_1.SetToolTip("Widget Package Name. %" % self.default_text)
        grid_sizer_4.Add(
            self.text_ctrl_1, 0, wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.RIGHT, 10
        )
        self.text_ctrl_1.Enable(False)

        self.panel_3 = wx.Panel(self.window_1, wx.ID_ANY)

        grid_sizer_5 = wx.FlexGridSizer(2, 1, 0, 0)

        grid_sizer_3 = wx.FlexGridSizer(2, 2, 0, 0)
        grid_sizer_5.Add(grid_sizer_3, 0, wx.EXPAND, 0)

        label_4 = wx.StaticText(self.panel_3, wx.ID_ANY, "Apply To:")
        label_4.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        grid_sizer_3.Add(label_4, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.radio_box_2 = wx.RadioBox(self.panel_3, wx.ID_ANY, "", choices=["Device(s)", "Group(s)"], majorDimension=1, style=wx.RA_SPECIFY_ROWS)
        self.radio_box_2.SetSelection(0)
        grid_sizer_3.Add(self.radio_box_2, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.EXPAND | wx.LEFT, 10)
        self.radio_box_2.SetToolTip("Apply Command to the uploaded identifers that represent Devices or Groups.\n\nWARNING: If the ID is not provided we will attempt to search and apply the command to the closest match.")

        self.button_1 = wx.Button(self.panel_3, wx.ID_ANY, "Upload")
        self.button_1.SetToolTip("Upload Identifers that should be targetted for the Widget Command.")
        grid_sizer_3.Add(self.button_1, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.BOTTOM | wx.LEFT, 10)

        grid_sizer_3.Add((0, 0), 0, 0, 0)

        grid_sizer_6 = wx.FlexGridSizer(2, 1, 0, 0)
        grid_sizer_5.Add(grid_sizer_6, 1, wx.EXPAND, 0)

        label_3 = wx.StaticText(self.panel_3, wx.ID_ANY, "Upload Preview:")
        label_3.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        grid_sizer_6.Add(label_3, 0, wx.ALL, 5)

        self.grid_1 = wx.grid.Grid(self.panel_3, wx.ID_ANY, size=(1, 1))
        self.grid_1.CreateGrid(10, 1)
        self.grid_1.SetColLabelValue(0, "Identifier")
        self.grid_1.SetColSize(0, 200)
        grid_sizer_6.Add(self.grid_1, 1, wx.ALL | wx.EXPAND, 10)

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

        self.Layout()

        self.button_1.Bind(wx.EVT_BUTTON, self.onUpload)
        self.radio_box_1.Bind(wx.EVT_RADIOBOX, self.onRadioSelection)
        self.text_ctrl_1.Bind(wx.EVT_CHAR_HOOK, self.checkInput)
        self.button_APPLY.Bind(wx.EVT_BUTTON, self.onClose)
        self.button_CANCEL.Bind(wx.EVT_BUTTON, self.onClose)

    @api_tool_decorator()
    def onEscapePressed(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_ESCAPE:
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
        self.DestroyLater()

    def checkInput(self, event=None):
        selection = self.radio_box_1.GetSelection()
        numRows = self.grid_1.GetNumberRows() - 1
        textValue = self.text_ctrl_1.GetValue()
        if (selection == 0 and textValue and textValue != self.default_text and numRows > 0) or (
            selection == 1 and numRows > 0
        ):
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
        inFile = ""
        result = None
        with wx.FileDialog(
            self,
            message="Open Idenifier Spreadsheet",
            defaultFile="",
            wildcard="Spreadsheet Files (*.csv;*.xlsx)|*.csv;*.xlsx|CSV Files (*.csv)|*.csv|Microsoft Excel Open XML Spreadsheet (*.xlsx)|*.xlsx",
            style=wx.FD_OPEN,
        ) as dlg:
            Globals.OPEN_DIALOGS.append(dlg)
            result = dlg.ShowModal()
            Globals.OPEN_DIALOGS.remove(dlg)
            inFile = dlg.GetPath()

        if result == wx.ID_OK:
            self.grid_1.DeleteRows(0, self.grid_1.GetNumberRows())
            fileData = None
            self.deviceList = []

            if inFile.endswith(".csv"):
                with open(inFile, "r") as csvFile:
                    reader = csv.reader(
                        csvFile, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True
                    )
                    fileData = list(reader)
                for entry in fileData:
                    identifer = entry[0]
                    if identifer and identifer not in self.deviceList:
                        self.grid_1.AppendRows(1)
                        self.grid_1.SetCellValue(
                            self.grid_1.GetNumberRows() - 1, 1, str(identifer)
                        )
                        self.deviceList.append(str(identifer))
            elif inFile.endswith(".xlsx"):
                dfs = None
                try:
                    dfs = pd.read_excel(
                        inFile, sheet_name=None, keep_default_na=False
                    )
                except:
                    pass
                if dfs:
                    sheetKeys = dfs.keys()
                    for sheet in sheetKeys:
                        identifer = dfs[sheet].columns.values.tolist()[0]
                        if identifer and identifer not in self.deviceList:
                            self.grid_1.AppendRows(1)
                            self.grid_1.SetCellValue(
                                self.grid_1.GetNumberRows() - 1, 1, str(identifer)
                            )
                            self.deviceList.append(str(identifer))
        self.checkInput(event)

    def getInputs(self):
        return (
            self.radio_box_1.GetSelection(),
            self.text_ctrl_1.GetValue(),
            self.radio_box_2.GetSelection(),
            self.deviceList,
        )
