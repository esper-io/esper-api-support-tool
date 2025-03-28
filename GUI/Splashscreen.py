import wx
from wx.adv import SplashScreen as SplashScreen

import Common.Globals as Globals
from GUI.WXFrameLayoutNew import NewFrameLayout as FrameLayout
from Utility.Resource import resourcePath, scale_bitmap


class MySplashScreen(SplashScreen):
    def __init__(self, parent=None):
        bitmap = scale_bitmap(resourcePath("Images/splash.png"), 1000, 372)
        splash = wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_TIMEOUT
        duration = 3000 # milliseconds

        super(MySplashScreen, self).__init__(bitmap=bitmap,
                                              splashStyle=splash,
                                              milliseconds=duration,
                                              parent=None,
                                              id=-1,
                                              pos=wx.DefaultPosition,
                                              size=wx.DefaultSize,
                                              style=wx.STAY_ON_TOP |
                                                    wx.BORDER_NONE)

        self.CenterOnScreen(wx.BOTH)
        self.Show()

        self.Bind(wx.EVT_CLOSE, self.OnExit)

    def OnExit(self, event):
         event.Skip()
         Globals.frame = FrameLayout(self)
