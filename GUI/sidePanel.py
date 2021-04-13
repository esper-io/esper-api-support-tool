#!/usr/bin/env python

from Common.enum import GeneralActions, GridActions
from Common.decorator import api_tool_decorator
import csv
import wx
import Common.Globals as Globals

from Utility.Resource import resourcePath, scale_bitmap
from GUI.Dialogs.MultiSelectSearchDlg import MultiSelectSearchDlg


class SidePanel(wx.Panel):
    def __init__(self, parentFrame, parent, parentSizer, *args, **kw):
        super().__init__(*args, **kw)

        self.parentFrame = parentFrame
        self.configChoice = {}
        self.selectedDevicesList = []
        self.devices = {}
        self.selectedGroupsList = []
        self.groups = {}
        self.enterpriseApps = []
        self.selectedDeviceApps = []
        self.knownApps = []

        self.groupMultiDialog = None
        self.deviceMultiDialog = None

        sizer_1 = wx.FlexGridSizer(5, 1, 0, 0)
        parentSizer.Add(sizer_1, 0, wx.EXPAND, 0)

        self.panel_2 = wx.Panel(parent, wx.ID_ANY)
        sizer_1.Add(self.panel_2, 1, wx.ALL | wx.EXPAND, 5)

        sizer_2 = wx.BoxSizer(wx.VERTICAL)

        self.panel_3 = wx.Panel(self.panel_2, wx.ID_ANY)
        sizer_2.Add(self.panel_3, 0, wx.EXPAND, 0)

        grid_sizer_1 = wx.GridSizer(1, 2, 0, 0)

        label_1 = wx.StaticText(self.panel_3, wx.ID_ANY, "Loaded Configuration:")
        label_1.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        grid_sizer_1.Add(label_1, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 0)

        remove_icon = scale_bitmap(resourcePath("Images/remove.png"), 16, 16)
        self.removeEndpointBtn = wx.BitmapButton(
            self.panel_3,
            wx.ID_DELETE,
            remove_icon,
        )
        grid_sizer_1.Add(
            self.removeEndpointBtn,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL,
            0,
        )
        self.removeEndpointBtn.SetToolTip("Remove Endpoint from %s" % Globals.TITLE)
        self.removeEndpointBtn.Enable(False)

        self.panel_4 = wx.Panel(self.panel_2, wx.ID_ANY)
        sizer_2.Add(self.panel_4, 1, wx.EXPAND, 0)

        grid_sizer_2 = wx.GridSizer(1, 1, 0, 0)

        self.configList = wx.TextCtrl(
            self.panel_4, wx.ID_ANY, "", style=wx.TE_MULTILINE | wx.TE_READONLY
        )
        self.configList.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "",
            )
        )
        grid_sizer_2.Add(self.configList, 0, wx.EXPAND, 0)
        self.configList.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "",
            )
        )

        self.panel_8 = wx.Panel(parent, wx.ID_ANY)
        sizer_1.Add(self.panel_8, 1, wx.ALL | wx.EXPAND, 5)

        grid_sizer_6 = wx.BoxSizer(wx.VERTICAL)

        self.groupChoice = wx.Button(self.panel_8, wx.ID_ANY, "Select Group(s)")
        self.groupChoice.SetToolTip(
            "Select which group(s) you wish to run an action on."
        )
        self.groupChoice.SetFocus()
        grid_sizer_6.Add(self.groupChoice, 0, wx.EXPAND, 0)

        self.panel_13 = wx.Panel(self.panel_8, wx.ID_ANY)
        grid_sizer_6.Add(self.panel_13, 1, wx.EXPAND | wx.TOP, 5)

        grid_sizer_8 = wx.GridSizer(1, 1, 0, 0)

        self.selectedGroups = wx.ListBox(self.panel_13, wx.ID_ANY, choices=[])
        self.selectedGroups.SetToolTip("Currently Selected Group(s)")
        grid_sizer_8.Add(self.selectedGroups, 0, wx.EXPAND, 0)

        self.panel_9 = wx.Panel(parent, wx.ID_ANY)
        sizer_1.Add(self.panel_9, 1, wx.ALL | wx.EXPAND, 5)

        grid_sizer_3 = wx.BoxSizer(wx.VERTICAL)

        self.deviceChoice = wx.Button(
            self.panel_9, wx.ID_ANY, "Select Device(s) [Optional]"
        )
        self.deviceChoice.SetToolTip(
            "Select which device(s) you specifically wish to run an action on, optional."
        )
        grid_sizer_3.Add(self.deviceChoice, 0, wx.EXPAND, 0)

        self.panel_12 = wx.Panel(self.panel_9, wx.ID_ANY)
        grid_sizer_3.Add(self.panel_12, 1, wx.EXPAND | wx.TOP, 5)

        grid_sizer_7 = wx.GridSizer(1, 1, 0, 0)

        self.selectedDevices = wx.ListBox(self.panel_12, wx.ID_ANY, choices=[])
        self.selectedDevices.SetToolTip("Currently Selected Device(s)")
        grid_sizer_7.Add(self.selectedDevices, 0, wx.EXPAND, 0)

        self.panel_10 = wx.Panel(parent, wx.ID_ANY)
        sizer_1.Add(self.panel_10, 1, wx.ALL | wx.EXPAND, 5)

        sizer_5 = wx.BoxSizer(wx.VERTICAL)

        label_5 = wx.StaticText(self.panel_10, wx.ID_ANY, "Select Action:")
        label_5.SetFont(
            wx.Font(
                9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""
            )
        )
        sizer_5.Add(label_5, 0, wx.EXPAND, 0)

        self.actionChoice = wx.ComboBox(
            self.panel_10,
            wx.ID_ANY,
            choices=[],
            style=wx.CB_DROPDOWN | wx.CB_READONLY,
        )
        actions = {
            **Globals.GENERAL_ACTIONS,
            **Globals.GRID_ACTIONS,
        }
        for key, val in actions.items():
            self.actionChoice.Append(key, val)
        sizer_5.Add(self.actionChoice, 0, wx.EXPAND, 0)

        label_4 = wx.StaticText(self.panel_10, wx.ID_ANY, "Select Application:")
        label_4.SetFont(
            wx.Font(
                9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""
            )
        )
        sizer_5.Add(label_4, 0, wx.EXPAND, 0)

        self.appChoice = wx.ComboBox(
            self.panel_10, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY
        )
        sizer_5.Add(self.appChoice, 0, wx.EXPAND, 0)

        self.panel_11 = wx.Panel(parent, wx.ID_ANY)
        sizer_1.Add(self.panel_11, 1, wx.EXPAND, 0)

        grid_sizer_5 = wx.GridSizer(1, 1, 0, 0)

        self.runBtn = wx.Button(self.panel_11, wx.ID_ANY, "Run")
        grid_sizer_5.Add(self.runBtn, 0, wx.ALL | wx.EXPAND, 5)

        self.panel_11.SetSizer(grid_sizer_5)

        self.panel_10.SetSizer(sizer_5)

        self.panel_12.SetSizer(grid_sizer_7)

        self.panel_9.SetSizer(grid_sizer_3)

        self.panel_13.SetSizer(grid_sizer_8)

        self.panel_8.SetSizer(grid_sizer_6)

        self.panel_4.SetSizer(grid_sizer_2)

        self.panel_3.SetSizer(grid_sizer_1)

        self.panel_2.SetSizer(sizer_2)

        sizer_1.AddGrowableRow(0)
        sizer_1.AddGrowableRow(1)
        sizer_1.AddGrowableRow(2)
        sizer_1.AddGrowableRow(3)
        sizer_1.AddGrowableRow(4)

        self.__set_properties()

    @api_tool_decorator
    def __set_properties(self):
        self.actionChoice.SetSelection(1)

        self.actionChoice.Enable(False)
        self.deviceChoice.Enable(False)
        self.groupChoice.Enable(False)
        self.appChoice.Enable(False)
        self.runBtn.Enable(False)

        self.removeEndpointBtn.Bind(wx.EVT_BUTTON, self.RemoveEndpoint)
        self.groupChoice.Bind(wx.EVT_BUTTON, self.onGroupSelection)
        self.deviceChoice.Bind(wx.EVT_BUTTON, self.onDeviceSelection)
        self.actionChoice.Bind(wx.EVT_COMBOBOX, self.onActionSelection)

        self.deviceChoice.Bind(
            wx.EVT_COMBOBOX, self.onDeviceSelection, self.deviceChoice
        )

    @api_tool_decorator
    def RemoveEndpoint(self, event):
        value = None
        if (
            event.GetEventType() == wx.EVT_BUTTON.typeId and event.Id == wx.ID_DELETE
        ) or event.KeyCode == wx.WXK_DELETE:
            value = self.configList.GetValue()
            value = value.split("\n")[3].replace("Enterprise = ", "")
            result = list(filter(lambda x: value in x, self.parentFrame.auth_data))
            if result:
                result = result[0]
            if value:
                res = wx.MessageBox(
                    "Are you sure you want to remove the configuration with the Enterprise Id of: %s?\nThis action cannot be undone once accepted."
                    % value,
                    style=wx.YES_NO | wx.ICON_WARNING,
                )
                if res == wx.YES:
                    self.parentFrame.auth_data.remove(result)
                    with open(self.parentFrame.authPath, "w", newline="") as csvfile:
                        writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
                        writer.writerows(self.parentFrame.auth_data)
                    for child in self.parentFrame.menubar.configMenu.GetMenuItems():
                        if value in self.configChoice[child.GetItemLabel()].values():
                            self.parentFrame.menubar.configMenu.Delete(child)
                    self.parentFrame.PopulateConfig()
                    wx.MessageBox(
                        "The configuration has been removed.",
                        style=wx.OK | wx.ICON_INFORMATION,
                    )

    @api_tool_decorator
    def clearGroupAndDeviceSelections(self):
        self.selectedGroups.Clear()
        self.selectedDevices.Clear()
        self.selectedGroupsList = []
        self.selectedDevicesList = []

    @api_tool_decorator
    def destroyMultiChoiceDialogs(self):
        if self.groupMultiDialog:
            self.groupMultiDialog.Close()
            self.groupMultiDialog.DestroyLater()
            self.groupMultiDialog = None
        if self.deviceMultiDialog:
            self.deviceMultiDialog.Close()
            self.deviceMultiDialog.DestroyLater()
            self.deviceMultiDialog = None

    @api_tool_decorator
    def onGroupSelection(self, event):
        choices = list(self.groups.keys())
        if self.groupMultiDialog:
            self.groupMultiDialog.Close()
            self.groupMultiDialog.DestroyLater()
            self.groupMultiDialog = None
        if not self.groupMultiDialog:
            self.groupMultiDialog = MultiSelectSearchDlg(
                self.parentFrame,
                choices,
                label="Select Group(s)",
                title="Select Group(s)",
            )

        if self.groupMultiDialog.ShowModal() == wx.ID_OK:
            self.parentFrame.menubar.disableConfigMenu()
            self.knownApps = []
            self.clearGroupAndDeviceSelections()
            selections = self.groupMultiDialog.GetSelections()
            if selections:
                for groupName in selections:
                    groupId = self.groups[groupName]
                    self.selectedGroups.Append(groupName)
                    if groupName.lower() == "all devices":
                        self.selectedGroups.Clear()
                        self.selectedGroupsList = []
                        self.selectedGroups.Append(groupName)
                        self.selectedGroupsList.append(groupId)
                        break
                    if groupId not in self.selectedGroupsList:
                        self.selectedGroupsList.append(groupId)

        if self.selectedGroupsList:
            self.parentFrame.setCursorBusy()
            self.devices = {}
            self.parentFrame.PopulateDevices(None)

    @api_tool_decorator
    def onDeviceSelection(self, event):
        choices = list(self.devices.keys())
        if self.deviceMultiDialog:
            self.deviceMultiDialog.Close()
            self.deviceMultiDialog.DestroyLater()
            self.deviceMultiDialog = None
        if not self.deviceMultiDialog:
            self.deviceMultiDialog = MultiSelectSearchDlg(
                self.parentFrame,
                choices,
                label="Select Device(s)",
                title="Select Device(s)",
            )
        if self.deviceMultiDialog.ShowModal() == wx.ID_OK:
            self.parentFrame.menubar.disableConfigMenu()
            self.appChoice.Clear()
            self.selectedDevices.Clear()
            self.selectedDevicesList = []
            self.selectedDeviceApps = []
            selections = self.deviceMultiDialog.GetSelections()
            for deviceName in selections:
                deviceId = self.devices[deviceName]
                self.selectedDevices.Append(deviceName)
                if deviceId not in self.selectedDevicesList:
                    self.selectedDevicesList.append(deviceId)
        self.parentFrame.onDeviceSelections(None)

    @api_tool_decorator
    def sortAndPopulateAppChoice(self):
        if not self.selectedDevicesList:
            self.apps = self.enterpriseApps
        else:
            self.apps = self.selectedDeviceApps
        if not self.apps:
            self.apps = self.knownApps + self.selectedDeviceApps + self.enterpriseApps
        self.apps = sorted(self.apps, key=lambda i: i["app_name"].lower())
        self.appChoice.Clear()
        self.appChoice.Append("", "")
        percent = self.parentFrame.gauge.GetValue()
        num = 0
        for entry in self.apps:
            for key, value in entry.items():
                if (
                    key != "app_name"
                    and key != "app_state"
                    and key not in self.appChoice.Items
                    and (
                        (Globals.SHOW_PKG_NAME and " (" in key)
                        or (not Globals.SHOW_PKG_NAME and " (" not in key)
                    )
                ):
                    self.appChoice.Append(key, value)
                    break
            num += 1
            val = percent + int(float(num / len(self.apps) / 2) * 100)
            self.parentFrame.setGaugeValue(val)

    @api_tool_decorator
    def onActionSelection(self, event):
        # item = self.actionChoice.GetValue()
        clientData = event.ClientData
        if not clientData:
            clientData = Globals.GENERAL_ACTIONS[self.actionChoice.GetValue()]
        if (
            clientData == GeneralActions.SET_KIOSK.value
            or clientData == GeneralActions.CLEAR_APP_DATA.value
            or clientData == GeneralActions.SET_APP_STATE_DISABLE.value
            or clientData == GeneralActions.SET_APP_STATE_HIDE.value
            or clientData == GeneralActions.SET_APP_STATE_SHOW.value
        ) and clientData < GridActions.MODIFY_ALIAS_AND_TAGS.value:
            # self.parentFrame.PopulateApps()
            self.appChoice.Enable(True)
        else:
            self.appChoice.Enable(False)
