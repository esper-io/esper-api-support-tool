# !/usr/bin/env python

import asyncio
import ctypes
import time
from threading import Event, Thread

import Common.Globals as Globals


# class for workers
class Worker(Thread):
    def __init__(self, name, queue, results, abort, idle, setLoop=False):
        """Thread executing tasks from a given tasks queue"""
        Thread.__init__(self)
        self.name = name
        self.queue = queue
        self.results = results
        self.abort = abort
        self.stopCurrentTask = Event()
        self.idle = idle
        self.daemon = True
        self.setLoop = setLoop
        self.start()

    def run(self):
        """Thread work loop calling the function with the params"""
        # keep running until told to abort
        if self.setLoop:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        while not self.abort.is_set():
            # Check abort before attempting to get a task
            if self.abort.is_set() or self.stopCurrentTask.is_set():
                break
            
            try:
                # Use a short timeout so we can check abort flags more frequently
                # This allows threads to exit immediately when abort is called
                func, args, kwargs = self.queue.get(timeout=0.1)
                self.idle.clear()
            except:
                # no work to do
                self.idle.set()
                # Small sleep to prevent busy-waiting, but short enough for responsive abort
                time.sleep(0.01)
                continue

            # Check abort again after getting task but before executing
            if self.abort.is_set() or self.stopCurrentTask.is_set():
                # Mark task as done even though we're not executing it
                self.queue.task_done()
                break

            try:
                # the function may raise
                result = func(*args, **kwargs)
                if result is not None:
                    self.results.put(result)
            except Exception as e:
                # so we move on and handle it in whatever way the caller wanted
                if Globals.API_LOGGER and hasattr(Globals.API_LOGGER, "LogError"):
                    Globals.API_LOGGER.LogError(e)
            finally:
                # task complete no matter what happened
                self.queue.task_done()
        self.idle.set()

    def raise_exception(self):
        thread_id = self.ident
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print("Exception raise failure")
