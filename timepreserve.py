#!python3
"""Save and restore file timestamps."""

import argparse
import os
import sys

import iterutil
import wildcard
import wintime


def parse_args():
    ap = argparse.ArgumentParser(
        description='save and restore file timestamps')
    add = ap.add_argument
    add('items', nargs='+', metavar='item',
        #help='item to preserve; on Windows, wildcards are allowed')
        help='item to preserve')
    add('-t', dest='times', default='cm',
        help='times to preserve; c=create, m=modify, a=access; '
        'default is "cm"')
    add('-v', dest='verbose', action='store_true',
        help='verbose; print item paths')
    args = ap.parse_args()
    unknown_times = set(args.times) - set('cma')
    if unknown_times:
        ap.error('invalid time flags: {!r}'.format(''.join(unknown_times)))
    return args


class WildError(Exception):
    pass


def wild(path):
    """Expand wildcard path to absolute paths.

    Wildcards are only allowed in the last element (i.e. not in parent dirs).
    """
    head, tail = os.path.split(path)

    # parent must exist verbatim (no wildcards allowed)
    if head:
        if wildcard.iswild(head):
            raise WildError('parent wildcards not allowed')
        elif not os.path.isdir(head):
            raise WildError('parent does not exist')

    # non-wildcard item must exist
    if not wildcard.iswild(tail):
        if not os.path.exists(path):
            raise WildError('item does not exist')
        else:
            return [os.path.abspath(path)]

    # expand wildcard items and verify that something actually matched
    names = wildcard.listdir(tail, head or '.')
    if not names:
        raise WildError('nothing matched')
    return [os.path.abspath(os.path.join(head, s)) for s in names]


def collect_paths(masks, onerror):
    """Expand list of masks (Windows-only) to abs paths and report errors.

    'onerror' is a callable taking an exception and mask string.
    """
    ret = []
    for s in masks:
        try:
            ret.extend(wild(s))
        except WildError as x:
            onerror(x, s)
    return ret


def main():
    args = parse_args()

    paths = collect_paths(
        args.items,
        lambda exc, s: print('{}: "{}"'.format(exc, s), file=sys.stderr))

    paths = list(iterutil.unique_everseen(paths, os.path.normcase))

    if args.verbose:
        for s in paths:
            print(s)
    print('items matched: {}'.format(len(paths)))

    times = [wintime.get_file_time(s) for s in paths]

    try:
        input('press Enter to restore or Ctrl-C to abort... ')
        print('restore')
    except KeyboardInterrupt:
        print('abort')
        sys.exit(1)

    something_failed = False
    for path, (c,a,m) in zip(paths, times):
        if 'c' not in args.times:
            c = None
        if 'a' not in args.times:
            a = None
        if 'm' not in args.times:
            m = None
        try:
            wintime.set_file_time(path, c, a, m)
        except Exception as x:
            print('could not set times of "{}": {}'.format(path, x), file=sys.stderr)
            something_failed = True
    sys.exit(1 if something_failed else 0)


if __name__ == '__main__':
    main()
