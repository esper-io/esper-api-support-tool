#!/usr/bin/env python3

import json
import platform
import threading

import wx
import wx.html as wxHtml

import Common.Globals as Globals
from Common.decorator import api_tool_decorator
from Utility.API.BlueprintUtility import (checkFeatureFlags,
                                          getAllBlueprintsFromHost,
                                          getGroupBlueprintDetailForHost)
from Utility.API.GroupUtility import getDeviceGroupsForHost
from Utility.Resource import (determineDoHereorMainThread, getEsperConfig,
                              openWebLinkInBrowser, setElmTheme)


class BlueprintsDialog(wx.Dialog):
    def __init__(self, configMenuOpt, parent=None, *args, **kwds):
        sizeTuple = (600, 400)
        super(BlueprintsDialog, self).__init__(
            parent,
            wx.ID_ANY,
            size=sizeTuple,
            style=wx.DEFAULT_DIALOG_STYLE
            | wx.MAXIMIZE_BOX
            | wx.MINIMIZE_BOX
            | wx.RESIZE_BORDER,
        )
        self.parent = parent
        self.SetSize(sizeTuple)
        self.SetMinSize(sizeTuple)
        self.SetTitle("Clone Blueprint")
        self.SetThemeEnabled(False)

        self.configMenuOpt = configMenuOpt
        self.blueprints = None
        self.toConfig = None
        self.fromConfig = None
        self.blueprint = None
        self.group = None
        choices = self.configMenuOpt.keys()

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_1, 1, wx.ALL | wx.EXPAND, 5)

        grid_sizer_2 = wx.FlexGridSizer(4, 1, 0, 0)

        sizer_5 = wx.GridSizer(1, 2, 0, 0)
        grid_sizer_2.Add(sizer_5, 1, wx.BOTTOM | wx.EXPAND, 5)

        label_3 = wx.StaticText(self.panel_1, wx.ID_ANY, "Source Tenant:")
        sizer_5.Add(label_3, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.combo_box_3 = wx.ComboBox(
            self.panel_1,
            value="",
            choices=list(choices),
            style=wx.CB_DROPDOWN | wx.CB_SORT | wx.CB_READONLY,
        )
        sizer_5.Add(self.combo_box_3, 0, wx.EXPAND, 0)

        grid_sizer_1 = wx.FlexGridSizer(2, 1, 0, 0)
        grid_sizer_2.Add(grid_sizer_1, 1, wx.EXPAND, 0)

        sizer_6 = wx.GridSizer(1, 2, 0, 0)
        grid_sizer_1.Add(sizer_6, 1, wx.BOTTOM | wx.EXPAND, 5)

        label_5 = wx.StaticText(self.panel_1, wx.ID_ANY, "Source Blueprint:")
        sizer_6.Add(label_5, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.combo_box_4 = wx.ComboBox(
            self.panel_1,
            value="",
            choices=[],
            style=wx.CB_DROPDOWN | wx.CB_SORT | wx.CB_READONLY,
        )
        self.combo_box_4.Enable(False)
        sizer_6.Add(self.combo_box_4, 0, wx.EXPAND, 0)

        grid_sizer_3 = wx.FlexGridSizer(2, 1, 0, 0)
        grid_sizer_1.Add(grid_sizer_3, 1, wx.BOTTOM | wx.EXPAND, 5)

        label_4 = wx.StaticText(self.panel_1, wx.ID_ANY, "Blueprint Preview:")
        grid_sizer_3.Add(label_4, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.text_ctrl_1 = wx.TextCtrl(
            self.panel_1,
            wx.ID_ANY,
            "",
            style=wx.HSCROLL
            | wx.TE_AUTO_URL
            | wx.TE_MULTILINE
            | wx.TE_READONLY
            | wx.TE_WORDWRAP,
        )
        grid_sizer_3.Add(self.text_ctrl_1, 0, wx.ALL | wx.EXPAND, 5)

        sizer_3 = wx.GridSizer(1, 2, 0, 0)
        grid_sizer_2.Add(sizer_3, 1, wx.BOTTOM | wx.EXPAND, 5)

        label_1 = wx.StaticText(self.panel_1, wx.ID_ANY, "Destination Tenant:")
        sizer_3.Add(label_1, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.combo_box_1 = wx.ComboBox(
            self.panel_1,
            value="",
            choices=list(choices),
            style=wx.CB_DROPDOWN | wx.CB_SORT | wx.CB_READONLY,
        )
        sizer_3.Add(self.combo_box_1, 0, wx.EXPAND, 0)

        sizer_4 = wx.GridSizer(1, 2, 0, 0)
        grid_sizer_2.Add(sizer_4, 1, wx.EXPAND, 0)

        label_2 = wx.StaticText(self.panel_1, wx.ID_ANY, "Destination Group:")
        sizer_4.Add(label_2, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.combo_box_2 = wx.ComboBox(
            self.panel_1,
            value="",
            choices=[],
            style=wx.CB_DROPDOWN | wx.CB_SORT | wx.CB_READONLY,
        )
        self.combo_box_2.Enable(False)
        sizer_4.Add(self.combo_box_2, 0, wx.EXPAND, 0)

        sizer_2 = wx.StdDialogButtonSizer()
        sizer_1.Add(sizer_2, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

        self.button_OK = wx.Button(self, wx.ID_OK, "")
        self.button_OK.SetDefault()
        self.button_OK.Enable(False)
        sizer_2.AddButton(self.button_OK)

        self.button_CANCEL = wx.Button(self, wx.ID_CANCEL, "")
        sizer_2.AddButton(self.button_CANCEL)

        sizer_2.Realize()

        grid_sizer_3.AddGrowableRow(1)
        grid_sizer_3.AddGrowableCol(0)

        grid_sizer_1.AddGrowableRow(1)
        grid_sizer_1.AddGrowableCol(0)

        grid_sizer_2.AddGrowableRow(1)
        grid_sizer_2.AddGrowableCol(0)
        self.panel_1.SetSizer(grid_sizer_2)

        self.SetSizer(sizer_1)

        self.SetAffirmativeId(self.button_OK.GetId())
        self.SetEscapeId(self.button_CANCEL.GetId())

        self.applyFontSize()
        setElmTheme(self)
        self.Layout()

        # Bind Events
        self.text_ctrl_1.Bind(
            wxHtml.EVT_HTML_LINK_CLICKED, openWebLinkInBrowser
        )
        self.button_OK.Bind(wx.EVT_BUTTON, self.OnClose)
        self.button_CANCEL.Bind(wx.EVT_BUTTON, self.OnClose)

        self.combo_box_1.Bind(wx.EVT_COMBOBOX, self.loadGroups)
        self.combo_box_2.Bind(wx.EVT_COMBOBOX, self.checkInputs)
        self.combo_box_3.Bind(wx.EVT_COMBOBOX, self.loadBlueprints)
        self.combo_box_4.Bind(wx.EVT_COMBOBOX, self.loadBlueprintPreview)

        self.changeCursorToWait()
        self.combo_box_3.Enable(False)
        self.combo_box_1.Enable(False)
        Globals.THREAD_POOL.enqueue(self.getBlueprintEnabledEndpoints)

    def getBlueprintEnabledEndpoints(self):
        if (
            platform.system() == "Darwin"
            and "main" not in threading.current_thread().name.lower()
        ):
            determineDoHereorMainThread(
                self.getBlueprintEnabledEndpoints,
            )
            return
        self.combo_box_3.Clear()
        self.combo_box_1.Clear()
        Globals.THREAD_POOL.join(tolerance=1)
        choices = self.configMenuOpt.keys()
        for choice in choices:
            self.combo_box_3.Append(choice)
            self.combo_box_1.Append(choice)
        self.combo_box_3.Enable(True)
        self.combo_box_1.Enable(True)
        self.combo_box_3.SetSelection(-1)
        self.combo_box_1.SetSelection(-1)
        self.checkInputs()

    def changeCursorToWait(self):
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)

    def changeCursorToDefault(self):
        myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
        self.SetCursor(myCursor)

    @api_tool_decorator()
    def loadGroups(self, event):
        self.changeCursorToWait()
        self.combo_box_2.Enable(False)
        self.combo_box_2.Clear()
        config = self.configMenuOpt[event.String]
        self.toConfig = config
        Globals.THREAD_POOL.enqueue(self.loadGroupHelper, config)

    @api_tool_decorator()
    def loadGroupHelper(self, config):
        if (
            platform.system() == "Darwin"
            and "main" not in threading.current_thread().name.lower()
        ):
            determineDoHereorMainThread(self.loadGroupHelper, config)
            return
        destinationGroups = getDeviceGroupsForHost(
            getEsperConfig(config["apiHost"], config["apiKey"]),
            config["enterprise"],
            tolerance=1,
        )
        for group in destinationGroups.results:
            self.combo_box_2.Append(group.path, group.id)
        self.combo_box_2.Enable(True)
        self.checkInputs()

    @api_tool_decorator()
    def loadBlueprints(self, event):
        self.changeCursorToWait()
        self.combo_box_4.Enable(False)
        self.combo_box_4.Clear()
        config = self.configMenuOpt[event.String]
        self.fromConfig = config
        Globals.THREAD_POOL.enqueue(self.loadBlueprintsHelper, config)

    @api_tool_decorator()
    def loadBlueprintsHelper(self, config):
        bps = getAllBlueprintsFromHost(
            config["apiHost"], config["apiKey"], config["enterprise"]
        )
        if bps:
            self.blueprints = bps.json()
            for blueprint in self.blueprints["results"]:
                if blueprint["name"]:
                    self.combo_box_4.Append(blueprint["name"], blueprint["id"])
                else:
                    self.combo_box_4.Append(
                        "Blueprint %s" % blueprint["id"], blueprint["id"]
                    )
            self.checkInputs()
        self.combo_box_4.Enable(True)

    @api_tool_decorator()
    def loadBlueprintPreview(self, event):
        self.changeCursorToWait()
        match = list(
            filter(
                lambda x: x["id"] == event.ClientData,
                self.blueprints["results"],
            )
        )
        if match:
            match = match[0]
        config = self.configMenuOpt[
            self.combo_box_3.GetString(self.combo_box_3.GetSelection())
        ]
        if match["group"]:
            Globals.THREAD_POOL.enqueue(
                self.loadBlueprintHelper, event, match, config
            )
        else:
            self.text_ctrl_1.SetValue("No preview available")
        self.checkInputs()

    @api_tool_decorator()
    def loadBlueprintHelper(self, event, match, config):
        if (
            platform.system() == "Darwin"
            and "main" not in threading.current_thread().name.lower()
        ):
            determineDoHereorMainThread(
                self.loadBlueprintHelper, event, match, config
            )
            return
        revision = getGroupBlueprintDetailForHost(
            config["apiHost"],
            config["apiKey"],
            config["enterprise"],
            match["group"],
            event.ClientData,
        )
        self.blueprint = revision
        formattedRes = ""
        try:
            formattedRes = json.dumps(revision.json(), indent=2).replace(
                "\\n", "\n"
            )
        except:
            formattedRes = json.dumps(str(revision.json()), indent=2).replace(
                "\\n", "\n"
            )
        self.text_ctrl_1.SetValue(formattedRes)
        self.checkInputs()

    @api_tool_decorator()
    def checkInputs(self, event=None):
        if (
            self.combo_box_1.GetValue()
            and self.combo_box_2.GetValue()
            and self.combo_box_3.GetValue()
            and self.combo_box_4.GetValue()
            and self.combo_box_1.GetValue() != self.combo_box_3.GetValue()
            and self.blueprint
        ):
            self.button_OK.Enable(True)
        else:
            self.button_OK.Enable(False)
        if self.combo_box_2.GetSelection() > -1:
            self.group = self.combo_box_2.GetClientData(
                self.combo_box_2.GetSelection()
            )
        self.changeCursorToDefault()

    @api_tool_decorator()
    def OnClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        elif self.IsShown():
            self.Close()

    def getBlueprint(self):
        if self.blueprint:
            return self.blueprint.json()

    def getDestinationGroup(self):
        return self.group

    def applyFontSize(self):
        normalFont = wx.Font(
            Globals.FONT_SIZE,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL,
            0,
            "Normal",
        )
        normalBoldFont = wx.Font(
            Globals.FONT_SIZE,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD,
            0,
            "NormalBold",
        )

        self.applyFontHelper(self, normalFont, normalBoldFont)

    def applyFontHelper(self, elm, font, normalBoldFont):
        childen = elm.GetChildren()
        for child in childen:
            if hasattr(child, "SetFont"):
                if isinstance(child, wx.StaticText):
                    child.SetFont(normalBoldFont)
                else:
                    child.SetFont(font)
            self.applyFontHelper(child, font, normalBoldFont)
