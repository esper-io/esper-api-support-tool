#!/usr/bin/env python3

import copy
import math
import platform
import threading

import wx

import Common.Globals as Globals
from Common.decorator import api_tool_decorator
from Utility.API.DeviceUtility import getAllDevices
from Utility.API.GroupUtility import getAllGroups
from Utility.Resource import (determineDoHereorMainThread,
                              getStrRatioSimilarity, resourcePath,
                              scale_bitmap)


class MultiSelectSearchDlg(wx.Dialog):
    def __init__(self, parent, choices, label="", title="", single=False, resp=None):
        size = (500, 400)
        super(MultiSelectSearchDlg, self).__init__(
            parent,
            wx.ID_ANY,
            size=size,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.SetSize(size)
        self.SetMinSize(size)
        self.SetTitle(title)
        self.SetThemeEnabled(False)
        self.originalChoices = [choices]
        self.selected = []
        self.onBoxCalledPrior = False
        self.isFiltered = False
        self.label = label
        self.page = 0
        self.resp = resp
        self.limit = 0
        self.allDeviceStr = ""

        if "group" in label.lower():
            self.allDeviceStr = Globals.ALL_DEVICES_IN_TENANT

        if resp and hasattr(resp, "count") and hasattr(resp, "results"):
            if len(resp.results) > 0:
                self.limit = math.floor(resp.count / len(resp.results))
        elif type(resp) == dict and "count" in resp and "results" in resp:
            if len(resp["results"]) > 0:
                self.limit = math.floor(resp["count"] / len(resp["results"]))
        self.group = None

        if hasattr(parent, "sidePanel"):
            self.group = parent.sidePanel.selectedGroupsList

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_1, 1, wx.ALL | wx.EXPAND, 5)

        sizer_3 = wx.FlexGridSizer(3, 1, 0, 0)

        self.panel_3 = wx.Panel(self.panel_1, wx.ID_ANY)
        sizer_3.Add(self.panel_3, 1, wx.EXPAND, 0)

        grid_sizer_2 = wx.GridSizer(1, 2, 0, 0)

        label_1 = wx.StaticText(self.panel_3, wx.ID_ANY, label)
        label_1.SetFont(
            wx.Font(
                Globals.FONT_SIZE,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "NormalBold",
            )
        )
        grid_sizer_2.Add(label_1, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.panel_4 = wx.Panel(self.panel_1, wx.ID_ANY)
        sizer_3.Add(self.panel_4, 1, wx.EXPAND, 0)

        sizer_4 = wx.GridSizer(1, 2, 0, 0)

        self.checkbox_1 = wx.CheckBox(self.panel_4, wx.ID_ANY, "Select All")
        self.checkbox_1.SetToolTip("Select all entries on the page")
        sizer_4.Add(self.checkbox_1, 0, wx.EXPAND, 5)

        self.search = wx.SearchCtrl(self.panel_4, wx.ID_ANY, "")
        self.search.ShowCancelButton(True)
        sizer_4.Add(self.search, 0, wx.ALIGN_RIGHT, 0)

        self.panel_2 = wx.Panel(self.panel_1, wx.ID_ANY)
        sizer_3.Add(self.panel_2, 1, wx.EXPAND | wx.TOP, 5)

        grid_sizer_1 = wx.FlexGridSizer(2, 1, 0, 0)

        listStyle = (
            wx.LB_MULTIPLE | wx.LB_NEEDED_SB | wx.LB_SORT
            if not single
            else wx.LB_NEEDED_SB | wx.LB_SORT
        )
        self.check_list_box_1 = wx.CheckListBox(
            self.panel_2,
            wx.ID_ANY,
            choices=choices,
            style=listStyle,
        )
        grid_sizer_1.Add(self.check_list_box_1, 0, wx.EXPAND, 0)

        grid_sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_1.Add(grid_sizer_3, 1, wx.ALIGN_RIGHT | wx.EXPAND | wx.TOP, 5)

        prev_icon = scale_bitmap(resourcePath("Images/prev.png"), 18, 18)
        self.button_1 = wx.BitmapButton(
            self.panel_2,
            wx.ID_BACKWARD,
            prev_icon,
        )
        grid_sizer_3.Add(self.button_1, 0, wx.RIGHT, 5)

        next_icon = scale_bitmap(resourcePath("Images/next.png"), 18, 18)
        self.button_2 = wx.BitmapButton(
            self.panel_2,
            wx.ID_FORWARD,
            next_icon,
        )
        grid_sizer_3.Add(self.button_2, 0, wx.LEFT, 5)

        sizer_2 = wx.StdDialogButtonSizer()
        sizer_1.Add(sizer_2, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

        self.button_OK = wx.Button(self, wx.ID_OK, "")
        self.button_OK.SetDefault()
        sizer_2.AddButton(self.button_OK)

        sizer_2.Realize()

        grid_sizer_1.AddGrowableRow(0)
        grid_sizer_1.AddGrowableCol(0)
        self.panel_2.SetSizer(grid_sizer_1)

        self.panel_4.SetSizer(sizer_4)

        self.panel_3.SetSizer(grid_sizer_2)

        sizer_3.AddGrowableRow(2)
        sizer_3.AddGrowableCol(0)
        self.panel_1.SetSizer(sizer_3)

        self.SetSizer(sizer_1)

        self.SetAffirmativeId(self.button_OK.GetId())

        self.Layout()

        self.checkbox_1.Bind(wx.EVT_CHECKBOX, self.onSelectAll)

        self.search.Bind(wx.EVT_SEARCH, self.onSearch)
        self.search.Bind(wx.EVT_SEARCH_CANCEL, self.onSearch)
        self.search.Bind(wx.EVT_CHAR, self.onKey)

        self.Bind(wx.EVT_CLOSE, self.onClose)

        self.Bind(wx.EVT_LISTBOX, self.OnListSelection)
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnBoxSelection)
        self.Bind(wx.EVT_CHAR_HOOK, self.onEscapePressed)

        self.button_2.Bind(wx.EVT_BUTTON, self.onNext)
        self.button_1.Bind(wx.EVT_BUTTON, self.onPrev)
        self.checkPageButton()

        self.Fit()

    @api_tool_decorator()
    def onClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        elif self.IsShown():
            self.Close()
        self.DestroyLater()

    @api_tool_decorator()
    def onChar(self, event):
        event.Skip()

    @api_tool_decorator()
    def onSearch(self, event=None):
        if event:
            event.Skip()
        queryString = ""
        searchInput = self.search.GetValue()
        if hasattr(event, "GetString"):
            queryString = event.GetString()
        else:
            queryString = searchInput

        self.check_list_box_1.Clear()
        if queryString:
            sortedList = list(
                filter(
                    lambda i: queryString.lower() in i.lower()
                    or getStrRatioSimilarity(i.lower(), queryString) > 90,
                    self.originalChoices[self.page],
                )
            )
            match = []
            for item in sortedList:
                self.check_list_box_1.Append(item)
                if item in self.selected:
                    match.append(item)
            self.check_list_box_1.SetCheckedStrings(match)
            self.isFiltered = True
        else:
            for item in self.originalChoices[self.page]:
                self.check_list_box_1.Append(item)
            self.check_list_box_1.SetCheckedStrings(self.selected)
            self.isFiltered = False
        self.search_queue = ""

    @api_tool_decorator()
    def OnListSelection(self, event):
        selection = event.GetSelection()
        selectionStr = self.check_list_box_1.GetString(selection)
        checked = list(self.check_list_box_1.GetCheckedItems())
        if self.onBoxCalledPrior and platform.system() != "Windows":
            self.onBoxCalledPrior = False
            self.check_list_box_1.Deselect(selection)
            return
        self.onBoxCalledPrior = False
        if selection in checked:
            checked.remove(selection)
            if selectionStr in self.selected:
                self.selected.remove(selectionStr)
        else:
            checked.append(selection)
            if selectionStr not in self.selected:
                self.selected.append(selectionStr)
        self.check_list_box_1.Deselect(selection)
        self.check_list_box_1.SetCheckedItems(tuple(checked))

        if self.allDeviceStr and self.allDeviceStr in self.selected:
            self.checkbox_1.Set3StateValue(wx.CHK_CHECKED)
            self.onSelectEvent()
        elif len(self.selected) != len(self.originalChoices[self.page]):
            self.checkbox_1.Set3StateValue(wx.CHK_UNCHECKED)
        else:
            self.checkbox_1.Set3StateValue(wx.CHK_CHECKED)

    @api_tool_decorator()
    def OnBoxSelection(self, event):
        selection = event.GetSelection()
        selectionStr = self.check_list_box_1.GetString(selection)
        self.onBoxCalledPrior = True
        if selectionStr in self.selected:
            self.selected.remove(selectionStr)
        elif selectionStr not in self.selected:
            self.selected.append(selectionStr)

        if self.allDeviceStr and self.allDeviceStr in self.selected:
            self.checkbox_1.Set3StateValue(wx.CHK_CHECKED)
            self.onSelectEvent()
        elif len(self.selected) != len(self.originalChoices[self.page]):
            self.checkbox_1.Set3StateValue(wx.CHK_UNCHECKED)
        else:
            self.checkbox_1.Set3StateValue(wx.CHK_CHECKED)

    @api_tool_decorator()
    def GetSelections(self):
        return self.selected

    @api_tool_decorator()
    def onSelectAll(self, event):
        event.Skip()
        wx.CallAfter(self.onSelectEvent)

    @api_tool_decorator()
    def onSelectEvent(self):
        if self.checkbox_1.IsChecked():
            if (
                self.allDeviceStr
                and self.allDeviceStr in self.originalChoices[self.page]
            ):
                self.selected = [self.allDeviceStr]
            elif "device" in self.label.lower():
                Globals.THREAD_POOL.enqueue(self.selectAllDevices)
                return
            else:
                tmp = copy.deepcopy(self.originalChoices[self.page])
                self.selected = self.selected + tmp
        else:
            self.selected = []
        if not self.isFiltered:
            self.check_list_box_1.SetCheckedStrings(self.selected)
        if self.selected != self.originalChoices[self.page] and self.isFiltered:
            self.check_list_box_1.SetCheckedStrings([])

    @api_tool_decorator()
    def onEscapePressed(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_ESCAPE:
            self.onClose(event)
        event.Skip()

    @api_tool_decorator()
    def onKey(self, event):
        keycode = event.GetKeyCode()
        # CTRL + C or CTRL + Insert
        if event.ControlDown() and keycode in [67, 322]:
            self.on_copy(event)
        # CTRL + V
        elif event.ControlDown() and keycode == 86:
            self.on_paste(event)
        elif keycode == wx.WXK_ESCAPE:
            self.onClose(event)
        else:
            self.onChar(event)

    @api_tool_decorator()
    def on_copy(self, event):
        widget = self.FindFocus()
        data = wx.TextDataObject()
        data.SetText(widget.GetStringSelection())
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()

    @api_tool_decorator()
    def on_paste(self, event):
        widget = self.FindFocus()
        success = False
        data = wx.TextDataObject()
        if wx.TheClipboard.Open():
            success = wx.TheClipboard.GetData(data)
            wx.TheClipboard.Close()
        if success:
            widget.WriteText(data.GetText())

    def onNext(self, event):
        self.setCursorBusy()
        self.checkbox_1.Set3StateValue(wx.CHK_UNCHECKED)
        self.checkbox_1.Enable(False)
        self.check_list_box_1.Enable(False)
        if self.page < self.limit:
            self.page += 1
        Globals.THREAD_POOL.enqueue(self.processNext)

    def processNext(self):
        self.button_1.Enable(False)
        self.button_2.Enable(False)
        self.button_OK.Enable(False)
        self.search.Enable(False)
        self.updateChoices()
        self.checkPageButton()
        self.search.Clear()
        self.checkbox_1.Enable(True)
        self.check_list_box_1.Enable(True)
        self.search.Enable(True)
        self.button_OK.Enable(True)
        self.setCursorDefault()

    def onPrev(self, event):
        self.setCursorBusy()
        self.checkbox_1.Set3StateValue(wx.CHK_UNCHECKED)
        if self.page > 0:
            self.page -= 1
        Globals.THREAD_POOL.enqueue(self.processPrev)

    def processPrev(self):
        self.checkbox_1.Enable(False)
        self.check_list_box_1.Enable(False)
        self.search.Enable(False)
        self.button_1.Enable(False)
        self.button_2.Enable(False)
        self.button_OK.Enable(False)
        self.updateChoices()
        self.checkPageButton()
        self.search.Clear()
        self.checkbox_1.Enable(True)
        self.check_list_box_1.Enable(True)
        self.search.Enable(True)
        self.button_OK.Enable(True)
        self.setCursorDefault()

    def checkPageButton(self):
        if self.page == self.limit or (self.page == 0 and self.limit == 1):
            self.button_2.Enable(False)
        elif hasattr(self.resp, "next") and self.resp.next:
            self.button_2.Enable(True)
        elif type(self.resp) == dict and "next" in self.resp:
            self.button_2.Enable(True)

        if self.page == 0:
            self.button_1.Enable(False)
        elif hasattr(self.resp, "previous") and self.resp.previous:
            self.button_1.Enable(True)
        elif type(self.resp) == dict and "previous" in self.resp:
            self.button_1.Enable(True)

    def updateChoices(self):
        resp = None
        if len(self.originalChoices) > self.page:
            resp = self.originalChoices[self.page]
        else:
            resultLimit = Globals.limit
            resultOffset = Globals.limit
            if hasattr(self.resp, "results"):
                resultLimit = len(self.resp.results)
                resultOffset = len(self.resp.results) * self.page
            elif type(self.resp) == dict and "results" in self.resp:
                resultLimit = len(self.resp["results"])
                resultOffset = len(self.resp["results"]) * self.page

            if "device" in self.label.lower():
                resp = getAllDevices(
                    self.group, limit=resultLimit, offset=resultOffset, tolarance=1
                )
            elif "group" in self.label.lower():
                resp = getAllGroups(offset=resultOffset, tolerance=1)
            if resp:
                if hasattr(resp, "results"):
                    self.originalChoices.append(self.processDevices(resp.results))
                elif type(resp) == dict and "results" in resp:
                    self.originalChoices.append(self.processDevices(resp["results"]))

        determineDoHereorMainThread(self.updateChoicesFromResp, resp)

    def updateChoicesFromResp(self, resp):
        if resp:
            self.check_list_box_1.Clear()
            choices = self.originalChoices[self.page]
            for entry in self.selected:
                if entry not in choices:
                    choices.append(entry)
            for item in choices:
                self.check_list_box_1.Append(item)
            self.check_list_box_1.SetCheckedStrings(self.selected)

    def setCursorBusy(self):
        """ Set cursor icon to busy state """
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)

    def setCursorDefault(self):
        """ Set cursor icon to busy state """
        myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
        self.SetCursor(myCursor)

    def processDevices(self, chunk):
        nameList = []
        for device in chunk:
            name = ""
            if hasattr(device, "hardware_info"):
                name = "%s %s %s %s" % (
                    device.hardware_info["manufacturer"] if "model" in device.hardware_info else "",
                    device.hardware_info["model"] if "model" in device.hardware_info else "",
                    device.device_name,
                    device.alias_name if device.alias_name else "",
                )
            else:
                name = "%s %s %s %s" % (
                    device["hardwareInfo"]["manufacturer"] if "manufacturer" in device["hardwareInfo"] else "",
                    device["hardwareInfo"]["model"] if "model" in device["hardwareInfo"] else "",
                    device["device_name"],
                    device["alias_name"] if device["alias_name"] else "",
                )
            if name and name not in self.Parent.sidePanel.devicesExtended:
                if hasattr(device, "id"):
                    self.Parent.sidePanel.devicesExtended[name] = device.id
                else:
                    self.Parent.sidePanel.devicesExtended[name] = device["id"]
            if name not in nameList:
                nameList.append(name)
        return nameList

    def selectAllDevices(self):
        if platform.system() == "Darwin" and "main" not in threading.current_thread().name.lower():
            determineDoHereorMainThread(self.selectAllDevices)
            return
        self.setCursorBusy()
        self.button_1.Enable(False)
        self.button_2.Enable(False)
        self.button_OK.Enable(False)
        self.search.Enable(False)
        self.checkbox_1.Enable(False)
        self.check_list_box_1.Enable(False)

        count = 0
        selectedGroups = self.Parent.sidePanel.selectedGroups.GetStrings()
        for group in selectedGroups:
            parts = group.split("Device Count: ")
            if len(parts) > 1:
                num = parts[1].replace(")", "")
                count += int(num)

        if count > len(self.originalChoices[0]):
            self.resp = getAllDevices(
                self.group, limit=Globals.limit, offset=0, fetchAll=True, tolarance=1
            )
            if self.resp:
                self.check_list_box_1.Clear()
                if hasattr(self.resp, "results"):
                    self.originalChoices[0] = self.processDevices(self.resp.results)
                elif type(self.resp) == dict and "results" in self.resp:
                    self.originalChoices[0] = self.processDevices(self.resp["results"])
                for item in self.originalChoices[0]:
                    self.check_list_box_1.Append(item)
        self.selected = copy.deepcopy(self.originalChoices[0])
        tmpSelection = []
        num = 0
        for item in self.selected:
            tmpSelection.append(num)
            num += 1
        self.check_list_box_1.SetCheckedItems(tmpSelection)

        self.search.Clear()
        self.checkbox_1.Enable(True)
        self.check_list_box_1.Enable(True)
        self.search.Enable(True)
        self.button_OK.Enable(True)
        self.setCursorDefault()
