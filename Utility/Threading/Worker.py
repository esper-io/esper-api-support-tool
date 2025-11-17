# !/usr/bin/env python

import asyncio
import ctypes
import time
from threading import Event, Thread

import Common.Globals as Globals
from Utility.Logging.ApiToolLogging import ApiToolLog


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
        taskDoneCalled = False
        while not self.abort.is_set():
            # Check abort before attempting to get a task
            if self.abort.is_set() or Globals.KILL:
                break
            if self.stopCurrentTask.is_set():
                continue

            try:
                func, args, kwargs = self.queue.get(block=False)
                self.idle.clear()
            except Exception:
                # Queue is empty, no work to do
                self.idle.set()
                # Small sleep to prevent busy-waiting, but short enough for responsive abort
                time.sleep(0.01)
                continue

            # Check abort again after getting task but before executing
            if self.abort.is_set() or Globals.KILL:
                self.queue.task_done()
                taskDoneCalled = True
                break
            if self.stopCurrentTask.is_set():
                self.queue.task_done()
                taskDoneCalled = True
                continue

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
                if not taskDoneCalled:
                    self.queue.task_done()
                taskDoneCalled = False
        self.idle.set()

    def raise_exception(self):
        """Forcefully raise an exception in this thread to terminate it"""
        thread_id = self.ident
        
        # Validate thread_id before attempting to raise exception
        if thread_id is None:
            raise RuntimeError("Cannot raise exception: thread has not been started or has no valid thread ID")
        
        # Ensure thread_id is a valid C long integer
        try:
            thread_id = ctypes.c_long(thread_id)
        except (TypeError, ValueError) as e:
            raise RuntimeError(f"Invalid thread ID: {thread_id}") from e
        
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, ctypes.py_object(SystemExit))
        if res == 0:
            raise RuntimeError(f"Thread ID {thread_id} not found")
        elif res > 1:
            # If more than one thread was affected, revert the action
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            raise RuntimeError("Exception raise failure: multiple threads affected")
