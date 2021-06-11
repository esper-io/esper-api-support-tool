#!/usr/bin/env python3
from requests.api import head
from wx.core import YES
from Utility.EsperAPICalls import createNewUser
import os
from Common.decorator import api_tool_decorator
import Common.Globals as Globals
import Utility.wxThread as wxThread
from Utility.Resource import (
    createNewFile,
    displayMessageBox,
    postEventToFrame,
)
import csv
import wx
import wx.grid


class UserCreation(wx.Frame):
    def __init__(self, parent, *args, **kwds):
        wx.Frame.__init__(self, None, style=wx.DEFAULT_FRAME_STYLE)
        self.SetSize((671, 560))
        self.SetTitle("User Creation")
        self.users = []
        self.headers = [
            "First Name",
            "Last Name",
            "Email",
            "Username",
            "Password",
            "Role",
            "Groups",
        ]
        self.parent = parent
        self.lastFilePath = ""

        grid_sizer_2 = wx.GridSizer(1, 1, 0, 0)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        grid_sizer_2.Add(self.panel_1, 1, wx.EXPAND, 0)

        grid_sizer_3 = wx.GridSizer(1, 1, 0, 0)

        self.panel_2 = wx.Panel(self.panel_1, wx.ID_ANY)
        grid_sizer_3.Add(self.panel_2, 1, wx.ALL | wx.EXPAND, 5)

        sizer_1 = wx.FlexGridSizer(8, 1, 0, 0)

        label_1 = wx.StaticText(self.panel_2, wx.ID_ANY, "User Creation")
        label_1.SetFont(
            wx.Font(
                Globals.HEADER_FONT_SIZE,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        sizer_1.Add(label_1, 0, 0, 0)

        static_line_1 = wx.StaticLine(self.panel_2, wx.ID_ANY)
        sizer_1.Add(static_line_1, 0, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0)

        grid_sizer_1 = wx.FlexGridSizer(1, 2, 0, 0)
        sizer_1.Add(grid_sizer_1, 1, wx.EXPAND, 0)

        label_2 = wx.StaticText(
            self.panel_2, wx.ID_ANY, "Download and Fill in the Template:"
        )
        label_2.SetFont(
            wx.Font(
                Globals.FONT_SIZE,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "",
            )
        )
        grid_sizer_1.Add(label_2, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.button_1 = wx.Button(self.panel_2, wx.ID_ANY, "Download")
        grid_sizer_1.Add(
            self.button_1, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.LEFT, 5
        )

        grid_sizer_5 = wx.FlexGridSizer(1, 2, 0, 0)
        sizer_1.Add(grid_sizer_5, 1, wx.EXPAND | wx.TOP, 5)

        label_4 = wx.StaticText(self.panel_2, wx.ID_ANY, "Upload CSV:")
        label_4.SetFont(
            wx.Font(
                Globals.FONT_SIZE,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "",
            )
        )
        grid_sizer_5.Add(label_4, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.button_2 = wx.Button(self.panel_2, wx.ID_ANY, "Upload")
        grid_sizer_5.Add(
            self.button_2, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.LEFT, 5
        )

        label_3 = wx.StaticText(self.panel_2, wx.ID_ANY, "Preview:")
        label_3.SetFont(
            wx.Font(
                Globals.FONT_SIZE,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "",
            )
        )
        sizer_1.Add(label_3, 0, wx.TOP, 5)

        self.panel_3 = wx.Panel(self.panel_2, wx.ID_ANY)
        sizer_1.Add(self.panel_3, 1, wx.EXPAND, 0)

        grid_sizer_6 = wx.GridSizer(1, 1, 0, 0)

        self.grid_1 = wx.grid.Grid(self.panel_3, wx.ID_ANY, size=(1, 1))
        self.grid_1.CreateGrid(0, 7)
        self.grid_1.EnableEditing(0)
        self.grid_1.EnableDragRowSize(0)
        self.grid_1.SetColLabelValue(0, "First Name")
        self.grid_1.SetColLabelValue(1, "Last Name")
        self.grid_1.SetColLabelValue(2, "Email")
        self.grid_1.SetColLabelValue(3, "Username")
        self.grid_1.SetColLabelValue(4, "Password")
        self.grid_1.SetColLabelValue(5, "Role")
        self.grid_1.SetColLabelValue(6, "Groups")
        grid_sizer_6.Add(self.grid_1, 1, wx.EXPAND | wx.TOP, 2)

        static_line_2 = wx.StaticLine(self.panel_2, wx.ID_ANY)
        sizer_1.Add(
            static_line_2,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.EXPAND | wx.TOP,
            5,
        )

        grid_sizer_4 = wx.GridSizer(1, 2, 0, 0)
        sizer_1.Add(grid_sizer_4, 1, wx.EXPAND | wx.TOP, 5)

        grid_sizer_4.Add((0, 0), 0, 0, 0)

        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_4.Add(sizer_3, 1, wx.ALIGN_RIGHT | wx.EXPAND, 0)

        self.button_6 = wx.Button(self.panel_2, wx.ID_ANY, "Create")
        sizer_3.Add(self.button_6, 0, wx.RIGHT, 5)

        self.button_7 = wx.Button(self.panel_2, wx.ID_ANY, "Cancel")
        sizer_3.Add(self.button_7, 0, wx.RIGHT, 5)

        self.panel_3.SetSizer(grid_sizer_6)

        grid_sizer_5.AddGrowableCol(1)

        grid_sizer_1.AddGrowableCol(1)

        sizer_1.AddGrowableRow(5)
        sizer_1.AddGrowableCol(0)
        self.panel_2.SetSizer(sizer_1)

        self.panel_1.SetSizer(grid_sizer_3)

        self.SetSizer(grid_sizer_2)

        self.Layout()
        self.Centre()

        self.button_6.Enable(False)

        self.button_1.Bind(wx.EVT_BUTTON, self.downloadTemplate)
        self.button_2.Bind(wx.EVT_BUTTON, self.upload)
        self.button_6.Bind(wx.EVT_BUTTON, self.onCreate)
        self.button_7.Bind(wx.EVT_BUTTON, self.onClose)
        self.Bind(wx.EVT_DROP_FILES, self.onFileDrop)
        self.Bind(wx.EVT_KEY_UP, self.onEscapePressed)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.DragAcceptFiles(True)

    @api_tool_decorator()
    def onEscapePressed(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_ESCAPE:
            self.onClose(event)

    @api_tool_decorator()
    def onClose(self, event):
        if Globals.frame:
            Globals.frame.isRunning = False
            Globals.frame.toggleEnabledState(
                not Globals.frame.isRunning and not Globals.frame.isSavingPrefs
            )
        if event.EventType != wx.EVT_CLOSE.typeId:
            self.Close()
        self.DestroyLater()

    def downloadTemplate(self, event):
        dlg = wx.FileDialog(
            self,
            message="Save User Creation CSV Template",
            defaultFile="",
            wildcard="*.csv",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )
        result = dlg.ShowModal()
        inFile = dlg.GetPath()
        dlg.DestroyLater()

        if result == wx.ID_OK:
            createNewFile(inFile)

            gridData = []
            gridData.append(self.headers)
            with open(inFile, "w", newline="") as csvfile:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
                writer.writerows(gridData)
            return True
        return False

    @api_tool_decorator()
    def upload(self, event):
        with wx.FileDialog(
            self,
            "Open User CSV File",
            wildcard="CSV files (*.csv)|*.csv",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
            defaultDir=str(self.lastFilePath),
        ) as fileDialog:
            result = fileDialog.ShowModal()
            if result == wx.ID_OK:
                self.lastFilePath = fileDialog.GetPath()
                if not os.path.isdir(self.lastFilePath):
                    self.lastFilePath = os.path.abspath(
                        os.path.join(self.lastFilePath, os.pardir)
                    )
                self.processUpload(fileDialog.GetPath())

    @api_tool_decorator()
    def onFileDrop(self, event):
        for file in event.Files:
            if file.endswith(".csv"):
                self.processUpload(file)

    @api_tool_decorator()
    def processUpload(self, file):
        if self.grid_1.GetNumberRows() > 0:
            self.grid_1.DeleteRows(0, self.grid_1.GetNumberRows())
        data = None
        with open(file, "r") as csvFile:
            reader = csv.reader(
                csvFile, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True
            )
            data = list(reader)
        invalidUsers = []
        if data:
            self.grid_1.Freeze()
            headers = None
            for entry in data:
                if "Username" not in entry:
                    if (
                        (
                            "Username" not in headers
                            or (
                                "First Name" not in headers
                                and "Last Name" not in headers
                            )
                        )
                        and "Password" not in headers
                        and "Role" not in headers
                        and "Email" not in headers
                    ):
                        displayMessageBox(
                            (
                                "Failed to add Users. Please make sure that Username (or First and Last Name), Email, Password, and Role columns exist and are filled out for each User.",
                                wx.ICON_ERROR,
                            )
                        )
                        break
                    if (
                        (
                            not entry[headers.index("Username")]
                            and not entry[headers.index("First Name")]
                            and not entry[headers.index("Last Name")]
                        )
                        or not entry[headers.index("Password")]
                        or not entry[headers.index("Role")]
                    ) or (
                        (
                            entry[headers.index("Role")] != "Enterprise Admin"
                            and entry[headers.index("Role")] != "Viewer"
                        )
                        and not entry[headers.index("Groups")]
                    ):
                        invalidUsers.append(entry)
                    else:
                        self.grid_1.AppendRows()
                        col = 0
                        user = {}
                        for field in entry:
                            if len(headers) > col:
                                if headers[col]:
                                    indx = self.headers.index(headers[col])
                                    self.grid_1.SetCellValue(
                                        self.grid_1.GetNumberRows() - 1,
                                        indx,
                                        str(field),
                                    )
                                    user[headers[col].lower().replace(" ", "_")] = str(
                                        field
                                    )
                            col += 1
                        if "first_name" not in user:
                            user["first_name"] = ""
                        if "last_name" not in user:
                            user["last_name"] = ""
                        if "username" in user and not user["username"]:
                            user["username"] = user["first_name"] + user["last_name"]
                            self.grid_1.SetCellValue(
                                self.grid_1.GetNumberRows() - 1,
                                self.headers.index("Username"),
                                str(user["username"]),
                            )
                        self.users.append(user)
                else:
                    headers = entry
        self.grid_1.Thaw()
        self.grid_1.AutoSizeColumns()
        if self.grid_1.GetNumberRows() > 0:
            self.button_6.Enable(True)
        if invalidUsers:
            displayMessageBox(
                (
                    "Successfully added %s of %s users!\nPlease make sure all necessary fields are filled in for each User entry."
                    % (len(self.users), len(data) - 1),
                    wx.ICON_INFORMATION,
                )
            )

    @api_tool_decorator()
    def onCreate(self, event):
        if not self.grid_1.GetNumberRows() > 0:
            self.button_6.Enable(False)
            return
        res = displayMessageBox(
            (
                'You are about to add the previewed Users to "%s", are you sure?'
                % Globals.frame.configMenuItem.GetItemLabelText(),
                wx.ICON_INFORMATION | wx.YES_NO,
            )
        )
        if res == wx.YES:
            num = 0
            numCreated = 0
            self.dialog = wx.ProgressDialog(
                "Creating Users",
                "Time remaining",
                100,
                style=wx.PD_CAN_ABORT | wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME,
            )
            for user in self.users:
                username = (
                    user["username"]
                    if "username" in user.keys()
                    else (user["first_name"] + user["last_name"])
                )
                resp = createNewUser(user)
                num += 1
                logMsg = ""
                if resp.status_code > 299:
                    logMsg = "Successfully created user account: %s" % username
                    numCreated += 1
                else:
                    logMsg = "ERROR: failed to create user account: %s" % username
                postEventToFrame(
                    wxThread.myEVT_UPDATE_GAUGE, int(num / len(self.users) * 100)
                )
                self.dialog.Update(
                    int(num / len(self.users) * 100),
                    "Successfully created %s of %s users!"
                    % (numCreated, len(self.users)),
                )
                postEventToFrame(wxThread.myEVT_LOG, logMsg)
            self.dialog.Close()
            if self.grid_1.GetNumberRows() > 0:
                self.grid_1.DeleteRows(0, self.grid_1.GetNumberRows())
            self.grid_1.SetScrollLineX(15)
            self.grid_1.SetScrollLineY(15)
            self.button_2.SetFocus()

    def tryToMakeActive(self):
        self.Raise()
        self.Iconize(False)
        style = self.GetWindowStyle()
        self.SetWindowStyle(style | wx.STAY_ON_TOP)
        self.SetFocus()
        self.SetWindowStyle(style)
