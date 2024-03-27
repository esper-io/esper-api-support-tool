# !/usr/bin/env python

import math
import threading
import time

import wx

import Common.Globals as Globals
import Utility.EventUtility as eventUtil
from Common.decorator import api_tool_decorator
from Common.enum import GridActions
from Utility.Resource import joinThreadList, postEventToFrame


@api_tool_decorator()
def waitTillThreadsFinish(
    threads, action, entId, source, event=None, maxGauge=1, tolerance=0
):
    """ Wait till all threads have finished then send a signal back to the Main thread """
    if threads == Globals.THREAD_POOL.threads:
        Globals.THREAD_POOL.join(tolerance)
    else:
        joinThreadList(threads)
    initPercent = 0
    if Globals.frame.statusBar.gauge:
        initPercent = Globals.frame.statusBar.gauge.GetValue()
    initVal = 0
    if source == 1:
        deviceList = {}
        if maxGauge:
            initVal = math.ceil((initPercent / 100) * maxGauge)
        if threads == Globals.THREAD_POOL.threads:
            resp = Globals.THREAD_POOL.results()
            for thread in resp:
                if type(thread) == tuple:
                    deviceList = {**deviceList, **thread[1]}
                    if maxGauge:
                        val = int((initVal + len(deviceList)) / maxGauge * 100)
                        postEventToFrame(
                            eventUtil.myEVT_UPDATE_GAUGE,
                            val,
                        )
        else:
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
        statuses = []
        devices = []
        tracker = {
            "success": 0,
            "fail": 0,
            "progress": 0,
            "sent": 0,
            "skip": 0,
        }
        if threads == Globals.THREAD_POOL.threads:
            resp = Globals.THREAD_POOL.results()
            for thread in resp:
                if type(thread) == tuple:
                    thread_tracker = thread[0]
                    tracker["success"] += thread_tracker["success"]
                    tracker["fail"] += thread_tracker["fail"]
                    tracker["sent"] += thread_tracker["sent"]
                    tracker["skip"] += thread_tracker["skip"]
                    tracker["progress"] += thread_tracker["progress"]

                    devices += thread[1]
                    statuses += thread[2]
        else:
            for thread in threads:
                if type(thread.result) == tuple:
                    thread_tracker = thread.result[0]
                    tracker["success"] += thread_tracker["success"]
                    tracker["fail"] += thread_tracker["fail"]
                    tracker["sent"] += thread_tracker["sent"]
                    tracker["skip"] += thread_tracker["skip"]
                    tracker["progress"] += thread_tracker["progress"]

                    devices += thread._args[1]
                    statuses += thread.result[2]
        msg = ""
        if action == GridActions.MODIFY_TAGS.value:
            msg = "Requested %s tag changes. %s succeeded, %s failed, %s skipped (no tags found to apply), %s in-progress. \n\nREMINDER: Only %s tags MAX may be currently applied to a device!" % (
                tracker["sent"],
                tracker["success"],
                tracker["fail"],
                tracker["skip"],
                tracker["progress"],
                Globals.MAX_TAGS
            )
        else:
            msg = "Requested %s Alias changes. %s succeeded, %s failed. %s skipped (either no Alias found or is already applied). %s in-progress." % (
                tracker["sent"],
                tracker["success"],
                tracker["fail"],
                tracker["skip"],
                tracker["progress"],
            )
        postEventToFrame(eventUtil.myEVT_LOG, msg)
        postEventToFrame(eventUtil.myEVT_COMMAND, (msg, statuses))
    if source == 3:
        deviceList = {}
        if threads == Globals.THREAD_POOL.threads:
            resp = Globals.THREAD_POOL.results()
            for thread in resp:
                if type(thread) == dict:
                    deviceList = {**deviceList, **thread}
                    if maxGauge:
                        val = int((initVal + len(deviceList)) / maxGauge * 100)
                        postEventToFrame(
                            eventUtil.myEVT_UPDATE_GAUGE,
                            val,
                        )
        else:
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
        elif action == GridActions.INSTALL_APP.value:
            msg = "Results of installing given app packages."
        elif action == GridActions.UNINSTALL_APP.value:
            msg = "Results of uninstalling given app packages."
        elif action == GridActions.FACTORY_RESET.value:
            msg = "Results of Factory Reset."
        else:
            msg = "Results:"
        statuses = []
        if threads == Globals.THREAD_POOL.threads:
            resp = Globals.THREAD_POOL.results()
            for t in resp:
                if t and type(t) == dict:
                    for val in t.values():
                        statuses.append(val)
                elif t and type(t) == list:
                    for val in t:
                        statuses.append(val)
        else:
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
            if self.isStopped():
                return
            try:
                return super().start()
            except Exception as e:
                time.sleep(3)
                if attempt == Globals.MAX_RETRY - 1:
                    raise e
