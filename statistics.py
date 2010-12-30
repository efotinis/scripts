"""Statistical functions.

Source: <http://en.wikibooks.org/wiki/Statistics>
"""

from __future__ import division
import math
import collections


def amean(a):
    """Arithmetic mean."""
    if len(a) == 0:
        raise ValueError('empty sequence')
    return sum(a) / len(a)

def gmean(a):
    """Geometric mean."""
    if len(a) == 0:
        raise ValueError('empty sequence')
    return math.exp(sum(math.log(x) for x in a) / len(a))

def hmean(a):
    """Harmonic mean."""
    if len(a) == 0:
        raise ValueError('empty sequence')
    try:
        return len(a) / sum(1/x for x in a)
    except ZeroDivisionError:
        raise ValueError('sequence contains 0')

def mode(a):
    """List of the most common value or values."""
    if len(a) == 0:
        raise ValueError('empty sequence')
    values_and_counts_decr = collections.Counter(a).most_common()
    maxcount = values_and_counts_decr[0][1]
    ret = []
    for val, cnt in values_and_counts_decr:
        if cnt == maxcount:
            ret += [val]
        else:
            break
    return ret

def median(a):
    """The 'middle' value."""
    if len(a) == 0:
        raise ValueError('empty sequence')
    a = sorted(a)
    size = len(a)
    if size % 2 == 1:
        return a[(size - 1) // 2]
    else:
        i = (size // 2) - 1
        return mean(a[i:i+2])

def rangewidth(a):
    if len(a) == 0:
        raise ValueError('empty sequence')
    return max(a) - min(a)

def minmax(a):
    if len(a) == 0:
        raise ValueError('empty sequence')
    return min(a), max(a)

def variance(a):
    if len(a) == 0:
        raise ValueError('empty sequence')
    mean = amean(a)
    return sum((x - mean)**2 for x in a) / len(a)

def stddev(a):
    return math.sqrt(variance(a))
