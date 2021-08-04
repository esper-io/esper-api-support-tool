#!/usr/bin/env python

from GUI.Dialogs.InstalledDevicesDlg import InstalledDevicesDlg
from Common.enum import Color, GeneralActions, GridActions
from Common.decorator import api_tool_decorator
import csv
import wx
import Common.Globals as Globals

from Utility.Resource import resourcePath, scale_bitmap
from GUI.Dialogs.MultiSelectSearchDlg import MultiSelectSearchDlg


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
        self.enterpriseApps = []
        self.selectedDeviceApps = []
        self.selectedAppEntry = []
        self.knownApps = []

        self.groupMultiDialog = None
        self.deviceMultiDialog = None

        sizer_1 = wx.FlexGridSizer(7, 1, 0, 0)

        self.panel_2 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_2, 0, wx.ALL | wx.EXPAND, 5)

        sizer_2 = wx.FlexGridSizer(2, 1, 0, 0)

        self.panel_3 = wx.Panel(self.panel_2, wx.ID_ANY)
        sizer_2.Add(self.panel_3, 0, wx.EXPAND, 0)

        grid_sizer_1 = wx.GridSizer(1, 2, 0, 0)

        label_1 = wx.StaticText(self.panel_3, wx.ID_ANY, "Loaded Endpoint:")
        label_1.SetFont(
            wx.Font(
                Globals.FONT_SIZE,
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

        self.configList = wx.TextCtrl(
            self.panel_2,
            wx.ID_ANY,
            "",
            style=wx.TE_MULTILINE | wx.TE_READONLY,
        )
        self.configList.SetFont(
            wx.Font(
                Globals.FONT_SIZE,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "",
            )
        )
        sizer_2.Add(self.configList, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 3)

        static_line_4 = wx.StaticLine(self, wx.ID_ANY)
        sizer_1.Add(
            static_line_4,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.EXPAND | wx.TOP,
            5,
        )

        self.notebook_1 = wx.Notebook(self, wx.ID_ANY)
        self.notebook_1.SetFont(
            wx.Font(
                9,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
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

        self.selectedGroups = wx.ListBox(self.panel_13, wx.ID_ANY, choices=[])
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

        self.selectedDevices = wx.ListBox(self.panel_12, wx.ID_ANY, choices=[])
        self.selectedDevices.SetToolTip("Currently Selected Device(s)")
        grid_sizer_7.Add(self.selectedDevices, 0, wx.EXPAND, 0)

        self.panel_16 = wx.Panel(self.notebook_1, wx.ID_ANY)
        self.notebook_1.AddPage(self.panel_16, "Application")

        sizer_8 = wx.BoxSizer(wx.VERTICAL)

        self.appChoice = wx.Button(self.panel_16, wx.ID_ANY, "Select Application")
        sizer_8.Add(self.appChoice, 0, wx.EXPAND | wx.TOP, 5)

        self.panel_17 = wx.Panel(self.panel_16, wx.ID_ANY)
        sizer_8.Add(self.panel_17, 1, wx.EXPAND | wx.TOP, 5)

        grid_sizer_9 = wx.GridSizer(1, 1, 0, 0)

        self.selectedApp = wx.ListBox(self.panel_17, wx.ID_ANY, choices=[])
        self.selectedApp.SetToolTip("Currently Selected Application")
        grid_sizer_9.Add(self.selectedApp, 0, wx.EXPAND, 0)

        static_line_2 = wx.StaticLine(self, wx.ID_ANY)
        sizer_1.Add(static_line_2, 0, wx.BOTTOM | wx.EXPAND | wx.TOP, 5)

        self.panel_10 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_10, 1, wx.ALL | wx.EXPAND, 5)

        sizer_5 = wx.BoxSizer(wx.VERTICAL)

        label_5 = wx.StaticText(self.panel_10, wx.ID_ANY, "Select Action:")
        label_5.SetFont(
            wx.Font(
                Globals.FONT_SIZE,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        sizer_5.Add(label_5, 0, wx.EXPAND, 0)

        self.actionChoice = wx.ComboBox(
            self.panel_10, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY
        )
        sizer_5.Add(self.actionChoice, 0, wx.EXPAND | wx.TOP, 5)

        static_line_3 = wx.StaticLine(self, wx.ID_ANY)
        sizer_1.Add(static_line_3, 0, wx.BOTTOM | wx.EXPAND | wx.TOP, 5)

        self.runBtn = wx.Button(self, wx.ID_ANY, "Run", style=wx.BU_AUTODRAW)
        sizer_1.Add(self.runBtn, 0, wx.ALL | wx.EXPAND, 5)

        self.panel_10.SetSizer(sizer_5)

        self.panel_17.SetSizer(grid_sizer_9)

        self.panel_16.SetSizer(sizer_8)

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
        self.appChoice.Enable(False)
        self.runBtn.Enable(False)

        self.removeEndpointBtn.Bind(wx.EVT_BUTTON, self.RemoveEndpoint)
        self.groupChoice.Bind(wx.EVT_BUTTON, self.onGroupSelection)
        self.deviceChoice.Bind(wx.EVT_BUTTON, self.onDeviceSelection)
        self.appChoice.Bind(wx.EVT_BUTTON, self.onAppSelection)
        self.actionChoice.Bind(wx.EVT_COMBOBOX, self.onActionSelection)

        self.deviceChoice.Bind(
            wx.EVT_COMBOBOX, self.onDeviceSelection, self.deviceChoice
        )

    @api_tool_decorator()
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

    @api_tool_decorator()
    def clearGroupAndDeviceSelections(self):
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
            if self.groupMultiDialog:
                self.groupMultiDialog = None
            if not self.groupMultiDialog:
                self.groupMultiDialog = MultiSelectSearchDlg(
                    self.parentFrame,
                    choices,
                    label="Select Group(s)",
                    title="Select Group(s)",
                    resp=self.groupsResp,
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

    @api_tool_decorator()
    def onDeviceSelection(self, event):
        if not self.parentFrame.isRunning:
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
            if self.deviceMultiDialog.ShowModal() == wx.ID_OK:
                self.parentFrame.menubar.disableConfigMenu()
                # self.appChoice.Clear()
                self.selectedDevices.Clear()
                self.selectedDevicesList = []
                self.selectedDeviceApps = []
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
            self.parentFrame.onDeviceSelections(None)

    def clearStoredApps(self):
        self.apps = []
        self.selectedDeviceApps = []
        self.enterpriseApps = []

    @api_tool_decorator()
    def sortAndPopulateAppChoice(self):
        if not self.selectedDevicesList:
            self.apps = self.enterpriseApps
        else:
            self.apps = self.selectedDeviceApps
        if not self.apps:
            self.apps = self.knownApps + self.selectedDeviceApps + self.enterpriseApps
        tmp = []
        for app in self.apps:
            if app not in tmp:
                tmp.append(app)
        self.apps = tmp
        self.apps = sorted(self.apps, key=lambda i: i["app_name"].lower())
        if len(self.apps):
            percent = self.parentFrame.gauge.GetValue()
            val = percent + int(float(len(self.apps) / 2) * 25)
            self.parentFrame.setGaugeValue(val)

    @api_tool_decorator()
    def onActionSelection(self, event):
        clientData = event.ClientData
        if not clientData:
            action = self.actionChoice.GetValue()
            if action in Globals.GENERAL_ACTIONS:
                clientData = Globals.GENERAL_ACTIONS[action]
            elif action in Globals.GRID_ACTIONS:
                clientData = Globals.GRID_ACTIONS[action]
        self.setAppChoiceState(clientData)

    @api_tool_decorator()
    def setAppChoiceState(self, clientData):
        if (
            clientData == GeneralActions.SET_KIOSK.value
            or clientData == GeneralActions.CLEAR_APP_DATA.value
            or clientData == GeneralActions.SET_APP_STATE_DISABLE.value
            or clientData == GeneralActions.SET_APP_STATE_HIDE.value
            or clientData == GeneralActions.SET_APP_STATE_SHOW.value
            or clientData == GeneralActions.INSTALL_APP.value
            or clientData == GeneralActions.UNINSTALL_APP.value
        ) and clientData < GridActions.MODIFY_ALIAS_AND_TAGS.value:
            self.appChoice.Enable(True)
            if self.selectedGroupsList or self.selectedDevicesList:
                self.notebook_1.SetSelection(2)
        else:
            self.appChoice.Enable(False)
            if self.selectedGroupsList:
                self.notebook_1.SetSelection(1)
            else:
                self.notebook_1.SetSelection(0)

    def onAppSelection(self, event):
        res = version = pkg = app_id = app_name = None
        self.selectedApp.Clear()
        action = self.actionChoice.GetClientData(self.actionChoice.GetSelection())
        hideVersion = True if action != GeneralActions.INSTALL_APP.value else False
        with InstalledDevicesDlg(
            self.apps, hide_version=hideVersion, title="Select Application"
        ) as dlg:
            res = dlg.ShowModal()
            if res == wx.ID_OK:
                app_id, version, pkg, app_name = dlg.getAppValues(
                    returnPkgName=True, returnAppName=True
                )
        if app_name:
            self.selectedApp.Append(app_name)
            self.selectedApp.SetSelection(0)
            self.selectedAppEntry = {
                "id": app_id,
                "version": version,
                "pkgName": pkg,
                "name": app_name,
            }
        if event:
            event.Skip()
