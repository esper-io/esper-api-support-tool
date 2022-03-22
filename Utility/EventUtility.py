#!/usr/bin/env python

import wx

myEVT_FETCH = wx.NewEventType()
EVT_FETCH = wx.PyEventBinder(myEVT_FETCH, 1)

myEVT_COMPLETE = wx.NewEventType()
EVT_COMPLETE = wx.PyEventBinder(myEVT_COMPLETE, 1)

myEVT_GROUP = wx.NewEventType()
EVT_GROUP = wx.PyEventBinder(myEVT_GROUP, 1)

myEVT_APPS = wx.NewEventType()
EVT_APPS = wx.PyEventBinder(myEVT_APPS, 1)

myEVT_LOG = wx.NewEventType()
EVT_LOG = wx.PyEventBinder(myEVT_LOG, 1)

myEVT_COMMAND = wx.NewEventType()
EVT_COMMAND = wx.PyEventBinder(myEVT_COMMAND, 1)

myEVT_UPDATE_GAUGE = wx.NewEventType()
EVT_UPDATE_GAUGE = wx.PyEventBinder(myEVT_UPDATE_GAUGE, 1)

myEVT_UPDATE_GAUGE_LATER = wx.NewEventType()
EVT_UPDATE_GAUGE_LATER = wx.PyEventBinder(myEVT_UPDATE_GAUGE_LATER, 1)

myEVT_UPDATE_TAG_CELL = wx.NewEventType()
EVT_UPDATE_TAG_CELL = wx.PyEventBinder(myEVT_UPDATE_TAG_CELL, 1)

myEVT_UNCHECK_CONSOLE = wx.NewEventType()
EVT_UNCHECK_CONSOLE = wx.PyEventBinder(myEVT_UNCHECK_CONSOLE, 1)

myEVT_ON_FAILED = wx.NewEventType()
EVT_ON_FAILED = wx.PyEventBinder(myEVT_ON_FAILED, 1)

myEVT_CONFIRM_CLONE = wx.NewEventType()
EVT_CONFIRM_CLONE = wx.PyEventBinder(myEVT_CONFIRM_CLONE, 1)

myEVT_CONFIRM_CLONE_UPDATE = wx.NewEventType()
EVT_CONFIRM_CLONE_UPDATE = wx.PyEventBinder(myEVT_CONFIRM_CLONE_UPDATE, 1)

myEVT_MESSAGE_BOX = wx.NewEventType()
EVT_MESSAGE_BOX = wx.PyEventBinder(myEVT_MESSAGE_BOX, 1)

myEVT_THREAD_WAIT = wx.NewEventType()
EVT_THREAD_WAIT = wx.PyEventBinder(myEVT_THREAD_WAIT, 1)

myEVT_UPDATE_GRID_CONTENT = wx.NewEventType()
EVT_UPDATE_GRID_CONTENT = wx.PyEventBinder(myEVT_UPDATE_GRID_CONTENT, 1)

myEVT_DISPLAY_NOTIFICATION = wx.NewEventType()
EVT_DISPLAY_NOTIFICATION = wx.PyEventBinder(myEVT_DISPLAY_NOTIFICATION, 1)

myEVT_PROCESS_FUNCTION = wx.NewEventType()
EVT_PROCESS_FUNCTION = wx.PyEventBinder(myEVT_PROCESS_FUNCTION, 1)


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
