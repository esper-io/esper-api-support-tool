def safeEnable(widget, enable=True):
    """Safely enable/disable a widget if it exists and is not deleted."""
    try:
        if widget and hasattr(widget, "Enable") and widget.IsOk():
            widget.Enable(enable)
    except RuntimeError:
        pass

def safeSetSelection(widget, idx):
    try:
        if widget and hasattr(widget, "SetSelection") and widget.IsOk():
            widget.SetSelection(idx)
    except RuntimeError:
        pass

def safeBind(widget, eventType, handler, source=None):
    try:
        if widget and hasattr(widget, "Bind") and widget.IsOk():
            if source:
                widget.Bind(eventType, handler, source)
            else:
                widget.Bind(eventType, handler)
    except RuntimeError:
        pass