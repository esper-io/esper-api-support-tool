# !/usr/bin/env python

import threading
import time

from queue import Queue
from threading import Event, current_thread

from Utility.Threading.Worker import Worker


# class for thread pool
class Pool:
    def __init__(self, thread_count, batch_mode=False, thread_name="thread"):
        """Pool of threads consuming tasks from a queue"""
        # batch mode means block when adding tasks if no threads available to process
        self.queue = Queue(thread_count if batch_mode else 0)
        self.resultQueue = Queue(0)
        self.thread_count = int(thread_count)
        self.aborts = []
        self.idles = []
        self.threads = []
        self.thread_name = thread_name

    def __del__(self):
        """Tell my threads to quit"""
        try:
            self.abort()
        except:
            pass

    def run(self, block=False):
        """Start the threads, or restart them if you've aborted"""
        # either wait for them to finish or return false if some arent
        if block:
            time_waiting = time.perf_counter()
            while self.alive():
                time.sleep(1)
                if time.perf_counter() - time_waiting > 60:
                    for t in self.threads:
                        try:
                            t.raise_exception()
                        except:
                            pass
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
            self.threads.append(
                Worker(
                    "%s-%d" % (self.thread_name, n),
                    self.queue,
                    self.resultQueue,
                    abort,
                    idle,
                )
            )
        return True

    def clearQueue(self):
        self.queue.queue.clear()

    def enqueue(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.queue.put((func, args, kargs))

    def join(self, tolerance=0, timeout=-1):
        """Wait for completion of all the tasks in the queue"""
        if current_thread() not in self.threads and tolerance == 0:
            self.queue.join()
        else:
            time.sleep(1)
            startTime = time.perf_counter()
            while True:
                isAbortSet = False
                if hasattr(threading.current_thread(), "abort"):
                    isAbortSet = threading.current_thread().abort.is_set()
                if (
                    (timeout > 0 and time.perf_counter() - startTime >= timeout)
                    or self.isDoneWithinTolerance(queueTolerance=tolerance)
                    or isAbortSet
                ):
                    break
                time.sleep(0.01)

    def abort(self, block=False):
        """Tell each worker that its done working"""
        # tell the threads to stop after they are done with what they are currently doing
        for a in self.aborts:
            if a:
                a.set()
            else:
                print(a)
        # wait for them to finish if requested
        while block and self.alive():
            time.sleep(1)

    def alive(self):
        """Returns True if any threads are currently running"""
        return True in [t.is_alive() for t in self.threads]

    def idle(self, tolarance=0):
        """Returns True if all threads are waiting for work"""
        numActive = [i.is_set() for i in self.idles].count(False)
        return numActive <= tolarance

    def done(self):
        """Returns True if not tasks are left to be completed"""
        return self.queue.empty()

    def isDoneWithinTolerance(self, queueTolerance=0):
        return self.idle(queueTolerance)

    def results(self, wait=0):
        """Get the set of results that have been processed, repeatedly call until done"""
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
