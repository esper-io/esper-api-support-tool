#!/usr/bin/env python

import Common.Globals as Globals
import Utility.EsperTemplateUtil as templateUtil
import wx
import json


class TemplateDialog(wx.Dialog):
    def __init__(self, configMenuOpt, parent=None, *args, **kwds):
        # begin wxGlade: MyDialog.__init__
        super(TemplateDialog, self).__init__(
            None,
            wx.ID_ANY,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.STAY_ON_TOP,
        )
        self.parent = parent
        self.sourceTemplate = []
        self.destTemplate = []
        self.configMenuOpt = configMenuOpt
        self.chosenTemplate = None

        choices = list(self.configMenuOpt.keys())
        choices.insert(0, "")

        size = (600, 500)
        self.SetSize(size)
        self.SetMinSize(size)
        self.panel_2 = wx.Panel(self, wx.ID_ANY)
        self.panel_5 = wx.Panel(self.panel_2, wx.ID_ANY)
        self.choice_1 = self.choice_1 = wx.Choice(
            self.panel_5, wx.ID_ANY, choices=choices, style=wx.CB_SORT
        )
        self.panel_6 = wx.Panel(self.panel_2, wx.ID_ANY)
        self.choice_2 = wx.Choice(
            self.panel_6, wx.ID_ANY, choices=choices, style=wx.CB_SORT
        )
        self.check_list_box_1 = wx.ListBox(
            self.panel_2, wx.ID_ANY, choices=[], style=wx.LB_NEEDED_SB | wx.LB_SINGLE
        )
        self.text_ctrl_1 = wx.TextCtrl(
            self.panel_2,
            wx.ID_ANY,
            "",
            style=wx.HSCROLL | wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP,
        )
        self.panel_4 = wx.Panel(self.panel_2, wx.ID_ANY)
        self.button_1 = wx.Button(self.panel_4, wx.ID_OK, "Clone")
        self.button_2 = wx.Button(self.panel_4, wx.ID_CANCEL, "Cancel")

        self.button_1.Bind(wx.EVT_BUTTON, self.OnClose)
        self.button_2.Bind(wx.EVT_BUTTON, self.OnClose)
        self.choice_1.Bind(wx.EVT_CHOICE, self.onChoice1Select)
        self.choice_2.Bind(wx.EVT_CHOICE, self.onChoice2Select)
        self.check_list_box_1.Bind(wx.EVT_LISTBOX, self.OnSelection)
        self.check_list_box_1.Bind(wx.EVT_LISTBOX_DCLICK, self.OnSelection)

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MyDialog.__set_properties
        self.SetTitle("Clone Template")
        self.SetSize((515, 315))
        self.choice_1.SetSelection(0)
        self.choice_2.SetSelection(0)
        self.button_1.Enable(False)
        self.button_2.SetFocus()
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MyDialog.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_2 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_3 = wx.GridSizer(1, 1, 0, 0)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_5 = wx.StaticBoxSizer(
            wx.StaticBox(self.panel_2, wx.ID_ANY, "Source Template"), wx.VERTICAL
        )
        grid_sizer_4 = wx.GridSizer(1, 2, 0, 0)
        grid_sizer_1 = wx.GridSizer(1, 2, 0, 0)
        sizer_4 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        label_1 = wx.StaticText(self.panel_5, wx.ID_ANY, "Source Endpoint")
        sizer_3.Add(label_1, 0, wx.ALL, 5)
        sizer_3.Add(self.choice_1, 0, wx.ALL | wx.EXPAND, 5)
        self.panel_5.SetSizer(sizer_3)
        grid_sizer_1.Add(self.panel_5, 1, wx.EXPAND, 0)
        label_2 = wx.StaticText(self.panel_6, wx.ID_ANY, "Destination Endpoint")
        sizer_4.Add(label_2, 0, wx.ALL, 5)
        sizer_4.Add(self.choice_2, 0, wx.ALL | wx.EXPAND, 5)
        self.panel_6.SetSizer(sizer_4)
        grid_sizer_1.Add(self.panel_6, 1, wx.EXPAND, 0)
        grid_sizer_2.Add(grid_sizer_1, 0, wx.EXPAND, 0)
        grid_sizer_4.Add(self.check_list_box_1, 0, wx.ALL | wx.EXPAND, 5)
        grid_sizer_4.Add(self.text_ctrl_1, 0, wx.ALL | wx.EXPAND, 5)
        sizer_5.Add(grid_sizer_4, 1, wx.EXPAND, 0)
        grid_sizer_2.Add(sizer_5, 1, wx.EXPAND, 0)
        sizer_2.Add(self.button_1, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
        sizer_2.Add(self.button_2, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
        self.panel_4.SetSizer(sizer_2)
        grid_sizer_3.Add(self.panel_4, 1, wx.ALIGN_RIGHT | wx.EXPAND, 0)
        grid_sizer_2.Add(grid_sizer_3, 0, wx.EXPAND, 0)
        self.panel_2.SetSizer(grid_sizer_2)
        sizer_1.Add(self.panel_2, 1, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(sizer_1)
        self.Layout()
        self.Centre()

    def getInputSelections(self):
        return (
            self.configMenuOpt[self.choice_1.GetString(self.choice_1.GetSelection())],
            self.configMenuOpt[self.choice_2.GetString(self.choice_2.GetSelection())],
            self.check_list_box_1.GetString(self.check_list_box_1.GetSelection()),
        )

    def OnClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        else:
            self.Close()
        self.Destroy()

    def OnSelection(self, event):
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)
        selection = event.GetSelection()
        name = self.check_list_box_1.GetString(selection)
        template = list(filter(lambda x: x["name"] == name, self.sourceTemplate))
        if template:
            self.chosenTemplate = self.getTemplate(template[0])
            self.text_ctrl_1.AppendText(json.dumps(self.chosenTemplate, indent=2))
            self.text_ctrl_1.ShowPosition(0)

        if (
            self.choice_1.GetString(self.choice_1.GetSelection())
            != self.choice_2.GetString(self.choice_2.GetSelection())
            and self.choice_1.GetString(self.choice_1.GetSelection())
            and self.choice_2.GetString(self.choice_2.GetSelection())
            and self.check_list_box_1.GetSelection()
        ):
            self.button_1.Enable(True)
        else:
            self.button_1.Enable(False)
        myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
        self.SetCursor(myCursor)

    def onChoice1Select(self, event):
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)
        self.sourceTemplate = []
        self.check_list_box_1.Clear()
        if event.String:
            self.sourceTemplate = self.getTemplates(self.configMenuOpt[event.String])
            for template in self.sourceTemplate:
                self.check_list_box_1.Append(template["name"])

        if (
            self.choice_1.GetString(self.choice_1.GetSelection())
            == self.choice_2.GetString(self.choice_2.GetSelection())
            or not self.choice_1.GetString(self.choice_1.GetSelection())
            or not self.choice_2.GetString(self.choice_2.GetSelection())
            or not self.check_list_box_1.GetSelection()
        ):
            self.button_1.Enable(False)
        else:
            self.button_1.Enable(True)
        myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
        self.SetCursor(myCursor)

    def onChoice2Select(self, event):
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)
        self.destTemplate = []
        if event.String:
            self.destTemplate = self.getTemplates(self.configMenuOpt[event.String])
        if (
            self.choice_1.GetString(self.choice_1.GetSelection())
            == self.choice_2.GetString(self.choice_2.GetSelection())
            or not self.choice_1.GetString(self.choice_1.GetSelection())
            or not self.choice_2.GetString(self.choice_2.GetSelection())
            or self.check_list_box_1.GetSelection()
        ):
            self.button_1.Enable(False)
        else:
            self.button_1.Enable(True)
        myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
        self.SetCursor(myCursor)

    def getTemplates(self, dataSrc):
        util = templateUtil.EsperTemplateUtil(dataSrc, None, None)
        tempList = util.getTemplates(
            dataSrc["apiHost"], dataSrc["apiKey"], dataSrc["enterprise"]
        )
        return tempList["results"]

    def getTemplate(self, template):
        util = templateUtil.EsperTemplateUtil()
        dataSrc = self.configMenuOpt[
            self.choice_1.GetString(self.choice_1.GetSelection())
        ]
        return util.getTemplate(
            dataSrc["apiHost"], dataSrc["apiKey"], dataSrc["enterprise"], template["id"]
        )
