#!/usr/bin/env python3

import json
import platform
import threading

import wx
import wx.html as wxHtml

import Common.Globals as Globals
import Utility.API.EsperTemplateUtil as templateUtil
from Common.decorator import api_tool_decorator
from Utility.API.BlueprintUtility import checkFeatureFlags
from Utility.API.GroupUtility import getDeviceGroupsForHost
from Utility.Resource import (
    determineDoHereorMainThread,
    getEsperConfig,
    openWebLinkInBrowser,
)


class BlueprintsConvertDialog(wx.Dialog):
    def __init__(self, configMenuOpt, parent=None, *args, **kwds):
        sizeTuple = (600, 400)
        super(BlueprintsConvertDialog, self).__init__(
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
        self.SetTitle("Convert Template to Blueprint")

        self.SetThemeEnabled(False)

        self.configMenuOpt = configMenuOpt
        self.blueprints = None
        self.toConfig = None
        self.fromConfig = None
        self.chosenTemplate = None
        self.group = None
        self.sourceTemplate = []
        templateSrc = self.configMenuOpt.keys()
        blueprintDest = self.configMenuOpt.keys()

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_1, 1, wx.ALL | wx.EXPAND, 5)

        grid_sizer_2 = wx.FlexGridSizer(4, 1, 0, 0)

        sizer_5 = wx.GridSizer(1, 2, 0, 0)
        grid_sizer_2.Add(sizer_5, 1, wx.BOTTOM | wx.EXPAND, 5)

        label_3 = wx.StaticText(self.panel_1, wx.ID_ANY, "Source Tenant:")
        label_3.SetFont(
            wx.Font(
                12,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        sizer_5.Add(label_3, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.combo_box_3 = wx.ComboBox(
            self.panel_1,
            value="",
            choices=templateSrc,
            style=wx.CB_DROPDOWN | wx.CB_SORT | wx.CB_READONLY,
        )
        sizer_5.Add(self.combo_box_3, 0, wx.EXPAND, 0)

        grid_sizer_1 = wx.FlexGridSizer(2, 1, 0, 0)
        grid_sizer_2.Add(grid_sizer_1, 1, wx.EXPAND, 0)

        sizer_6 = wx.GridSizer(1, 2, 0, 0)
        grid_sizer_1.Add(sizer_6, 1, wx.BOTTOM | wx.EXPAND, 5)

        label_5 = wx.StaticText(self.panel_1, wx.ID_ANY, "Source Template:")
        label_5.SetFont(
            wx.Font(
                12,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
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

        label_4 = wx.StaticText(self.panel_1, wx.ID_ANY, "Template Preview:")
        label_4.SetFont(
            wx.Font(
                12,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
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
        label_1.SetFont(
            wx.Font(
                12,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
        sizer_3.Add(label_1, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.combo_box_1 = wx.ComboBox(
            self.panel_1,
            value="",
            choices=blueprintDest,
            style=wx.CB_DROPDOWN | wx.CB_SORT | wx.CB_READONLY,
        )
        sizer_3.Add(self.combo_box_1, 0, wx.EXPAND, 0)

        sizer_4 = wx.GridSizer(1, 2, 0, 0)
        grid_sizer_2.Add(sizer_4, 1, wx.EXPAND, 0)

        label_2 = wx.StaticText(self.panel_1, wx.ID_ANY, "Destination Group:")
        label_2.SetFont(
            wx.Font(
                12,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
                0,
                "",
            )
        )
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

        self.Layout()

        # Bind Events
        self.text_ctrl_1.Bind(
            wxHtml.EVT_HTML_LINK_CLICKED, openWebLinkInBrowser
        )
        self.button_OK.Bind(wx.EVT_BUTTON, self.OnClose)
        self.button_CANCEL.Bind(wx.EVT_BUTTON, self.OnClose)

        self.combo_box_1.Bind(wx.EVT_COMBOBOX, self.loadGroups)
        self.combo_box_2.Bind(wx.EVT_COMBOBOX, self.checkInputs)
        self.combo_box_3.Bind(wx.EVT_COMBOBOX, self.loadTemplates)
        self.combo_box_4.Bind(wx.EVT_COMBOBOX, self.loadTemplatePreview)

        self.changeCursorToWait()
        self.combo_box_3.Enable(False)
        self.combo_box_1.Enable(False)
        Globals.THREAD_POOL.enqueue(self.getBlueprintEnabledEndpoints)

    def getBlueprintEnabledEndpoints(self):
        if (
            platform.system() == "Darwin"
            and "main" not in threading.current_thread().name.lower()
        ):
            determineDoHereorMainThread(self.getBlueprintEnabledEndpoints)
            return
        self.combo_box_3.Clear()
        self.combo_box_1.Clear()
        for config in self.configMenuOpt.values():
            if "isBlueprintsEnabled" not in config:
                Globals.THREAD_POOL.enqueue(checkFeatureFlags, config)
        Globals.THREAD_POOL.join(tolerance=1)
        enabled = disabled = self.configMenuOpt.keys()
        for choice in enabled:
            self.combo_box_1.Append(choice)
        for choice in disabled:
            self.combo_box_3.Append(choice)
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
    def checkInputs(self, event=None):
        if (
            self.combo_box_1.GetValue()
            and self.combo_box_2.GetValue()
            and self.combo_box_3.GetValue()
            and self.combo_box_4.GetValue()
            and self.chosenTemplate
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

    def getTemplate(self):
        if self.chosenTemplate and hasattr(self.chosenTemplate, "json"):
            return self.chosenTemplate.json()
        elif self.chosenTemplate:
            return self.chosenTemplate

    def getDestinationGroup(self):
        return self.group

    def loadTemplatePreview(self, event):
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)
        selection = event.GetSelection()
        name = self.combo_box_4.GetString(selection)
        template = list(
            filter(lambda x: x["name"] == name, self.sourceTemplate)
        )

        if type(template) == list:
            template = template[0]
        if template:
            self.chosenTemplate = self.getTemplateDetails(template)
            self.text_ctrl_1.Clear()
            if self.chosenTemplate:
                self.text_ctrl_1.AppendText(
                    json.dumps(self.chosenTemplate, indent=2)
                )
            else:
                self.text_ctrl_1.AppendText(
                    "An ERROR occured when fetching the template, please try again."
                )
            self.text_ctrl_1.ShowPosition(0)
        self.checkInputs()

    def loadTemplates(self, event):
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)
        self.sourceTemplate = []
        self.combo_box_4.Clear()
        Globals.THREAD_POOL.enqueue(
            self.populateSourceTempaltes,
            event.String if event.String else False,
        )

    @api_tool_decorator()
    def populateSourceTempaltes(self, srcName):
        if (
            platform.system() == "Darwin"
            and "main" not in threading.current_thread().name.lower()
        ):
            determineDoHereorMainThread(self.populateSourceTempaltes, srcName)
            return
        if srcName:
            self.sourceTemplate = self.getTemplates(self.configMenuOpt[srcName])
            if self.sourceTemplate:
                for template in self.sourceTemplate:
                    self.combo_box_4.Append(template["name"])
                self.combo_box_4.Enable(True)
        self.checkInputs()

    @api_tool_decorator()
    def getTemplates(self, dataSrc):
        util = templateUtil.EsperTemplateUtil(dataSrc, None)
        tempList = util.getTemplates(
            dataSrc["apiHost"], dataSrc["apiKey"], dataSrc["enterprise"]
        )
        return (
            tempList["results"] if tempList and "results" in tempList else None
        )

    @api_tool_decorator()
    def getTemplateDetails(self, template):
        util = templateUtil.EsperTemplateUtil()
        dataSrc = self.configMenuOpt[
            self.combo_box_3.GetString(self.combo_box_3.GetSelection())
        ]
        return util.getTemplate(
            dataSrc["apiHost"],
            dataSrc["apiKey"],
            dataSrc["enterprise"],
            template["id"],
        )
