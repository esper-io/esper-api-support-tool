#!/usr/bin/env python3

import wx


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

        # self.Parent = parent
        self.originalChoices = choices
        self.selected = []

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_1, 1, wx.ALL | wx.EXPAND, 5)

        sizer_3 = wx.FlexGridSizer(2, 1, 0, 0)

        self.panel_3 = wx.Panel(self.panel_1, wx.ID_ANY)
        sizer_3.Add(self.panel_3, 1, wx.EXPAND, 0)

        grid_sizer_2 = wx.GridSizer(1, 2, 0, 0)

        label_1 = wx.StaticText(self.panel_3, wx.ID_ANY, label)
        grid_sizer_2.Add(label_1, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.search = wx.SearchCtrl(self.panel_3, wx.ID_ANY, "")
        self.search.ShowCancelButton(True)
        grid_sizer_2.Add(self.search, 0, wx.ALIGN_RIGHT, 0)
        self.search.SetFocus()

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

        self.panel_3.SetSizer(grid_sizer_2)

        sizer_3.AddGrowableRow(1)
        sizer_3.AddGrowableCol(0)
        self.panel_1.SetSizer(sizer_3)

        self.SetSizer(sizer_1)

        self.SetAffirmativeId(self.button_OK.GetId())
        self.SetEscapeId(wx.ID_CANCEL)

        self.search.Bind(wx.EVT_SEARCH, self.onSearch)
        self.search.Bind(wx.EVT_CHAR, self.onChar)
        self.search.Bind(wx.EVT_SEARCH_CANCEL, self.onSearch)

        self.Bind(wx.EVT_CLOSE, self.onClose)

        self.Bind(wx.EVT_LISTBOX, self.OnListSelection)
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnBoxSelection)

        self.Layout()

    def onClose(self, event):
        if event.EventType != wx.EVT_CLOSE.typeId:
            self.Close()
        self.Destroy()

    def onChar(self, event):
        event.Skip()
        wx.CallAfter(self.onSearch, event)

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
        self.check_list_box_1.SetCheckedItems(tuple(checked))

    def OnBoxSelection(self, event):
        selection = event.GetSelection()
        selectionStr = self.check_list_box_1.GetString(selection)
        if selectionStr in self.selected:
            self.selected.remove(selectionStr)
        elif not selectionStr in self.selected:
            self.selected.append(selectionStr)

    def GetSelections(self):
        return self.selected
