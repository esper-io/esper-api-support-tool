#!/usr/bin/env python

from Common.decorator import api_tool_decorator
import Common.Globals as Globals
import wx


class ColumnVisibilityDialog(wx.Dialog):
    def __init__(self, parent, grid, choiceData=[]):
        # begin wxGlade: MyDialog.__init__
        super(ColumnVisibilityDialog, self).__init__(
            parent,
            wx.ID_ANY,
            style=wx.DEFAULT_DIALOG_STYLE,
        )
        self.grid = grid

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.panel_3 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.check_list_box_1 = wx.CheckListBox(
            self.panel_3,
            wx.ID_ANY,
            choices=choiceData,
            style=wx.LB_HSCROLL | wx.LB_NEEDED_SB,
        )
        self.panel_2 = wx.Panel(self, wx.ID_ANY)
        self.button_1 = wx.Button(self.panel_2, wx.ID_APPLY, "Apply")
        self.button_2 = wx.Button(self.panel_2, wx.ID_CANCEL, "Cancel")

        self.button_1.Bind(wx.EVT_BUTTON, self.OnApply)
        self.button_2.Bind(wx.EVT_BUTTON, self.OnClose)

        if (
            hasattr(self.Parent.parentFrame, "WINDOWS")
            and self.Parent.parentFrame.WINDOWS
        ):
            self.Bind(wx.EVT_LISTBOX, self.OnSelection)
            self.Bind(wx.EVT_LISTBOX_DCLICK, self.OnSelection)

        colNum = 0
        for _ in choiceData:
            isShown = self.grid.IsColShown(colNum + 1)
            self.check_list_box_1.Check(colNum, isShown)
            colNum += 1

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    @api_tool_decorator
    def OnSelection(self, event):
        selection = event.GetSelection()
        self.check_list_box_1.Deselect(selection)
        checked = list(self.check_list_box_1.GetCheckedItems())
        if selection in checked:
            checked.remove(selection)
        else:
            checked.append(selection)
        self.check_list_box_1.SetCheckedItems(tuple(checked))

    @api_tool_decorator
    def OnApply(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        elif self.IsShown():
            self.Close()
        # self.DestroyLater()

    @api_tool_decorator
    def OnClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        elif self.IsShown():
            self.Close()
        self.DestroyLater()

    @api_tool_decorator
    def isChecked(self, item):
        return self.check_list_box_1.IsChecked(item)

    @api_tool_decorator
    def __set_properties(self):
        # begin wxGlade: MyDialog.__set_properties
        self.SetTitle("Column Visibility")
        self.panel_3.SetMinSize((354, 150))
        self.panel_3.SetBackgroundColour(wx.Colour(255, 119, 255))
        # end wxGlade

    @api_tool_decorator
    def __do_layout(self):
        # begin wxGlade: MyDialog.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.GridSizer(1, 2, 0, 0)
        grid_sizer_1 = wx.GridSizer(1, 2, 0, 0)
        sizer_3 = wx.StaticBoxSizer(
            wx.StaticBox(self.panel_1, wx.ID_ANY, "Column Visibility"), wx.VERTICAL
        )
        sizer_4 = wx.GridSizer(1, 1, 0, 0)
        sizer_4.Add(self.check_list_box_1, 0, wx.EXPAND, 0)
        self.panel_3.SetSizer(sizer_4)
        sizer_3.Add(self.panel_3, 0, wx.ALL | wx.EXPAND, 5)
        self.panel_1.SetSizer(sizer_3)
        sizer_1.Add(self.panel_1, 0, wx.ALL | wx.EXPAND, 5)
        sizer_2.Add((0, 0), 0, 0, 0)
        grid_sizer_1.Add(
            self.button_1, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, 5
        )
        grid_sizer_1.Add(
            self.button_2, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, 5
        )
        sizer_2.Add(grid_sizer_1, 1, wx.EXPAND, 0)
        self.panel_2.SetSizer(sizer_2)
        sizer_1.Add(self.panel_2, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()
        # end wxGlade
