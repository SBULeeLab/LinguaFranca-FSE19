"""Lingua Franca: Parallelism

Classes and methods to help with parallelizing a set of tasks.
"""

import multiprocessing

import os

import time
import random

import libLF.lf_utils as lf_utils

####
# Public API.
####

def map(tasks, nWorkers, rateLimit, limitUnits, jitter):
    """Run a bunch of tasks in parallel.

    @param tasks: An iterable that returns WorkerTask's
    @param nWorkers: Number of workers. Use one of CPUCount.{CPU|IO|NETWORK}_BOUND
    @param rateLimit: RateLimitEnums.NO_RATE_LIMIT or some positive integer
    @param limitUnits: RateLimitEnums.NO_RATE_LIMIT or RateLimitEnums.PER_X
    @param jitter: if true, inject some jitter to avoid lockstepped tasks
    @return results[]: in same order as tasks. If any task.run() throws then we put the exception in the list
    """

    # Build an RLWT
    rlwt = _RateLimitedParallelTasks(tasks, rateLimit, limitUnits)

    # Which _runWorkerTask to use?
    runParallelTask = _runParallelTask
    if jitter:
        runParallelTask = _runParallelTaskJitter

    with multiprocessing.Pool(nWorkers) as pool:
        # TODO Can we return an iterable or yield or something?
        results = list(pool.imap(runParallelTask, rlwt))
    return results

class CPUCount():
    """Estimates of number of CPUs you want. {CPU | IO | NETWORK}_BOUND"""
    if os.cpu_count():
        _nCPUs = os.cpu_count()
    else:
      _nCPUs = 4

    CPU_BOUND = _nCPUs
    IO_BOUND = 2 * _nCPUs
    NETWORK_BOUND = 4 * _nCPUs

class RateLimitEnums():
    """Enums to express rate limit. NO_RATE_LIMIT or PER_{SECOND | MINUTE | HOUR}"""
    NO_RATE_LIMIT = 'NO_RATE_LIMIT'
    PER_SECOND = 'PER_SECOND'
    PER_MINUTE = 'PER_MINUTE'
    PER_HOUR = 'PER_HOUR'

class ParallelTask():
    """Sub-class this. Override the run() method."""
    def __init__(self):
        pass
    def run(self):
        pass

####
# Helpers
####

def _runParallelTask(parallelTask):
    """Return the result of parallelTask.run(), or the exception generated when we attempt."""
    ret = None
    try:
        ret = parallelTask.run()
    except BaseException as err:
        ret = err
    return ret 

def _runParallelTaskJitter(parallelTask):
    """_runWorkerTask with some pre-run jitter (O(fractions of a second))."""
    time.sleep(0.1 * random.random()) # TODO Sleep <= 0.1 seconds.
    return _runParallelTask(parallelTask)

class _RateLimitedParallelTasks():
    """Wrap a list of ParallelTasks.
    
    This is an iterable that returns only within a rate limit.
    For use with multiprocessing.

    Use this such that elements are retrieved on-demand.
    Thus only use with imap-style.
    map converts into a list prior to handling, so the rate limit
    is eaten up front during conversion and ignored during use.
    cf. https://stackoverflow.com/a/26521507
    """
    def __init__(self, tasks, rateLimit, limitUnits):
        self.tasks = tasks
        self.firstEmission = True
        self.rateLimit = rateLimit
        self.limitUnits = limitUnits

        # Initialize window variables.
        self._beginWindow()
        self.windowLengthInSeconds = self._windowLengthInSeconds()

        self.ix = 0

    def __iter__(self):
        return self
    
    def __next__(self):
        """Return next elt. May sleep until current window expires."""
        if self.firstEmission:
            self.firstEmission = False
            self._beginWindow()

        # Get the next task
        if len(self.tasks) <= self.ix:
            raise StopIteration
        nextTask = self.tasks[self.ix]
        self.ix += 1

        if self.rateLimit != RateLimitEnums.NO_RATE_LIMIT:
            # Apply rate limiting
            if self.remainingEmissionsThisWindow == 0:
                # Sleep out the remainder of the window
                remainingTime = self._secsLeftInWindow()
                if 0 < remainingTime:
                    lf_utils.log('Rate limiting: Sleeping {} secs to finish out the window'.format(remainingTime))
                    time.sleep(remainingTime)
                self._beginWindow()
            self.remainingEmissionsThisWindow -= 1
        return nextTask

    # Rate limit management    
    def _windowLengthInSeconds(self):
        if self.limitUnits == RateLimitEnums.PER_HOUR:
            return 60*60
        elif self.limitUnits == RateLimitEnums.PER_MINUTE:
            return 60
        elif self.limitUnits == RateLimitEnums.PER_SECOND:
            return 1
        elif self.limitUnits == RateLimitEnums.NO_RATE_LIMIT:
            return 0
        else:
            raise(ValueError('Unexpected limitUnits'))
        
    def _beginWindow(self):
        self.windowBegan = time.time()
        self.remainingEmissionsThisWindow = self.rateLimit
    
    def _secsSinceWindowBegan(self):
        return time.time() - self.windowBegan
    
    def _secsLeftInWindow(self):
        return self.windowLengthInSeconds - self._secsSinceWindowBegan()
