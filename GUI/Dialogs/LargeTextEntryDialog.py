#!/usr/bin/env python3

from Common.decorator import api_tool_decorator
import wx


class LargeTextEntryDialog(wx.Dialog):
    def __init__(
        self,
        parent,
        label,
        title="",
        textPlaceHolder="",
        enableEdit=True,
        *args,
        **kwds
    ):
        kwds["style"] = (
            kwds.get("style", 0) | wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        wx.Dialog.__init__(self, parent, *args, **kwds)
        self.SetSize((400, 300))
        self.SetTitle(title)

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        sizer_1.Add(self.panel_1, 1, wx.ALL | wx.EXPAND, 5)

        sizer_3 = wx.BoxSizer(wx.VERTICAL)

        label_1 = wx.StaticText(
            self.panel_1,
            wx.ID_ANY,
            label,
        )
        label_1.Wrap(300)
        label_1.SetToolTip(label)
        label_1.SetFont(
            wx.Font(
                12,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "",
            )
        )
        sizer_3.Add(label_1, 0, 0, 0)

        grid_sizer_1 = wx.GridSizer(1, 1, 0, 0)
        sizer_3.Add(grid_sizer_1, 1, wx.EXPAND, 0)

        self.text_ctrl_1 = wx.TextCtrl(
            self.panel_1, wx.ID_ANY, "", style=wx.TE_MULTILINE | wx.TE_WORDWRAP
        )
        self.text_ctrl_1.SetValue(str(textPlaceHolder))
        self.text_ctrl_1.SetEditable(enableEdit)
        grid_sizer_1.Add(self.text_ctrl_1, 0, wx.ALL | wx.EXPAND, 5)

        sizer_2 = wx.StdDialogButtonSizer()
        sizer_1.Add(sizer_2, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

        self.button_OK = wx.Button(self, wx.ID_OK, "")
        self.button_OK.SetDefault()
        sizer_2.AddButton(self.button_OK)

        self.button_CANCEL = wx.Button(self, wx.ID_CANCEL, "")
        sizer_2.AddButton(self.button_CANCEL)

        sizer_2.Realize()

        self.panel_1.SetSizer(sizer_3)

        self.SetSizer(sizer_1)

        self.SetAffirmativeId(self.button_OK.GetId())
        self.SetEscapeId(self.button_CANCEL.GetId())
        self.text_ctrl_1.Bind(wx.EVT_KEY_DOWN, self.onKey)

        self.Layout()
        self.Centre()

    @api_tool_decorator
    def GetValue(self):
        return self.text_ctrl_1.GetValue()

    @api_tool_decorator
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

    @api_tool_decorator
    def on_copy(self, event):
        widget = self.FindFocus()
        data = wx.TextDataObject()
        data.SetText(widget.GetStringSelection())
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()

    @api_tool_decorator
    def on_paste(self, event):
        widget = self.FindFocus()
        success = False
        data = wx.TextDataObject()
        if wx.TheClipboard.Open():
            success = wx.TheClipboard.GetData(data)
            wx.TheClipboard.Close()
        if success:
            widget.WriteText(data.GetText())
