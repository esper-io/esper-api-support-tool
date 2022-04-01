#!/usr/bin/env python3

import json
import wx
import wx.html as wxHtml

from Common.decorator import api_tool_decorator
from GUI.PromptingComboBox import PromptingComboBox
from Utility.API.BlueprintUtility import getAllBlueprintsFromHost, getGroupBlueprintDetail
from Utility.API.GroupUtility import getDeviceGroupsForHost
from Utility.Resource import getEsperConfig, openWebLinkInBrowser


class BlueprintsDialog(wx.Dialog):
    def __init__(self, configMenuOpt, *args, **kwds):
        sizeTuple = (600, 400)
        super(BlueprintsDialog, self).__init__(
            None,
            wx.ID_ANY,
            size=sizeTuple,
            style=wx.DEFAULT_DIALOG_STYLE | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX | wx.RESIZE_BORDER | wx.STAY_ON_TOP,
        )
        self.SetSize(sizeTuple)
        self.SetMinSize(sizeTuple)
        self.SetTitle("Clone Blueprint")

        self.configMenuOpt = configMenuOpt
        self.blueprints = None
        choices = list(self.configMenuOpt.keys())

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_1, 1, wx.ALL | wx.EXPAND, 5)

        grid_sizer_2 = wx.FlexGridSizer(4, 1, 0, 0)

        sizer_5 = wx.GridSizer(1, 2, 0, 0)
        grid_sizer_2.Add(sizer_5, 1, wx.BOTTOM | wx.EXPAND, 5)

        label_3 = wx.StaticText(self.panel_1, wx.ID_ANY, "Source Endpoint:")
        label_3.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        sizer_5.Add(label_3, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        # self.combo_box_3 = wx.ComboBox(self.panel_1, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY | wx.CB_SORT)
        self.combo_box_3 = PromptingComboBox(self.panel_1, "", choices=choices, style=wx.CB_DROPDOWN | wx.CB_SORT)
        sizer_5.Add(self.combo_box_3, 0, wx.EXPAND, 0)

        grid_sizer_1 = wx.FlexGridSizer(2, 1, 0, 0)
        grid_sizer_2.Add(grid_sizer_1, 1, wx.EXPAND, 0)

        sizer_6 = wx.GridSizer(1, 2, 0, 0)
        grid_sizer_1.Add(sizer_6, 1, wx.BOTTOM | wx.EXPAND, 5)

        label_5 = wx.StaticText(self.panel_1, wx.ID_ANY, "Source Blueprint:")
        label_5.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        sizer_6.Add(label_5, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        # self.combo_box_4 = wx.ComboBox(self.panel_1, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY | wx.CB_SORT)
        self.combo_box_4 = PromptingComboBox(self.panel_1, "", choices=[], style=wx.CB_DROPDOWN | wx.CB_SORT)
        sizer_6.Add(self.combo_box_4, 0, wx.EXPAND, 0)

        grid_sizer_3 = wx.FlexGridSizer(2, 1, 0, 0)
        grid_sizer_1.Add(grid_sizer_3, 1, wx.BOTTOM | wx.EXPAND, 5)

        label_4 = wx.StaticText(self.panel_1, wx.ID_ANY, "Blueprint Preview:")
        label_4.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        grid_sizer_3.Add(label_4, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.text_ctrl_1 = wx.TextCtrl(self.panel_1, wx.ID_ANY, "", style=wx.HSCROLL | wx.TE_AUTO_URL | wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP)
        grid_sizer_3.Add(self.text_ctrl_1, 0, wx.ALL | wx.EXPAND, 5)

        sizer_3 = wx.GridSizer(1, 2, 0, 0)
        grid_sizer_2.Add(sizer_3, 1, wx.BOTTOM | wx.EXPAND, 5)

        label_1 = wx.StaticText(self.panel_1, wx.ID_ANY, "Destination Endpoint:")
        label_1.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        sizer_3.Add(label_1, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        # self.combo_box_1 = wx.ComboBox(self.panel_1, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY | wx.CB_SORT)
        self.combo_box_1 = PromptingComboBox(self.panel_1, "", choices=choices, style=wx.CB_DROPDOWN | wx.CB_SORT)
        sizer_3.Add(self.combo_box_1, 0, wx.EXPAND, 0)

        sizer_4 = wx.GridSizer(1, 2, 0, 0)
        grid_sizer_2.Add(sizer_4, 1, wx.EXPAND, 0)

        label_2 = wx.StaticText(self.panel_1, wx.ID_ANY, "Destination Group:")
        label_2.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        sizer_4.Add(label_2, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        # self.combo_box_2 = wx.ComboBox(self.panel_1, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY | wx.CB_SORT)
        self.combo_box_2 = PromptingComboBox(self.panel_1, "", choices=[], style=wx.CB_DROPDOWN | wx.CB_SORT)
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
        self.text_ctrl_1.Bind(wxHtml.EVT_HTML_LINK_CLICKED, openWebLinkInBrowser)
        self.button_OK.Bind(wx.EVT_BUTTON, self.OnClose)
        self.button_CANCEL.Bind(wx.EVT_BUTTON, self.OnClose)

        self.combo_box_1.Bind(wx.EVT_COMBOBOX, self.loadGroups)
        self.combo_box_2.Bind(wx.EVT_COMBOBOX, self.checkInputs)
        self.combo_box_3.Bind(wx.EVT_COMBOBOX, self.loadBlueprints)
        self.combo_box_4.Bind(wx.EVT_COMBOBOX, self.loadBlueprintPreview)

    def changeCursorToWait(self):
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)

    def changeCursorToDefault(self):
        myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
        self.SetCursor(myCursor)

    @api_tool_decorator()
    def loadGroups(self, event):
        print("Loading Dest Groups")
        config = self.configMenuOpt[event.String]
        destinationGroups = getDeviceGroupsForHost(
            getEsperConfig(config["apiHost"], config["apiKey"]), config["enterprise"]
        )
        for group in destinationGroups.results:
            self.combo_box_2.Append(group.path, group.id)
        self.checkInputs()

    @api_tool_decorator()
    def loadBlueprints(self, event):
        self.changeCursorToWait()
        print("Loading Src BP")
        config = self.configMenuOpt[event.String]
        bps = getAllBlueprintsFromHost(config["apiHost"], config["apiKey"], config["enterprise"])
        if bps:
            self.blueprints = bps.json()
            for blueprint in self.blueprints["results"]:
                if blueprint["name"]:
                    self.combo_box_4.Append(blueprint["name"], blueprint["id"])
                else:
                    self.combo_box_4.Append("Blueprint %s" % blueprint["id"], blueprint["id"])
            self.checkInputs()

    @api_tool_decorator()
    def loadBlueprintPreview(self, event):
        print("Loading Src BP Preview")
        match = list(filter(
            lambda x: x["id"] == event.ClientData,
            self.blueprints["results"],
        ))
        if match:
            match = match[0]
        config = self.configMenuOpt[self.combo_box_3.GetString(self.combo_box_3.GetSelection())]
        if match["group"]:
            revision = getGroupBlueprintDetail(config["apiHost"], config["apiKey"], config["enterprise"], match["group"], event.ClientData)
            formattedRes = ""
            try:
                formattedRes = json.dumps(revision.json(), indent=2).replace("\\n", "\n")
            except:
                formattedRes = json.dumps(str(revision.json()), indent=2).replace("\\n", "\n")
            self.text_ctrl_1.SetValue(formattedRes)
        else:
            self.text_ctrl_1.SetValue("No preview available")
        self.checkInputs()

    @api_tool_decorator()
    def checkInputs(self, event=None):
        if (
            self.combo_box_1.GetValue()
            and self.combo_box_2.GetValue()
            and self.combo_box_3.GetValue()
            and self.combo_box_4.GetValue()
            and self.combo_box_1.GetValue() != self.combo_box_3.GetValue()
        ):
            self.button_OK.Enable(True)
        else:
            self.button_OK.Enable(False)
        self.changeCursorToDefault()

    @api_tool_decorator()
    def OnClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        elif self.IsShown():
            self.Close()
