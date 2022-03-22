#!/usr/bin/env python3

import wx


class TabPanel(wx.Panel):
    def __init__(self, parent, id, name):
        """"""
        super().__init__(parent=parent, id=id)
        self.name = name
