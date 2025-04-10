#!/usr/bin/env python3

from datetime import datetime, timedelta

import wx
import wx.adv

import Common.Globals as Globals
from Common.enum import FontStyles
from Utility.Resource import getFont, setElmTheme


class ScheduleCmdDialog(wx.Dialog):
    def __init__(self, *args, **kwds):
        super(ScheduleCmdDialog, self).__init__(
            Globals.frame,
            wx.ID_ANY,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.SetTitle("Schedule Command")
        self.SetSize((400, 400))
        self.SetMinSize((400, 400))
        self.SetThemeEnabled(False)

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_1, 1, wx.EXPAND, 0)

        grid_sizer_1 = wx.FlexGridSizer(3, 1, 0, 0)

        headerBold = getFont(FontStyles.HEADER_BOLD.value)
        normalBold = getFont(FontStyles.NORMAL_BOLD.value)
        label_1 = wx.StaticText(self.panel_1, wx.ID_ANY, "Schedule Command")
        label_1.SetFont(headerBold)
        grid_sizer_1.Add(label_1, 0, wx.EXPAND | wx.LEFT | wx.TOP, 2)

        self.radio_box_1 = wx.RadioBox(
            self.panel_1,
            wx.ID_ANY,
            "Time relative to",
            choices=["Console", "Device"],
            majorDimension=1,
            style=wx.RA_SPECIFY_COLS,
        )
        self.radio_box_1.SetSelection(1)
        grid_sizer_1.Add(self.radio_box_1, 0, wx.ALL | wx.EXPAND, 5)

        self.window_1 = wx.SplitterWindow(
            self.panel_1, wx.ID_ANY, style=wx.SP_3D | wx.SP_BORDER
        )
        self.window_1.SetMinimumPaneSize(50)
        grid_sizer_1.Add(self.window_1, 1, wx.EXPAND, 0)

        self.panel_2 = wx.Panel(self.window_1, wx.ID_ANY)

        grid_sizer_3 = wx.FlexGridSizer(2, 1, 0, 0)

        self.checkbox_1 = wx.CheckBox(
            self.panel_2, wx.ID_ANY, "Recurring schedule"
        )
        grid_sizer_3.Add(self.checkbox_1, 0, wx.ALL, 5)
        self.checkbox_1.Bind(wx.EVT_CHECKBOX, self.checkInputs)

        self.panel_3 = wx.Panel(self.panel_2, wx.ID_ANY)
        grid_sizer_3.Add(self.panel_3, 1, wx.EXPAND | wx.TOP, 2)

        sizer_3 = wx.BoxSizer(wx.VERTICAL)

        label_2 = wx.StaticText(self.panel_3, wx.ID_ANY, "Days to Repeat On:")
        label_2.SetFont(normalBold)
        sizer_3.Add(label_2, 0, wx.LEFT, 2)

        self.check_list_box_1 = wx.CheckListBox(
            self.panel_3,
            wx.ID_ANY,
            choices=[
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ],
        )
        sizer_3.Add(self.check_list_box_1, 0, wx.ALL | wx.EXPAND, 5)
        self.check_list_box_1.Enable(False)

        self.window_1_pane_2 = wx.Panel(self.window_1, wx.ID_ANY)

        grid_sizer_2 = wx.FlexGridSizer(4, 1, 0, 0)

        sizer_4 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_2.Add(sizer_4, 1, wx.EXPAND, 0)

        label_3 = wx.StaticText(self.window_1_pane_2, wx.ID_ANY, "Start Date:")
        label_3.SetFont(normalBold)
        sizer_4.Add(label_3, 0, wx.LEFT, 2)

        self.datepicker_ctrl_1 = wx.adv.DatePickerCtrl(
            self.window_1_pane_2, wx.ID_ANY
        )
        self.datepicker_ctrl_1.Bind(wx.adv.EVT_DATE_CHANGED, self.checkInputs)
        sizer_4.Add(self.datepicker_ctrl_1, 0, wx.ALL | wx.EXPAND, 5)

        sizer_6 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_2.Add(sizer_6, 1, wx.EXPAND, 0)

        label_5 = wx.StaticText(self.window_1_pane_2, wx.ID_ANY, "End Date:")
        label_5.SetFont(normalBold)
        sizer_6.Add(label_5, 0, wx.LEFT, 2)

        self.datepicker_ctrl_2 = wx.adv.DatePickerCtrl(
            self.window_1_pane_2, wx.ID_ANY
        )
        self.datepicker_ctrl_2.Bind(wx.adv.EVT_DATE_CHANGED, self.checkInputs)
        sizer_6.Add(self.datepicker_ctrl_2, 0, wx.ALL | wx.EXPAND, 5)

        sizer_5 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_2.Add(sizer_5, 1, wx.EXPAND, 0)

        label_4 = wx.StaticText(
            self.window_1_pane_2, wx.ID_ANY, "Start Time  (24 hour format):"
        )
        label_4.SetFont(normalBold)
        sizer_5.Add(label_4, 0, wx.LEFT, 2)

        self.text_ctrl_1 = wx.adv.TimePickerCtrl(
            self.window_1_pane_2, wx.ID_ANY
        )
        self.text_ctrl_1.Bind(wx.adv.EVT_TIME_CHANGED, self.verifyTime)
        sizer_5.Add(self.text_ctrl_1, 0, wx.ALL | wx.EXPAND, 5)

        sizer_7 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_2.Add(sizer_7, 1, wx.EXPAND, 0)

        label_6 = wx.StaticText(
            self.window_1_pane_2, wx.ID_ANY, "End Time (24 hour format):"
        )
        label_6.SetFont(normalBold)
        sizer_7.Add(label_6, 0, wx.LEFT, 2)

        self.text_ctrl_2 = wx.adv.TimePickerCtrl(
            self.window_1_pane_2, wx.ID_ANY
        )
        self.text_ctrl_2.Bind(wx.adv.EVT_TIME_CHANGED, self.checkInputs)
        sizer_7.Add(self.text_ctrl_2, 0, wx.ALL | wx.EXPAND, 5)

        sizer_2 = wx.StdDialogButtonSizer()
        sizer_1.Add(sizer_2, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

        self.button_OK = wx.Button(self, wx.ID_OK, "")
        self.button_OK.SetDefault()
        sizer_2.AddButton(self.button_OK)
        self.button_OK.Enable(False)

        self.button_CANCEL = wx.Button(self, wx.ID_CANCEL, "")
        sizer_2.AddButton(self.button_CANCEL)

        sizer_2.Realize()

        grid_sizer_2.AddGrowableRow(0)
        grid_sizer_2.AddGrowableRow(1)
        grid_sizer_2.AddGrowableRow(2)
        grid_sizer_2.AddGrowableRow(3)
        grid_sizer_2.AddGrowableCol(0)
        self.window_1_pane_2.SetSizer(grid_sizer_2)

        self.panel_3.SetSizer(sizer_3)

        grid_sizer_3.AddGrowableRow(1)
        grid_sizer_3.AddGrowableCol(0)
        self.panel_2.SetSizer(grid_sizer_3)

        self.window_1.SplitVertically(self.panel_2, self.window_1_pane_2)

        grid_sizer_1.AddGrowableCol(0)
        self.panel_1.SetSizer(grid_sizer_1)

        self.SetSizer(sizer_1)
        sizer_1.Fit(self)

        self.SetAffirmativeId(self.button_OK.GetId())
        self.SetEscapeId(self.button_CANCEL.GetId())

        self.Bind(wx.EVT_SYS_COLOUR_CHANGED, Globals.frame.onThemeChange)

        setElmTheme(self)
        self.Layout()
        self.Centre()

    def isRecurring(self):
        return self.checkbox_1.IsChecked()

    def verifyTime(self, event=None):
        time = self.text_ctrl_1.GetTime()
        now = datetime.now().time()
        if (
            now.hour >= time[0]
            and now.minute >= time[1]
            and now.second >= time[2]
        ):
            newTime = datetime.combine(datetime.today(), now) + timedelta(
                minutes=5
            )
            self.text_ctrl_1.SetTime(
                (newTime.hour, newTime.minute, newTime.second)
            )

        self.checkInputs()

    def checkInputs(self, event=None):
        isValid = True
        if self.checkbox_1.IsChecked():
            self.check_list_box_1.Enable(True)
            if len(list(self.check_list_box_1.GetCheckedStrings())) == 0:
                isValid = False
        else:
            self.check_list_box_1.Enable(False)
            self.check_list_box_1.SetCheckedItems([])

        startDateTime, endDateTime, _, _ = self.getDateTimeStrings()

        dt = datetime.strptime(startDateTime, "%Y-%m-%dT%H:%M:%SZ")
        dt2 = datetime.strptime(endDateTime, "%Y-%m-%dT%H:%M:%SZ")

        if (dt2 - dt).total_seconds() <= 0:
            isValid = False
        else:
            isValid = bool(isValid and True)

        self.button_OK.Enable(isValid)

    def getDateTimeStrings(self):
        startDateTime = None
        startDate = self.datepicker_ctrl_1.GetValue().Format("%Y-%m-%d")
        startTime = self.text_ctrl_1.GetValue().Format("%H:%M:%S")
        startDateTime = "%sT%sZ" % (startDate, startTime)
        startTime = self.text_ctrl_1.GetValue().Format("%H:%M")

        endDateTime = None
        endDate = self.datepicker_ctrl_2.GetValue().Format("%Y-%m-%d")
        endTime = self.text_ctrl_2.GetValue().Format("%H:%M:%S")
        endDateTime = "%sT%sZ" % (endDate, endTime)
        endTime = self.text_ctrl_2.GetValue().Format("%H:%M")

        return startDateTime, endDateTime, startTime, endTime

    def getScheduleDict(self):
        days = []

        if self.checkbox_1.IsChecked():
            days = list(self.check_list_box_1.GetCheckedStrings())

        startDateTime, endDateTime, startTime, endtime = (
            self.getDateTimeStrings()
        )

        return {
            "name": "%s Blueprint Update" % str(datetime.now()),
            "start_datetime": startDateTime,
            "end_datetime": endDateTime,
            "time_type": self.radio_box_1.GetStringSelection().lower(),
            "window_start_time": startTime,
            "window_end_time": endtime,
            "days": days,
        }
