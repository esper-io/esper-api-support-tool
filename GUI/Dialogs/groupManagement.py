#!/usr/bin/env python3

from wx.core import TextEntryDialog
from Utility.Resource import displayMessageBox, resourcePath, scale_bitmap
from Common.decorator import api_tool_decorator
from Utility.EsperAPICalls import createGroup, deleteGroup, getAllGroups
import wx


class GroupManagement(wx.Dialog):
    def __init__(self, groups, *args, **kwds):
        # begin wxGlade: MyDialog.__init__
        self.groups = groups
        self.groupTree = {}
        self.tree = {}

        super(GroupManagement, self).__init__(
            None,
            wx.ID_ANY,
            style=wx.DEFAULT_DIALOG_STYLE | wx.MAXIMIZE_BOX | wx.RESIZE_BORDER,
        )
        self.SetSize((400, 500))
        self.SetMinSize((400, 500))
        self.SetTitle("Group Management")

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_1, 1, wx.ALL | wx.EXPAND, 5)

        grid_sizer_1 = wx.FlexGridSizer(4, 1, 0, 0)

        label_1 = wx.StaticText(self.panel_1, wx.ID_ANY, "Groups:")
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
            self.panel_1,
            wx.ID_ANY,
            "Select a group from the list below and then select one of the actions below",
        )
        label_2.Wrap(375)
        grid_sizer_1.Add(label_2, 0, wx.BOTTOM | wx.EXPAND, 5)

        ref_icon = scale_bitmap(resourcePath("Images/refresh.png"), 16, 16)
        self.button_3 = wx.BitmapButton(
            self.panel_1,
            wx.ID_REFRESH,
            ref_icon,
        )
        self.button_3.SetMinSize((20, 20))
        grid_sizer_1.Add(self.button_3, 0, wx.ALIGN_RIGHT | wx.BOTTOM, 5)

        self.tree_ctrl_1 = wx.TreeCtrl(
            self.panel_1,
            wx.ID_ANY,
            style=wx.TR_HAS_BUTTONS | wx.TR_SINGLE | wx.WANTS_CHARS,
        )
        grid_sizer_1.Add(self.tree_ctrl_1, 1, wx.EXPAND, 0)

        sizer_2 = wx.StdDialogButtonSizer()
        sizer_1.Add(sizer_2, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

        self.button_1 = wx.Button(self, wx.ID_ADD, "")
        sizer_2.Add(self.button_1, 0, wx.RIGHT, 5)

        self.button_2 = wx.Button(self, wx.ID_DELETE, "")
        sizer_2.Add(self.button_2, 0, wx.LEFT, 5)

        sizer_2.Realize()

        grid_sizer_1.AddGrowableRow(3)
        grid_sizer_1.AddGrowableCol(0)
        self.panel_1.SetSizer(grid_sizer_1)

        self.SetSizer(sizer_1)

        self.Layout()

        self.button_2.Enable(False)
        self.button_1.Enable(False)

        self.button_3.Bind(wx.EVT_BUTTON, self.refreshTree)
        self.button_2.Bind(wx.EVT_BUTTON, self.deleteGroup)
        self.button_1.Bind(wx.EVT_BUTTON, self.addSubGroup)
        self.tree_ctrl_1.Bind(wx.EVT_TREE_SEL_CHANGED, self.checkActions)

        self.createTreeLayout()
        self.tree_ctrl_1.ExpandAll()

    def createTreeLayout(self):
        unsorted = []
        for group in self.groups:
            parentId = group.parent.split("/")[-2] if group.parent else None
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
                parentId = group.parent.split("/")[-2] if group.parent else None
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
        hasChild = self.tree_ctrl_1.ItemHasChildren(self.tree_ctrl_1.GetSelection())
        if (
            not hasChild
            and self.tree_ctrl_1.GetItemData(self.tree_ctrl_1.GetSelection())
            not in self.groupTree.keys()
        ):
            self.setCursorBusy()
            deleteGroup(self.tree_ctrl_1.GetItemData(self.tree_ctrl_1.GetSelection()))
            self.refreshTree()
            self.setCursorDefault()

    def addSubGroup(self, event):
        groupName = None
        with TextEntryDialog(
            self,
            "Please enter new Group Name:",
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                groupName = dlg.GetValue()
        if groupName:
            self.setCursorBusy()
            resp = createGroup(
                groupName, self.tree_ctrl_1.GetItemData(self.tree_ctrl_1.GetSelection())
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
        self.setCursorDefault()

    def checkActions(self, event):
        if self.tree_ctrl_1.GetSelection():
            self.button_1.Enable(True)
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
