#!/usr/bin/env python

import Common.Globals as Globals
import wx
from GUI.Dialogs.ConfirmTextDialog import ConfirmTextDialog


class CmdConfirmDialog(ConfirmTextDialog):
    def __init__(
        self, commandType, cmdFormatted, schType, schFormatted, applyToType, applyTo
    ):
        label = ""
        if schType.startswith("i"):
            label = (
                "About to try applying an %s %s command on the %s, %s, continue?"
                % (schType.lower(), commandType, applyToType, applyTo)
            )
        else:
            label = "About to try applying a %s %s command on the %s, %s, continue?" % (
                schType.lower(),
                commandType,
                applyToType,
                applyTo,
            )
        super(CmdConfirmDialog, self).__init__(
            "Command Confirmation",
            label,
            "Commnd Confirmation",
            (cmdFormatted + "\n\n" + schFormatted),
        )
