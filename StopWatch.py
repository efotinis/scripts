"""Stop watch classes for incremental time tracking."""

import time


class Base:
    """Abstract base timer. timeFunc() must return seconds as float."""

    def __init__(self, timeFunc, autoStart=False):
        self.timeFunc = timeFunc
        self.reset(autoStart)

    def start(self):
        if self.begin is None:
            self.begin = self.timeFunc()

    def stop(self):
        if self.begin is not None:
            self.accum += self.timeFunc() - self.begin
            self.begin = None

    def get(self):
        if self.begin is None:
            return self.accum
        else:
            return self.accum + self.timeFunc() - self.begin

    def reset(self, autoStart=False):
        self.accum = 0
        self.begin = self.timeFunc() if autoStart else None


def Simple(autoStart=False):
    """Timer using time.time(); typical resolution in WinNT is ~15ms."""
    return Base(time.time, autoStart)


def Performance(autoStart=False):
    """Timer using time.clock(); typical resolution in WinNT is ~1us."""
    return Base(time.clock, autoStart)
