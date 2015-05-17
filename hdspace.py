"""Display hard disk space usage bars."""

import argparse
import win32file
import win32con

import diskutil
import efutil


def bar(full, total, scale, width):
    a = int(round(float(full) / scale * width))
    b = int(round(float(total) / scale * width))
    return '#' * a + '-' * (b - a)


def parse_args():
    ap = argparse.ArgumentParser(
        description='show fixed disk space usage')
    add = ap.add_argument
    return ap.parse_args()


if __name__ == '__main__':
    args = parse_args()

    hdds = [s + ':' for s in diskutil.logical_drives(win32con.DRIVE_FIXED)]
    drive_size_free = [(s,) + tuple(win32file.GetDiskFreeSpaceEx(s)[1:]) for s in hdds]

    maxsize = max(s for d,s,f in drive_size_free)

    BARSIZE = 50
    print '       size           free'
    print '  --------- --------------'
    for drive, size, free in drive_size_free:
        print '{} {:>9} {:>9} {:>4.0%} [{}]'.format(
            drive[:1],
            efutil.prettysize(size),
            efutil.prettysize(free),
            float(free) / size,
            bar(size - free, size, maxsize, BARSIZE))

    total_size = sum(s for d,s,f in drive_size_free)
    total_free = sum(f for d,s,f in drive_size_free)
    print '* {:>9} {:>9} {:>4.0%}'.format(
        efutil.prettysize(total_size),
        efutil.prettysize(total_free),
        float(total_free) / total_size)
