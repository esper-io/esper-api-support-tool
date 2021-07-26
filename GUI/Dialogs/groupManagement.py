#!/usr/bin/env python3

import csv
from wx.core import TextEntryDialog
from Utility.Resource import displayMessageBox, resourcePath, scale_bitmap
from Common.decorator import api_tool_decorator
from Utility.EsperAPICalls import (
    createGroup,
    deleteGroup,
    fetchGroupName,
    getAllGroups,
    renameGroup,
)

import wx
import wx.grid as gridlib
import Common.Globals as Globals


class TabPanel(wx.Panel):
    def __init__(self, parent, id, name):
        """"""
        super().__init__(parent=parent, id=id)
        self.name = name


class GroupManagement(wx.Dialog):
    def __init__(self, groups, *args, **kwds):
        # begin wxGlade: MyDialog.__init__
        self.groups = groups
        self.groupTree = {}
        self.tree = {}
        self.current_page = None

        super(GroupManagement, self).__init__(
            None,
            wx.ID_ANY,
            style=wx.DEFAULT_DIALOG_STYLE | wx.MAXIMIZE_BOX | wx.RESIZE_BORDER,
        )
        self.SetSize((800, 500))
        self.SetMinSize((800, 500))
        self.SetTitle("Group Management")

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        self.notebook_1 = wx.Notebook(self, wx.ID_ANY)
        sizer_1.Add(self.notebook_1, 1, wx.ALL | wx.EXPAND, 5)

        self.notebook_1_pane_1 = TabPanel(self.notebook_1, wx.ID_ANY, "Single")
        self.notebook_1.AddPage(self.notebook_1_pane_1, "Single")

        grid_sizer_1 = wx.FlexGridSizer(4, 1, 0, 0)

        label_1 = wx.StaticText(self.notebook_1_pane_1, wx.ID_ANY, "Groups:")
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

        self.button_3 = wx.Button(self.notebook_1_pane_1, wx.ID_REFRESH, "")
        self.button_3.SetToolTip("Rerfresh Group listing")
        grid_sizer_1.Add(self.button_3, 0, wx.ALIGN_RIGHT | wx.BOTTOM, 5)

        self.tree_ctrl_1 = wx.TreeCtrl(
            self.notebook_1_pane_1,
            wx.ID_ANY,
            style=wx.TR_EDIT_LABELS | wx.TR_HAS_BUTTONS | wx.TR_SINGLE | wx.WANTS_CHARS,
        )
        grid_sizer_1.Add(self.tree_ctrl_1, 1, wx.EXPAND, 0)

        self.notebook_1_pane_2 = TabPanel(self.notebook_1, wx.ID_ANY, "Bulk")
        self.notebook_1.AddPage(self.notebook_1_pane_2, "Bulk")

        grid_sizer_4 = wx.FlexGridSizer(4, 1, 0, 0)

        label_4 = wx.StaticText(self.notebook_1_pane_2, wx.ID_ANY, "CSV Upload:")
        label_4.SetFont(
            wx.Font(
                11,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        grid_sizer_4.Add(label_4, 0, 0, 0)

        label_3 = wx.StaticText(
            self.notebook_1_pane_2,
            wx.ID_ANY,
            "Upload a CSV bulk perform an Action (Adding Groups works best with unique Parent names): ",
            style=wx.ST_ELLIPSIZE_END,
        )
        label_3.SetToolTip(
            "Select a group from the list below and then select one of the actions below"
        )
        label_3.Wrap(1)
        grid_sizer_4.Add(label_3, 0, wx.BOTTOM | wx.EXPAND, 5)

        self.button_6 = wx.Button(self.notebook_1_pane_2, wx.ID_ANY, "Upload CSV")
        self.button_6.SetToolTip("Upload CSV file")
        grid_sizer_4.Add(self.button_6, 0, wx.ALIGN_RIGHT | wx.BOTTOM | wx.RIGHT, 5)

        self.grid_1 = wx.grid.Grid(self.notebook_1_pane_2, wx.ID_ANY, size=(1, 1))
        self.grid_1.CreateGrid(0, 3)
        self.grid_1.EnableDragGridSize(0)
        self.grid_1.SetColLabelValue(0, "Group Name")
        self.grid_1.SetColLabelValue(1, "Parent Group")
        self.grid_1.SetColLabelValue(2, "New Group Name")
        grid_sizer_4.Add(self.grid_1, 1, wx.EXPAND, 0)

        sizer_2 = wx.StdDialogButtonSizer()
        sizer_1.Add(sizer_2, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

        self.button_1 = wx.Button(self, wx.ID_ADD, "")
        sizer_2.Add(self.button_1, 0, wx.RIGHT, 5)

        self.button_4 = wx.Button(self, wx.ID_ANY, "Rename")
        sizer_2.Add(self.button_4, 0, 0, 0)

        self.button_2 = wx.Button(self, wx.ID_DELETE, "")
        sizer_2.Add(self.button_2, 0, wx.LEFT, 5)

        sizer_2.Realize()

        grid_sizer_4.AddGrowableRow(3)
        grid_sizer_4.AddGrowableCol(0)
        self.notebook_1_pane_2.SetSizer(grid_sizer_4)

        grid_sizer_1.AddGrowableRow(3)
        grid_sizer_1.AddGrowableCol(0)
        self.notebook_1_pane_1.SetSizer(grid_sizer_1)

        self.SetSizer(sizer_1)

        self.Layout()

        self.grid_1.AutoSizeColumns()

        self.button_2.Enable(False)
        self.button_1.Enable(False)
        self.button_4.Enable(False)

        self.button_4.Bind(wx.EVT_BUTTON, self.renameGroup)
        self.button_3.Bind(wx.EVT_BUTTON, self.refreshTree)
        self.button_2.Bind(wx.EVT_BUTTON, self.deleteGroup)
        self.button_1.Bind(wx.EVT_BUTTON, self.addSubGroup)
        self.button_6.Bind(wx.EVT_BUTTON, self.uploadCSV)
        self.tree_ctrl_1.Bind(wx.EVT_TREE_SEL_CHANGED, self.checkActions)
        self.notebook_1.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_tab_change)

        self.createTreeLayout()
        self.tree_ctrl_1.ExpandAll()

    def createTreeLayout(self):
        unsorted = []
        for group in self.groups:
            parentId = self.getGroupIdFromURL(group.parent)
            if not group.parent:
                self.groupTree[group.id] = []
                self.root = self.tree_ctrl_1.AddRoot(group.name, data=group.id)
                self.tree[group.id] = self.root
                continue
            if parentId in self.groupTree.keys():
                self.groupTree[parentId].append({group.id: []})
                entry = self.tree_ctrl_1.AppendItem(
                    self.tree[parentId], group.name, data=group.id
                )
                self.tree[group.id] = entry
            else:
                unsorted.append(group)

        while len(unsorted) > 0:
            newUnsorted = []
            for group in unsorted:
                parentId = self.getGroupIdFromURL(group.parent)
                success = self.addGroupAsChild(self.groupTree, parentId, group)
                if not success:
                    newUnsorted.append(group)
            unsorted = newUnsorted

    def addGroupAsChild(self, src, dest, group):
        for key, value in src.items():
            if key == dest:
                value.append({group.id: []})
                entry = self.tree_ctrl_1.AppendItem(
                    self.tree[dest], group.name, data=group.id
                )
                self.tree[group.id] = entry
                return True
            for child in value:
                success = self.addGroupAsChild(child, dest, group)
                if success:
                    return True
        return False

    def refreshTree(self, event=None):
        self.setCursorBusy()
        self.tree_ctrl_1.DeleteAllItems()
        self.groups = getAllGroups().results
        self.createTreeLayout()
        self.tree_ctrl_1.ExpandAll()
        self.setCursorDefault()

    @api_tool_decorator()
    def setCursorDefault(self):
        """ Set cursor icon to default state """
        try:
            self.isBusy = False
            myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
            self.SetCursor(myCursor)
        except:
            pass

    @api_tool_decorator()
    def setCursorBusy(self):
        """ Set cursor icon to busy state """
        self.isBusy = True
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)

    def deleteGroup(self, event):
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
                    self.refreshTree()
                    self.setCursorDefault()
        elif self.grid_1.GetNumberRows() > 0 and self.current_page.name == "Bulk":
            numSuccess = 0
            for row in range(self.grid_1.GetNumberRows()):
                oldName = self.grid_1.GetCellValue(row, 0)
                parent = self.grid_1.GetCellValue(row, 1)

                if oldName and parent:
                    matchingGroups = getAllGroups(name=oldName)
                    for group in matchingGroups.results:
                        parentName = fetchGroupName(group.parent)
                        if parent == parentName:
                            deleteGroup(group.id)
                            numSuccess += 1
                            break
            displayMessageBox("%s Groups should be deleted" % (numSuccess))

    def addSubGroup(self, event):
        self.setCursorBusy()
        if not self.current_page or self.current_page.name == "Single":
            if self.tree_ctrl_1.GetSelection():
                groupName = None
                with TextEntryDialog(
                    self,
                    "Please enter new Group Name:",
                ) as dlg:
                    if dlg.ShowModal() == wx.ID_OK:
                        groupName = dlg.GetValue()
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
                        self.refreshTree()
        elif self.grid_1.GetNumberRows() > 0 and self.current_page.name == "Bulk":
            numSuccess = 0
            for row in range(self.grid_1.GetNumberRows()):
                oldName = self.grid_1.GetCellValue(row, 0)
                parent = self.grid_1.GetCellValue(row, 1)

                if oldName and parent:
                    matchingGroups = getAllGroups(name=parent)
                    for group in matchingGroups.results:
                        if parent == group.name:
                            resp = createGroup(oldName, group.id)
                            if resp:
                                numSuccess += 1
                            break
            displayMessageBox(
                "%s out of %s Groups have been created"
                % (numSuccess, self.grid_1.GetNumberRows())
            )
        self.setCursorDefault()

    def checkActions(self, event=None):
        if self.tree_ctrl_1.GetSelection():
            self.button_1.Enable(True)
            self.button_4.Enable(True)
            hasChild = self.tree_ctrl_1.ItemHasChildren(self.tree_ctrl_1.GetSelection())
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

        if self.grid_1.GetNumberRows() > 0:
            self.button_1.Enable(True)
            self.button_2.Enable(True)
            self.button_4.Enable(True)
        else:
            self.button_1.Enable(False)
            self.button_2.Enable(False)
            self.button_4.Enable(False)

    def getSubGroups(self, groupId):
        return self.getSubGroupsHelper(self.groupTree, groupId)

    def getSubGroupsHelper(self, src, groupId):
        for id, children in src.items():
            if id == groupId:
                childIds = []
                self.getChildIds(children, childIds)
                return childIds
            else:
                for child in children:
                    childrenList = self.getSubGroupsHelper(child, groupId)
                    if childrenList:
                        return childrenList
        return []

    def getChildIds(self, children, childIds):
        for childDict in children:
            childIds += list(childDict.keys())
            if not Globals.GET_IMMEDIATE_SUBGROUPS:
                for c in childDict.values():
                    self.getChildIds(c, childIds)

    def getGroupIdFromURL(self, url):
        return url.split("/")[-2] if url else None

    def renameGroup(self, event):
        if not self.current_page or self.current_page.name == "Single":
            if self.tree_ctrl_1.GetSelection():
                groupName = None
                with TextEntryDialog(
                    self,
                    "Please enter new Group Name for %s:"
                    % self.tree_ctrl_1.GetItemText(self.tree_ctrl_1.GetSelection()),
                ) as dlg:
                    if dlg.ShowModal() == wx.ID_OK:
                        groupName = dlg.GetValue()
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
                    else:
                        displayMessageBox("%s has been renamed" % groupName)
                        self.refreshTree()
                self.setCursorDefault()
        elif self.grid_1.GetNumberRows() > 0 and self.current_page.name == "Bulk":
            numSuccess = 0
            for row in range(self.grid_1.GetNumberRows()):
                oldName = self.grid_1.GetCellValue(row, 0)
                parent = self.grid_1.GetCellValue(row, 1)
                newName = self.grid_1.GetCellValue(row, 2)

                if oldName and parent and newName:
                    matchingGroups = getAllGroups(name=oldName)
                    for group in matchingGroups.results:
                        parentName = fetchGroupName(group.parent)
                        if parent == parentName:
                            resp = renameGroup(group.id, newName)
                            if (
                                resp
                                and resp.status_code <= 299
                                and resp.status_code >= 200
                            ):
                                numSuccess += 1
                            break
            displayMessageBox(
                "%s out of %s Groups have been renamed"
                % (numSuccess, self.grid_1.GetNumberRows())
            )

    def uploadCSV(self, event):
        filePath = None
        with wx.FileDialog(
            self,
            "Open CSV File",
            wildcard="CSV files (*.csv)|*.csv",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as fileDialog:
            result = fileDialog.ShowModal()
            if result == wx.ID_OK:
                # Proceed loading the file chosen by the user
                filePath = fileDialog.GetPath()
        if filePath:
            self.tree_ctrl_1.UnselectAll()
            data = None
            try:
                with open(filePath, "r", encoding="utf-8-sig") as csvFile:
                    reader = csv.reader(
                        csvFile, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True
                    )
                    data = list(reader)
            except UnicodeDecodeError as e:
                with open(filePath, "r") as csvFile:
                    reader = csv.reader(
                        csvFile, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True
                    )
                    data = list(reader)
            for row in data:
                self.grid_1.AppendRows(1)
                colNum = 0
                for col in row:
                    self.grid_1.SetCellValue(
                        self.grid_1.GetNumberRows() - 1, colNum, str(col)
                    )
                    colNum += 1
            self.grid_1.AutoSizeColumns()
            self.checkActions()

    def on_tab_change(self, event):
        self.current_page = self.notebook_1.GetPage(event.GetSelection())
        if self.current_page.name == "Single":
            self.refreshTree()
        elif self.grid_1.GetNumberRows() > 0:
            self.grid_1.DeleteRows(0, self.grid_1.GetNumberRows())
        event.Skip()
