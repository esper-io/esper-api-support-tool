# !/usr/bin/env python

import time
import Utility.EventUtility as eventUtil
import math
import Common.Globals as Globals
import threading
import wx

from Common.decorator import api_tool_decorator
from Common.enum import GridActions
from Utility.Resource import joinThreadList, postEventToFrame


@api_tool_decorator()
def waitTillThreadsFinish(threads, action, entId, source, event=None, maxGauge=1):
    """ Wait till all threads have finished then send a signal back to the Main thread """
    joinThreadList(threads)

    initPercent = 0
    if Globals.frame.gauge:
        initPercent = Globals.frame.gauge.GetValue()
    initVal = 0
    if source == 1:
        deviceList = {}
        if maxGauge:
            initVal = math.ceil((initPercent / 100) * maxGauge)
        for thread in threads:
            if type(thread.result) == tuple:
                deviceList = {**deviceList, **thread.result[1]}
                if maxGauge:
                    val = int((initVal + len(deviceList)) / maxGauge * 100)
                    postEventToFrame(
                        eventUtil.myEVT_UPDATE_GAUGE,
                        val,
                    )
        postEventToFrame(event, action)
        return (action, entId, deviceList, True, len(deviceList) * 3)
    if source == 2:
        postEventToFrame(eventUtil.myEVT_COMPLETE, None)
        changeSucceeded = succeeded = numNewName = 0
        statuses = []
        devices = []
        for thread in threads:
            if type(thread.result) == tuple:
                changeSucceeded += thread.result[0]
                succeeded += thread.result[1]
                numNewName += thread.result[2]
                devices += thread._args[1]
                statuses += thread.result[4]
        msg = (
            "Successfully changed tags for %s of %s devices and aliases for %s of %s devices.\n\nREMINDER: Only %s tags MAX may be currently applied to a device!"
            % (changeSucceeded, len(devices), succeeded, numNewName, Globals.MAX_TAGS)
        )
        postEventToFrame(eventUtil.myEVT_LOG, msg)
        postEventToFrame(eventUtil.myEVT_COMMAND, (msg, statuses))
    if source == 3:
        deviceList = {}
        for thread in threads:
            if type(thread.result) == dict:
                deviceList = {**deviceList, **thread.result}
                if maxGauge:
                    val = int((initVal + len(deviceList)) / maxGauge * 100)
                    postEventToFrame(
                        eventUtil.myEVT_UPDATE_GAUGE,
                        val,
                    )
        return (
            action,
            Globals.enterprise_id,
            deviceList,
            True,
            len(deviceList) * 3,
        )
    if source == 4:
        postEventToFrame(eventUtil.myEVT_THREAD_WAIT, (threads, 3, action))
    if source == 5:
        msg = ""
        if action == GridActions.MOVE_GROUP.value:
            msg = "Results of moving devices' groups."
        if action == GridActions.INSTALL_LATEST_APP.value:
            msg = "Results of installing given app packages."
        if action == GridActions.UNINSTALL_LISTED_APP.value:
            msg = "Results of uninstalling given app packages."
        if action == GridActions.FACTORY_RESET.value:
            msg = "Results of Factory Reset."
        statuses = []
        for t in threads:
            if t.result and type(t.result) == dict:
                for val in t.result.values():
                    statuses.append(val)
            elif t.result and type(t.result) == list:
                for val in t.result:
                    statuses.append(val)
        postEventToFrame(eventUtil.myEVT_COMPLETE, None)
        postEventToFrame(eventUtil.myEVT_COMMAND, (msg, statuses))


class GUIThread(threading.Thread):
    def __init__(
        self,
        parent,
        target,
        args,
        optArgs=None,
        eventType=None,
        eventArg=None,
        sendEventArgInsteadOfResult=False,
        callback=None,
        callbackArgs=None,
        optCallbackArgs=None,
        name=None,
    ):
        threading.Thread.__init__(self)
        self._parent = parent
        self._target = target
        self._args = args
        self._optArgs = optArgs
        self.eventType = eventType
        self.eventArg = eventArg
        self.sendEventArgInsteadOfResult = sendEventArgInsteadOfResult
        self.result = None
        self._callback = callback
        self._cbArgs = callbackArgs
        self._optCbArgs = optCallbackArgs
        self.daemon = True

        if name:
            self.name = name

        self.parent = threading.current_thread()

        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def isStopped(self):
        if self.parent and hasattr(self.parent, "isStopped"):
            return self._stop_event.is_set() or self.parent.isStopped()
        return self._stop_event.is_set()

    def run(self):
        """Overrides Thread.run. Don't call this directly its called internally
        when you call Thread.startWithRetry().
        """
        if self._target:
            if self._optArgs:
                if type(self._args) == tuple and type(self._optArgs) == tuple:
                    self.result = self._target(*self._args, *self._optArgs)
                elif type(self._args) != tuple and type(self._optArgs) == tuple:
                    self.result = self._target(self._args, *self._optArgs)
                elif type(self._args) == tuple and type(self._optArgs) != tuple:
                    self.result = self._target(*self._args, self._optArgs)
                elif type(self._args) != tuple and type(self._optArgs) != tuple:
                    self.result = self._target(self._args, self._optArgs)
            elif self._args:
                if type(self._args) != tuple:
                    self.result = self._target(self._args)
                elif type(self._args) == tuple:
                    self.result = self._target(*self._args)
            else:
                self.result = self._target()

        if self.isStopped():
            return

        if self._callback:
            self.result = (self.result, self._callback, self._cbArgs, self._optCbArgs)

        if self.isStopped():
            return

        if self.eventType:
            evt = None
            if self.sendEventArgInsteadOfResult:
                evt = eventUtil.CustomEvent(self.eventType, -1, self.eventArg)
            else:
                evt = eventUtil.CustomEvent(self.eventType, -1, self.result)
            if self._parent:
                wx.PostEvent(self._parent, evt)

    def startWithRetry(self):
        for attempt in range(Globals.MAX_RETRY):
            try:
                return super().start()
            except Exception as e:
                time.sleep(3)
                if attempt == Globals.MAX_RETRY - 1:
                    raise e
