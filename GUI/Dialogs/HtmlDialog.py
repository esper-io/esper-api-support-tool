import wx
import wx.html as html

import Common.Globals as Globals


class HtmlDialog(wx.Dialog):
    def __init__(
        self, showCheckbox=False, checkboxLabel="Don't show this again", *args, **kwds
    ):
        super(HtmlDialog, self).__init__(
            Globals.frame,
            wx.ID_ANY,
            size=Globals.MIN_SIZE,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.SetSize(Globals.MIN_SIZE)
        self.SetMinSize((50, 50))
        self.SetTitle("Terms and Conditions")
        self.SetThemeEnabled(False)

        sizer_1 = wx.FlexGridSizer(2, 1, 0, 0)

        self.htmlWin = html.HtmlWindow(
            self,
            name="Terms And Conditions",
            style=html.HW_SCROLLBAR_AUTO,
            size=Globals.MIN_SIZE,
        )
        if "gtk2" in wx.PlatformInfo:
            self.htmlWin.SetStandardFonts()
        self.htmlWin.SetPage(Globals.TERMS_AND_CONDITIONS)
        sizer_1.Add(self.htmlWin, 1, wx.ALL | wx.EXPAND, 5)

        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(sizer_2, 1, wx.ALL | wx.EXPAND, 5)

        self.checkbox_1 = None
        if showCheckbox:
            self.checkbox_1 = wx.CheckBox(self, wx.ID_ANY, checkboxLabel)
            sizer_2.Add(self.checkbox_1, 0, 0, 0)

        sizer_1.AddGrowableRow(0)
        sizer_1.AddGrowableCol(0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)

        self.Layout()

    def isCheckboxChecked(self):
        return self.checkbox_1.IsChecked() if self.checkbox_1 else False
