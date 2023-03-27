import wx
import wx.html as html

import Common.Globals as Globals

class HtmlDialog(wx.Dialog):
    def __init__(self, *args, **kwds):
        super(HtmlDialog, self).__init__(
            None,
            wx.ID_ANY,
            size=Globals.MIN_SIZE,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.SetSize(Globals.MIN_SIZE)
        self.SetMinSize((50, 50))
        self.SetTitle("Terms and Conditions")
        self.SetThemeEnabled(False)

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        self.htmlWin = html.HtmlWindow(self,
                                  name="Terms And Conditions",
                                  style=html.HW_SCROLLBAR_AUTO,
                                  size=Globals.MIN_SIZE
        )
        if "gtk2" in wx.PlatformInfo:
            self.htmlWin.SetStandardFonts()
        self.htmlWin.SetPage(Globals.TERMS_AND_CONDITIONS)
        sizer_1.Add(self.htmlWin, 1, wx.EXPAND, 0)

        self.SetSizer(sizer_1)
        sizer_1.Fit(self)

        self.Layout()
