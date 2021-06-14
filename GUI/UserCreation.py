#!/usr/bin/env python3
from GUI.Dialogs.ConfirmTextDialog import ConfirmTextDialog
import json
from requests.api import head
from wx.core import YES
from Utility.EsperAPICalls import createNewUser, deleteUser, modifyUser
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
        self.SetTitle("User Management")
        self.users = []
        self.headers = {
            "First Name": 0,
            "firstname": 0,
            "Last Name": 1,
            "lastname": 1,
            "Email": 2,
            "email": 2,
            "Username": 3,
            "username": 3,
            "Password": 4,
            "password": 4,
            "Role": 5,
            "role": 5,
            "Groups": 6,
            "groups": 6,
        }
        self.roles = ["Enterprise Admin", "Viewer", "Group Viewer", "Group Admin"]
        self.parent = parent
        self.lastFilePath = ""

        grid_sizer_2 = wx.GridSizer(1, 1, 0, 0)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        grid_sizer_2.Add(self.panel_1, 1, wx.EXPAND, 0)

        grid_sizer_3 = wx.GridSizer(1, 1, 0, 0)

        self.panel_2 = wx.Panel(self.panel_1, wx.ID_ANY)
        grid_sizer_3.Add(self.panel_2, 1, wx.ALL | wx.EXPAND, 5)

        sizer_1 = wx.FlexGridSizer(10, 1, 0, 0)

        label_1 = wx.StaticText(self.panel_2, wx.ID_ANY, "User Management")
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
        sizer_1.Add(
            static_line_1,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.EXPAND | wx.TOP,
            5,
        )

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

        grid_sizer_7 = wx.FlexGridSizer(1, 2, 0, 0)
        sizer_1.Add(grid_sizer_7, 1, wx.EXPAND | wx.TOP, 5)

        label_5 = wx.StaticText(self.panel_2, wx.ID_ANY, "Select Action:")
        label_5.SetFont(
            wx.Font(
                Globals.FONT_SIZE,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "",
            )
        )
        grid_sizer_7.Add(label_5, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.choice_1 = wx.Choice(
            self.panel_2, wx.ID_ANY, choices=["Add", "Modify", "Delete"]
        )
        self.choice_1.SetSelection(0)
        grid_sizer_7.Add(self.choice_1, 0, wx.ALIGN_RIGHT | wx.EXPAND, 0)

        static_line_3 = wx.StaticLine(self.panel_2, wx.ID_ANY)
        sizer_1.Add(
            static_line_3,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.EXPAND | wx.TOP,
            5,
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
        self.grid_1.CreateGrid(41, 7)
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

        self.button_6 = wx.Button(self.panel_2, wx.ID_ANY, "Exectute")
        sizer_3.Add(self.button_6, 0, wx.RIGHT, 5)

        self.button_7 = wx.Button(self.panel_2, wx.ID_ANY, "Cancel")
        sizer_3.Add(self.button_7, 0, wx.RIGHT, 5)

        self.panel_3.SetSizer(grid_sizer_6)

        grid_sizer_7.AddGrowableCol(1)

        grid_sizer_5.AddGrowableCol(1)

        grid_sizer_1.AddGrowableCol(1)

        sizer_1.AddGrowableRow(7)
        sizer_1.AddGrowableCol(0)
        self.panel_2.SetSizer(sizer_1)

        self.panel_1.SetSizer(grid_sizer_3)

        self.SetSizer(grid_sizer_2)

        self.Layout()
        self.Centre()

        self.button_6.Enable(False)

        self.button_1.Bind(wx.EVT_BUTTON, self.downloadTemplate)
        self.button_2.Bind(wx.EVT_BUTTON, self.upload)
        self.button_6.Bind(wx.EVT_BUTTON, self.onExecute)
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
        self.users = []
        data = None
        with open(file, "r") as csvFile:
            reader = csv.reader(
                csvFile, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True
            )
            data = list(reader)
        invalidUsers = []
        if data:
            self.grid_1.Freeze()
            headers = []
            for entry in data:
                if "username" not in entry and "Username" not in entry:
                    if (
                        (
                            "username" not in headers
                            or (
                                "firstname" not in headers and "lastname" not in headers
                            )
                        )
                        and "password" not in headers
                        and "role" not in headers
                        and "email" not in headers
                        and self.choice_1.GetStringSelection() != "Delete"
                    ) or (
                        self.choice_1.GetStringSelection() == "Delete"
                        and "username" not in headers
                    ):
                        displayMessageBox(
                            (
                                "Failed to add Users. Please make sure that Username (or First and Last Name), Email, Password, and Role columns exist and are filled out for each User.",
                                wx.ICON_ERROR,
                            )
                        )
                        break
                    if not entry:
                        continue
                    if (
                        (
                            (
                                not entry[headers.index("username")]
                                and (
                                    len(entry) > headers.index("firstname")
                                    and not entry[headers.index("firstname")]
                                )
                                and (
                                    len(entry) > headers.index("lastname")
                                    and not entry[headers.index("lastname")]
                                )
                            )
                            or (
                                (
                                    len(entry) > headers.index("password")
                                    and not entry[headers.index("password")]
                                )
                                or (
                                    len(entry) > headers.index("role")
                                    and not entry[headers.index("role")]
                                )
                            )
                            and self.choice_1.GetStringSelection() != "Delete"
                        )
                        or (
                            (
                                len(entry) > headers.index("role")
                                and entry[headers.index("role")] != "Enterprise Admin"
                                and entry[headers.index("role")] != "Viewer"
                            )
                            and (
                                len(entry) > headers.index("groups")
                                and not entry[headers.index("groups")]
                            )
                            and self.choice_1.GetStringSelection() != "Delete"
                        )
                        or (
                            self.choice_1.GetStringSelection() != "Delete"
                            and (
                                len(entry) > headers.index("role")
                                and entry[headers.index("role")] not in self.roles
                            )
                        )
                    ):
                        invalidUsers.append(entry)
                    else:
                        self.grid_1.AppendRows()
                        col = 0
                        user = {}
                        for field in entry:
                            if len(headers) > col:
                                if headers[col]:
                                    indx = self.headers[headers[col]]
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
                                self.headers["Username"],
                                str(user["username"]),
                            )
                        if "role" in user and (
                            "Enterprise Admin" == user["role"]
                            or "Viewer" == user["role"]
                        ):
                            user["groups"] = []
                        if "groups" in user and type(user["groups"]) == str:
                            groups = user["groups"].split(",")
                            tmp = []
                            for group in groups:
                                tmp.append(group.strip())
                            user["groups"] = tmp
                        self.users.append(user)
                else:
                    # headers = entry
                    for header in entry:
                        headers.append(header.lower().replace(" ", ""))
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

    def onExecute(self, event):
        res = None
        if self.choice_1.GetStringSelection() == "Add":
            res = self.onCreate()
        elif self.choice_1.GetStringSelection() == "Modify":
            res = self.onModify()
        elif self.choice_1.GetStringSelection() == "Delete":
            res = self.onDelete()
        self.dialog.Update(self.dialog.GetRange())
        self.dialog.Destroy()
        formattedRes = ""
        try:
            formattedRes = json.dumps(res, indent=2).replace("\\n", "\n")
        except:
            formattedRes = json.dumps(str(res), indent=2).replace("\\n", "\n")
        if formattedRes:
            formattedRes += "\n\n"
        with ConfirmTextDialog(
            "User Management Results",
            "User Management Results",
            "",
            formattedRes,
            parent=self,
        ) as dialog:
            res = dialog.ShowModal()
        if self.grid_1.GetNumberRows() > 0:
            self.grid_1.DeleteRows(0, self.grid_1.GetNumberRows())
            self.users = []
        self.grid_1.SetScrollLineX(15)
        self.grid_1.SetScrollLineY(15)
        self.button_2.SetFocus()
        self.button_6.Enable(False)
        self.button_7.Enable(True)
        event.Skip()

    @api_tool_decorator()
    def onModify(self):
        if not self.grid_1.GetNumberRows() > 0:
            self.button_6.Enable(False)
            return
        res = displayMessageBox(
            (
                'You are about to modify the previewed Users on "%s", are you sure?'
                % Globals.frame.configMenuItem.GetItemLabelText(),
                wx.ICON_INFORMATION | wx.YES_NO,
            )
        )
        if res == wx.YES:
            self.button_6.Enable(False)
            self.button_7.Enable(False)
            num = 0
            numCreated = 0
            self.dialog = wx.ProgressDialog(
                "Modifying Users",
                "Time remaining",
                100,
                style=wx.PD_CAN_ABORT
                | wx.PD_ELAPSED_TIME
                | wx.PD_AUTO_HIDE
                | wx.PD_ESTIMATED_TIME,
            )
            logs = []
            for user in self.users:
                username = (
                    user["username"]
                    if "username" in user.keys()
                    else (user["first_name"] + user["last_name"])
                )
                if self.dialog.WasCancelled():
                    break
                resp = modifyUser(user)
                num += 1
                logMsg = ""
                if resp.status_code < 299:
                    logMsg = "Successfully modified user account: %s" % username
                    numCreated += 1
                else:
                    logMsg = (
                        "ERROR: failed to modified user account: %s\nReason: %s"
                        % (
                            username,
                            resp.text,
                        )
                    )
                if logMsg:
                    logs.append(logMsg)
                postEventToFrame(
                    wxThread.myEVT_UPDATE_GAUGE, int(num / len(self.users) * 100)
                )
                self.dialog.Update(
                    int(num / len(self.users) * 100),
                    "Successfully modified %s of %s users!"
                    % (numCreated, len(self.users)),
                )
                postEventToFrame(wxThread.myEVT_LOG, logMsg)
            return res

    @api_tool_decorator()
    def onCreate(self):
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
            self.button_6.Enable(False)
            self.button_7.Enable(False)
            num = 0
            numCreated = 0
            self.dialog = wx.ProgressDialog(
                "Creating Users",
                "Time remaining",
                100,
                style=wx.PD_CAN_ABORT
                | wx.PD_ELAPSED_TIME
                | wx.PD_AUTO_HIDE
                | wx.PD_ESTIMATED_TIME,
            )
            logs = []
            for user in self.users:
                username = (
                    user["username"]
                    if "username" in user.keys()
                    else (user["first_name"] + user["last_name"])
                )
                if self.dialog.WasCancelled():
                    break
                resp = createNewUser(user)
                num += 1
                logMsg = ""
                if resp.status_code < 299:
                    logMsg = "Successfully created user account: %s" % username
                    numCreated += 1
                else:
                    logMsg = "ERROR: failed to create user account: %s\nReason: %s" % (
                        username,
                        resp.text,
                    )
                if logMsg:
                    logs.append(logMsg)
                postEventToFrame(
                    wxThread.myEVT_UPDATE_GAUGE, int(num / len(self.users) * 100)
                )
                self.dialog.Update(
                    int(num / len(self.users) * 100),
                    "Successfully created %s of %s users!"
                    % (numCreated, len(self.users)),
                )
                postEventToFrame(wxThread.myEVT_LOG, logMsg)
            return logs

    def onDelete(self):
        if not self.grid_1.GetNumberRows() > 0:
            self.button_6.Enable(False)
            return
        res = displayMessageBox(
            (
                'You are about to delete the previewed Users on "%s", are you sure?'
                % Globals.frame.configMenuItem.GetItemLabelText(),
                wx.ICON_INFORMATION | wx.YES_NO,
            )
        )
        if res == wx.YES:
            self.button_6.Enable(False)
            self.button_7.Enable(False)
            num = 0
            numCreated = 0
            self.dialog = wx.ProgressDialog(
                "Deleting Users",
                "Time remaining",
                100,
                style=wx.PD_CAN_ABORT
                | wx.PD_ELAPSED_TIME
                | wx.PD_AUTO_HIDE
                | wx.PD_ESTIMATED_TIME,
            )
            logs = []
            for user in self.users:
                username = (
                    user["username"]
                    if "username" in user.keys()
                    else (user["first_name"] + user["last_name"])
                )
                if self.dialog.WasCancelled():
                    break
                resp = deleteUser(user)
                num += 1
                logMsg = ""
                if resp.status_code < 299:
                    logMsg = "Successfully deleted user account: %s" % username
                    numCreated += 1
                else:
                    logMsg = "ERROR: failed to deleted user account: %s\nReason: %s" % (
                        username,
                        resp.text,
                    )
                if logMsg:
                    logs.append(logMsg)
                postEventToFrame(
                    wxThread.myEVT_UPDATE_GAUGE, int(num / len(self.users) * 100)
                )
                self.dialog.Update(
                    int(num / len(self.users) * 100),
                    "Successfully deleted %s of %s users!"
                    % (numCreated, len(self.users)),
                )
                postEventToFrame(wxThread.myEVT_LOG, logMsg)
            return logs

    def tryToMakeActive(self):
        self.Raise()
        self.Iconize(False)
        style = self.GetWindowStyle()
        self.SetWindowStyle(style | wx.STAY_ON_TOP)
        self.SetFocus()
        self.SetWindowStyle(style)
