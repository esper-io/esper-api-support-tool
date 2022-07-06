# !/usr/bin/env python

import asyncio

from threading import Thread


# class for workers
class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""
    def __init__(self, name, queue, results, abort, idle, setLoop=False):
        Thread.__init__(self)
        self.name = name
        self.queue = queue
        self.results = results
        self.abort = abort
        self.idle = idle
        self.daemon = True
        self.setLoop = setLoop
        self.start()

    """Thread work loop calling the function with the params"""
    def run(self):
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
                result = func(*args, **kwargs)
                if (result is not None):
                    self.results.put(result)
            except Exception as e:
                # so we move on and handle it in whatever way the caller wanted
                print(e)
            finally:
                # task complete no matter what happened
                self.queue.task_done()
