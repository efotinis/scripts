#!python
"""Stop watch class."""

from __future__ import print_function
import time


class StopWatch:
    """Create stopwatch instance and optionally start timing.

    Use timefunc to specify a custom function returning seconds.
    """

    def __init__(self, timefunc=time.clock, autostart=False):
        self.timefunc = timefunc
        self.reset(autostart)

    def start(self):
        """Start timing (if stopped)."""
        if self.begin is None:
            self.begin = self.timefunc()

    def stop(self):
        """Stop timing (if started)."""
        if self.begin is not None:
            self.accum += self.timefunc() - self.begin
            self.begin = None

    def get(self):
        """Accumulated time in seconds."""
        if self.begin is None:
            return self.accum
        else:
            return self.accum + self.timefunc() - self.begin

    def reset(self, autostart=False):
        """Clear accumulator and optionally start timing."""
        self.accum = 0
        self.begin = self.timefunc() if autostart else None

    def isrunning(self):
        """Test whether timer is running."""
        return self.begin is not None


if __name__ == '__main__':
    t = StopWatch()

    intervals = (10, 50, 200)
    for msec in intervals:
        print('sleeping for %d msec...' % msec, end=' ')
        t.reset(autostart=True)
        time.sleep(msec / 1000.0)
        t.stop()
        print('%.2f msec measured' % (t.get() * 1000.0))

    print('resolution in sec:')
    for i in range(5):
        t.start()
        prev = t.get()
        while True:
            cur = t.get()
            if cur > prev:
                break
        print('  %.6e' % (cur - prev))
