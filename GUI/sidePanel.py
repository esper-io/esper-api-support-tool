#!/usr/bin/env python


import wx

import Common.Globals as Globals
from Common.decorator import api_tool_decorator
from Common.enum import FontStyles
from GUI.Dialogs.MultiSelectSearchDlg import MultiSelectSearchDlg
from Utility.FileUtility import write_data_to_csv
from Utility.Resource import (applyFontHelper, getFont, resourcePath,
                              scale_bitmap)


class SidePanel(wx.Panel):
    def __init__(self, parentFrame, parent, *args, **kw):
        super().__init__(parent, *args, **kw)

        self.parentFrame = parentFrame
        self.configChoice = {}
        self.selectedDevicesList = []
        self.deviceResp = None
        self.devices = {}
        self.devicesExtended = {}
        self.selectedGroupsList = []
        self.groupsResp = None
        self.groups = {}
        self.groupDeviceCount = {}

        self.groupMultiDialog = None
        self.deviceMultiDialog = None

        self.SetThemeEnabled(False)

        sizer_1 = wx.FlexGridSizer(7, 1, 0, 0)

        self.panel_2 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_2, 0, wx.ALL | wx.EXPAND, 5)
        self.SetMinSize((300, 400))

        sizer_2 = wx.FlexGridSizer(2, 1, 0, 0)

        self.panel_3 = wx.Panel(self.panel_2, wx.ID_ANY)
        sizer_2.Add(self.panel_3, 0, wx.EXPAND, 0)

        grid_sizer_1 = wx.GridSizer(1, 2, 0, 0)

        label_1 = wx.StaticText(self.panel_3, wx.ID_ANY, "Loaded Tenant:")
        grid_sizer_1.Add(label_1, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 0)

        remove_icon = scale_bitmap(resourcePath("Images/remove.png"), 16, 16)
        self.removeEndpointBtn = wx.BitmapButton(
            self.panel_3,
            wx.ID_DELETE,
            remove_icon,
        )
        self.removeEndpointBtn.SetToolTip("Remove Tenant")
        grid_sizer_1.Add(
            self.removeEndpointBtn,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.RIGHT,
            3,
        )

        self.configList = wx.TextCtrl(
            self.panel_2,
            wx.ID_ANY,
            "",
            style=wx.TE_MULTILINE | wx.TE_READONLY,
        )
        sizer_2.Add(
            self.configList, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 3
        )

        static_line_4 = wx.StaticLine(self, wx.ID_ANY)
        sizer_1.Add(
            static_line_4,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.EXPAND | wx.TOP,
            5,
        )

        self.notebook_1 = wx.Notebook(self, wx.ID_ANY)
        self.notebook_1.SetThemeEnabled(False)
        sizer_1.Add(self.notebook_1, 1, wx.ALL | wx.EXPAND, 5)

        self.panel_8 = wx.Panel(self.notebook_1, wx.ID_ANY)
        self.notebook_1.AddPage(self.panel_8, "Groups")

        grid_sizer_6 = wx.BoxSizer(wx.VERTICAL)

        self.groupChoice = wx.Button(self.panel_8, wx.ID_ANY, "Select Group(s)")
        self.groupChoice.SetToolTip(
            "Select which group(s) you wish to run an action on."
        )
        self.groupChoice.SetFocus()
        grid_sizer_6.Add(self.groupChoice, 0, wx.EXPAND | wx.TOP, 5)

        self.panel_13 = wx.Panel(self.panel_8, wx.ID_ANY)
        grid_sizer_6.Add(self.panel_13, 1, wx.EXPAND | wx.TOP, 5)

        grid_sizer_8 = wx.GridSizer(1, 1, 0, 0)

        self.selectedGroups = wx.ListBox(
            self.panel_13, wx.ID_ANY, choices=[], style=wx.LB_HSCROLL
        )
        self.selectedGroups.SetToolTip("Currently Selected Group(s)")
        grid_sizer_8.Add(self.selectedGroups, 0, wx.EXPAND, 0)

        self.panel_9 = wx.Panel(self.notebook_1, wx.ID_ANY)
        self.notebook_1.AddPage(self.panel_9, "Devices")

        grid_sizer_3 = wx.BoxSizer(wx.VERTICAL)

        self.deviceChoice = wx.Button(
            self.panel_9, wx.ID_ANY, "Select Device(s) [Optional]"
        )
        self.deviceChoice.SetToolTip(
            "Select which device(s) you specifically wish to run an action on, optional."
        )
        grid_sizer_3.Add(self.deviceChoice, 0, wx.EXPAND | wx.TOP, 5)

        self.panel_12 = wx.Panel(self.panel_9, wx.ID_ANY)
        grid_sizer_3.Add(self.panel_12, 1, wx.EXPAND | wx.TOP, 5)

        grid_sizer_7 = wx.GridSizer(1, 1, 0, 0)

        self.selectedDevices = wx.ListBox(
            self.panel_12, wx.ID_ANY, choices=[], style=wx.LB_HSCROLL
        )
        self.selectedDevices.SetToolTip("Currently Selected Device(s)")
        grid_sizer_7.Add(self.selectedDevices, 0, wx.EXPAND, 0)

        static_line_2 = wx.StaticLine(self, wx.ID_ANY)
        sizer_1.Add(static_line_2, 0, wx.BOTTOM | wx.EXPAND | wx.TOP, 5)

        self.panel_10 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_10, 1, wx.ALL | wx.EXPAND, 5)

        sizer_5 = wx.BoxSizer(wx.VERTICAL)

        label_5 = wx.StaticText(self.panel_10, wx.ID_ANY, "Select Action:")
        sizer_5.Add(label_5, 0, wx.EXPAND, 0)

        self.actionChoice = wx.ComboBox(
            self.panel_10,
            wx.ID_ANY,
            choices=[],
            style=wx.CB_DROPDOWN | wx.CB_READONLY,
        )
        sizer_5.Add(self.actionChoice, 0, wx.EXPAND | wx.TOP, 5)

        static_line_3 = wx.StaticLine(self, wx.ID_ANY)
        sizer_1.Add(static_line_3, 0, wx.BOTTOM | wx.EXPAND | wx.TOP, 5)

        self.runBtn = wx.Button(self, wx.ID_ANY, "Run", style=wx.BU_AUTODRAW)
        self.runBtn.SetToolTip("Run Selected Action")
        sizer_1.Add(self.runBtn, 0, wx.ALL | wx.EXPAND, 5)

        self.panel_10.SetSizer(sizer_5)

        self.panel_12.SetSizer(grid_sizer_7)

        self.panel_9.SetSizer(grid_sizer_3)

        self.panel_13.SetSizer(grid_sizer_8)

        self.panel_8.SetSizer(grid_sizer_6)

        self.panel_3.SetSizer(grid_sizer_1)

        sizer_2.AddGrowableRow(1)
        sizer_2.AddGrowableCol(0)
        self.panel_2.SetSizer(sizer_2)

        sizer_1.AddGrowableRow(0)
        sizer_1.AddGrowableRow(2)
        sizer_1.AddGrowableRow(4)
        sizer_1.AddGrowableRow(6)

        sizer_1.AddGrowableCol(0)

        self.SetSizer(sizer_1)

        self.applyFontSize()
        self.Layout()

        actions = {
            **Globals.GENERAL_ACTIONS,
            **Globals.GRID_ACTIONS,
        }
        for key, val in actions.items():
            self.actionChoice.Append(key, val)

        self.__set_properties()

    @api_tool_decorator()
    def __set_properties(self):
        self.actionChoice.SetSelection(1)

        self.removeEndpointBtn.Enable(False)
        self.actionChoice.Enable(False)
        self.deviceChoice.Enable(False)
        self.groupChoice.Enable(False)
        self.runBtn.Enable(False)

        self.removeEndpointBtn.Bind(wx.EVT_BUTTON, self.RemoveEndpoint)
        self.groupChoice.Bind(wx.EVT_BUTTON, self.onGroupSelection)
        self.deviceChoice.Bind(wx.EVT_BUTTON, self.onDeviceSelection)
        self.actionChoice.Bind(wx.EVT_COMBOBOX, self.onActionSelection)

        self.deviceChoice.Bind(
            wx.EVT_COMBOBOX, self.onDeviceSelection, self.deviceChoice
        )

    @api_tool_decorator()
    def RemoveEndpoint(self, event):
        value = None
        if (
            event.GetEventType() == wx.EVT_BUTTON.typeId
            and event.Id == wx.ID_DELETE
        ) or event.KeyCode == wx.WXK_DELETE:
            value = self.configList.GetValue()
            value = value.split("\n")
            # TODO: Search for entry based on host url instead of enterprise id
            if len(value) > 0:
                value = value[0].replace("API Host = ", "").strip()
            result = list(
                filter(
                    lambda x: value == x["apiHost"], self.parentFrame.auth_data
                )
            )
            if result:
                result = result[0]
            if value:
                res = wx.MessageBox(
                    "Are you sure you want to remove the configuration with the Enterprise Id of: %s?\nThis action cannot be undone once accepted."
                    % value,
                    style=wx.YES_NO | wx.ICON_WARNING,
                    parent=Globals.frame,
                )
                if res == wx.YES:
                    if result in self.parentFrame.auth_data:
                        self.parentFrame.auth_data.remove(result)
                    data = [
                        ["name", "apiHost", "enterprise", "apiKey", "apiPrefix"]
                    ]
                    for entry in self.parentFrame.auth_data:
                        authEntry = []
                        num = 0
                        for auth in entry.values():
                            if num == 4:
                                break
                            authEntry.append(auth)
                            num += 1
                        if authEntry not in data:
                            data.append(authEntry)
                    write_data_to_csv(self.parentFrame.authPath, data)
                    for (
                        child
                    ) in self.parentFrame.menubar.configMenu.GetMenuItems():
                        if (
                            value
                            in self.configChoice[child.GetItemLabel()].values()
                        ):
                            self.parentFrame.menubar.configMenu.Delete(child)
                    self.parentFrame.PopulateConfig()
                    wx.MessageBox(
                        "The configuration has been removed.",
                        style=wx.OK | wx.ICON_INFORMATION,
                        parent=Globals.frame,
                    )

    @api_tool_decorator()
    def clearSelections(self):
        self.selectedGroups.Clear()
        self.selectedDevices.Clear()
        self.selectedGroupsList = []
        self.selectedDevicesList = []

    @api_tool_decorator()
    def destroyMultiChoiceDialogs(self):
        if self.groupMultiDialog:
            self.groupMultiDialog.Close()
            self.groupMultiDialog.DestroyLater()
            self.groupMultiDialog = None
        if self.deviceMultiDialog:
            self.deviceMultiDialog.Close()
            self.deviceMultiDialog.DestroyLater()
            self.deviceMultiDialog = None

    @api_tool_decorator()
    def onGroupSelection(self, event):
        if not self.parentFrame.isRunning:
            choices = list(self.groups.keys())
            newChoices = []
            for choice in choices:
                match = self.groupDeviceCount.get(choice)
                if (
                    match is not None
                    and choice != Globals.ALL_DEVICES_IN_TENANT
                ):
                    newChoices.append("%s (Device Count: %s)" % (choice, match))
                elif choice == Globals.ALL_DEVICES_IN_TENANT:
                    newChoices.append(Globals.ALL_DEVICES_IN_TENANT)

            if self.groupMultiDialog:
                self.groupMultiDialog = None
            if not self.groupMultiDialog:
                self.groupMultiDialog = MultiSelectSearchDlg(
                    self.parentFrame,
                    newChoices,
                    label="Select Group(s)",
                    title="Select Group(s)",
                    resp=self.groupsResp,
                )

            Globals.OPEN_DIALOGS.append(self.groupMultiDialog)
            if self.groupMultiDialog.ShowModal() == wx.ID_OK:
                self.parentFrame.menubar.disableConfigMenu()
                self.clearSelections()
                selections = self.groupMultiDialog.GetSelections()
                if selections:
                    for groupName in selections:
                        groupNameProper = groupName.split(" (Device Count:")[0]
                        groupId = (
                            self.groups[groupNameProper]
                            if groupNameProper in self.groups
                            else groupNameProper
                        )
                        self.selectedGroups.Append(groupName)
                        if groupNameProper.lower() == "all devices":
                            self.selectedGroups.Clear()
                            self.selectedGroupsList = []
                            self.selectedGroups.Append(groupName)
                            self.selectedGroupsList.append(groupId)
                            break
                        if groupId not in self.selectedGroupsList:
                            self.selectedGroupsList.append(groupId)
            Globals.OPEN_DIALOGS.remove(self.groupMultiDialog)
            self.destroyMultiChoiceDialogs()
            if (
                self.selectedGroupsList
                and not self.parentFrame.preferences
                or self.parentFrame.preferences["enableDevice"] is True
            ):
                self.parentFrame.setCursorBusy()
                self.devices = {}
                self.parentFrame.PopulateDevices(None)
            else:
                self.parentFrame.menubar.enableConfigMenu()
            Globals.frame.Refresh()

    @api_tool_decorator()
    def onDeviceSelection(self, event):
        if not self.parentFrame.isRunning and self.devices:
            choices = list(self.devices.keys())
            if self.deviceMultiDialog:
                self.deviceMultiDialog = None
            if not self.deviceMultiDialog:
                self.deviceMultiDialog = MultiSelectSearchDlg(
                    self.parentFrame,
                    choices,
                    label="Select Device(s)",
                    title="Select Device(s)",
                    resp=self.deviceResp,
                )
            Globals.OPEN_DIALOGS.append(self.deviceMultiDialog)
            if self.deviceMultiDialog.ShowModal() == wx.ID_OK:
                self.parentFrame.menubar.disableConfigMenu()
                self.selectedDevices.Clear()
                self.selectedDevicesList = []
                selections = self.deviceMultiDialog.GetSelections()
                for deviceName in selections:
                    deviceId = None
                    if deviceName in self.devices.keys():
                        deviceId = self.devices[deviceName]
                    elif deviceName in self.devicesExtended.keys():
                        deviceId = self.devicesExtended[deviceName]
                        self.devices[deviceName] = deviceId
                    if deviceId:
                        self.selectedDevices.Append(deviceName)
                        if deviceId not in self.selectedDevicesList:
                            self.selectedDevicesList.append(deviceId)
            self.parentFrame.menubar.enableConfigMenu()
            Globals.OPEN_DIALOGS.remove(self.deviceMultiDialog)
            self.destroyMultiChoiceDialogs()
            Globals.frame.Refresh()

    @api_tool_decorator()
    def onActionSelection(self, event):
        clientData = event.ClientData
        if not clientData:
            action = self.actionChoice.GetValue()
            if action in Globals.GENERAL_ACTIONS:
                clientData = Globals.GENERAL_ACTIONS[action]
            elif action in Globals.GRID_ACTIONS:
                clientData = Globals.GRID_ACTIONS[action]

    def applyFontSize(self):
        normalBoldFont = getFont(FontStyles.NORMAL_BOLD.value)

        fontRules = {
            wx.StaticText: normalBoldFont,
            wx.Notebook: normalBoldFont,
            wx.Button: normalBoldFont,
        }
        applyFontHelper(fontRules, self, self)

    def getFriendlySelectedGroupNames(self):
        friendlyNames = []
        for groupId in self.selectedGroupsList:
            found = True
            for groupName, group in self.groups.items():
                if groupId == group:
                    friendlyNames.append(groupName)
                    found = True
                    break
            if not found:
                friendlyNames.append(groupId)
        return friendlyNames

    def getFriendlySelectedDeviceNames(self):
        friendlyNames = []
        for deviceId in self.selectedDevicesList:
            found = True
            for deviceName, device in self.devices.items():
                if deviceId == device:
                    friendlyNames.append(deviceName)
                    found = True
                    break
            if not found:
                friendlyNames.append(deviceId)
        return friendlyNames

    def reset_panel(self):
        self.groups = {}
        self.devices = {}
        self.groupDeviceCount = {}
        self.clearSelections()
        self.destroyMultiChoiceDialogs()
        self.deviceChoice.Enable(False)
        self.removeEndpointBtn.Enable(False)
        self.notebook_1.SetSelection(0)