import Common.Globals as Globals
import threading
import wx

myEVT_RESPONSE = wx.NewEventType()
EVT_RESPONSE = wx.PyEventBinder(myEVT_RESPONSE, 1)

myEVT_UPDATE = wx.NewEventType()
EVT_UPDATE = wx.PyEventBinder(myEVT_UPDATE, 1)

myEVT_COMPLETE = wx.NewEventType()
EVT_COMPLETE = wx.PyEventBinder(myEVT_COMPLETE, 1)

myEVT_GROUP = wx.NewEventType()
EVT_GROUP = wx.PyEventBinder(myEVT_GROUP, 1)

myEVT_DEVICE = wx.NewEventType()
EVT_DEVICE = wx.PyEventBinder(myEVT_DEVICE, 1)

myEVT_APPS = wx.NewEventType()
EVT_APPS = wx.PyEventBinder(myEVT_APPS, 1)

myEVT_LOG = wx.NewEventType()
EVT_LOG = wx.PyEventBinder(myEVT_LOG, 1)

myEVT_COMMAND = wx.NewEventType()
EVT_COMMAND = wx.PyEventBinder(myEVT_COMMAND, 1)

def doAPICallInThread(
    frame,
    func,
    args=None,
    eventType=myEVT_UPDATE,
    callback=None,
    callbackArgs=None,
    waitForJoin=True,
):
    t = GUIThread(
        frame,
        func,
        args=args,
        eventType=eventType,
        passArgAsTuple=True,
        callback=callback,
        callbackArgs=callbackArgs,
    )
    t.start()
    if waitForJoin:
        t.join()
    return t


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
    def __init__(
        self,
        parent,
        target,
        args,
        eventType=None,
        passArgAsTuple=False,
        callback=None,
        callbackArgs=None,
    ):
        """
        @param parent: The gui object that should recieve the value
        @param target: The function to run
        @param args: Arguements for target function
        """
        threading.Thread.__init__(self)
        self._parent = parent
        self._target = target
        self._args = args
        self.eventType = eventType
        self.passArgAsTuple = passArgAsTuple
        self.result = None
        self._callback = callback
        self._cbArgs = callbackArgs

    def run(self):
        """Overrides Thread.run. Don't call this directly its called internally
        when you call Thread.start().
        """
        if not self.passArgAsTuple:
            self.result = self._target(*self._args)
        else:
            self.result = self._target(self._args)

        if self._callback:
            self.result = (self.result, self._callback, self._cbArgs)

        if self.eventType:
            evt = CustomEvent(self.eventType, -1, self.result)
            wx.PostEvent(self._parent, evt)
