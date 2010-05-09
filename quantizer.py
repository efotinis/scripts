from __future__ import division


class Quantizer(object):
    """Converts data pairs to linearly interpolated, fixed size elements.

    For example, size-time pairs with varying time intervals (e.g. download speed statistics)
    can be converted to fixed (e.g. 1-second) size chunks, to facilitate moving average speed calculations.
    """

    def __init__(self, granularity, maxsamples=None):
        """'granularity' specifies the fixed size of the 2nd data series.
        If 'maxsamples' is specified, older data pairs are disgarded.
        """
        self.granularity = granularity
        self.maxsamples = maxsamples
        self.pending_a = 0
        self.pending_b = 0  # pending_b < granularity
        self.data = []

    def add(self, (value_a, value_b)):
        """Add a data pair."""
        while value_b + self.pending_b >= self.granularity:
            b = self.granularity - self.pending_b
            a = value_a * b / value_b  # lerp
            self.data.append(a)
            if self.maxsamples is not None and len(self.data) > self.maxsamples:
                del self.data[:-self.maxsamples]
            value_a -= a
            value_b -= b
            self.pending_a = 0
            self.pending_b = 0
        # accumulate leftovers to pending
        self.pending_a += value_a
        self.pending_b += value_b

    def __iadd__(self, ab):
        self.add(ab)
        return self


class TimeQuantizer(Quantizer):
    """Quantizer of a single data series with implied time.

    Time deltas are based on the system time when adding data.
    Useful for quantizing speeds without manually keeping track of time.
    """

    def __init__(self, granularity, maxsamples=None):
        Quantizer.__init__(self, granularity, maxsamples)
        self.lasttime = time.time()

    def add(self, value):
        curtime = time.time()
        dt = curtime - self.lasttime
        self.lasttime = curtime
        Quantizer.add(self, (value, dt))


##def split(value, cur, total):
##    #assert cur <= total
##    ratio = float(cur) / total
##    return value * ratio
##
##
##class MovingAverage(object):
##
##    def __init__(self, granularity, depth):
##        self.granularity = granularity
##        #self.data = [0] * depth
##        self.data = None
##        self.depth = depth
##        self.lasttime = time.time()
##        self.pendingtime = 0
##        self.pendingvalue = 0
##
##    def add(self, value):
##        curtime = time.time()
##        dt = curtime - self.lasttime
##        self.lasttime = curtime
##
##        while self.pendingtime + dt >= self.granularity:
##            t = self.granularity - self.pendingtime
##            v = split(value, t, dt)
##            if self.data:
##                self.data = [self.pendingvalue + v] + self.data[:-1]
##            else:
##                self.data = [self.pendingvalue + v] * self.depth
##            dt -= t
##            value -= v
##            self.pendingtime = 0
##            self.pendingvalue = 0
##
##        self.pendingtime += dt
##        self.pendingvalue += value
##
##    def calc(self):
##        if not self.data:
##            return 0
##        depth = len(self.data)
##        numerator, denumerator = 0, 0
##        for i, n in enumerate(self.data):
##            numerator += (depth - i) * n / self.granularity
##            denumerator += depth - i
##        return numerator / denumerator
