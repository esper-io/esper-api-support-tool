import wx

import Common.Globals as Globals
from Common.decorator import api_tool_decorator
from Common.enum import FontStyles
from Utility.Resource import applyFontHelper, determineKeyEventClose, getFont


class ThemeMessageBox(wx.Dialog):
    def __init__(self, size=(400, 200), minSize=(400, 200), description="", caption="", *args, **kwargs):
        style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        if kwargs.get("style", None) is not None:
            style |= kwargs["style"]
        super(ThemeMessageBox, self).__init__(
            Globals.frame,
            wx.ID_ANY,
            title=kwargs.get("title", ""),
            style=style,
        )
        self.SetSize(size)
        self.SetMinSize(minSize)

        """
           [icon|description]
           [caption]
           [buttons]
        """

        baseFlexGridSizer = wx.FlexGridSizer(3, 1, 0, 0)
        baseFlexGridSizer.AddGrowableRow(1)
        baseFlexGridSizer.AddGrowableCol(0)

        rowFlexGridSizer = wx.FlexGridSizer(1, 2, 0, 0)
        rowFlexGridSizer.AddGrowableCol(1)
        baseFlexGridSizer.Add(rowFlexGridSizer, 1, wx.EXPAND | wx.ALL, 5)

        # icon
        icon = None
        if wx.ICON_ERROR & style:
            icon = wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_MESSAGE_BOX)
        elif wx.ICON_INFORMATION & style:
            icon = wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_MESSAGE_BOX)
        elif wx.ICON_QUESTION & style:
            icon = wx.ArtProvider.GetBitmap(wx.ART_QUESTION, wx.ART_MESSAGE_BOX)
        elif wx.ICON_WARNING & style:
            icon = wx.ArtProvider.GetBitmap(wx.ART_WARNING, wx.ART_MESSAGE_BOX)
        elif wx.ICON_EXCLAMATION & style:
            icon = wx.ArtProvider.GetBitmap(wx.ART_WARNING, wx.ART_MESSAGE_BOX)
        elif wx.ICON_STOP & style:
            icon = wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_MESSAGE_BOX)
        elif wx.ICON_ASTERISK & style:
            icon = wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_MESSAGE_BOX)
        elif wx.ICON_HAND & style:
            icon = wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_MESSAGE_BOX)
        elif wx.ICON_AUTH_NEEDED & style:
            icon = wx.ArtProvider.GetBitmap(wx.ART_AUTH_NEEDED, wx.ART_MESSAGE_BOX)
        elif wx.ICON_MASK & style:
            icon = wx.ArtProvider.GetBitmap(wx.ART_MASK, wx.ART_MESSAGE_BOX)
        elif wx.ICON_SCREEN_DEPTH & style:
            icon = wx.ArtProvider.GetBitmap(wx.ART_SCREEN_DEPTH, wx.ART_MESSAGE_BOX)
        elif wx.ICON_STOP & style:
            icon = wx.ArtProvider.GetBitmap(wx.ART_STOP, wx.ART_MESSAGE_BOX)

        if icon:
            iconCtrl = wx.StaticBitmap(self, wx.ID_ANY, icon)
            rowFlexGridSizer.Add(iconCtrl, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        # text
        descriptionText = wx.StaticText(self, wx.ID_ANY, description)
        descriptionText.Wrap(350)  # Wrap text to a reasonable width
        descriptionText.SetMaxSize((350, -1))  # Limit the width of the text
        rowFlexGridSizer.Add(
            descriptionText,
            0,
            wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.ALL,
            5,
        )

        captionText = wx.StaticText(self, wx.ID_ANY, caption)
        baseFlexGridSizer.Add(
            captionText,
            0,
            wx.EXPAND | wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.ALL,
            5,
        )

        # buttons
        self.buttons = []
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        baseFlexGridSizer.Add(buttonSizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        if wx.OK & style or wx.OK_DEFAULT & style:
            button_OK = wx.Button(self, wx.ID_OK, "OK")
            self.buttons.append(button_OK)
            buttonSizer.Add(button_OK, 0, wx.ALL, 5)
        if wx.CANCEL & style or wx.CANCEL_DEFAULT & style:
            button_CANCEL = wx.Button(self, wx.ID_CANCEL, "Cancel")
            self.buttons.append(button_CANCEL)
            buttonSizer.Add(button_OK, 0, wx.ALL, 5)
        if wx.APPLY & style and not (wx.OK & style or wx.OK_DEFAULT & style):
            button_APPLY = wx.Button(self, wx.ID_APPLY, "Apply")
            self.buttons.append(button_APPLY)
            buttonSizer.Add(button_OK, 0, wx.ALL, 5)

        # Bind
        for btn in self.buttons:
            btn.Bind(wx.EVT_BUTTON, self.OnClose)
        self.Bind(wx.EVT_CHAR_HOOK, self.onEscapePressed)
        self.Bind(wx.EVT_SYS_COLOUR_CHANGED, Globals.frame.onThemeChange)

        self.SetSizer(baseFlexGridSizer)
        self.Layout()
        self.applyFontSize()
        self.Centre(wx.BOTH)

    @api_tool_decorator()
    def onEscapePressed(self, event):
        if determineKeyEventClose(event):
            self.onClose(event)
        event.Skip()

    @api_tool_decorator()
    def OnClose(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        elif self.IsShown():
            self.Close()

    def applyFontSize(self):
        applyFontHelper({}, self, self)
