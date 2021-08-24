#!/usr/bin/env python

from Utility.Resource import getStrRatioSimilarity, openWebLinkInBrowser
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
        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        grid_sizer_1 = wx.FlexGridSizer(4, 1, 0, 0)
        sizer_1.Add(grid_sizer_1, 1, wx.EXPAND, 0)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        grid_sizer_1.Add(self.panel_1, 1, wx.ALL | wx.EXPAND, 5)

        grid_sizer_2 = wx.GridSizer(1, 2, 0, 0)

        sizer_5 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_2.Add(sizer_5, 1, wx.EXPAND, 0)

        label_1 = wx.StaticText(self.panel_1, wx.ID_ANY, "Source Endpoint:")
        sizer_5.Add(label_1, 0, 0, 0)

        self.choice_1 = wx.Choice(self.panel_1, wx.ID_ANY, choices=choices)
        sizer_5.Add(self.choice_1, 0, wx.EXPAND | wx.RIGHT, 5)

        sizer_6 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_2.Add(sizer_6, 1, wx.EXPAND | wx.LEFT, 5)

        label_2 = wx.StaticText(self.panel_1, wx.ID_ANY, "Destination Endpoint:")
        sizer_6.Add(label_2, 0, 0, 0)

        self.choice_2 = wx.Choice(self.panel_1, wx.ID_ANY, choices=choices)
        sizer_6.Add(self.choice_2, 0, wx.EXPAND | wx.RIGHT, 5)

        static_line_1 = wx.StaticLine(self, wx.ID_ANY)
        grid_sizer_1.Add(static_line_1, 0, wx.BOTTOM | wx.EXPAND | wx.TOP, 5)

        self.panel_2 = wx.Panel(self, wx.ID_ANY)
        grid_sizer_1.Add(self.panel_2, 1, wx.ALL | wx.EXPAND, 5)

        grid_sizer_4 = wx.GridSizer(1, 2, 0, 0)

        grid_sizer_3 = wx.FlexGridSizer(2, 1, 0, 0)
        grid_sizer_4.Add(grid_sizer_3, 1, wx.EXPAND, 0)

        sizer_3 = wx.FlexGridSizer(1, 2, 0, 0)
        grid_sizer_3.Add(sizer_3, 1, wx.BOTTOM | wx.EXPAND, 5)

        label_3 = wx.StaticText(self.panel_2, wx.ID_ANY, "Source Template:")
        sizer_3.Add(label_3, 0, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND | wx.LEFT, 5)

        self.templateSearch = wx.SearchCtrl(self.panel_2, wx.ID_ANY, "")
        self.templateSearch.ShowCancelButton(True)
        sizer_3.Add(self.templateSearch, 0, wx.RIGHT, 5)

        self.list_box_1 = wx.ListBox(
            self.panel_2,
            wx.ID_ANY,
            choices=[],
            style=wx.LB_NEEDED_SB | wx.LB_SINGLE | wx.LB_SORT,
        )
        grid_sizer_3.Add(self.list_box_1, 0, wx.ALL | wx.EXPAND, 5)

        grid_sizer_5 = wx.FlexGridSizer(2, 1, 0, 0)
        grid_sizer_4.Add(grid_sizer_5, 1, wx.EXPAND, 0)

        sizer_4 = wx.FlexGridSizer(1, 2, 0, 0)
        grid_sizer_5.Add(sizer_4, 1, wx.BOTTOM | wx.EXPAND, 12)

        label_4 = wx.StaticText(self.panel_2, wx.ID_ANY, "Template Preview:")
        sizer_4.Add(label_4, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

        sizer_4.Add((0, 0), 0, 0, 0)

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
        grid_sizer_5.Add(self.text_ctrl_1, 0, wx.ALL | wx.EXPAND, 5)

        static_line_2 = wx.StaticLine(self, wx.ID_ANY)
        grid_sizer_1.Add(static_line_2, 0, wx.BOTTOM | wx.EXPAND | wx.TOP, 5)

        sizer_2 = wx.StdDialogButtonSizer()
        sizer_1.Add(sizer_2, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

        self.button_OK = wx.Button(self, wx.ID_OK, "")
        self.button_OK.SetDefault()
        sizer_2.AddButton(self.button_OK)

        self.button_CANCEL = wx.Button(self, wx.ID_CANCEL, "")
        sizer_2.AddButton(self.button_CANCEL)

        sizer_2.Realize()

        sizer_4.AddGrowableRow(0)
        sizer_4.AddGrowableCol(0)

        grid_sizer_5.AddGrowableRow(1)
        grid_sizer_5.AddGrowableCol(0)

        sizer_3.AddGrowableRow(0)
        sizer_3.AddGrowableCol(0)

        grid_sizer_3.AddGrowableRow(1)
        grid_sizer_3.AddGrowableCol(0)

        self.panel_2.SetSizer(grid_sizer_4)

        self.panel_1.SetSizer(grid_sizer_2)

        grid_sizer_1.AddGrowableRow(2)
        grid_sizer_1.AddGrowableCol(0)

        self.SetSizer(sizer_1)

        self.SetAffirmativeId(self.button_OK.GetId())
        self.SetEscapeId(self.button_CANCEL.GetId())

        self.Layout()

        self.templateSearch.Bind(wx.EVT_SEARCH, self.onSearchTemplate)
        self.templateSearch.Bind(wx.EVT_CHAR, self.onSearchTemplateChar)
        self.templateSearch.Bind(wx.EVT_SEARCH_CANCEL, self.onSearchTemplate)

        self.text_ctrl_1.Bind(wxHtml.EVT_HTML_LINK_CLICKED, openWebLinkInBrowser)
        self.button_OK.Bind(wx.EVT_BUTTON, self.OnClose)
        self.button_CANCEL.Bind(wx.EVT_BUTTON, self.OnClose)
        self.choice_1.Bind(wx.EVT_CHOICE, self.onChoice1Select)
        self.choice_2.Bind(wx.EVT_CHOICE, self.onChoice2Select)
        if hasattr(self.parent, "WINDOWS") and self.parent.WINDOWS:
            self.list_box_1.Bind(wx.EVT_LISTBOX, self.OnSelection)
            self.list_box_1.Bind(wx.EVT_LISTBOX_DCLICK, self.OnSelection)

        self.__set_properties()

    @api_tool_decorator()
    def __set_properties(self):
        # begin wxGlade: MyDialog.__set_properties
        self.SetTitle("Clone Template")
        self.SetSize((515, 315))
        self.choice_1.SetSelection(0)
        self.choice_2.SetSelection(0)
        self.button_OK.Enable(False)
        self.button_CANCEL.SetFocus()
        # end wxGlade

    @api_tool_decorator()
    def getInputSelections(self):
        return (
            self.configMenuOpt[self.choice_2.GetString(self.choice_2.GetSelection())],
            self.list_box_1.GetString(self.list_box_1.GetSelection()),
        )

    @api_tool_decorator()
    def OnClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        elif self.IsShown():
            self.Close()

    @api_tool_decorator()
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

    @api_tool_decorator()
    def OnSelection(self, event):
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)
        selection = event.GetSelection()
        name = self.list_box_1.GetString(selection)
        template = list(filter(lambda x: x["name"] == name, self.sourceTemplate))
        self.populateTemplatePreview(template)

    @api_tool_decorator()
    def populateSourceTempaltes(self, srcName):
        if srcName:
            self.sourceTemplate = self.getTemplates(self.configMenuOpt[srcName])
            for template in self.sourceTemplate:
                self.list_box_1.Append(template["name"])
        self.checkInputValues()

    @api_tool_decorator()
    def onChoice1Select(self, event):
        myCursor = wx.Cursor(wx.CURSOR_WAIT)
        self.SetCursor(myCursor)
        self.sourceTemplate = []
        self.list_box_1.Clear()
        self.choice1thread = wxThread.GUIThread(
            self,
            self.populateSourceTempaltes,
            (event.String if event.String else False),
            name="populateSourceTempaltes",
        )
        self.choice1thread.start()

    @api_tool_decorator()
    def fetchDestTempaltes(self, destName):
        if destName:
            self.destTemplate = self.getTemplates(self.configMenuOpt[destName])
        self.checkInputValues()

    @api_tool_decorator()
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

    @api_tool_decorator()
    def getTemplates(self, dataSrc):
        util = templateUtil.EsperTemplateUtil(dataSrc, None)
        tempList = util.getTemplates(
            dataSrc["apiHost"], dataSrc["apiKey"], dataSrc["enterprise"]
        )
        return tempList["results"]

    @api_tool_decorator()
    def getTemplate(self, template):
        util = templateUtil.EsperTemplateUtil()
        dataSrc = self.configMenuOpt[
            self.choice_1.GetString(self.choice_1.GetSelection())
        ]
        return util.getTemplate(
            dataSrc["apiHost"], dataSrc["apiKey"], dataSrc["enterprise"], template["id"]
        )

    @api_tool_decorator()
    def checkInputValues(self):
        if (
            self.choice_1.GetString(self.choice_1.GetSelection())
            == self.choice_2.GetString(self.choice_2.GetSelection())
            or not self.choice_1.GetString(self.choice_1.GetSelection())
            or not self.choice_2.GetString(self.choice_2.GetSelection())
            or self.list_box_1.GetSelection() == wx.NOT_FOUND
        ):
            self.button_OK.Enable(False)
        else:
            self.button_OK.Enable(True)
        myCursor = wx.Cursor(wx.CURSOR_DEFAULT)
        self.SetCursor(myCursor)

    @api_tool_decorator()
    def onSearchTemplateChar(self, event):
        event.Skip()
        wx.CallAfter(self.onSearchTemplate, wx.EVT_CHAR.typeId)

    def onSearchTemplate(self, event):
        queryString = ""
        if hasattr(event, "GetString"):
            queryString = event.GetString()
        elif isinstance(event, str):
            queryString = event
        else:
            queryString = self.templateSearch.GetValue()
        self.list_box_1.Clear()
        if queryString:
            filteredList = list(
                filter(
                    lambda x: queryString.lower() in x["name"].lower()
                    or getStrRatioSimilarity(x["name"], queryString) > 90,
                    self.sourceTemplate,
                )
            )
            for template in filteredList:
                self.list_box_1.Append(template["name"])
        else:
            for template in self.sourceTemplate:
                self.list_box_1.Append(template["name"])
