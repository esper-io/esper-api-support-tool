def safeEnable(widget, enable=True):
    """Safely enable/disable a widget if it exists and is not deleted."""
    try:
        if widget and hasattr(widget, "Enable"):
            widget.Enable(enable)
    except RuntimeError:
        pass

def safeSetSelection(widget, idx):
    try:
        if widget and hasattr(widget, "SetSelection"):
            widget.SetSelection(idx)
    except RuntimeError:
        pass

def safeBind(widget, eventType, handler, source=None):
    try:
        if widget and hasattr(widget, "Bind"):
            if source:
                widget.Bind(eventType, handler, source)
            else:
                widget.Bind(eventType, handler)
    except RuntimeError:
        pass