# !/usr/bin/env python

import time

from queue import Queue
from threading import Event

from Utility.Threading.Worker import Worker


# class for thread pool
class Pool:
    """Pool of threads consuming tasks from a queue"""
    def __init__(self, thread_count, batch_mode=False, thread_name="thread"):
        # batch mode means block when adding tasks if no threads available to process
        self.queue = Queue(thread_count if batch_mode else 0)
        self.resultQueue = Queue(0)
        self.thread_count = int(thread_count)
        self.aborts = []
        self.idles = []
        self.threads = []
        self.thread_name = thread_name

    """Tell my threads to quit"""
    def __del__(self):
        try:
            self.abort()
        except:
            pass

    """Start the threads, or restart them if you've aborted"""
    def run(self, block=False):
        # either wait for them to finish or return false if some arent
        if block:
            while self.alive():
                time.sleep(1)
        elif self.alive():
            return False

        # go start them
        self.aborts = []
        self.idles = []
        self.threads = []
        for n in range(self.thread_count):
            abort = Event()
            idle = Event()
            self.aborts.append(abort)
            self.idles.append(idle)
            self.threads.append(Worker('%s-%d' % (self.thread_name, n), self.queue, self.resultQueue, abort, idle))
        return True

    """Add a task to the queue"""
    def enqueue(self, func, *args, **kargs):
        self.queue.put((func, args, kargs))

    """Wait for completion of all the tasks in the queue"""
    def join(self):
        self.queue.join()

    """Tell each worker that its done working"""
    def abort(self, block=False):
        # tell the threads to stop after they are done with what they are currently doing
        for a in self.aborts:
            if a:
                a.set()
            else:
                print(a)
        # wait for them to finish if requested
        while block and self.alive():
            time.sleep(1)

    """Returns True if any threads are currently running"""
    def alive(self):
        return True in [t.is_alive() for t in self.threads]

    """Returns True if all threads are waiting for work"""
    def idle(self):
        return False not in [i.is_set() for i in self.idles]

    """Returns True if not tasks are left to be completed"""
    def done(self):
        return self.queue.empty()

    """Get the set of results that have been processed, repeatedly call until done"""
    def results(self, wait=0):
        time.sleep(wait)
        results = []
        try:
            while True:
                # get a result, raises empty exception immediately if none available
                results.append(self.resultQueue.get(False))
                self.resultQueue.task_done()
        except:
            pass
        return results
