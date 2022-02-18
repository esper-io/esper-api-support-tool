#!/usr/bin/env python3

import wx
import csv
import Common.Globals as Globals
import wx.grid
from Utility import wxThread
from Utility.API.DeviceUtility import get_all_devices
from Utility.API.GroupUtility import getAllGroups, getGroupById
# from Utility.API.EsperAPICalls import searchForMatchingDevices

from Utility.Resource import displayMessageBox, getHeader
from Utility.Web.WebRequests import performPostRequestWithRetry


class GeofenceDialog(wx.Dialog):
    def __init__(self, *args, **kwds):
        super(GeofenceDialog, self).__init__(
            None,
            wx.ID_ANY,
            size=(650, 500),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.SetSize((650, 500))
        self.SetMinSize((650, 500))
        self.SetTitle("Create Geofence")

        self.groups = []
        self.gridHeaderLabels = [
            "Given Group Identifer",
            "Calculated Group Path",
            "Group Id"
        ]

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        grid_sizer_4 = wx.FlexGridSizer(2, 1, 0, 0)
        sizer_1.Add(grid_sizer_4, 1, wx.EXPAND, 0)

        label_7 = wx.StaticText(self, wx.ID_ANY, "Create Geofence")
        label_7.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        grid_sizer_4.Add(label_7, 0, wx.ALL, 5)

        grid_sizer_1 = wx.GridSizer(1, 2, 0, 0)
        grid_sizer_4.Add(grid_sizer_1, 1, wx.EXPAND, 0)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        grid_sizer_1.Add(self.panel_1, 1, wx.EXPAND | wx.RIGHT, 5)

        grid_sizer_2 = wx.GridSizer(6, 1, 0, 0)

        grid_sizer_5 = wx.FlexGridSizer(1, 2, 0, 0)
        grid_sizer_2.Add(grid_sizer_5, 1, wx.EXPAND, 0)

        label_1 = wx.StaticText(self.panel_1, wx.ID_ANY, "Name:")
        grid_sizer_5.Add(label_1, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

        self.text_ctrl_1 = wx.TextCtrl(self.panel_1, wx.ID_ANY, "")
        grid_sizer_5.Add(self.text_ctrl_1, 0, wx.EXPAND, 0)

        grid_sizer_6 = wx.FlexGridSizer(1, 2, 0, 0)
        grid_sizer_2.Add(grid_sizer_6, 1, wx.EXPAND, 0)

        label_2 = wx.StaticText(self.panel_1, wx.ID_ANY, "Latitude:")
        grid_sizer_6.Add(label_2, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

        self.text_ctrl_2 = wx.TextCtrl(self.panel_1, wx.ID_ANY, "")
        grid_sizer_6.Add(self.text_ctrl_2, 0, wx.EXPAND, 0)

        grid_sizer_7 = wx.FlexGridSizer(1, 2, 0, 0)
        grid_sizer_2.Add(grid_sizer_7, 1, wx.EXPAND, 0)

        label_3 = wx.StaticText(self.panel_1, wx.ID_ANY, "Longitude:")
        grid_sizer_7.Add(label_3, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

        self.text_ctrl_3 = wx.TextCtrl(self.panel_1, wx.ID_ANY, "")
        grid_sizer_7.Add(self.text_ctrl_3, 0, wx.EXPAND, 0)

        grid_sizer_8 = wx.FlexGridSizer(1, 2, 0, 0)
        grid_sizer_2.Add(grid_sizer_8, 1, wx.EXPAND, 0)

        label_4 = wx.StaticText(self.panel_1, wx.ID_ANY, "Radius (Meters):")
        grid_sizer_8.Add(label_4, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

        self.spin_ctrl_1 = wx.SpinCtrl(self.panel_1, wx.ID_ANY, "100", min=100, max=10000)
        grid_sizer_8.Add(self.spin_ctrl_1, 0, wx.EXPAND, 0)

        grid_sizer_9 = wx.FlexGridSizer(3, 1, 0, 0)
        grid_sizer_2.Add(grid_sizer_9, 1, wx.EXPAND, 0)

        label_5 = wx.StaticText(self.panel_1, wx.ID_ANY, "Device Actions:")
        grid_sizer_9.Add(label_5, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

        self.checkbox_1 = wx.CheckBox(self.panel_1, wx.ID_ANY, "Beep")
        grid_sizer_9.Add(self.checkbox_1, 0, wx.LEFT, 10)

        self.checkbox_2 = wx.CheckBox(self.panel_1, wx.ID_ANY, "Lock Down")
        grid_sizer_9.Add(self.checkbox_2, 0, wx.LEFT, 10)

        grid_sizer_10 = wx.FlexGridSizer(2, 1, 0, 0)
        grid_sizer_2.Add(grid_sizer_10, 1, wx.EXPAND, 0)

        label_6 = wx.StaticText(self.panel_1, wx.ID_ANY, "Description:")
        grid_sizer_10.Add(label_6, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

        self.text_ctrl_4 = wx.TextCtrl(self.panel_1, wx.ID_ANY, "", style=wx.TE_MULTILINE | wx.TE_WORDWRAP)
        grid_sizer_10.Add(self.text_ctrl_4, 0, wx.EXPAND | wx.LEFT, 10)

        grid_sizer_3 = wx.FlexGridSizer(2, 1, 0, 0)
        grid_sizer_1.Add(grid_sizer_3, 0, wx.ALL | wx.EXPAND, 5)

        self.button_1 = wx.Button(self, wx.ID_ANY, "Upload Devices (CSV)")
        grid_sizer_3.Add(self.button_1, 0, wx.ALIGN_RIGHT, 0)

        self.grid_1 = wx.grid.Grid(self, wx.ID_ANY, size=(1, 1))
        self.grid_1.CreateGrid(0, 0)
        grid_sizer_3.Add(self.grid_1, 1, wx.EXPAND | wx.TOP, 5)

        sizer_2 = wx.StdDialogButtonSizer()
        sizer_1.Add(sizer_2, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

        self.button_CANCEL = wx.Button(self, wx.ID_CANCEL, "")
        sizer_2.AddButton(self.button_CANCEL)

        self.button_APPLY = wx.Button(self, wx.ID_APPLY, "")
        sizer_2.AddButton(self.button_APPLY)

        sizer_2.Realize()

        grid_sizer_3.AddGrowableRow(1)
        grid_sizer_3.AddGrowableCol(0)

        grid_sizer_10.AddGrowableRow(1)
        grid_sizer_10.AddGrowableCol(0)

        grid_sizer_9.AddGrowableCol(0)

        grid_sizer_8.AddGrowableCol(0)
        grid_sizer_8.AddGrowableCol(1)

        grid_sizer_7.AddGrowableCol(0)
        grid_sizer_7.AddGrowableCol(1)

        grid_sizer_6.AddGrowableCol(0)
        grid_sizer_6.AddGrowableCol(1)

        grid_sizer_5.AddGrowableCol(0)
        grid_sizer_5.AddGrowableCol(1)

        self.panel_1.SetSizer(grid_sizer_2)

        grid_sizer_4.AddGrowableRow(1)
        grid_sizer_4.AddGrowableCol(0)

        self.SetSizer(sizer_1)

        self.SetEscapeId(self.button_CANCEL.GetId())

        self.Layout()

        self.button_APPLY.Bind(wx.EVT_BUTTON, self.createGeofence)
        self.button_1.Bind(wx.EVT_BUTTON, self.onUpload)
        self.button_CANCEL.Bind(wx.EVT_BUTTON, self.onClose)

        self.fillGridHeaders()
        self.grid_1.UseNativeColHeader()
        self.grid_1.HideCol(2)
        self.grid_1.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.toogleViewMenuItem)

    def onClose(self, event):
        if Globals.frame:
            Globals.frame.isRunning = False
            Globals.frame.toggleEnabledState(
                not Globals.frame.isRunning and not Globals.frame.isSavingPrefs
            )
        if event.EventType != wx.EVT_CLOSE.typeId:
            self.Close()
        self.DestroyLater()

    def fillGridHeaders(self):
        """ Populate Grid Headers """
        num = 0
        try:
            for head in self.gridHeaderLabels:
                if head:
                    if self.grid_1.GetNumberCols() < len(self.gridHeaderLabels):
                        self.grid_1.AppendCols(1)
                    self.grid_1.SetColLabelValue(num, head)
                    num += 1
        except:
            pass
        self.grid_1.AutoSizeColumns()

    def onUpload(self, event):
        with wx.FileDialog(
            self,
            "Open Geofence CSV File",
            wildcard="CSV files (*.csv)|*.csv",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as fileDialog:
            result = fileDialog.ShowModal()
            if result == wx.ID_OK:
                # Clear list of devices
                self.groups = []
                filePath = fileDialog.GetPath()
                # Clear grid on previous content
                thread = wxThread.GUIThread(None, self.processUpload, (filePath,))
                thread.start()

    def processUpload(self, filePath):
        if self.grid_1.GetNumberRows() > 0:
            self.grid_1.DeleteRows(0, self.grid_1.GetNumberRows())
        # Read data from given CSV file
        data = None
        with open(filePath, "r") as csvFile:
            reader = csv.reader(
                csvFile, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True
            )
            data = list(reader)
        if data:
            self.grid_1.Freeze()
            # Iterate through each row and populate grid
            for entry in data:
                self.grid_1.AppendRows()
                self.grid_1.SetCellValue(
                    self.grid_1.GetNumberRows() - 1,
                    0,
                    str(entry[0]),
                )
                self.groups.append(entry[0])
                # Add identifier to list of devices
                group = None
                if len(entry[0].split("-")) == 5:
                    self.grid_1.SetCellValue(
                        self.grid_1.GetNumberRows() - 1,
                        2,
                        str(entry[0]),
                    )
                    group = getGroupById(str(entry[0]))
                else:
                    groups = getAllGroups(name=entry[0])
                    if groups:
                        for groupRes in groups.results:
                            if groupRes.name == str(entry[0]) or groupRes.path == str(entry[0]):
                                group = groupRes
                                break
                    if group:
                        self.grid_1.SetCellValue(
                            self.grid_1.GetNumberRows() - 1,
                            2,
                            group.id,
                        )
                if group:
                    self.grid_1.SetCellValue(
                        self.grid_1.GetNumberRows() - 1,
                        1,
                        group.path,
                    )
                else:
                    self.grid_1.SetCellValue(
                        self.grid_1.GetNumberRows() - 1,
                        1,
                        "<Could Not Find Group>",
                    )
                self.grid_1.SetReadOnly(self.grid_1.GetNumberRows() - 1, 0)
                self.grid_1.SetReadOnly(self.grid_1.GetNumberRows() - 1, 1)
                self.grid_1.SetReadOnly(self.grid_1.GetNumberRows() - 1, 2)
            self.grid_1.AutoSizeColumns()
            self.grid_1.Thaw()

    def createGeofence(self, event):
        # Read in inputs from text fields
        name = self.text_ctrl_1.GetValue()
        latitude = self.text_ctrl_2.GetValue()
        description = self.text_ctrl_4.GetValue()
        longitude = self.text_ctrl_3.GetValue()
        radius = self.spin_ctrl_1.GetValue()
        actionsList = []

        if self.checkbox_1.IsChecked():
            actionsList.append("beep")

        if self.checkbox_2.IsChecked():
            actionsList.append("lock_down")

        properGroupIdList = []
        for rowNum in range(self.grid_1.GetNumberRows()):
            identifier = self.grid_1.GetCellValue(rowNum, 2)
            if len(identifier.split("-")) == 5:
                properGroupIdList.append(identifier)

        # Ensure that inputs are vaild before calling API
        if name and latitude and description and longitude and radius and actionsList:
            dialog = displayMessageBox(
                (
                    'Found group ids for %s out of %s uploaded entries. Would you like to proceed?' % (len(properGroupIdList), len(self.groups)),
                    wx.ICON_INFORMATION | wx.YES_NO,
                )
            )
            if dialog == wx.YES:
                self.button_APPLY.Enable(False)
                self.setCursorBusy()
                thread = wxThread.GUIThread(None, self.processCreateGeoFenceRequest, (properGroupIdList, name, description, latitude, longitude, radius, actionsList))
                thread.start()
        else:
            displayMessageBox(
                (
                    'You are missing some required input!',
                    wx.ICON_ERROR | wx.OK,
                )
            )

    def processCreateGeoFenceRequest(self, properGroupIdList, name, description, latitude, longitude, radius, actionsList):
        deviceList = []
        for groupId in properGroupIdList:
            devices = get_all_devices(groupId, Globals.limit, 0)
            deviceList += devices.results
        # Only add active devices
        deviceList = list(
            filter(
                lambda x: (x.status != 20),
                deviceList,
            )
        )
        deviceIdList = [device.id for device in deviceList]
        if not deviceIdList:
            displayMessageBox(
                (
                    'No devices found for the uploaded groups',
                    wx.ICON_ERROR | wx.OK,
                )
            )
        else:
            resp = self.createApplyGeofence(name, description, latitude, longitude, radius, deviceIdList, actions=actionsList)
            # You can choose to do something with the response, e.g. showcase the user the results of the API
            if resp and hasattr(resp, "status_code") and resp.status_code < 300 and resp.status_code >= 200:
                displayMessageBox(
                    (
                        'Successfully created Geofence.',
                        wx.ICON_INFORMATION | wx.OK,
                    )
                )
            else:
                displayMessageBox(
                    (
                        'Failed to create geofence!\n%s' % resp.text,
                        wx.ICON_ERROR | wx.OK,
                    )
                )
        self.button_APPLY.Enable(True)
        self.setCursorDefault()

    def createApplyGeofence(self, name, description, lat, long, radius, devices, radiusUnit="METERS", actions=["lock_down", "beep"]):
        tenant = Globals.configuration.host.replace("https://", "").replace(
            "-api.esper.cloud/api", ""
        )
        url = "https://{endpoint}-api.esper.cloud/api/v0/enterprise/{enterprise_id}/create-apply-geo-fence/".format(
            endpoint=tenant,
            enterprise_id=Globals.enterprise_id
        )
        body = {
            "name": name,
            "description": description,
            "latitude": lat,
            "longitude": long,
            "radius": radius,
            "radius_unit": radiusUnit,
            "device_actions": actions,
            "devices": devices if type(devices) == list else [devices]
        }
        resp = performPostRequestWithRetry(url, headers=getHeader(), json=body)

        return resp

    def toogleViewMenuItem(self, event):
        """
        Disable native headers ability to hide columns when clicking an entry from the context menu
        """
        return

    def setCursorDefault(self):
        """ Set cursor icon to default state """
        try:
            self.isBusy = False
            myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
            self.SetCursor(myCursor)
        except:
            pass

    def setCursorBusy(self):
        """ Set cursor icon to busy state """
        self.isBusy = True
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)
