#!/usr/bin/env python3

import csv
from pathlib import Path

import pandas as pd
import wx
import wx.grid as gridlib

import Common.Globals as Globals
from Common.decorator import api_tool_decorator
from Common.enum import Color
from GUI.GridTable import GridTable
from GUI.TabPanel import TabPanel
from Utility.API.GroupUtility import (
    createGroup,
    deleteGroup,
    fetchGroupName,
    getAllGroups,
    renameGroup,
)
from Utility.FileUtility import read_csv_via_pandas, read_data_from_csv, read_excel_via_openpyxl, write_data_to_csv
from Utility.Resource import (
    correctSaveFileName,
    displayMessageBox,
    displayFileDialog,
    isApiKey,
    openWebLinkInBrowser,
    resourcePath,
    scale_bitmap,
)


class GroupManagement(wx.Dialog):
    def __init__(self, groups, *args, **kwds):

        self.groups = groups
        self.groupTree = {}
        self.tree = {}
        self.uploadTreeItems = {}
        self.uploadCSVTreeItems = []
        self.current_page = None
        self.groupNameToId = {}
        self.groupIdToName = {}
        self.isBusy = False
        self.expectedHeaders = [
            "Group Name",
            "Parent Group Identifier",
            "New Group Name",
        ]
        self.rootId = None
        self.root = None

        super(GroupManagement, self).__init__(
            Globals.frame,
            wx.ID_ANY,
            style=wx.DEFAULT_DIALOG_STYLE | wx.MAXIMIZE_BOX | wx.RESIZE_BORDER,
        )
        self.SetSize((800, 500))
        self.SetMinSize((800, 500))
        self.SetTitle("Group Management")
        self.SetThemeEnabled(False)

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        self.notebook_1 = wx.Notebook(self, wx.ID_ANY)
        self.notebook_1.SetThemeEnabled(False)
        sizer_1.Add(self.notebook_1, 1, wx.ALL | wx.EXPAND, 5)

        self.notebook_1_pane_1 = TabPanel(self.notebook_1, wx.ID_ANY, "Single")
        self.notebook_1.AddPage(self.notebook_1_pane_1, "Single")

        grid_sizer_1 = wx.FlexGridSizer(5, 1, 0, 0)

        label_1 = wx.StaticText(self.notebook_1_pane_1, wx.ID_ANY, "Groups:")
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
        grid_sizer_1.Add(label_1, 0, 0, 0)

        label_2 = wx.StaticText(
            self.notebook_1_pane_1,
            wx.ID_ANY,
            "Select a group from the list below and then select one of the actions below",
            style=wx.ST_ELLIPSIZE_END,
        )
        label_2.SetToolTip(
            "Select a group from the list below and then select one of the actions below"
        )
        label_2.Wrap(1)
        grid_sizer_1.Add(label_2, 0, wx.BOTTOM | wx.EXPAND, 5)

        grid_sizer_2 = wx.GridSizer(1, 2, 0, 0)
        grid_sizer_1.Add(grid_sizer_2, 1, wx.BOTTOM | wx.EXPAND | wx.TOP, 5)

        label_5 = wx.StaticText(self.notebook_1_pane_1, wx.ID_ANY, "Group Name")
        label_5.SetFont(
            wx.Font(
                Globals.FONT_SIZE,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "NormalBold",
            )
        )
        grid_sizer_2.Add(label_5, 0, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0)

        self.text_ctrl_1 = wx.TextCtrl(self.notebook_1_pane_1, wx.ID_ANY, "")
        grid_sizer_2.Add(self.text_ctrl_1, 0, wx.EXPAND, 0)

        self.button_3 = wx.Button(self.notebook_1_pane_1, wx.ID_REFRESH, "")
        self.button_3.SetToolTip("Refresh Group listing")
        grid_sizer_1.Add(self.button_3, 0, wx.ALIGN_RIGHT | wx.BOTTOM, 5)

        self.tree_ctrl_1 = wx.TreeCtrl(
            self.notebook_1_pane_1,
            wx.ID_ANY,
            style=wx.TR_EDIT_LABELS
            | wx.TR_HAS_BUTTONS
            | wx.TR_SINGLE
            | wx.WANTS_CHARS
            | wx.TR_HIDE_ROOT,
        )
        grid_sizer_1.Add(self.tree_ctrl_1, 1, wx.EXPAND, 0)

        self.notebook_1_pane_2 = TabPanel(self.notebook_1, wx.ID_ANY, "Bulk")
        self.notebook_1.AddPage(self.notebook_1_pane_2, "Bulk")

        grid_sizer_4 = wx.FlexGridSizer(4, 1, 0, 0)

        label_4 = wx.StaticText(self.notebook_1_pane_2, wx.ID_ANY, "CSV Upload:")
        label_4.SetFont(
            wx.Font(
                Globals.FONT_SIZE,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "NormalBold",
            )
        )
        grid_sizer_4.Add(label_4, 0, 0, 0)

        label_3 = wx.StaticText(
            self.notebook_1_pane_2,
            wx.ID_ANY,
            "Upload a CSV to rename a bunch of groups: ",
            style=wx.ST_ELLIPSIZE_END,
        )
        label_3.SetToolTip(
            "Select a group from the list below and then select one of the actions below"
        )
        label_3.Wrap(1)
        grid_sizer_4.Add(label_3, 0, wx.BOTTOM | wx.EXPAND, 5)

        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_4.Add(sizer_3, 1, wx.ALIGN_RIGHT | wx.EXPAND, 0)

        self.button_7 = wx.Button(
            self.notebook_1_pane_2, wx.ID_ANY, "Download Group CSV"
        )
        self.button_7.SetToolTip("Upload CSV file")
        sizer_3.Add(self.button_7, 0, wx.BOTTOM | wx.RIGHT, 5)

        self.button_6 = wx.Button(self.notebook_1_pane_2, wx.ID_ANY, "Upload CSV")
        self.button_6.SetToolTip("Upload CSV file")
        sizer_3.Add(self.button_6, 0, wx.BOTTOM | wx.RIGHT, 5)

        self.notebook_2 = wx.Notebook(self.notebook_1_pane_2, wx.ID_ANY)
        grid_sizer_4.Add(self.notebook_2, 1, wx.EXPAND, 0)

        self.notebook_2_pane_1 = TabPanel(self.notebook_2, wx.ID_ANY, "Tree")
        self.notebook_2.AddPage(self.notebook_2_pane_1, "Tree Preview")

        sizer_4 = wx.FlexGridSizer(2, 1, 0, 0)

        refresh = scale_bitmap(resourcePath("Images/refresh.png"), 14, 14)
        self.button_5 = wx.BitmapButton(
            self.notebook_2_pane_1,
            wx.ID_ANY,
            refresh,
        )
        self.button_5.SetToolTip("Refresh Preview Tree. Will clear uploaded data.")
        self.button_5.SetMinSize((20, 20))
        sizer_4.Add(self.button_5, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        self.tree_ctrl_2 = wx.TreeCtrl(
            self.notebook_2_pane_1, wx.ID_ANY, style=wx.TR_HIDE_ROOT
        )
        sizer_4.Add(self.tree_ctrl_2, 1, wx.EXPAND, 0)

        self.notebook_2_pane_2 = TabPanel(self.notebook_2, wx.ID_ANY, "Grid")
        self.notebook_2.AddPage(self.notebook_2_pane_2, "Grid Preview")

        sizer_5 = wx.GridSizer(1, 1, 0, 0)

        self.group_grid = GridTable(self.notebook_2_pane_2, headers=self.expectedHeaders)
        sizer_5.Add(self.group_grid, 1, wx.EXPAND, 0)

        sizer_2 = wx.StdDialogButtonSizer()
        sizer_1.Add(sizer_2, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

        self.button_1 = wx.Button(self, wx.ID_ADD, "")
        sizer_2.Add(self.button_1, 0, wx.RIGHT, 5)

        self.button_4 = wx.Button(self, wx.ID_ANY, "Rename")
        sizer_2.Add(self.button_4, 0, 0, 0)

        self.button_2 = wx.Button(self, wx.ID_DELETE, "")
        sizer_2.Add(self.button_2, 0, wx.LEFT, 5)

        sizer_2.Realize()

        self.notebook_2_pane_2.SetSizer(sizer_5)

        sizer_4.AddGrowableRow(1)
        sizer_4.AddGrowableCol(0)
        self.notebook_2_pane_1.SetSizer(sizer_4)

        grid_sizer_4.AddGrowableRow(3)
        grid_sizer_4.AddGrowableCol(0)
        self.notebook_1_pane_2.SetSizer(grid_sizer_4)

        grid_sizer_1.AddGrowableRow(4)
        grid_sizer_1.AddGrowableCol(0)
        self.notebook_1_pane_1.SetSizer(grid_sizer_1)

        self.SetSizer(sizer_1)

        self.Layout()

        self.group_grid.AutoSizeColumns()

        self.button_2.Enable(False)
        self.button_1.Enable(False)
        self.button_4.Enable(False)

        self.Bind(wx.EVT_CHAR_HOOK, self.onEscapePressed)

        self.button_3.Bind(wx.EVT_BUTTON, self.refreshTree)
        self.button_4.Bind(wx.EVT_BUTTON, self.renameGroup)
        self.button_2.Bind(wx.EVT_BUTTON, self.deleteGroup)
        self.button_1.Bind(wx.EVT_BUTTON, self.addSubGroup)
        self.button_6.Bind(wx.EVT_BUTTON, self.onUpload)
        self.button_7.Bind(wx.EVT_BUTTON, self.downloadCSV)
        self.button_5.Bind(wx.EVT_BUTTON, self.refreshTree)
        self.tree_ctrl_1.Bind(wx.EVT_TREE_SEL_CHANGED, self.checkActions)
        self.notebook_1.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_tab_change)

        self.createRootNodes()
        self.createTreeLayout()
        self.tree_ctrl_1.ExpandAll()
        self.tree_ctrl_2.ExpandAll()

        self.Fit()

    def createRootNodes(self):
        self.root = self.tree_ctrl_1.AddRoot("", -1)
        self.rootId = -1
        self.tree[self.rootId] = self.root

        root = self.tree_ctrl_2.AddRoot("", -1)
        self.uploadTreeItems[self.rootId] = root

    @api_tool_decorator()
    def onEscapePressed(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_ESCAPE:
            self.onClose(event)
        event.Skip()

    @api_tool_decorator()
    def onClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        elif self.IsShown():
            self.Close()
        self.DestroyLater()

    def createTreeLayout(self):
        unsorted = []
        if self.groups:
            for group in self.groups:
                groupName, groupId, groupParent = self.obtainGroupInfoFromGroupObject(
                    group
                )
                if groupName not in self.groupNameToId:
                    self.groupNameToId[groupName] = []
                self.groupNameToId[groupName].append(groupId)
                self.groupIdToName[groupId] = groupName
                parentId = self.getGroupIdFromURL(groupParent)
                if not groupParent and not self.root:
                    self.rootId = groupId
                    self.groupTree[groupId] = []
                    self.root = self.tree_ctrl_1.AddRoot(groupName, data=groupId)
                    root2 = self.tree_ctrl_2.AddRoot(groupName, data=groupId)
                    self.tree[groupId] = self.root
                    self.uploadTreeItems[groupId] = root2
                    continue
                elif not groupParent and self.root:
                    self.groupTree[groupId] = []
                    entry = self.tree_ctrl_1.AppendItem(
                        self.tree[self.rootId], groupName, data=groupId
                    )
                    entry2 = self.tree_ctrl_2.AppendItem(
                        self.uploadTreeItems[self.rootId], groupName, data=groupId
                    )
                    self.tree[groupId] = entry
                    self.uploadTreeItems[groupId] = entry2
                    continue
                if parentId in self.groupTree.keys():
                    self.groupTree[parentId].append({groupId: []})
                    entry = self.tree_ctrl_1.AppendItem(
                        self.tree[parentId], groupName, data=groupId
                    )
                    entry2 = self.tree_ctrl_2.AppendItem(
                        self.uploadTreeItems[parentId], groupName, data=groupId
                    )
                    self.tree[groupId] = entry
                    self.uploadTreeItems[groupId] = entry2
                else:
                    unsorted.append(group)

        if len(unsorted) > 250:
            for group in unsorted:
                groupName, groupId, _ = self.obtainGroupInfoFromGroupObject(group)
                entry = self.tree_ctrl_1.AppendItem(
                    self.tree[self.rootId], groupName, data=groupId
                )
                entry2 = self.tree_ctrl_2.AppendItem(
                    self.uploadTreeItems[self.rootId], groupName, data=groupId
                )
                self.tree[groupId] = entry
                self.uploadTreeItems[groupId] = entry2
        else:
            while len(unsorted) > 0:
                newUnsorted = []
                for group in unsorted:
                    _, _, groupParent = self.obtainGroupInfoFromGroupObject(group)
                    parentId = self.getGroupIdFromURL(groupParent)
                    success = self.addGroupAsChild(self.groupTree, parentId, group)
                    if not success:
                        newUnsorted.append(group)
                unsorted = newUnsorted

    def addGroupAsChild(self, src, dest, group):
        for key, value in src.items():
            groupName, groupId, _ = self.obtainGroupInfoFromGroupObject(group)
            if key == dest:
                value.append({groupId: []})
                entry = self.tree_ctrl_1.AppendItem(
                    self.tree[dest], groupName, data=groupId
                )
                entry2 = self.tree_ctrl_2.AppendItem(
                    self.uploadTreeItems[dest], groupName, data=groupId
                )
                self.tree[groupId] = entry
                self.uploadTreeItems[groupId] = entry2
                return True
            for child in value:
                success = self.addGroupAsChild(child, dest, group)
                if success:
                    return True
        return False

    def refreshTree(self, event=None, forceRefresh=False):
        if not self.isBusy or forceRefresh:
            self.setCursorBusy()
            self.tree_ctrl_1.DeleteAllItems()
            self.tree_ctrl_2.DeleteAllItems()
            self.groupTree = {}
            self.tree = {}
            self.uploadTreeItems = {}
            self.uploadCSVTreeItems = []
            self.createRootNodes()
            groupResp = getAllGroups(tolerance=1)
            if hasattr(groupResp, "results"):
                self.groups = groupResp.results
            elif type(groupResp) is dict and "results" in groupResp:
                self.groups = groupResp["results"]
            else:
                self.groups = None
            self.createTreeLayout()
            self.tree_ctrl_1.ExpandAll()
            self.tree_ctrl_2.ExpandAll()
            self.setCursorDefault()
        if self.group_grid.GetNumberRows() > 0 and forceRefresh:
            df = pd.DataFrame(columns=self.expectedHeaders)
            self.group_grid.applyNewDataFrame(df)

    @api_tool_decorator()
    def setCursorDefault(self):
        """ Set cursor icon to default state """
        try:
            self.isBusy = False
            myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
            self.SetCursor(myCursor)
            self.group_grid.GetGridWindow().SetCursor(myCursor)
            self.group_grid.GetTargetWindow().SetCursor(myCursor)
        except:
            pass

    @api_tool_decorator()
    def setCursorBusy(self):
        """ Set cursor icon to busy state """
        self.isBusy = True
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)
        self.group_grid.GetGridWindow().SetCursor(myCursor)
        self.group_grid.GetTargetWindow().SetCursor(myCursor)

    def deleteGroup(self, event):
        if not self.isBusy:
            self.setActionButtonState(False)
            Globals.THREAD_POOL.enqueue(self.deleteGroupHelper)

    def deleteGroupHelper(self):
        self.isBusy = True
        if not self.current_page or self.current_page.name == "Single":
            if self.tree_ctrl_1.GetSelection():
                hasChild = self.tree_ctrl_1.ItemHasChildren(
                    self.tree_ctrl_1.GetSelection()
                )
                if (
                    not hasChild
                    and self.tree_ctrl_1.GetItemData(self.tree_ctrl_1.GetSelection())
                    not in self.groupTree.keys()
                ):
                    self.setCursorBusy()
                    deleteGroup(
                        self.tree_ctrl_1.GetItemData(self.tree_ctrl_1.GetSelection())
                    )
                    self.refreshTree(forceRefresh=True)
                    self.setCursorDefault()
        elif self.group_grid.GetNumberRows() > 0 and self.current_page.name == "Bulk":
            numSuccess = 0
            for row in range(self.group_grid.GetNumberRows()):
                oldName = self.group_grid.GetCellValue(row, 0)
                parent = self.group_grid.GetCellValue(row, 1)
                treeItem = None
                groupId = oldName
                if oldName in self.groupNameToId:
                    groupId = self.groupNameToId[oldName]
                    if groupId:
                        groupId = groupId[0]
                if groupId in self.uploadTreeItems:
                    treeItem = self.uploadTreeItems[groupId]

                if oldName and parent:
                    if treeItem:
                        itemData = self.tree_ctrl_2.GetItemData(treeItem)
                        itemText = self.tree_ctrl_2.GetItemText(treeItem)
                        if oldName in itemText and itemData:
                            deleteGroup(itemData)
                            if treeItem:
                                self.tree_ctrl_2.SetItemTextColour(
                                    treeItem, Color.green.value
                                )
                                self.tree_ctrl_2.SetItemFont(
                                    treeItem,
                                    wx.Font(
                                        Globals.FONT_SIZE,
                                        wx.FONTFAMILY_DEFAULT,
                                        wx.FONTSTYLE_NORMAL,
                                        wx.FONTWEIGHT_BOLD,
                                        True,
                                        "NormalBold",
                                    ).Strikethrough(),
                                )
                        else:
                            numSuccess = self.fetchGroupsThenDelete(
                                oldName, parent, numSuccess
                            )
                    else:
                        numSuccess = self.fetchGroupsThenDelete(
                            oldName, parent, numSuccess
                        )
            displayMessageBox("%s Groups should be deleted" % (numSuccess))
            self.refreshTree(forceRefresh=True)
        self.setActionButtonState(True)
        self.isBusy = False

    def fetchGroupsThenDelete(self, oldName, parent, numSuccess):
        matchingGroups = getAllGroups(name=oldName)
        for group in matchingGroups.results:
            groupName, groupId, groupParent = self.obtainGroupInfoFromGroupObject(group)
            parentGroup = fetchGroupName(groupParent, returnJson=True)
            if parent == parentGroup["name"] or (
                isApiKey(parent) and parentGroup["id"] == parent
            ):
                treeItem = None
                if groupId in self.uploadTreeItems:
                    treeItem = self.uploadTreeItems[groupId]
                elif groupName in self.uploadTreeItems:
                    treeItem = self.uploadTreeItems[groupName]
                deleteGroup(groupId)
                if treeItem:
                    self.tree_ctrl_2.SetItemTextColour(treeItem, Color.green.value)
                    self.tree_ctrl_2.SetItemFont(
                        treeItem,
                        wx.Font(
                            Globals.FONT_SIZE,
                            wx.FONTFAMILY_DEFAULT,
                            wx.FONTSTYLE_NORMAL,
                            wx.FONTWEIGHT_BOLD,
                            True,
                            "NormalBold",
                        ).Strikethrough(),
                    )
                numSuccess += 1
                break
        return numSuccess

    def addSubGroup(self, event):
        if not self.isBusy:
            self.setActionButtonState(False)
            Globals.THREAD_POOL.enqueue(self.addSubGroupHelper)

    def addSubGroupHelper(self):
        self.isBusy = True
        self.setCursorBusy()
        if not self.current_page or self.current_page.name == "Single":
            if self.tree_ctrl_1.GetSelection():
                groupName = self.text_ctrl_1.GetValue()
                if groupName:
                    resp = createGroup(
                        groupName,
                        self.tree_ctrl_1.GetItemData(self.tree_ctrl_1.GetSelection()),
                    )
                    if type(resp) == dict and "errors" in resp:
                        displayMessageBox(
                            (
                                "Error (%s): %s" % (resp["status"], resp["message"]),
                                wx.ICON_ERROR,
                            )
                        )
                    else:
                        displayMessageBox("%s has been created" % groupName)
                        self.refreshTree(forceRefresh=True)
        elif self.group_grid.GetNumberRows() > 0 and self.current_page.name == "Bulk":
            numSuccess = 0
            numAlreadyExists = 0
            for row in range(self.group_grid.GetNumberRows()):
                oldName = self.group_grid.GetCellValue(row, 0)
                parent = self.group_grid.GetCellValue(row, 1)
                treeItem = None
                groupId = oldName
                if oldName in self.groupNameToId:
                    groupId = self.groupNameToId[oldName]
                    if groupId:
                        groupId = groupId[0]
                if groupId in self.uploadTreeItems:
                    treeItem = self.uploadTreeItems[groupId]

                if oldName and parent:
                    if isApiKey(parent):
                        resp = createGroup(oldName, parent)
                        if (
                            resp
                            and type(resp) == dict
                            and "message" in resp
                            and "Device group already exists" in resp["message"]
                        ):
                            numAlreadyExists += 1
                            if treeItem:
                                self.tree_ctrl_2.SetItemTextColour(
                                    treeItem, Color.green.value
                                )
                                text = self.tree_ctrl_2.GetItemText(treeItem)
                                text = text.replace(" (To Add)", "")
                                text = text.replace("To Add;", "")
                                self.tree_ctrl_2.SetItemText(treeItem, text)
                        elif resp:
                            numSuccess += 1
                            if treeItem:
                                self.tree_ctrl_2.SetItemTextColour(
                                    treeItem, Color.green.value
                                )
                                text = self.tree_ctrl_2.GetItemText(treeItem)
                                text = text.replace(" (To Add)", "")
                                text = text.replace("To Add;", "")
                                self.tree_ctrl_2.SetItemText(treeItem, text)
                        elif treeItem:
                            self.tree_ctrl_2.SetItemTextColour(
                                treeItem, Color.red.value
                            )
                    else:
                        if oldName in self.uploadTreeItems:
                            parentNode = self.tree_ctrl_2.GetItemParent(
                                self.uploadTreeItems[oldName]
                            )
                            parentData = self.tree_ctrl_2.GetItemData(parentNode)
                            parentText = self.tree_ctrl_2.GetItemText(parentNode)
                            if parent in parentText and parentData:
                                resp = createGroup(oldName, parentData)
                                (
                                    numAlreadyExists,
                                    numSuccess,
                                ) = self.processAddGroupResult(
                                    resp, numAlreadyExists, numSuccess, treeItem
                                )
                            else:
                                (
                                    numAlreadyExists,
                                    numSuccess,
                                ) = self.attemptParentGroupFetchThenAddGroup(
                                    parent, oldName, numAlreadyExists, numSuccess
                                )
                        else:
                            (
                                numAlreadyExists,
                                numSuccess,
                            ) = self.attemptParentGroupFetchThenAddGroup(
                                parent, oldName, numAlreadyExists, numSuccess
                            )
            displayMessageBox(
                "%s out of %s Groups have been created! %s already exists."
                % (numSuccess, self.group_grid.GetNumberRows(), numAlreadyExists)
            )
        self.setActionButtonState(True)
        self.isBusy = False
        self.setCursorDefault()

    def attemptParentGroupFetchThenAddGroup(
        self, parent, oldName, numAlreadyExists, numSuccess
    ):
        matchingGroups = getAllGroups(name=parent)
        for group in matchingGroups.results:
            groupName, groupId, _ = self.obtainGroupInfoFromGroupObject(group)
            treeItem = None
            if oldName in self.uploadTreeItems:
                treeItem = self.uploadTreeItems[oldName]
            if parent == groupName:
                resp = createGroup(oldName, groupId)
                if resp:
                    (numAlreadyExists, numSuccess,) = self.processAddGroupResult(
                        resp, numAlreadyExists, numSuccess, treeItem
                    )
                elif treeItem:
                    self.tree_ctrl_2.SetItemTextColour(treeItem, Color.red.value)
                break
        return numAlreadyExists, numSuccess

    def processAddGroupResult(self, resp, numAlreadyExists, numSuccess, treeItem):
        if (
            resp
            and type(resp) == dict
            and "message" in resp
            and "Device group already exists" in resp["message"]
        ):
            numAlreadyExists += 1
            if treeItem:
                self.tree_ctrl_2.SetItemTextColour(treeItem, Color.green.value)
                text = self.tree_ctrl_2.GetItemText(treeItem)
                text = text.replace(" (To Add)", "")
                text = text.replace("To Add;", "")
                self.tree_ctrl_2.SetItemText(treeItem, text)

        else:
            numSuccess += 1
            if treeItem:
                self.tree_ctrl_2.SetItemTextColour(treeItem, Color.green.value)
                text = self.tree_ctrl_2.GetItemText(treeItem)
                text = text.replace(" (To Add)", "")
                text = text.replace("To Add;", "")
                self.tree_ctrl_2.SetItemText(treeItem, text)
        return numAlreadyExists, numSuccess

    def checkActions(self, event=None):
        if not self.current_page or self.current_page.name == "Single":
            if self.tree_ctrl_1.GetSelection():
                self.button_1.Enable(True)
                self.button_4.Enable(True)
                hasChild = self.tree_ctrl_1.ItemHasChildren(
                    self.tree_ctrl_1.GetSelection()
                )
                if (
                    hasChild
                    or self.tree_ctrl_1.GetItemData(self.tree_ctrl_1.GetSelection())
                    in self.groupTree.keys()
                ):
                    self.button_2.Enable(False)
                else:
                    self.button_2.Enable(True)
            else:
                self.button_1.Enable(False)
                self.button_2.Enable(False)
                self.button_4.Enable(False)
        elif self.group_grid.GetNumberRows() > 0:
            self.button_1.Enable(True)
            self.button_2.Enable(True)
            self.button_4.Enable(True)
        else:
            self.button_1.Enable(False)
            self.button_2.Enable(False)
            self.button_4.Enable(False)

    def getChildIds(self, children, childIds):
        for childDict in children:
            childIds += list(childDict.keys())
            for c in childDict.values():
                self.getChildIds(c, childIds)

    def getGroupIdFromURL(self, url):
        return url.split("/")[-2] if url else None

    def setActionButtonState(self, state):
        self.button_4.Enable(state)
        self.button_2.Enable(state)
        self.button_1.Enable(state)
        self.notebook_1.Enable(state)

    def renameGroup(self, event):
        if not self.isBusy:
            self.setActionButtonState(False)
            Globals.THREAD_POOL.enqueue(self.renameGroupHelper)

    def renameGroupHelper(self):
        self.isBusy = True
        if not self.current_page or self.current_page.name == "Single":
            if self.tree_ctrl_1.GetSelection():
                groupName = self.text_ctrl_1.GetValue()
                if groupName:
                    self.setCursorBusy()
                    resp = renameGroup(
                        self.tree_ctrl_1.GetItemData(self.tree_ctrl_1.GetSelection()),
                        groupName,
                    )
                    if type(resp) == dict and "errors" in resp:
                        displayMessageBox(
                            (
                                "Error (%s): %s" % (resp["status"], resp["message"]),
                                wx.ICON_ERROR,
                            )
                        )
                    elif resp:
                        displayMessageBox("%s has been renamed" % groupName)
                        self.refreshTree(forceRefresh=True)
                self.setCursorDefault()
        elif self.group_grid.GetNumberRows() > 0 and self.current_page.name == "Bulk":
            numSuccess = 0
            for row in range(self.group_grid.GetNumberRows()):
                oldName = self.group_grid.GetCellValue(row, 0)
                parent = self.group_grid.GetCellValue(row, 1)
                newName = self.group_grid.GetCellValue(row, 2)

                treeItem = None
                groupId = oldName
                if oldName in self.groupNameToId:
                    groupId = self.groupNameToId[oldName]
                    if groupId:
                        groupId = groupId[0]
                if groupId in self.uploadTreeItems:
                    treeItem = self.uploadTreeItems[groupId]

                if oldName and parent and newName:
                    if treeItem:
                        itemData = self.tree_ctrl_2.GetItemData(treeItem)
                        itemText = self.tree_ctrl_2.GetItemText(treeItem)
                        if oldName in itemText and itemData:
                            resp = renameGroup(itemData, newName)
                            self.processRenameGroupResult(
                                resp, numSuccess, treeItem, newName
                            )
                        else:
                            numSuccess = self.attemptGroupFetchThenRename(
                                oldName, parent, newName, numSuccess
                            )
                    else:
                        numSuccess = self.attemptGroupFetchThenRename(
                            oldName, parent, newName, numSuccess
                        )
            displayMessageBox(
                "%s out of %s Groups have been renamed!"
                % (numSuccess, self.group_grid.GetNumberRows())
            )
        self.setActionButtonState(True)
        self.isBusy = False

    def attemptGroupFetchThenRename(self, oldName, parent, newName, numSuccess):
        matchingGroups = getAllGroups(name=oldName)
        if hasattr(matchingGroups, "results") and matchingGroups.results:
            for group in matchingGroups.results:
                groupName, groupId, groupParent = self.obtainGroupInfoFromGroupObject(
                    group
                )
                treeItem = None
                if groupId in self.uploadTreeItems:
                    treeItem = self.uploadTreeItems[groupId]
                elif groupName in self.uploadTreeItems:
                    treeItem = self.uploadTreeItems[groupName]
                elif groupId in self.tree:
                    treeItem = self.tree[groupId]
                parentGroup = fetchGroupName(groupParent, returnJson=True)
                if parent == parentGroup["name"] or (
                    isApiKey(parent) and parentGroup["id"] == parent
                ):
                    resp = renameGroup(groupId, newName)
                    self.processRenameGroupResult(resp, numSuccess, treeItem, newName)
                    break
        else:
            treeItem = None
            groupId = oldName
            if oldName in self.groupNameToId:
                groupId = self.groupNameToId[oldName]
            if groupId in self.uploadTreeItems:
                treeItem = self.uploadTreeItems[groupId]
            if treeItem:
                self.tree_ctrl_2.SetItemTextColour(treeItem, Color.red.value)
        return numSuccess

    def processRenameGroupResult(self, resp, numSuccess, treeItem, newName):
        if resp and resp.status_code <= 299 and resp.status_code >= 200:
            numSuccess += 1
            if treeItem:
                self.tree_ctrl_2.SetItemTextColour(treeItem, Color.green.value)
                replaceText = "Rename To: %s" % newName
                text = self.tree_ctrl_2.GetItemText(treeItem)
                text = text.replace(replaceText, "")
                text = text.replace(" ()", "")
                self.tree_ctrl_2.SetItemText(treeItem, text)
        elif treeItem:
            self.tree_ctrl_2.SetItemTextColour(treeItem, Color.red.value)

    def onUpload(self, event):
        filePath = displayFileDialog(
            "Open Spreadsheet File",
            wildcard="Spreadsheet Files (*.csv;*.xlsx)|*.csv;*.xlsx|CSV Files (*.csv)|*.csv|Microsoft Excel Open XML Spreadsheet (*.xlsx)|*.xlsx",
            styles=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        
        if filePath and filePath.endswith(".csv"):
            Globals.THREAD_POOL.enqueue(self.uploadCSV, filePath)
        elif filePath and filePath.endswith(".xlsx"):
            Globals.THREAD_POOL.enqueue(self.uploadXlsx, filePath)

    def uploadCSV(self, filePath):
        self.handlePreUploadActivity()
        data = read_csv_via_pandas(filePath)
        self.processUploadData(data)

    def uploadXlsx(self, filePath):
        self.handlePreUploadActivity()
        data = read_excel_via_openpyxl(filePath, readAnySheet=True)
        self.processUploadData(data)

    def handlePreUploadActivity(self):
        self.setCursorBusy()
        if self.group_grid.GetNumberRows() > 0:
            df = pd.DataFrame(columns=self.expectedHeaders)
            self.group_grid.applyNewDataFrame(df)
        self.tree_ctrl_1.UnselectAll()
        self.tree_ctrl_2.UnselectAll()
        for item in self.uploadCSVTreeItems:
            self.tree_ctrl_2.Delete(item)
        self.uploadCSVTreeItems = []

    @api_tool_decorator()
    def processUploadData(self, data):
        if data is not None:
            if data.columns.tolist() != self.expectedHeaders:
                raise Exception("Invalid Spreadsheet File: Headers don't match")
            
            self.group_grid.applyNewDataFrame(data)
            dataList = data.values.tolist()
            for row in dataList:
                if row != self.expectedHeaders:
                    colNum = 0
                    rowEntry = []
                    for col in row:
                        if (colNum == 0 or colNum == 1) and not isApiKey(str(col)):
                            groupId = None
                            if str(col) in self.groupNameToId:
                                groupId = self.groupNameToId[str(col)]
                            if groupId:
                                groupId = groupId[0]
                                rowEntry.append(groupId)
                            else:
                                rowEntry.append(str(col))
                        else:
                            rowEntry.append(str(col))
                        colNum += 1
                    if rowEntry[0] in self.uploadTreeItems:
                        item = self.uploadTreeItems[rowEntry[0]]
                        self.tree_ctrl_2.SetItemFont(
                            item,
                            wx.Font(
                                Globals.FONT_SIZE,
                                wx.FONTFAMILY_DEFAULT,
                                wx.FONTSTYLE_NORMAL,
                                wx.FONTWEIGHT_BOLD,
                                True,
                                "NormalBold",
                            ),
                        )
                        self.tree_ctrl_2.SetItemTextColour(item, Color.blue.value)
                        name = rowEntry[0]
                        if isApiKey(name) and rowEntry[0] in self.groupIdToName:
                            name = self.groupIdToName[rowEntry[0]]
                        if len(rowEntry) > 2 and rowEntry[2]:
                            name = "%s (Deletable;Rename To: %s)" % (
                                self.tree_ctrl_2.GetItemText(item),
                                rowEntry[2],
                            )
                        else:
                            name = "%s (Deletable)" % (
                                self.tree_ctrl_2.GetItemText(item)
                            )
                        self.tree_ctrl_2.SetItemText(item, name)
                    elif len(rowEntry) > 1 and rowEntry[1] in self.uploadTreeItems:
                        item = self.uploadTreeItems[rowEntry[1]]
                        name = rowEntry[0]
                        if isApiKey(name) and rowEntry[0] in self.groupIdToName:
                            name = self.groupIdToName[rowEntry[0]]
                        if len(rowEntry) > 2 and rowEntry[2]:
                            name = "%s (To Add;Rename To: %s)" % (
                                rowEntry[0],
                                rowEntry[2],
                            )
                        else:
                            name = "%s (To Add)" % (rowEntry[0])
                        entry = self.tree_ctrl_2.AppendItem(item, name)
                        self.tree_ctrl_2.SetItemFont(
                            entry,
                            wx.Font(
                                Globals.FONT_SIZE,
                                wx.FONTFAMILY_DEFAULT,
                                wx.FONTSTYLE_NORMAL,
                                wx.FONTWEIGHT_BOLD,
                                True,
                                "NormalBold",
                            ),
                        )
                        self.tree_ctrl_2.SetItemTextColour(entry, Color.blue.value)
                        self.uploadTreeItems[rowEntry[0]] = entry
                        self.uploadTreeItems[name] = entry
        self.tree_ctrl_2.ExpandAll()
        self.group_grid.AutoSizeColumns()
        self.checkActions()
        self.setCursorDefault()

    def on_tab_change(self, event):
        if event.EventObject == self.notebook_1:
            self.current_page = self.notebook_1.GetPage(event.GetSelection())
            if self.current_page.name == "Single":
                self.refreshTree()
            elif self.group_grid.GetNumberRows() > 0:
                self.notebook_2.SetSelection(0)
                self.group_grid.DeleteRows(0, self.group_grid.GetNumberRows())
        event.Skip()

    def downloadCSV(self, event):
        inFile = displayFileDialog(
            "Save Group Manage CSV as...",
            "CSV files (*.csv)|*.csv",
        )

        if inFile:
            self.setCursorBusy()
            self.button_7.Enable(False)
            Globals.THREAD_POOL.enqueue(self.saveGroupCSV, inFile)

    def saveGroupCSV(self, inFile):
        gridData = []
        gridData.append(self.expectedHeaders)
        self.getGroupCSV(self.groupTree, None, gridData)

        write_data_to_csv(inFile, gridData)
        res = displayMessageBox(
            (
                "Group Template CSV Saved\n\n File saved at: %s\n\nWould you like to navigate to the file?"
                % inFile,
                wx.YES_NO | wx.ICON_INFORMATION,
            )
        )
        if res == wx.YES:
            parentDirectory = Path(inFile).parent.absolute()
            openWebLinkInBrowser(parentDirectory, isfile=True)
        self.button_7.Enable(True)
        self.setCursorDefault()

    def getGroupCSV(self, src, parentId, gridData):
        data = []
        tenant = Globals.configuration.host.replace("https://", "").replace(
            "-api.esper.cloud/api", ""
        )
        for id, children in src.items():
            url = "https://%s-api.esper.cloud/api/enterprise/%s/devicegroup/%s/" % (
                tenant,
                Globals.enterprise_id,
                id,
            )
            groupName = fetchGroupName(url)
            if groupName and groupName.lower() != "all devices":
                data.append(groupName)
                data.append(parentId)
                data.append("")
                if data not in gridData:
                    gridData.append(data)
            for child in children:
                self.getGroupCSV(child, id, gridData)

    def obtainGroupInfoFromGroupObject(self, group):
        groupName = ""
        groupId = ""
        groupParent = ""
        if hasattr(group, "name"):
            groupName = group.name
            groupId = group.id
            groupParent = group.parent if hasattr(group, "parent") else ""
        elif type(group) is dict and "name" in group:
            groupName = group["name"]
            groupId = group["id"]
            groupParent = group["parent"] if "parent" in group else ""
        return groupName, groupId, groupParent
