# 2008.02.17  Created

import datetime


class DateRange:
    """Date range iterator (stop date exclusive). Default delta is 1 day."""
    def __init__(self, start, end, delta=None):
        self.current = start
        self.end = end
        self.increasing = start <= end
        if delta is None:
            #delta = 1 if self.increasing else -1
            delta = 1
        elif delta == 0:
            raise ValueError('DateRange() delta must be nonzero')
        self.delta = datetime.timedelta(delta)
        self.ended = self.increasing == bool(delta < 0) or self._testend()
    def __iter__(self):
        return self
    def next(self):
        if self.ended:
            raise StopIteration
        ret = self.current
        self.current += self.delta
        if self._testend():
            self.ended = True
        return ret
    def _testend(self):
        """Test whether iteration is complete."""
        if self.increasing:
            return self.current >= self.end
        else:
            return self.current <= self.end


if __name__ == '__main__':

    def getresult(params):
        start = datetime.date(*params[0:3])
        end = datetime.date(*params[3:6])
        other = params[6:]
        try:
            ret = []
            for d in DateRange(start, end, *other):
                ret += [(d.year, d.month, d.day)]
            return tuple(ret)
        except Exception, x:
            return x

    def runtest(test):
        name, params, result = test
        print '    %s ...' % name,
        x = getresult(params)
        if isinstance(x, Exception):
            ok = isinstance(x, result)
        else:
            ok = x == result
        print 'OK' if ok else 'FAIL'
        return ok
        
    # name, params (6 or 7), result (tuples of date elements or exception type)
    tests = (
        (   'forward, default step',
            (2000,1,1, 2000,1,4),
            ((2000,1,1), (2000,1,2), (2000,1,3))),
        (   'backward, single step',
            (2000,1,4, 2000,1,1, -1),
            ((2000,1,4), (2000,1,3), (2000,1,2))),
        (   'zero step',
            (2000,1,1, 2000,1,4, 0),
            ValueError),
        (   'forward, big step',
            (2000,1,1, 2000,1,10, 3),
            ((2000,1,1), (2000,1,4), (2000,1,7))),
        (   'backward, big step',
            (2000,1,10, 2000,1,2, -3),
            ((2000,1,10), (2000,1,7), (2000,1,4))),
        (   'empty range #1',
            (2000,1,1, 2000,1,1),
            ()),
        (   'empty range #2',
            (2000,1,10, 2000,1,1),
            ()),
        (   'empty range #3',
            (2000,1,1, 2000,1,10, -1),
            ()),
    )

    failed = 0
    print 'DateRange tests:'
    for test in tests:
        if not runtest(test):
            failed += 1
    print 'tests/failed: %d/%d' % (len(tests), failed)
    