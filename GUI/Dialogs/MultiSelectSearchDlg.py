#!/usr/bin/env python3

import wx

from Common.decorator import api_tool_decorator


class MultiSelectSearchDlg(wx.Dialog):
    def __init__(self, parent, choices, label="", title=""):
        super(MultiSelectSearchDlg, self).__init__(
            parent,
            wx.ID_ANY,
            size=(400, 200),
            style=wx.DEFAULT_DIALOG_STYLE,
        )
        self.SetSize((400, 300))
        self.SetTitle(title)

        self.originalChoices = choices
        self.selected = []

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_1, 1, wx.ALL | wx.EXPAND, 5)

        sizer_3 = wx.FlexGridSizer(4, 1, 0, 0)

        self.panel_3 = wx.Panel(self.panel_1, wx.ID_ANY)
        sizer_3.Add(self.panel_3, 1, wx.EXPAND, 0)

        grid_sizer_2 = wx.GridSizer(1, 2, 0, 0)

        label_1 = wx.StaticText(self.panel_3, wx.ID_ANY, label)
        label_1.SetFont(
            wx.Font(
                12,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        grid_sizer_2.Add(label_1, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.panel_4 = wx.Panel(self.panel_1, wx.ID_ANY)
        sizer_3.Add(self.panel_4, 1, wx.EXPAND, 0)

        sizer_4 = wx.GridSizer(1, 2, 0, 0)

        self.checkbox_1 = wx.CheckBox(self.panel_4, wx.ID_ANY, "Select All")
        self.checkbox_1.Bind(wx.EVT_CHECKBOX, self.onSelectAll)
        sizer_4.Add(self.checkbox_1, 0, wx.EXPAND, 5)

        self.search = wx.SearchCtrl(self.panel_4, wx.ID_ANY, "")
        self.search.ShowCancelButton(True)
        sizer_4.Add(self.search, 0, wx.ALIGN_RIGHT, 0)

        self.panel_2 = wx.Panel(self.panel_1, wx.ID_ANY)
        sizer_3.Add(self.panel_2, 1, wx.EXPAND | wx.TOP, 5)

        grid_sizer_1 = wx.GridSizer(1, 1, 0, 0)

        self.check_list_box_1 = wx.CheckListBox(
            self.panel_2,
            wx.ID_ANY,
            choices=choices,
            style=wx.LB_MULTIPLE | wx.LB_NEEDED_SB,
        )
        grid_sizer_1.Add(self.check_list_box_1, 0, wx.EXPAND, 0)

        sizer_2 = wx.StdDialogButtonSizer()
        sizer_1.Add(sizer_2, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

        self.button_OK = wx.Button(self, wx.ID_OK, "")
        self.button_OK.SetDefault()
        sizer_2.AddButton(self.button_OK)

        sizer_2.Realize()

        self.panel_2.SetSizer(grid_sizer_1)

        self.panel_4.SetSizer(sizer_4)

        self.panel_3.SetSizer(grid_sizer_2)

        sizer_3.AddGrowableRow(2)
        sizer_3.AddGrowableCol(0)
        self.panel_1.SetSizer(sizer_3)

        self.SetSizer(sizer_1)

        self.SetAffirmativeId(self.button_OK.GetId())
        self.SetEscapeId(wx.ID_CANCEL)

        self.search.Bind(wx.EVT_SEARCH, self.onSearch)
        self.search.Bind(wx.EVT_CHAR, self.onChar)
        self.search.Bind(wx.EVT_SEARCH_CANCEL, self.onSearch)

        self.Bind(wx.EVT_CLOSE, self.onClose)

        if hasattr(self.Parent, "WINDOWS") and self.Parent.WINDOWS:
            self.Bind(wx.EVT_LISTBOX, self.OnListSelection)
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnBoxSelection)
        self.Bind(wx.EVT_CHAR_HOOK, self.onEscapePressed)

        self.Layout()

    @api_tool_decorator
    def onClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        else:
            self.Close()
        self.DestroyLater()

    @api_tool_decorator
    def onChar(self, event):
        event.Skip()
        wx.CallAfter(self.onSearch, event)

    @api_tool_decorator
    def onSearch(self, event=None):
        if event:
            event.Skip()
        queryString = ""
        if hasattr(event, "GetString"):
            queryString = event.GetString()
        else:
            queryString = self.search.GetValue()
        self.check_list_box_1.Clear()

        if queryString:
            sortedList = list(
                filter(
                    lambda i: queryString.lower() in i.lower(),
                    self.originalChoices,
                )
            )
            for item in sortedList:
                self.check_list_box_1.Append(item)
        else:
            for item in self.originalChoices:
                self.check_list_box_1.Append(item)
            self.check_list_box_1.SetCheckedStrings(self.selected)

    @api_tool_decorator
    def OnListSelection(self, event):
        selection = event.GetSelection()
        selectionStr = self.check_list_box_1.GetString(selection)
        checked = list(self.check_list_box_1.GetCheckedItems())
        if selection in checked:
            checked.remove(selection)
            if selectionStr in self.selected:
                self.selected.remove(selectionStr)
        else:
            checked.append(selection)
            if not selectionStr in self.selected:
                self.selected.append(selectionStr)
        self.check_list_box_1.Deselect(selection)
        self.check_list_box_1.SetCheckedItems(tuple(checked))

        if "All devices" in self.selected:
            self.checkbox_1.Set3StateValue(wx.CHK_CHECKED)
            self.onSelectEvent()
        elif len(self.selected) != len(self.originalChoices):
            self.checkbox_1.Set3StateValue(wx.CHK_UNCHECKED)
        else:
            self.checkbox_1.Set3StateValue(wx.CHK_CHECKED)

    @api_tool_decorator
    def OnBoxSelection(self, event):
        selection = event.GetSelection()
        selectionStr = self.check_list_box_1.GetString(selection)
        if selectionStr in self.selected:
            self.selected.remove(selectionStr)
        elif not selectionStr in self.selected:
            self.selected.append(selectionStr)

        if "All devices" in self.selected:
            self.checkbox_1.Set3StateValue(wx.CHK_CHECKED)
            self.onSelectEvent()
        elif len(self.selected) != len(self.originalChoices):
            self.checkbox_1.Set3StateValue(wx.CHK_UNCHECKED)
        else:
            self.checkbox_1.Set3StateValue(wx.CHK_CHECKED)

    @api_tool_decorator
    def GetSelections(self):
        return self.selected

    @api_tool_decorator
    def onSelectAll(self, event):
        event.Skip()
        wx.CallAfter(self.onSelectEvent)

    @api_tool_decorator
    def onSelectEvent(self):
        if self.checkbox_1.IsChecked():
            if "All devices" in self.originalChoices:
                self.selected = ["All devices"]
            else:
                self.selected = self.originalChoices
        else:
            self.selected = []
        self.check_list_box_1.SetCheckedStrings(self.selected)

    @api_tool_decorator
    def onEscapePressed(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_ESCAPE:
            self.onClose(event)
