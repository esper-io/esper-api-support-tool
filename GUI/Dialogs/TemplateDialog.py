#!/usr/bin/env python

from Utility.Resource import openWebLinkInBrowser
from Common.decorator import api_tool_decorator
import Utility.EsperTemplateUtil as templateUtil
import Utility.wxThread as wxThread
import wx
import wx.html as wxHtml
import json


class TemplateDialog(wx.Dialog):
    def __init__(self, configMenuOpt, parent=None):
        # begin wxGlade: MyDialog.__init__
        super(TemplateDialog, self).__init__(
            None,
            wx.ID_ANY,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.parent = parent
        self.sourceTemplate = []
        self.destTemplate = []
        self.configMenuOpt = configMenuOpt
        self.chosenTemplate = None
        self.choice1thread = None
        self.choice2thread = None

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
            self.panel_2,
            wx.ID_ANY,
            choices=[],
            style=wx.LB_NEEDED_SB | wx.LB_SINGLE | wx.LB_SORT,
        )
        self.text_ctrl_1 = wx.TextCtrl(
            self.panel_2,
            wx.ID_ANY,
            "",
            style=wx.HSCROLL
            | wx.TE_MULTILINE
            | wx.TE_READONLY
            | wx.TE_WORDWRAP
            | wx.TE_AUTO_URL,
        )
        self.text_ctrl_1.Bind(wxHtml.EVT_HTML_LINK_CLICKED, openWebLinkInBrowser)
        self.panel_4 = wx.Panel(self.panel_2, wx.ID_ANY)
        self.button_1 = wx.Button(self.panel_4, wx.ID_OK, "Clone")
        self.button_2 = wx.Button(self.panel_4, wx.ID_CANCEL, "Cancel")

        self.button_1.Bind(wx.EVT_BUTTON, self.OnClose)
        self.button_2.Bind(wx.EVT_BUTTON, self.OnClose)
        self.choice_1.Bind(wx.EVT_CHOICE, self.onChoice1Select)
        self.choice_2.Bind(wx.EVT_CHOICE, self.onChoice2Select)
        if hasattr(self.parent, "WINDOWS") and self.parent.WINDOWS:
            self.check_list_box_1.Bind(wx.EVT_LISTBOX, self.OnSelection)
            self.check_list_box_1.Bind(wx.EVT_LISTBOX_DCLICK, self.OnSelection)

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    @api_tool_decorator
    def __set_properties(self):
        # begin wxGlade: MyDialog.__set_properties
        self.SetTitle("Clone Template")
        self.SetSize((515, 315))
        self.choice_1.SetSelection(0)
        self.choice_2.SetSelection(0)
        self.button_1.Enable(False)
        self.button_2.SetFocus()
        # end wxGlade

    @api_tool_decorator
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

    @api_tool_decorator
    def getInputSelections(self):
        return (
            self.configMenuOpt[self.choice_2.GetString(self.choice_2.GetSelection())],
            self.check_list_box_1.GetString(self.check_list_box_1.GetSelection()),
        )

    @api_tool_decorator
    def OnClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        elif self.IsShown():
            self.Close()
        # self.DestroyLater()

    @api_tool_decorator
    def populateTemplatePreview(self, template):
        if type(template) == list:
            template = template[0]
        if template:
            self.chosenTemplate = self.getTemplate(template)
            self.text_ctrl_1.Clear()
            if self.chosenTemplate:
                self.text_ctrl_1.AppendText(json.dumps(self.chosenTemplate, indent=2))
            else:
                self.text_ctrl_1.AppendText(
                    "An ERROR occured when fetching the template, please try again."
                )
            self.text_ctrl_1.ShowPosition(0)
        self.checkInputValues()

    @api_tool_decorator
    def OnSelection(self, event):
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)
        selection = event.GetSelection()
        name = self.check_list_box_1.GetString(selection)
        template = list(filter(lambda x: x["name"] == name, self.sourceTemplate))
        self.populateTemplatePreview(template)

    @api_tool_decorator
    def populateSourceTempaltes(self, srcName):
        if srcName:
            self.sourceTemplate = self.getTemplates(self.configMenuOpt[srcName])
            for template in self.sourceTemplate:
                self.check_list_box_1.Append(template["name"])
        self.checkInputValues()

    @api_tool_decorator
    def onChoice1Select(self, event):
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)
        self.sourceTemplate = []
        self.check_list_box_1.Clear()
        self.choice1thread = wxThread.GUIThread(
            self,
            self.populateSourceTempaltes,
            (event.String if event.String else False),
            name="populateSourceTempaltes",
        )
        self.choice1thread.start()

    @api_tool_decorator
    def fetchDestTempaltes(self, destName):
        if destName:
            self.destTemplate = self.getTemplates(self.configMenuOpt[destName])
        self.checkInputValues()

    @api_tool_decorator
    def onChoice2Select(self, event):
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)
        self.destTemplate = []
        self.choice2thread = wxThread.GUIThread(
            self,
            self.fetchDestTempaltes,
            (event.String if event.String else False),
            name="fetchDestTempaltes",
        )
        self.choice2thread.start()

    @api_tool_decorator
    def getTemplates(self, dataSrc):
        util = templateUtil.EsperTemplateUtil(dataSrc, None)
        tempList = util.getTemplates(
            dataSrc["apiHost"], dataSrc["apiKey"], dataSrc["enterprise"]
        )
        return tempList["results"]

    @api_tool_decorator
    def getTemplate(self, template):
        util = templateUtil.EsperTemplateUtil()
        dataSrc = self.configMenuOpt[
            self.choice_1.GetString(self.choice_1.GetSelection())
        ]
        return util.getTemplate(
            dataSrc["apiHost"], dataSrc["apiKey"], dataSrc["enterprise"], template["id"]
        )

    @api_tool_decorator
    def checkInputValues(self):
        if (
            self.choice_1.GetString(self.choice_1.GetSelection())
            == self.choice_2.GetString(self.choice_2.GetSelection())
            or not self.choice_1.GetString(self.choice_1.GetSelection())
            or not self.choice_2.GetString(self.choice_2.GetSelection())
            or self.check_list_box_1.GetSelection() == wx.NOT_FOUND
        ):
            self.button_1.Enable(False)
        else:
            self.button_1.Enable(True)
        myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
        self.SetCursor(myCursor)
