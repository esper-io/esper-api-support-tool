import threading
import wx

myEVT_UPDATE = wx.NewEventType()
EVT_UPDATE = wx.PyEventBinder(myEVT_UPDATE, 1)


class CustomEvent(wx.PyCommandEvent):
    """Event to signal that a count value is ready"""

    def __init__(self, etype, eid, value=None):
        """Creates the event object"""
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._value = value

    def GetValue(self):
        """Returns the value from the event.
        @return: the value of this event

        """
        return self._value


class GUIThread(threading.Thread):
    def __init__(self, parent, target, args):
        """
        @param parent: The gui object that should recieve the value
        @param target: The function to run
        @param args: Arguements for target function
        """
        threading.Thread.__init__(self)
        self._parent = parent
        self._target = target
        self._args = args

    def run(self):
        """Overrides Thread.run. Don't call this directly its called internally
        when you call Thread.start().
        """
        action, result = self._target(*self._args)
        evt = CustomEvent(myEVT_UPDATE, -1, (action, result))
        wx.PostEvent(self._parent, evt)
