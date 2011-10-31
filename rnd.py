"""Random int/float generator and path selector."""

import argparse
import glob
import random
import sys
import textwrap

import six


def deduce_input(s):
    """Convert params to deduced value/type."""
    try:
        return int(s), 'int'
    except ValueError:
        pass
    try:
        return float(s), 'float'
    except ValueError:
        pass
    return s, 'path'


def parse_args():
    ap = argparse.ArgumentParser(
        description='print random ints/floats or select random paths',
        add_help=False)
    ap.add_argument('values', nargs='*', metavar='VAL',
                    help='specify the input range; use -?? for more help')
    ap.add_argument('-c', dest='count', type=int, default=1,
                    help='multiple values; default: %(default)s')
    ap.add_argument('-u', dest='unique', action='store_true',
                    help='unique discrete (non-float) values')
    ap.add_argument('-r', dest='onerow', action='store_true',
                    help='single row output')
    ap.add_argument('-f', dest='format', default='%f',
                    help='output format for floats; default: %(default)s'),
    ap.add_argument('-??', dest='details', action='store_true',
                    help=argparse.SUPPRESS)
    ap.add_argument('-?', action='help', help='this help')
    args = ap.parse_args()

    if args.details:
        six.print_(textwrap.dedent("""
            possible value types are int, float, and path string (deduced by conversion):
            
              types  params/defaults  range
              -----  ---------------  -----
              int    [A=1] B          input is [A,B]
              float  [A=0.0] [B=1.0]  input is [A,B)
              path   MASK [MASK ...]  glob masks"""))
        sys.exit()

    if args.count < 1:
        ap.error('count must be >= 1')

    if len(args.values) > 2:
        params = [(s, 'path') for s in args.values]
    elif args.values:
        params = [deduce_input(s) for s in args.values]
    else:
        params = [(1.0, 'float')]

    types = set(type_ for (_,type_) in params)
    if len(types) > 1:
        ap.error('multiple value types specified: %s' % types)

    args.type_ = types.pop()
    args.values = [value for (value,_) in params]

    if args.unique and args.type_ == 'float':
        ap.error('cannot return unique floats')

    return args


def get_range(a, defmin):
    """Return the first pair of items -or- the specified min and the first item."""
    if len(a) > 1:
        return a[0], a[1]
    else:
        return defmin, a[0]


def generate_ints(v1, v2, count, unique):
    if v1 > v2:
        raise ValueError('empty range: [%d,%d]' % (v1, v2))
    if unique and count > v2 - v1 + 1:
        raise ValueError('range too small for %d unique values: [%d,%d]' % (count, v1, v2))
        
    if unique:
        for n in random.sample(range(v1, v2 + 1), count):
            yield n
    else:
        for i in six.moves.xrange(count):
            yield random.randint(v1, v2)


def generate_floats(v1, v2, count):
    if v1 >= v2:
        raise ValueError('empty range: [%f,%f)' % (v1, v2))
    for i in six.moves.xrange(count):
        yield v1 + random.random() * (v2 - v1)


def generate_paths(masks, count, unique):
    paths = []
    for mask in masks:
        a = glob.glob(mask)
        if not a:
            six.print_('WARNING: no matches for "%s"' % mask, file=sys.stderr)
        paths += a

    if not paths:
        raise ValueError('no paths to select from')
    if unique and count > len(paths):
        raise ValueError('too few items (%d) for %d unique paths' % (len(paths), count))

    if unique:
        for s in random.sample(paths, count):
            yield s
    else:
        for i in six.moves.xrange(count):
            yield random.choice(paths)


if __name__ == '__main__':

    args = parse_args()

    try:
        if args.type_ == 'int':
            v1, v2 = get_range(args.values, 1)
            items = generate_ints(v1, v2, args.count, args.unique)
        elif args.type_ == 'float':
            v1, v2 = get_range(args.values, 0.0)
            items = (args.format % n for n in generate_floats(v1, v2, args.count))
        else:  # args.type_ == 'path'
            items = generate_paths(args.values, args.count, args.unique)

        sep = ' ' if args.onerow else '\n'
        six.print_(*items, sep=sep)
    except ValueError as x:
        sys.exit(x)




import os
import tempfile
import unittest


class IntTests(unittest.TestCase):

    def test_range(self):
        v1, v2, count = 1, 100, 1000

        # test failure on empty range
        with self.assertRaises(ValueError):
            list(generate_ints(v2, v1, count, unique=False))

        # make sure results are in range
        g = generate_ints(v1, v2, count, unique=False)
        self.assertTrue(all(v1 <= n <= v2 for n in g))

    def test_unique(self):
        v1, v2, count = 1, 100, 100
        
        # test failure on request for more unique values than possible
        max_unique = v2 - v1 + 1
        with self.assertRaises(ValueError):
            list(generate_ints(v1, v2, max_unique + 1, unique=True))

        # make sure there are no duplicates
        a = list(generate_ints(v1, v2, count, unique=True))
        self.assertEqual(len(a), len(set(a)))


class FloatTests(unittest.TestCase):

    def test_range(self):
        v1, v2, count = 0.0, 1.0, 100

        # test failure on empty range
        with self.assertRaises(ValueError):
            list(generate_floats(v2, v1, count))

        # make sure results are in range
        g = generate_floats(v1, v2, count)
        self.assertTrue(all(v1 <= n < v2 for n in g))
        #
        v1, v2 = -10.0, 10.0
        g = generate_floats(v1, v2, count)
        self.assertTrue(all(v1 <= n < v2 for n in g))


class PathTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        self.filenames = 'a.py b.py c.py d.py e.py a.txt b.txt c.txt'.split()
        for s in self.filenames:
            open(s, 'w').close()

    def tearDown(self):
        for s in self.filenames:
            os.unlink(s)
        os.chdir(self.old_cwd)
        os.rmdir(self.temp_dir)

    def test_all(self):
        # test failure on no matches
        with self.assertRaises(ValueError):
            list(generate_paths(['*.doc', '*.jpg'], 1, unique=False))

        # test failure on request for more unique values than possible
        max_unique = len(self.filenames)
        with self.assertRaises(ValueError):
            list(generate_paths(['*'], max_unique + 1, unique=True))

        # make sure results are in range
        g = generate_paths(['a.*'], 2, unique=False)
        self.assertTrue(all(s in self.filenames for s in g))

