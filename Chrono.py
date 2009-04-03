"""
Timing utilities.
"""

import time


class Error(Exception):
    """
    Base module exception.
    """
    def __init__(self, msg):
        Exception.__init__(self, msg)


class BaseTimer:
    """
    Abstract base timer.
    Derivatives must define a "timestamp" function, returning seconds.
    """
    def __init__(self, autoStart=False):
        self.reset(autoStart)
    def start(self):
        if self.begin is None:
            self.begin = self.timestamp()
##        else:
##            raise Error('timer already running')
    def stop(self):
        if self.begin is not None:
            self.accum += self.timestamp() - self.begin
            self.begin = None
##        else:
##            raise Error('timer already stopped')
    def get(self):
        if self.begin is None:
            return self.accum
        else:
            return self.accum + self.timestamp() - self.begin
    def reset(self, autoStart=False):
        self.accum = 0
        self.begin = self.timestamp() if autoStart else None


class SimpleTimer(BaseTimer):
    """
    Timer that uses "time.time" for the timestamp.
    Typical resolution in WinXP is 15ms.
    """
    def __init__(self, autoStart=False):
        BaseTimer.__init__(self, autoStart)
    def timestamp(self):
        return time.time()


class PerfTimer(BaseTimer):
    """
    Timer that uses "time.clock" for the timestamp.
    Typical resolution in WinXP is ~1us.
    """
    def __init__(self, autoStart=False):
        BaseTimer.__init__(self, autoStart)
    def timestamp(self):
        return time.clock()
