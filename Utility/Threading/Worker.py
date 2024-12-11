# !/usr/bin/env python

import asyncio
import ctypes
import signal
from threading import Thread

import Common.Globals as Globals


class timeout:
    def __init__(self, seconds=1, error_message="Timeout"):
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, type, value, traceback):
        signal.alarm(0)


# class for workers
class Worker(Thread):
    def __init__(self, name, queue, results, abort, idle, setLoop=False):
        """Thread executing tasks from a given tasks queue"""
        Thread.__init__(self)
        self.name = name
        self.queue = queue
        self.results = results
        self.abort = abort
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
            try:
                # get a task and raise immediately if none available
                func, args, kwargs = self.queue.get(False)
                self.idle.clear()
            except:
                # no work to do
                self.idle.set()
                continue

            try:
                # the function may raise
                result = None
                with timeout(seconds=60):
                    result = func(*args, **kwargs)
                if result is not None:
                    self.results.put(result)
            except Exception as e:
                # so we move on and handle it in whatever way the caller wanted
                if Globals.API_LOGGER and hasattr(
                    Globals.API_LOGGER, "LogError"
                ):
                    Globals.API_LOGGER.LogError(e)
            finally:
                # task complete no matter what happened
                self.queue.task_done()
        self.idle.set()

    def raise_exception(self):
        thread_id = self.ident
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            thread_id, ctypes.py_object(SystemExit)
        )
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print("Exception raise failure")
