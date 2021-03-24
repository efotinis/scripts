"""Change console columns and fit window width."""

import argparse
import win32console

import console_stuff


def parse_args():
    ap = argparse.ArgumentParser(
        description='change console columns')
    add = ap.add_argument
    add('newcols', type=int, nargs='?',
        help='new column count; if missing, prints the current value')
    args = ap.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()

    stdout = win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)

    if args.newcols is None:
        info = stdout.GetConsoleScreenBufferInfo()
        print(info['Size'].X)
    else:
        try:
            console_stuff.set_full_width(stdout, args.newcols)
        except win32console.error:
            raise SystemExit('could not set specified buffer size')
        else:
            actual = stdout.GetConsoleScreenBufferInfo()['Size'].X
            if actual != args.newcols:
                msg = 'buffer columns set to {0} instead of requested {1}'
                raise SystemExit(msg.format(actual, args.newcols))
