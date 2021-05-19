#!/usr/bin/env python3

from Common.decorator import api_tool_decorator
from Utility.Resource import resourcePath, scale_bitmap
from Common.enum import Color
import wx
import Common.Globals as Globals

from Utility.CollectionsApi import (
    fetchCollectionList,
    createCollection,
    updateCollection,
    deleteCollection,
)


class CollectionsDialog(wx.Dialog):
    def __init__(self, parent, *args, **kwds):
        super(CollectionsDialog, self).__init__(
            None,
            wx.ID_ANY,
            size=(583, 407),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.SetSize((583, 407))
        self.SetMinSize((583, 407))
        self.SetTitle("Collections")

        self.parentFrame = parent

        self.prevSelection = None
        self.selectedCollection = None

        self.collResp, self.collections = fetchCollectionList()

        sizer_1 = wx.FlexGridSizer(2, 1, 0, 0)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_1, 1, wx.ALL | wx.EXPAND, 3)

        sizer_3 = wx.FlexGridSizer(1, 1, 0, 0)

        self.window_1 = wx.SplitterWindow(self.panel_1, wx.ID_ANY)
        self.window_1.SetMinimumPaneSize(20)
        sizer_3.Add(self.window_1, 1, wx.EXPAND, 0)

        self.window_1_pane_1 = wx.Panel(self.window_1, wx.ID_ANY)

        grid_sizer_1 = wx.FlexGridSizer(3, 1, 0, 0)

        self.panel_2 = wx.Panel(self.window_1_pane_1, wx.ID_ANY)
        grid_sizer_1.Add(self.panel_2, 1, wx.ALL | wx.EXPAND, 2)

        grid_sizer_3 = wx.GridSizer(1, 2, 0, 0)

        label_1 = wx.StaticText(self.panel_2, wx.ID_ANY, "Collection List:")
        label_1.SetFont(
            wx.Font(
                9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""
            )
        )
        grid_sizer_3.Add(label_1, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        refresh = scale_bitmap(resourcePath("Images/refresh.png"), 14, 14)
        self.bitmap_button_1 = wx.BitmapButton(
            self.panel_2,
            wx.ID_ANY,
            refresh,
        )
        self.bitmap_button_1.SetMinSize((20, 20))
        grid_sizer_3.Add(self.bitmap_button_1, 0, wx.ALIGN_RIGHT, 0)

        self.list_box_1 = wx.ListBox(
            self.window_1_pane_1, wx.ID_ANY, choices=self.collections
        )
        grid_sizer_1.Add(self.list_box_1, 0, wx.EXPAND, 0)

        self.button_1 = wx.Button(self.window_1_pane_1, wx.ID_ANY, "Delete")
        self.button_1.SetToolTip("Delete Selected Collection")
        grid_sizer_1.Add(self.button_1, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP, 2)

        self.window_1_pane_2 = wx.Panel(self.window_1, wx.ID_ANY)

        grid_sizer_2 = wx.FlexGridSizer(3, 1, 0, 0)

        self.checkbox_1 = wx.CheckBox(
            self.window_1_pane_2, wx.ID_ANY, "Modify Current Selection"
        )
        self.checkbox_1.SetFont(
            wx.Font(
                9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""
            )
        )
        grid_sizer_2.Add(
            self.checkbox_1, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL | wx.EXPAND, 2
        )

        self.panel_6 = wx.Panel(self.window_1_pane_2, wx.ID_ANY)
        grid_sizer_2.Add(self.panel_6, 1, wx.EXPAND, 0)

        grid_sizer_7 = wx.FlexGridSizer(3, 1, 0, 0)

        self.panel_3 = wx.Panel(self.panel_6, wx.ID_ANY)
        grid_sizer_7.Add(self.panel_3, 1, wx.ALL | wx.EXPAND, 2)

        grid_sizer_4 = wx.FlexGridSizer(1, 2, 0, 0)

        label_2 = wx.StaticText(self.panel_3, wx.ID_ANY, "Name:")
        label_2.SetFont(
            wx.Font(
                9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""
            )
        )
        grid_sizer_4.Add(label_2, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.text_ctrl_1 = wx.TextCtrl(self.panel_3, wx.ID_ANY, "")
        self.text_ctrl_1.SetFocus()
        grid_sizer_4.Add(self.text_ctrl_1, 0, wx.EXPAND | wx.LEFT, 5)

        self.panel_4 = wx.Panel(self.panel_6, wx.ID_ANY)
        grid_sizer_7.Add(self.panel_4, 1, wx.EXPAND, 0)

        grid_sizer_5 = wx.FlexGridSizer(2, 1, 0, 0)

        label_3 = wx.StaticText(self.panel_4, wx.ID_ANY, "Description:")
        label_3.SetFont(
            wx.Font(
                9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""
            )
        )
        grid_sizer_5.Add(label_3, 0, 0, 0)

        self.text_ctrl_3 = wx.TextCtrl(
            self.panel_4,
            wx.ID_ANY,
            "",
            style=wx.TE_MULTILINE | wx.TE_WORDWRAP,
        )
        grid_sizer_5.Add(self.text_ctrl_3, 0, wx.EXPAND, 0)

        self.panel_5 = wx.Panel(self.panel_6, wx.ID_ANY)
        grid_sizer_7.Add(self.panel_5, 1, wx.EXPAND, 0)

        grid_sizer_6 = wx.FlexGridSizer(2, 1, 0, 0)

        label_4 = wx.StaticText(self.panel_5, wx.ID_ANY, "EQL:")
        label_4.SetFont(
            wx.Font(
                9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""
            )
        )
        grid_sizer_6.Add(label_4, 0, 0, 0)

        self.text_ctrl_4 = wx.TextCtrl(
            self.panel_5,
            wx.ID_ANY,
            "",
            style=wx.TE_MULTILINE | wx.TE_WORDWRAP,
        )
        grid_sizer_6.Add(self.text_ctrl_4, 0, wx.EXPAND, 0)

        self.button_3 = wx.Button(self.window_1_pane_2, wx.ID_ANY, "Create/Modify")
        self.button_3.SetToolTip("Create or Modify Collection")
        self.button_3.Enable(False)
        grid_sizer_2.Add(self.button_3, 0, wx.TOP, 2)

        sizer_2 = wx.StdDialogButtonSizer()
        sizer_1.Add(sizer_2, 0, wx.ALIGN_RIGHT, 0)

        self.button_2 = wx.Button(self, wx.ID_EXECUTE, "Execute EQL")
        self.button_2.Enable(False)
        sizer_2.Add(self.button_2, 0, wx.ALL, 5)

        sizer_2.Realize()

        grid_sizer_6.AddGrowableRow(1)
        grid_sizer_6.AddGrowableCol(0)
        self.panel_5.SetSizer(grid_sizer_6)

        grid_sizer_5.AddGrowableRow(1)
        grid_sizer_5.AddGrowableCol(0)
        self.panel_4.SetSizer(grid_sizer_5)

        grid_sizer_4.AddGrowableCol(1)
        self.panel_3.SetSizer(grid_sizer_4)

        grid_sizer_7.AddGrowableRow(1)
        grid_sizer_7.AddGrowableRow(2)
        grid_sizer_7.AddGrowableCol(0)
        self.panel_6.SetSizer(grid_sizer_7)

        grid_sizer_2.AddGrowableRow(1)
        grid_sizer_2.AddGrowableCol(0)
        self.window_1_pane_2.SetSizer(grid_sizer_2)

        self.panel_2.SetSizer(grid_sizer_3)

        grid_sizer_1.AddGrowableRow(1)
        grid_sizer_1.AddGrowableCol(0)
        self.window_1_pane_1.SetSizer(grid_sizer_1)

        self.window_1.SplitVertically(self.window_1_pane_1, self.window_1_pane_2)

        sizer_3.AddGrowableRow(0)
        sizer_3.AddGrowableCol(0)
        self.panel_1.SetSizer(sizer_3)

        sizer_1.AddGrowableRow(0)
        sizer_1.AddGrowableCol(0)
        self.SetSizer(sizer_1)

        self.SetAffirmativeId(self.button_2.GetId())

        self.Layout()
        self.Centre()

        if hasattr(self.parentFrame, "WINDOWS") and self.parentFrame.WINDOWS:
            self.list_box_1.Bind(wx.EVT_LISTBOX, self.onSelection)
            self.list_box_1.Bind(wx.EVT_LISTBOX_DCLICK, self.onSelection)
        self.button_1.Bind(wx.EVT_BUTTON, self.deleteCollection)
        self.button_2.Bind(wx.EVT_BUTTON, self.onExecute)
        self.button_3.Bind(wx.EVT_BUTTON, self.createCollection)

        self.checkbox_1.Bind(wx.EVT_CHECKBOX, self.onInput)
        self.text_ctrl_1.Bind(wx.EVT_CHAR, self.onInput)
        self.text_ctrl_3.Bind(wx.EVT_CHAR, self.onInput)
        self.text_ctrl_4.Bind(wx.EVT_CHAR, self.onInput)

        self.Bind(wx.EVT_CLOSE, self.onExecute)
        self.bitmap_button_1.Bind(wx.EVT_BUTTON, self.updateCollectionList)

    @api_tool_decorator
    def onExecute(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        elif self.IsShown():
            self.Close()
        # self.DestroyLater()

    @api_tool_decorator
    def onInput(self, event):
        event.Skip()
        wx.CallAfter(self.checkInputs)

    @api_tool_decorator
    def checkInputs(self):
        matchNames = list(
            filter(
                lambda x: x["name"] == self.text_ctrl_1.GetValue(),
                self.collResp["results"],
            )
        )
        if not self.text_ctrl_4.GetValue():
            self.text_ctrl_4.SetBackgroundColour(Color.lightRed.value)
        else:
            self.text_ctrl_4.SetBackgroundColour(Color.white.value)

        if matchNames and not self.checkbox_1.IsChecked():
            self.text_ctrl_1.SetBackgroundColour(Color.lightRed.value)
        elif not matchNames or self.checkbox_1.IsChecked():
            self.text_ctrl_1.SetBackgroundColour(Color.white.value)

        if not self.text_ctrl_4.GetValue():
            self.text_ctrl_4.SetBackgroundColour(Color.lightRed.value)
        else:
            self.text_ctrl_4.SetBackgroundColour(Color.white.value)
        if (
            self.text_ctrl_1.GetValue()
            and self.text_ctrl_4.GetValue()
            and not self.text_ctrl_4.GetBackgroundColour() == Color.lightRed.value
            and not self.text_ctrl_1.GetBackgroundColour() == Color.lightRed.value
        ):
            self.button_3.Enable(True)
        else:
            self.button_3.Enable(False)

    @api_tool_decorator
    def onSelection(self, event):
        currentSelection = self.list_box_1.GetSelection()
        if currentSelection == self.prevSelection:
            self.list_box_1.Deselect(currentSelection)
            self.text_ctrl_1.SetValue("")
            self.text_ctrl_3.SetValue("")
            self.text_ctrl_4.SetValue("")
            self.prevSelection = None
            self.button_2.Enable(False)
            return
        self.prevSelection = self.list_box_1.GetSelection()
        self.selectedCollection = None
        selectionStr = self.list_box_1.GetString(currentSelection)
        for collection in self.collResp["results"]:
            if collection["name"] == selectionStr:
                self.selectedCollection = collection
                break
        if self.selectedCollection:
            self.button_2.Enable(False)
            myCursor = wx.Cursor(wx.CURSOR_WAIT)
            self.SetCursor(myCursor)
            self.text_ctrl_1.SetValue(self.selectedCollection["name"])
            self.text_ctrl_3.SetValue(self.selectedCollection["description"])
            self.text_ctrl_4.SetValue(self.selectedCollection["eql"])
            self.button_2.Enable(True)
        elif self.parentFrame and hasattr(self.parentFrame, "Logging"):
            self.parentFrame.Logging("Failed to find matching collection", isError=True)
        myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
        self.SetCursor(myCursor)

    @api_tool_decorator
    def createCollection(self, event):
        error = False
        if not self.text_ctrl_3.GetValue():
            self.text_ctrl_3.SetBackgroundColour(Color.lightRed.value)
            error = True
        if not self.text_ctrl_1.GetValue():
            self.text_ctrl_1.SetBackgroundColour(Color.lightRed.value)
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
                        "name": self.text_ctrl_1.GetValue(),
                        "description": self.text_ctrl_3.GetValue(),
                        "eql": self.text_ctrl_4.GetValue(),
                    },
                )
            elif self.parentFrame and hasattr(self.parentFrame, "Logging"):
                self.parentFrame.Logging(
                    "Failed to find matching collection", isError=True
                )
        else:
            createCollection(
                {
                    "name": self.text_ctrl_1.GetValue(),
                    "enterprise_id": Globals.enterprise_id,
                    "description": self.text_ctrl_3.GetValue(),
                    "eql": self.text_ctrl_4.GetValue(),
                }
            )
        self.text_ctrl_1.SetBackgroundColour(Color.white.value)
        self.text_ctrl_3.SetBackgroundColour(Color.white.value)
        self.text_ctrl_4.SetBackgroundColour(Color.white.value)
        self.text_ctrl_1.SetValue("")
        self.text_ctrl_3.SetValue("")
        self.text_ctrl_4.SetValue("")
        self.button_3.Enable(False)
        self.updateCollectionList()

    @api_tool_decorator
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

    @api_tool_decorator
    def updateCollectionList(self, event=None):
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)
        self.button_2.Enable(False)
        self.prevSelection = None
        self.selectedCollection = None
        self.collResp, self.collections = fetchCollectionList()
        self.list_box_1.Clear()
        self.text_ctrl_1.SetValue("")
        self.text_ctrl_3.SetValue("")
        self.text_ctrl_4.SetValue("")
        self.checkbox_1.Set3StateValue(wx.CHK_UNCHECKED)
        for collection in self.collections:
            self.list_box_1.Append(collection)
        myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
        self.SetCursor(myCursor)

    @api_tool_decorator
    def getSelectionEql(self):
        if self.selectedCollection and "eql" in self.selectedCollection:
            return self.selectedCollection["eql"]
        else:
            return None
