import wx
from wx.adv import SplashScreen as SplashScreen

import Common.Globals as Globals
from GUI.WXFrameLayoutNew import NewFrameLayout as FrameLayout
from Utility.Resource import resourcePath, scale_bitmap


class MySplashScreen(SplashScreen):
    def __init__(self, parent=None):
        # bitmap = wx.Bitmap(name=resourcePath("Images/icon.png"), type=wx.BITMAP_  TYPE_PNG)
        image = wx.Image(resourcePath("Images/splash.png"))
        image = image.Scale(1000, 372, wx.IMAGE_QUALITY_HIGH)
        bitmap = wx.Bitmap(image)
        splash = wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_NO_TIMEOUT
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
