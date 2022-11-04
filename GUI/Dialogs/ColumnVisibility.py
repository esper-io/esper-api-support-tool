#!/usr/bin/env python

from Common.decorator import api_tool_decorator
import wx
from GUI.TabPanel import TabPanel

from Utility.Resource import getStrRatioSimilarity


class ColumnVisibility(wx.Dialog):
    def __init__(self, parent, pageGridDict={}, colLabelException={}):
        super(ColumnVisibility, self).__init__(
            parent,
            wx.ID_ANY,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.SetTitle("Column Visibility")
        self.SetMinSize((500, 500))
        self.SetSize((500, 500))
        self.SetThemeEnabled(False)

        self.choiceDataDict = {}
        self.pageGridDict = pageGridDict
        self.colLabelException = colLabelException
        self.isFiltered = False
        self.selected = {}
        self.current_page = None

        self.checkBoxes = {}
        for page in pageGridDict.keys():
            self.selected[page] = {}
            if not self.current_page:
                self.current_page = page

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        grid_sizer_1 = wx.FlexGridSizer(2, 1, 0, 0)
        sizer_1.Add(grid_sizer_1, 1, wx.EXPAND, 0)

        self.text_ctrl_1 = wx.SearchCtrl(self, wx.ID_ANY, "")
        self.text_ctrl_1.ShowCancelButton(True)
        grid_sizer_1.Add(self.text_ctrl_1, 0, wx.ALIGN_RIGHT | wx.ALL | wx.EXPAND, 5)

        self.notebook_1 = wx.Notebook(self, wx.ID_ANY)
        self.notebook_1.SetThemeEnabled(False)
        grid_sizer_1.Add(self.notebook_1, 1, wx.EXPAND, 0)

        for page in pageGridDict.keys():
            self.addColumnVisiblityPage(page)

        sizer_2 = wx.StdDialogButtonSizer()
        sizer_1.Add(sizer_2, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

        self.button_CANCEL = wx.Button(self, wx.ID_CANCEL, "")
        sizer_2.AddButton(self.button_CANCEL)

        self.button_APPLY = wx.Button(self, wx.ID_APPLY, "")
        sizer_2.AddButton(self.button_APPLY)

        sizer_2.Realize()

        grid_sizer_1.AddGrowableRow(1)
        grid_sizer_1.AddGrowableCol(0)

        self.SetSizer(sizer_1)
        sizer_1.Fit(self)

        self.SetEscapeId(self.button_CANCEL.GetId())
        self.SetAffirmativeId(self.button_APPLY.GetId())

        self.Layout()

        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.notebook_1.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_tab_change)

        self.text_ctrl_1.Bind(wx.EVT_SEARCH, self.onSearch)
        self.text_ctrl_1.Bind(wx.EVT_KEY_DOWN, self.onKey)
        self.text_ctrl_1.Bind(wx.EVT_CHAR, self.onSearchChar)
        self.text_ctrl_1.Bind(wx.EVT_SEARCH_CANCEL, self.onSearch)

        self.Bind(wx.EVT_LISTBOX, self.OnSelection)
        if (
            hasattr(self.Parent.parentFrame, "WINDOWS")
            and self.Parent.parentFrame.WINDOWS
        ):
            self.Bind(wx.EVT_LISTBOX_DCLICK, self.OnSelection)

        for page in pageGridDict.keys():
            self.setCheckedItemsFromGrid(page)

        self.Fit()
        self.Center()

    @api_tool_decorator()
    def onClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        elif self.IsShown():
            self.Close()
        self.DestroyLater()
        if event:
            event.Skip()

    def setCheckedItemsFromGrid(self, label):
        grid = self.pageGridDict[label]
        exemptCols = self.colLabelException[label]
        for num in range(grid.GetNumberCols()):
            colLabel = grid.GetColLabelValue(num)
            if colLabel in exemptCols:
                continue
            try:
                isShown = grid.IsColShown(num)
                if colLabel in self.choiceDataDict[label]:
                    self.checkBoxes[label].Check(
                        self.choiceDataDict[label].index(colLabel), isShown
                    )
                    self.selected[label][colLabel] = isShown
            except:
                pass

    def addColumnVisiblityPage(self, label):
        notebook_panel = TabPanel(self.notebook_1, wx.ID_ANY, label)
        self.notebook_1.AddPage(notebook_panel, label)

        sizer = wx.GridSizer(1, 1, 0, 0)

        choice = self.choiceDataDict[label] if label in self.choiceDataDict else []
        if not choice:
            grid = self.pageGridDict[label]
            exemptCols = self.colLabelException[label]
            for num in range(grid.GetNumberCols()):
                colLabel = grid.GetColLabelValue(num)
                if colLabel in exemptCols:
                    continue
                choice.append(colLabel)
            self.choiceDataDict[label] = choice
        check_list_box = wx.CheckListBox(notebook_panel, wx.ID_ANY, choices=choice)
        sizer.Add(check_list_box, 0, wx.ALL | wx.EXPAND, 3)
        self.checkBoxes[label] = check_list_box
        check_list_box.Bind(wx.EVT_CHECKLISTBOX, self.OnSelection)

        notebook_panel.SetSizer(sizer)

    def on_tab_change(self, event):
        self.current_page = self.notebook_1.GetPage(event.GetSelection()).name
        if self.checkBoxes[self.current_page]:
            self.checkBoxes[self.current_page].EnsureVisible(0)
        event.Skip()

    @api_tool_decorator()
    def onSearchChar(self, event):
        event.Skip()
        wx.CallAfter(self.onSearch, wx.EVT_CHAR.typeId)

    @api_tool_decorator()
    def onKey(self, event):
        keycode = event.GetKeyCode()
        # CTRL + C or CTRL + Insert
        if event.ControlDown() and keycode in [67, 322]:
            self.on_copy(event)
        # CTRL + V
        elif event.ControlDown() and keycode == 86:
            self.on_paste(event)
        else:
            event.Skip()

    @api_tool_decorator()
    def onSearch(self, event=None):
        queryString = ""
        if hasattr(event, "GetString"):
            queryString = event.GetString()
        elif isinstance(event, str):
            queryString = event
        else:
            queryString = self.text_ctrl_1.GetValue()

        for page in self.pageGridDict.keys():
            self.processSearch(page, queryString)

    def processSearch(self, label, queryString):
        checkbox = self.checkBoxes[label]
        checkbox.Clear()

        listToProcess = None
        if queryString:
            listToProcess = list(
                filter(
                    lambda i: queryString.lower() in i.lower()
                    or getStrRatioSimilarity(i.lower(), queryString) > 90,
                    self.choiceDataDict[label],
                )
            )
            self.isFiltered = True
        else:
            listToProcess = self.selected[label].keys()
            self.isFiltered = False

        if listToProcess:
            num = 0
            for item in listToProcess:
                checkbox.Append(item)
                checkbox.Check(num, self.selected[label][item])
                num += 1

    @api_tool_decorator()
    def OnSelection(self, event):
        selection = event.GetSelection()
        checkbox = self.checkBoxes[self.current_page]
        itemName = checkbox.GetString(selection)
        checkbox.Deselect(selection)
        checked = list(checkbox.GetCheckedItems())
        if (
            event.EventType == wx.EVT_LISTBOX.typeId
            or event.EventType == wx.EVT_LISTBOX_DCLICK.typeId
        ) and selection in checked:
            checked.remove(selection)
            self.selected[self.current_page][itemName] = False
        elif (
            event.EventType == wx.EVT_LISTBOX.typeId
            or event.EventType == wx.EVT_LISTBOX_DCLICK.typeId
        ) and selection not in checked:
            checked.append(selection)
            self.selected[self.current_page][itemName] = True
        elif selection in checked:
            self.selected[self.current_page][itemName] = True
        else:
            self.selected[self.current_page][itemName] = False
        checkbox.SetCheckedItems(tuple(checked))

    @api_tool_decorator()
    def OnApply(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        elif self.IsShown():
            self.Close()

    @api_tool_decorator()
    def OnClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        elif self.IsShown():
            self.Close()
        self.DestroyLater()

    @api_tool_decorator()
    def isChecked(self, item):
        cols = len(self.check_list_box_1.GetItems())
        if item < cols:
            return self.check_list_box_1.IsChecked(item)
        return True

    # def getChoiceDataDict(self):
    #     return self.choiceDataDict

    def getSelected(self):
        return self.selected

    # def getCheckboxes(self):
    #     return self.checkBoxes

    # def getCheckBox(self, label):
    #     return self.checkBoxes[label]
