#!/usr/bin/env python3

import csv
from wx.core import TextEntryDialog
from Utility.Resource import displayMessageBox, resourcePath, scale_bitmap
from Common.decorator import api_tool_decorator
from Utility.EsperAPICalls import (
    fetchGroupName,
    getAllGroups,
)
from Utility.GroupUtility import deleteGroup, createGroup, renameGroup

import wx
import wx.grid as gridlib
import Common.Globals as Globals
import Utility.wxThread as wxThread

from Common.enum import Color


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
        self.uploadTree = {}
        self.uploadTreeItems = {}
        self.uploadCSVTreeItems = []
        self.current_page = None
        self.groupNameToId = {}
        self.groupIdToName = {}
        self.expectedHeaders = [
            "Group Name",
            "Parent Group Identifier",
            "New Group Name",
        ]

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
            "Upload a CSV bulk perform an Action (Adding Groups works best with unique Parent names): ",
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

        sizer_4 = wx.GridSizer(1, 1, 0, 0)

        self.tree_ctrl_2 = wx.TreeCtrl(self.notebook_2_pane_1, wx.ID_ANY)
        sizer_4.Add(self.tree_ctrl_2, 1, wx.EXPAND, 0)

        self.notebook_2_pane_2 = TabPanel(self.notebook_2, wx.ID_ANY, "Grid")
        self.notebook_2.AddPage(self.notebook_2_pane_2, "Grid Preview")

        sizer_5 = wx.GridSizer(1, 1, 0, 0)

        self.grid_1 = gridlib.Grid(self.notebook_2_pane_2, wx.ID_ANY, size=(1, 1))
        self.grid_1.CreateGrid(0, 3)
        self.grid_1.EnableDragGridSize(0)
        self.grid_1.SetColLabelValue(0, "Group Name")
        self.grid_1.SetColLabelValue(1, "Parent Group Identifier")
        self.grid_1.SetColLabelValue(2, "New Group Name")
        sizer_5.Add(self.grid_1, 1, wx.EXPAND, 0)

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

        self.notebook_2_pane_1.SetSizer(sizer_4)

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
        self.button_6.Bind(wx.EVT_BUTTON, self.openCSV)
        self.button_7.Bind(wx.EVT_BUTTON, self.downloadCSV)
        self.tree_ctrl_1.Bind(wx.EVT_TREE_SEL_CHANGED, self.checkActions)
        self.notebook_1.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_tab_change)

        self.createTreeLayout()
        self.tree_ctrl_1.ExpandAll()
        self.tree_ctrl_2.ExpandAll()

    def createTreeLayout(self):
        unsorted = []
        for group in self.groups:
            if group.name not in self.groupNameToId:
                self.groupNameToId[group.name] = []
            self.groupNameToId[group.name].append(group.id)
            self.groupIdToName[group.id] = group.name
            parentId = self.getGroupIdFromURL(group.parent)
            if not group.parent:
                self.groupTree[group.id] = []
                self.uploadTree[group.id] = []
                self.root = self.tree_ctrl_1.AddRoot(group.name, data=group.id)
                root2 = self.tree_ctrl_2.AddRoot(group.name, data=group.id)
                self.tree[group.id] = self.root
                self.uploadTreeItems[group.id] = root2
                continue
            if parentId in self.groupTree.keys():
                self.groupTree[parentId].append({group.id: []})
                self.uploadTree[parentId].append({group.id: []})
                entry = self.tree_ctrl_1.AppendItem(
                    self.tree[parentId], group.name, data=group.id
                )
                entry2 = self.tree_ctrl_2.AppendItem(
                    self.uploadTreeItems[parentId], group.name, data=group.id
                )
                self.tree[group.id] = entry
                self.uploadTreeItems[group.id] = entry2
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
                entry2 = self.tree_ctrl_2.AppendItem(
                    self.uploadTreeItems[dest], group.name, data=group.id
                )
                self.tree[group.id] = entry
                self.uploadTreeItems[group.id] = entry2
                return True
            for child in value:
                success = self.addGroupAsChild(child, dest, group)
                if success:
                    return True
        return False

    def refreshTree(self, event=None):
        self.setCursorBusy()
        self.tree_ctrl_1.DeleteAllItems()
        self.tree_ctrl_2.DeleteAllItems()
        self.groups = getAllGroups().results
        self.createTreeLayout()
        self.tree_ctrl_1.ExpandAll()
        self.tree_ctrl_2.ExpandAll()
        self.setCursorDefault()

    @api_tool_decorator()
    def setCursorDefault(self):
        """ Set cursor icon to default state """
        try:
            self.isBusy = False
            myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
            self.SetCursor(myCursor)
            self.grid_1.GetGridWindow().SetCursor(myCursor)
            self.grid_1.GetTargetWindow().SetCursor(myCursor)
        except:
            pass

    @api_tool_decorator()
    def setCursorBusy(self):
        """ Set cursor icon to busy state """
        self.isBusy = True
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)
        self.grid_1.GetGridWindow().SetCursor(myCursor)
        self.grid_1.GetTargetWindow().SetCursor(myCursor)

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
                        parentGroup = fetchGroupName(group.parent, returnJson=True)
                        if parent == parentGroup["name"] or (
                            len(parent) == 36
                            and "-" in parent
                            and parentGroup["id"] == parent
                        ):
                            treeItem = None
                            if group.id in self.uploadTreeItems:
                                treeItem = self.uploadTreeItems[group.id]
                            deleteGroup(group.id)
                            if treeItem:
                                self.tree_ctrl_2.SetItemTextColour(
                                    treeItem, Color.green.value
                                )
                            numSuccess += 1
                            break
            self.refreshTree()
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
            numAlreadyExists = 0
            for row in range(self.grid_1.GetNumberRows()):
                oldName = self.grid_1.GetCellValue(row, 0)
                parent = self.grid_1.GetCellValue(row, 1)

                if oldName and parent:
                    if len(parent) == 36 and "-" in parent:
                        resp = createGroup(oldName, parent)
                        if resp:
                            numSuccess += 1
                    else:
                        matchingGroups = getAllGroups(name=parent)
                        for group in matchingGroups.results:
                            if parent == group.name:
                                treeItem = None
                                if group.id in self.uploadTreeItems:
                                    treeItem = self.uploadTreeItems[group.id]
                                resp = createGroup(oldName, group.id)
                                if resp:
                                    if type(resp) == dict and "message" in resp and "Device group already exists" in resp["message"]:
                                        numAlreadyExists += 1
                                        if treeItem:
                                            self.tree_ctrl_2.SetItemTextColour(
                                                treeItem, Color.green.value
                                            )
                                    else:
                                        numSuccess += 1
                                        if treeItem:
                                            self.tree_ctrl_2.SetItemTextColour(
                                                treeItem, Color.green.value
                                            )
                                elif treeItem:
                                    self.tree_ctrl_2.SetItemTextColour(
                                        treeItem, Color.red.value
                                    )
                                break
            self.refreshTree()
            displayMessageBox(
                "%s out of %s Groups have been created! %s already exists."
                % (numSuccess, self.grid_1.GetNumberRows(), numAlreadyExists)
            )
        self.setCursorDefault()

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
        elif self.grid_1.GetNumberRows() > 0:
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
                        parentGroup = fetchGroupName(group.parent, returnJson=True)
                        if parent == parentGroup["name"] or (
                            len(parent) == 36
                            and "-" in parent
                            and parentGroup["id"] == parent
                        ):
                            treeItem = None
                            if group.id in self.uploadTreeItems:
                                treeItem = self.uploadTreeItems[group.id]
                            resp = renameGroup(group.id, newName)
                            if (
                                resp
                                and resp.status_code <= 299
                                and resp.status_code >= 200
                            ):
                                numSuccess += 1
                                if treeItem:
                                    self.tree_ctrl_2.SetItemTextColour(
                                        treeItem, Color.green.value
                                    )
                            elif treeItem:
                                self.tree_ctrl_2.SetItemTextColour(
                                    treeItem, Color.red.value
                                )
                            break
            self.refreshTree()
            displayMessageBox(
                "%s out of %s Groups have been renamed"
                % (numSuccess, self.grid_1.GetNumberRows())
            )

    def openCSV(self, event):
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
            self.uploadCSV(filePath)

    def uploadCSV(self, filePath):
        self.setCursorBusy()
        if self.grid_1.GetNumberRows() > 0:
            self.grid_1.DeleteRows(0, self.grid_1.GetNumberRows())
        self.tree_ctrl_1.UnselectAll()
        data = None
        for item in self.uploadCSVTreeItems:
            self.tree_ctrl_2.Delete(item)
        self.uploadCSVTreeItems = []
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
            if row != self.expectedHeaders:
                self.grid_1.AppendRows(1)
                colNum = 0
                rowEntry = []
                for col in row:
                    self.grid_1.SetCellValue(
                        self.grid_1.GetNumberRows() - 1, colNum, str(col)
                    )
                    if (colNum == 0 or colNum == 1) and not (
                        len(str(col)) == 36 and "-" in str(col)
                    ):
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
                    if len(rowEntry) > 2 and rowEntry[2]:
                        name = "%s (Deletable;Rename To: %s)" % (
                            self.tree_ctrl_2.GetItemText(item),
                            rowEntry[2],
                        )
                    else:
                        name = "%s (Deletable)" % (self.tree_ctrl_2.GetItemText(item))
                    self.tree_ctrl_2.SetItemText(item, name)
                elif len(rowEntry) > 1 and rowEntry[1] in self.uploadTreeItems:
                    item = self.uploadTreeItems[rowEntry[1]]
                    name = rowEntry[0]
                    if len(rowEntry) > 2 and rowEntry[2]:
                        name = "%s (To Add;Rename To: %s)" % (rowEntry[0], rowEntry[2])
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
        self.grid_1.AutoSizeColumns()
        self.checkActions()
        self.setCursorDefault()

    def on_tab_change(self, event):
        if event.EventObject == self.notebook_1:
            self.current_page = self.notebook_1.GetPage(event.GetSelection())
            if self.current_page.name == "Single":
                self.refreshTree()
            elif self.grid_1.GetNumberRows() > 0:
                self.notebook_2.SetSelection(0)
                self.grid_1.DeleteRows(0, self.grid_1.GetNumberRows())
        event.Skip()

    def downloadCSV(self, event):
        dlg = wx.FileDialog(
            self,
            message="Save Group Manage CSV as...",
            defaultFile="",
            wildcard="*.csv",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )
        result = dlg.ShowModal()
        inFile = dlg.GetPath()
        dlg.DestroyLater()

        if result == wx.ID_OK:
            self.setCursorBusy()
            self.button_7.Enable(False)
            thread = wxThread.GUIThread(None, self.saveGroupCSV, (inFile))
            thread.start()

    def saveGroupCSV(self, inFile):
        gridData = []
        gridData.append(self.expectedHeaders)
        self.getGroupCSV(self.groupTree, None, gridData)

        with open(inFile, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerows(gridData)
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
