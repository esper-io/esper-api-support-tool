#!/usr/bin/env python3

from Common.enum import Color
import wx
import Common.Globals as Globals

from Utility.CollectionsApi import (
    fetchCollectionList,
    createCollection,
    retrieveCollection,
    updateCollection,
    deleteCollection,
)


class CollectionsDialog(wx.Dialog):
    def __init__(self, parent, *args, **kwds):
        super(CollectionsDialog, self).__init__(
            None,
            wx.ID_ANY,
            size=(583, 407),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.STAY_ON_TOP,
        )
        self.SetSize((583, 407))
        self.SetMinSize((583, 407))
        self.SetTitle("Collections")

        self.parentFrame = parent

        self.prevSelection = None

        self.collResp, self.collections = fetchCollectionList()

        sizer_1 = wx.FlexGridSizer(3, 1, 0, 0)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_1, 1, wx.ALL | wx.EXPAND, 3)

        sizer_3 = wx.FlexGridSizer(1, 1, 0, 0)

        self.window_1 = wx.SplitterWindow(self.panel_1, wx.ID_ANY)
        self.window_1.SetMinimumPaneSize(20)
        sizer_3.Add(self.window_1, 1, wx.EXPAND, 0)

        self.window_1_pane_1 = wx.Panel(self.window_1, wx.ID_ANY)

        sizer_4 = wx.FlexGridSizer(3, 1, 0, 0)

        label_2 = wx.StaticText(self.window_1_pane_1, wx.ID_ANY, "List of Collections:")
        sizer_4.Add(label_2, 0, 0, 0)

        self.list_box_1 = wx.ListBox(
            self.window_1_pane_1, wx.ID_ANY, choices=self.collections
        )
        sizer_4.Add(self.list_box_1, 0, wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.RIGHT, 0)

        self.button_1 = wx.Button(self.window_1_pane_1, wx.ID_ANY, "Delete")
        self.button_1.SetToolTip("Delete Selected Collection")
        sizer_4.Add(self.button_1, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.window_1_pane_2 = wx.Panel(self.window_1, wx.ID_ANY)

        sizer_5 = wx.FlexGridSizer(5, 1, 0, 0)

        label_4 = wx.StaticText(
            self.window_1_pane_2, wx.ID_ANY, "Create Collection (Insert EQL Below):"
        )
        sizer_5.Add(label_4, 0, 0, 0)

        self.checkbox_1 = wx.CheckBox(
            self.window_1_pane_2, wx.ID_ANY, "Modify Current Selection"
        )
        sizer_5.Add(self.checkbox_1, 0, 0, 0)

        grid_sizer_2 = wx.GridSizer(1, 2, 0, 0)
        sizer_5.Add(grid_sizer_2, 1, wx.EXPAND, 0)

        label_5 = wx.StaticText(self.window_1_pane_2, wx.ID_ANY, "Name:")
        grid_sizer_2.Add(label_5, 0, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0)

        self.text_ctrl_3 = wx.TextCtrl(self.window_1_pane_2, wx.ID_ANY, "")
        grid_sizer_2.Add(self.text_ctrl_3, 0, wx.EXPAND, 0)

        self.panel_4 = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        sizer_5.Add(self.panel_4, 1, wx.EXPAND | wx.TOP, 3)

        grid_sizer_1 = wx.GridSizer(1, 1, 0, 0)

        self.text_ctrl_2 = wx.TextCtrl(
            self.panel_4, wx.ID_ANY, "", style=wx.TE_BESTWRAP | wx.TE_MULTILINE
        )
        grid_sizer_1.Add(self.text_ctrl_2, 0, wx.EXPAND, 0)

        self.button_3 = wx.Button(self.window_1_pane_2, wx.ID_ANY, "Create")
        self.button_3.SetToolTip("Create Collection")
        self.button_3.Enable(False)
        sizer_5.Add(self.button_3, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0)

        self.panel_3 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_3, 1, wx.ALL | wx.EXPAND, 3)

        sizer_7 = wx.FlexGridSizer(2, 1, 0, 0)

        label_3 = wx.StaticText(
            self.panel_3, wx.ID_ANY, "Selected Collecction EQL Preview:"
        )
        sizer_7.Add(label_3, 0, 0, 0)

        self.text_ctrl_1 = wx.TextCtrl(self.panel_3, wx.ID_ANY, "")
        sizer_7.Add(self.text_ctrl_1, 0, wx.ALL | wx.EXPAND, 3)

        sizer_2 = wx.StdDialogButtonSizer()
        sizer_1.Add(sizer_2, 0, wx.ALIGN_RIGHT, 0)

        self.button_2 = wx.Button(self, wx.ID_ANY, "Execute EQL")
        sizer_2.Add(self.button_2, 0, wx.ALL, 5)

        sizer_2.Realize()

        sizer_7.AddGrowableRow(1)
        sizer_7.AddGrowableCol(0)
        self.panel_3.SetSizer(sizer_7)

        self.panel_4.SetSizer(grid_sizer_1)

        sizer_5.AddGrowableRow(3)
        sizer_5.AddGrowableCol(0)
        self.window_1_pane_2.SetSizer(sizer_5)

        sizer_4.AddGrowableRow(1)
        sizer_4.AddGrowableCol(0)
        self.window_1_pane_1.SetSizer(sizer_4)

        self.window_1.SplitVertically(self.window_1_pane_1, self.window_1_pane_2)

        sizer_3.AddGrowableRow(0)
        sizer_3.AddGrowableCol(0)
        self.panel_1.SetSizer(sizer_3)

        sizer_1.AddGrowableRow(0)
        sizer_1.AddGrowableRow(1)
        sizer_1.AddGrowableCol(0)
        self.SetSizer(sizer_1)

        self.SetAffirmativeId(self.button_2.GetId())

        self.Layout()
        self.Centre()

        self.list_box_1.Bind(wx.EVT_LISTBOX, self.onSelection)
        self.list_box_1.Bind(wx.EVT_LISTBOX_DCLICK, self.onSelection)
        self.button_1.Bind(wx.EVT_BUTTON, self.deleteCollection)
        self.button_3.Bind(wx.EVT_BUTTON, self.createCollection)
        self.text_ctrl_2.Bind(wx.EVT_CHAR, self.onInput)
        self.text_ctrl_3.Bind(wx.EVT_CHAR, self.onInput)

    def onInput(self, event):
        event.Skip()
        wx.CallAfter(self.checkInputs)

    def checkInputs(self):
        if self.text_ctrl_3.GetValue() and self.text_ctrl_2.GetValue():
            self.button_3.Enable(True)
        else:
            self.button_3.Enable(False)

    def onSelection(self, event):
        currentSelection = self.list_box_1.GetSelection()
        if currentSelection == self.prevSelection:
            self.list_box_1.Deselect(currentSelection)
            self.text_ctrl_1.SetValue("")
            self.prevSelection = None
            return
        self.prevSelection = self.list_box_1.GetSelection()
        id = None
        selectionStr = self.list_box_1.GetString(currentSelection)
        for collection in self.collResp["results"]:
            if collection["name"] == selectionStr:
                id = collection["id"]
                break
        if id:
            myCursor = wx.Cursor(wx.CURSOR_WAIT)
            self.SetCursor(myCursor)
            self.selectedCollection = retrieveCollection(id, returnJson=True)
            self.text_ctrl_1.SetValue(self.selectedCollection["eql"])
            self.text_ctrl_3.SetValue(self.selectedCollection["name"])
        elif self.parentFrame and hasattr(self.parentFrame, "Logging"):
            self.parentFrame.Logging("Failed to find matching collection", isError=True)
        myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
        self.SetCursor(myCursor)

    def createCollection(self, event):
        error = False
        if not self.text_ctrl_3.GetValue():
            self.text_ctrl_3.SetBackgroundColour(Color.lightRed.value)
            error = True
        if not self.text_ctrl_2.GetValue():
            self.text_ctrl_2.SetBackgroundColour(Color.lightRed.value)
            error = True
        if error:
            return

        if self.checkbox_1.IsChecked():
            id = None
            selectionStr = self.list_box_1.GetString(self.list_box_1.GetSelection())
            for collection in self.collResp["results"]:
                if collection["name"] == selectionStr:
                    id = collection["id"]
                    break
            if id:
                updateCollection(
                    id,
                    {
                        "name": self.text_ctrl_3.GetValue(),
                        "description": self.selectedCollection["description"],
                        "eql": self.text_ctrl_2.GetValue(),
                    },
                )
            elif self.parentFrame and hasattr(self.parentFrame, "Logging"):
                self.parentFrame.Logging(
                    "Failed to find matching collection", isError=True
                )
        else:
            createCollection(
                {
                    "name": self.text_ctrl_3.GetValue(),
                    "enterprise_id": Globals.enterprise_id,
                    "description": "",
                    "eql": self.text_ctrl_2.GetValue(),
                }
            )
        self.text_ctrl_2.SetBackgroundColour(Color.white.value)
        self.text_ctrl_3.SetBackgroundColour(Color.white.value)
        self.text_ctrl_3.SetValue(""),
        self.text_ctrl_2.SetValue(""),
        self.updateCollectionList()

    def deleteCollection(self, event):
        id = None
        selectionStr = self.list_box_1.GetString(self.list_box_1.GetSelection())
        for collection in self.collResp["results"]:
            if collection["name"] == selectionStr:
                id = collection["id"]
                break
        if id:
            myCursor = wx.Cursor(wx.CURSOR_WAIT)
            self.SetCursor(myCursor)
            deleteCollection(id)
            if self.parentFrame and hasattr(self.parentFrame, "Logging"):
                self.parentFrame.Logging("Collection has been deleted")
        elif self.parentFrame and hasattr(self.parentFrame, "Logging"):
            self.parentFrame.Logging("Failed to find matching collection", isError=True)
        self.updateCollectionList()

    def updateCollectionList(self):
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)
        self.prevSelection = None
        self.collResp, self.collections = fetchCollectionList()
        self.list_box_1.Clear()
        for collection in self.collections:
            self.list_box_1.Append(collection)
        myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
        self.SetCursor(myCursor)