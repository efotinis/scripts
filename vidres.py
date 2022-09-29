"""List video resolutions."""

import argparse
import fractions
import json

import windisplay


def parse_args():
    ap = argparse.ArgumentParser(
        description='list supported video resolutions')
    add = ap.add_argument
    add('-r', dest='ratios', metavar='X:Y', action='append', type=ratio,
        help='ratio to display; default is all; multiple allowed')
    add('-b', dest='bare', action='store_true',
        help='bare output (no header)')
    add('-m', dest='mpsort', action='store_true',
        help='sort by MP; default is by width,height')
    add('-j', dest='json', action='store_true',
        help='output in JSON')
    return ap.parse_args()


def ratio(s):
    x, y = s.split(':')
    return fractions.Fraction(int(x), int(y))


def ratio_str(r):
    return '{}:{}'.format(r.numerator, r.denominator)


'''
sample ratio counts on my card:
    8 4/3
    6 8/5
    3 16/9
    2 5/4
    1 3/2
    1 85/48
    1 85/64
    1 222/125
    1 53/30
    1 683/384
    1 5/3
'''


if __name__ == '__main__':
    args = parse_args()
    modes_xy = list(set((mode.PelsWidth, mode.PelsHeight)
                        for mode in windisplay.modes()))
    if args.mpsort:
        modes_xy.sort(key=lambda xy: xy[0] * xy[1])
    else:
        modes_xy.sort()

    if not args.bare and not args.json:
        print('horz vert    MP  ratio  x:y')
        print('---- ----  ----  -----  ---------')
    for x, y in modes_xy:
        ratio = fractions.Fraction(x, y)
        if args.ratios is None or ratio in args.ratios:
            mp = x*y/1000000
            if args.json:
                d = {
                    'Width': x,
                    'Height': y,
                    'Megapixel': mp,
                    'Ratio': x/y,
                    'IntRatio': [ratio.numerator, ratio.denominator]
                }
                print(json.dumps(d))
            else:
                print('%4d %4d  %.2f  %.3f  %s' % (x, y, mp, x/y, ratio_str(ratio)))
