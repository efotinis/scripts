"""Change console columns without affecting the window size."""

import argparse
import sys
import win32console

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
    info = stdout.GetConsoleScreenBufferInfo()
    if args.newcols is None:
        print('columns:', info['Size'].X)
        sys.exit()

    # need to restore window size in case of error
    org_rect = info['Window']

    # new window rect, limited by largest possible
    win_height = info['Window'].Bottom - info['Window'].Top + 1
    win_x_max = stdout.GetLargestConsoleWindowSize().X
    win_rect = win32console.PySMALL_RECTType(
        0, 0, min(args.newcols, win_x_max)-1, win_height - 1)

    # try requested columns and catch errors later
    # (max seems to be 32K-2, but min depends on UI settings)
    buf_coord = win32console.PyCOORDType(args.newcols, info['Size'].Y)

    try:
        if args.newcols < info['Size'].X:
            stdout.SetConsoleWindowInfo(True, win_rect)
            stdout.SetConsoleScreenBufferSize(buf_coord)
        elif args.newcols > info['Size'].X:
            stdout.SetConsoleScreenBufferSize(buf_coord)
            stdout.SetConsoleWindowInfo(True, win_rect)
        else:
            pass
    except win32console.error:
        # probably too small buffer; restore window
        stdout.SetConsoleWindowInfo(True, org_rect)
        sys.exit('could not set columns')
