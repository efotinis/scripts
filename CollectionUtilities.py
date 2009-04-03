"""
Utilities for collections/sequences.

2008.12.02  created; unique()
"""


def unique(seq, keyfunc=None):
    """Get list of unique items from a sequence.
    
    Only the first item from a group of duplicates is preserved. The relative order
    of the returned items is preserved.
    If 'keyfunc' is supplied, it is a unary function to calculate the key of each
    item; otherwise the item itself is the key (the key must be hashable).
    """
    ret = []
    keys = set()
    for item in seq:
        k = keyfunc(item) if keyfunc else item
        if k not in keys:
            keys.add(k)
            ret += [item]
    return ret
