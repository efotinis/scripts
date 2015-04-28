import argparse
import sys


def parse_args():
    DEF_CHARS = '-|+'

    ap = argparse.ArgumentParser(
        description='display a graphical ruler')
    add = ap.add_argument

    add('rulersize', type=int, default=79, nargs='?',
        help='total size; default: "%(default)s"')
    add('ticksize', type=int, default=10, nargs='?',
        help='numbered interval size; must be >0; default: "%(default)s"')
    add('subticksize', type=int, default=0, nargs='?',
        help='unnumbered interval size (0 for none); default: "%(default)s"')
    add('-c', dest='chars', default=DEF_CHARS,
        help='characters for ruler, tick, and subtick; default: "%(default)s"')

    args = ap.parse_args()

    if args.rulersize < 0:
        ap.error('total size must be >=0')
    if args.ticksize <= 0:
        ap.error('numbered interval size must be >0')
    if args.subticksize < 0:
        ap.error('unnumbered interval size must be >=0')

    s = args.chars[:3]
    if len(s) < len(DEF_CHARS):
        s += DEF_CHARS[len(s):]
    args.rulerchar, args.tickchar, args.subtickchar = s

    return args


if __name__ == '__main__':

    args = parse_args()
    
    # create a number print format with proper width (ie. ticksize)
    numfmt = "%%%dd" % args.ticksize
    
    # output number line (only full-width numbers)
    rng = range(args.ticksize, args.rulersize + 1, args.ticksize)
    print(''.join(numfmt % n for n in rng))
    
    setchr = lambda s, i, c: s[:i] + c + s[i+1:]

    # build ruler segment
    segment = args.rulerchar * args.ticksize
    if args.subticksize:
        rng = range(args.subticksize - 1, args.ticksize, args.subticksize)
        for n in rng:
            segment = setchr(segment, n, args.subtickchar)
    # set interval
    segment = setchr(segment, args.ticksize - 1, args.tickchar)
    
    # output graphical line
    full, part = divmod(args.rulersize, args.ticksize)
    print(segment * full + segment[:part])
