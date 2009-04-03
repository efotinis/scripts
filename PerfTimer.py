"""Windows performance timer interface."""

# 2008.01.30  Created.


import ctypes, SharedLib


BOOL = ctypes.c_long
LARGE_INTEGER = ctypes.c_longlong


QueryPerformanceFrequency = SharedLib.winfunc('kernel32',
    'QueryPerformanceFrequency', BOOL, [ctypes.POINTER(LARGE_INTEGER)])
QueryPerformanceCounter = SharedLib.winfunc('kernel32',
    'QueryPerformanceCounter', BOOL, [ctypes.POINTER(LARGE_INTEGER)])


class Error(Exception):
    """Performace timer error."""
    def __init__(self, s):
        Exception.__init__(self, s)
    

def getfreq():
    """Performace timer frequency."""
    ll = LARGE_INTEGER()
    if not QueryPerformanceFrequency(ctypes.byref(ll)):
        raise Error('could not get frequency')
    return ll.value
    

def getcounter():
    """Performace timer counter."""
    ll = LARGE_INTEGER()
    if not QueryPerformanceCounter(ctypes.byref(ll)):
        raise Error('could not get counter')
    return ll.value


class Counter:
    """Performace timer accumulator."""
    def __init__(self):
        self.running = False
        self.accum = 0
        self.begin = 0
        self.freq = getfreq()
    def start(self):
        """Must be stopped."""
        if self.running:
            raise Error('already running')
        self.begin = getcounter()
        self.running = True
    def stop(self):
        """Must be running."""
        if not self.running:
            raise Error('already stopped')
        self.accum += getcounter() - self.begin
        self.running = False
    def reset(self):
        """Zero accumulator."""
        self.accum = 0
        if self.running:
            self.begin = getcounter()
    def get(self):
        """Get accumulated seconds; must be stopped."""
        if self.running:
            raise Error('must be stopped first')
        return float(self.accum) / self.freq


if __name__ == '__main__':
    import win32api as api
    intervals = (100, 250, 500)
    t = PerfTimer()
    for msec in intervals:
        t.start()
        api.Sleep(msec)
        t.stop()
    print 'msec: %d (Sleep), %d (PerfTimer)' % (sum(intervals), t.get() * 1000)
