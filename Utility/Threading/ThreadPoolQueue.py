# !/usr/bin/env python

import threading
import time
from queue import Queue
from threading import Event, current_thread

from Utility.FileUtility import checkIfCurrentThreadStopped
from Utility.Threading.Worker import Worker


# class for thread pool
class Pool:
    def __init__(self, thread_count, batch_mode=False, thread_name="thread"):
        """Pool of threads consuming tasks from a queue"""
        # Validate thread_count parameter
        try:
            self.thread_count = int(thread_count)
            if self.thread_count <= 0:
                raise ValueError("thread_count must be positive")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid thread_count: {thread_count}. Must be a positive integer.") from e
        
        # batch mode means block when adding tasks if no threads available to process
        self.queue = Queue(self.thread_count if batch_mode else 0)
        self.resultQueue = Queue(0)
        self.aborts = []
        self.idles = []
        self.threads = []
        self.thread_name = thread_name
        self.abortJoin = Event()
        self._started = False
        self._clear_lock = threading.Lock()  # Lock to synchronize queue clearing

    def __del__(self):
        """Tell my threads to quit"""
        try:
            self.abort()
        except Exception:
            # Suppress all exceptions during cleanup to prevent issues during interpreter shutdown
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
                        if t.is_alive() and hasattr(t, 'raise_exception'):
                            try:
                                t.raise_exception()
                            except Exception as e:
                                # Log but continue with other threads
                                import Common.Globals as Globals
                                if Globals.API_LOGGER and hasattr(Globals.API_LOGGER, 'LogError'):
                                    Globals.API_LOGGER.LogError(f"Failed to raise exception in thread: {e}")
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
        self._started = True
        return True

    def clearQueue(self):
        """Clear the queue and mark all pending tasks as done"""
        with self._clear_lock:
            try:
                # Directly reset the queue state to prevent task_done() from hanging
                with self.queue.mutex:
                    # Get the number of items being cleared to track for task_done calls
                    num_cleared = self.queue.qsize()
                    
                    # Clear all items from the queue
                    self.queue.queue.clear()
                    
                    # Safely reset the unfinished_tasks counter
                    # Ensure it doesn't go negative if some task_done() calls are already in progress
                    if hasattr(self.queue, 'unfinished_tasks'):
                        self.queue.unfinished_tasks = 0
                    
                    # Notify all threads waiting on join()
                    self.queue.all_tasks_done.notify_all()
            except Exception as e:
                # If clearing fails, log it but don't crash
                import Common.Globals as Globals
                if Globals.API_LOGGER and hasattr(Globals.API_LOGGER, 'LogError'):
                    Globals.API_LOGGER.LogError(f"Error clearing queue: {e}")

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
                if hasattr(threading.current_thread(), "isStopped") and not isAbortSet:
                    isAbortSet = threading.current_thread().isStopped()
                if (
                    (timeout > 0 and time.perf_counter() - startTime >= timeout)
                    or self.isDoneWithinTolerance(queueTolerance=tolerance)
                    or isAbortSet
                    or self.abortJoin.is_set()
                    or checkIfCurrentThreadStopped()
                ):
                    self.abortJoin.clear()
                    break
                time.sleep(0.01)

    def abort(self, block=False):
        """Tell each worker that its done working"""
        # Clear the queue immediately to prevent new tasks from being processed
        self.clearQueue()
        
        # Set stopCurrentTask flag to interrupt any currently running tasks
        for thread in self.threads:
            if hasattr(thread, 'stopCurrentTask'):
                thread.stopCurrentTask.set()
        
        # tell the threads to stop after they are done with what they are currently doing
        for a in self.aborts:
            if a:
                a.set()
            else:
                print(a)
        # wait for them to finish if requested
        while block and self.alive():
            time.sleep(0.1)  # Reduced sleep time for faster response

    def alive(self):
        """Returns True if any threads are currently running"""
        return True in [t.is_alive() for t in self.threads]

    def idle(self, tolerance=0):
        """Returns True if all threads are waiting for work"""
        if not self._started or not self.idles:
            return True  # No threads running, so technically idle
        numActive = [i.is_set() for i in self.idles].count(False)
        return numActive <= tolerance

    def getNumberOfActiveThreads(self):
        if not self._started or not self.idles:
            return 0  # No threads running
        numActive = [i.is_set() for i in self.idles].count(False)
        return numActive

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
        except Exception:
            # Queue.Empty or any other exception means no more results
            pass
        return results

    def abortCurrentTasks(self, waitForIdle=True, clearFlagAtEnd=True):
        self.abortJoin.set()
        
        # Clear the queue immediately to prevent new tasks from being processed
        self.clearQueue()

        # Set stopCurrentTask flag for all threads to interrupt currently running tasks
        for thread in self.threads:
            if hasattr(thread, 'stopCurrentTask'):
                thread.stopCurrentTask.set()

        if waitForIdle:
            # Wait for threads to finish, but with a timeout to prevent hanging
            max_wait_time = 5.0  # Maximum 5 seconds to wait
            start_time = time.perf_counter()
            while self.idle() is False and (time.perf_counter() - start_time) < max_wait_time:
                time.sleep(0.01)
        
        if clearFlagAtEnd:
            for thread in self.threads:
                if hasattr(thread, 'stopCurrentTask'):
                    thread.stopCurrentTask.clear()