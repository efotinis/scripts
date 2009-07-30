"""Utilities to simplify getopt operations."""


def options_dict(opt, flags=None, negflags=None, values=None, multivalues=None):
    """Build an options dict by extracting switches from opt list.

    The optional params are dicts that map switch names to the return dict keys.
        param       init    set
        =====       ====    ===
        flags       False   True
        negflags    True    False
        values      None    last seen value
        multivalues []      all values

    No check is made to ensure that (neg)flags and (multi)values are
    mapped to options without and with arguments, respectively. That's
    because getopt doesn't differentiate a non-existing argument from
    an empty one (it would be nice if it returned None for the former).
    """

    # init missing dicts for simplicity
    flags = flags or {}
    negflags = negflags or {}
    values = values or {}
    multivalues = multivalues or {}
    
    # make sure there are no duplicate switches (e.g. '-h' both a flag and a value)
    # and no duplicate (across dicts) names (e.g. 'help' cannot be mapped in both
    # flags and values, although it's OK if more than one switch in a single dict
    # maps to it, like '-h' and '-?')
    alldicts = (flags, negflags, values, multivalues)
    dupkeys = _getdups(sum((d.keys() for d in alldicts), []))
    dupvalues = _getdups(sum((list(set(d.values())) for d in alldicts), []))
    if dupkeys:
        raise ValueError('duplicate switches found: ' + ', '.join(dupkeys))
    if dupvalues:
        raise ValueError('duplicate names found: ' + ', '.join(dupvalues))

    # set defaults
    ret = {}
    for s in flags.values():
        ret[s] = False
    for s in negflags.values():
        ret[s] = True
    for s in values.values():
        ret[s] = None
    for s in multivalues.values():
        ret[s] = []
    
    unprocessed = []
    for switch, value in opt:
        if switch in flags:
            ret[flags[switch]] = True
        elif switch in negflags:
            ret[negflags[switch]] = False
        elif switch in values:
            ret[values[switch]] = value
        elif switch in multivalues:
            ret[multivalues[switch]] += [value]
        else:
            unprocessed += [(switch, value)]

    opt[:] = unprocessed

    return ret
        

def _getdups(seq):
    """Get a set of the items that appear more than once in a sequence.

    Example:
    >>> _getdups('abcaaac')
    set(['a', 'c'])
    """
    seen = set()
    dups = set()
    for x in seq:
        if x in seen:
            dups.add(x)
        else:
            seen.add(x)
    return dups


if __name__ == '__main__':

    import getopt
    import unittest

    class TestSequenceFunctions(unittest.TestCase):

        def setUp(self):
            pass

        def test_options_dict(self):
            cmdline = '-h -v -a -o DIR1 -o DIR2 -i INC1 -i INC2 -b FOO'
            opt, args = getopt.getopt(cmdline.split(), 'hrvxao:p:i:l:b:')
            assert not args

            flags = {'-h':'help', '-?':'help', '-r':'recurse'}
            negflags = {'-v':'nonverbose', '-x':'nonspecial'}
            values = {'-o':'output', '-p':'password'}
            multivalues = {'-i':'include', '-l':'lib'}

            result = options_dict(opt, flags=flags, negflags=negflags,
                                  values=values, multivalues=multivalues)
            expected = dict(
                help=True, recurse=False,
                nonverbose=False, nonspecial=True,
                output='DIR2', password=None,
                include=['INC1','INC2'], lib=[])
            leftover = [('-a', ''), ('-b', 'FOO')]

            self.assertEqual(result, expected, 'incorrect result')
            self.assertEqual(opt, leftover, 'incorrect leftover')

            flags = {'-h':'help' }
            negflags = {'-h':'dishonest'}
            self.assertRaises(ValueError, options_dict, [],
                              flags=flags, negflags=negflags)

        def test_getdups(self):
            self.assertEqual(_getdups(''), set([]))
            self.assertEqual(_getdups('abc'), set([]))
            self.assertEqual(_getdups('abcaaac'), set(['a', 'c']))

    unittest.main()
