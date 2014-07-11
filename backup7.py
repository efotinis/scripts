"""7-Zip-based full/differential backup."""

import os
import sys
import argparse
import datetime
import subprocess
import getpass
import _winreg


def get_utc_timestamp():
    """Get current UTC time as 'YYYYMMDD-hhmmssxx'."""
    return datetime.datetime.strftime(
        datetime.datetime.utcnow(), '%Y%m%d-%H%M%S%f')[:-4]


def get_7zip_path():
    """Get the full path of the 7z.exe using the Registry install dir."""
    k = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, 'Software\\7-Zip')
    try:
        return os.path.join(_winreg.QueryValueEx(k, 'Path')[0], '7z.exe')
    finally:
        k.Close()


def gen_list_of_full_backups(base, timestamp_len):
    """Find full backups, given a base path and the timestamp length.

    Searches .7z files, with names starting with the base and ending with
    '-full'. The base must include the full directory and name prefix; for
    example, 'C:\\backups\\documents-' will find all files matching:
    'C:\\backups\\documents-XYZ-full.7z', where XYZ is any string of
    timestamp_len size.
    """
    parent, namebase = os.path.split(base)
    for s in os.listdir(parent):
        stem, ext = os.path.splitext(s)
        if os.path.normcase(ext) == '.7z':
            if stem[-5:].lower() == '-full':
                s2 = stem[:-5]
                if s2[:-timestamp_len] == namebase:
                    yield os.path.join(parent, s)


def parse_args():
    ap = argparse.ArgumentParser(
        description='7-Zip-based full/differential backup')
    add = ap.add_argument

    add('src', help='source dir')
    add('dst', help='destination; may include a directory path (abs/rel) and '
        'a file name prefix; output archives include a UTC timestamp and '
        'a suffix specifying full or diff backup')
    add('-d', dest='differential', action='store_true',
        help='perform differential backup; uses the last full backup deduced '
        'from destination argument; if a previous full backup is not found, '
        'a full backup is performed instead')
    add('-b', dest='blocksize', default='32m',
        help='set solid mode block size; see 7-Zip -ms switch; '
        'default: %(default)s')
    add('-x', dest='exclude', action='append', default=[],
        help='exclude items; see 7-Zip -x switch')
    add('-p', dest='password',
        help='set password; in case of diff backup, the same password is used '
        'for both the base and output archive')
    add('-P', dest='password_prompt', action='store_true',
        help='prompt for password interactively')

    args = ap.parse_args()

    if not os.path.isdir(args.src):
        ap.error('source directory does not exist: "%s"' % args.src)

    if args.password_prompt:
        try:
            args.password = getpass.getpass('password: ')
        except KeyboardInterrupt:
            ap.error('password entry cancelled')

    return args



if __name__ == '__main__':
    args = parse_args()

    sevenzip_path = get_7zip_path()
    timestamp = get_utc_timestamp()
    full_backups = list(gen_list_of_full_backups(args.dst, len(timestamp))) \
                   if args.differential else None

    # determine base (optional) and output archive paths;
    if args.differential and full_backups:
        output = args.dst + timestamp + '-diff.7z'
        base = full_backups[-1]
        print 'last full backup found:', base
    else:
        if args.differential:
            print 'no previous full backups found; switching to full backup'
            args.differential = False
        output = args.dst + timestamp + '-full.7z'
        base = None

    options = [
        '-ms=%s' % args.blocksize,
        '-mtc=on',
        '-mhe=on',
        '-ssw']
    if args.password is not None:
        options += ['-p' + args.password]
    if args.exclude:
        options += ['-x' + s for s in args.exclude]

    # ensure archive paths are absolute, since we need to change the CWD
    # of 7-Zip to the input directory to store proper relative paths
    output = os.path.abspath(output)
    if base is not None:
        base = os.path.abspath(base)

    if args.differential:
        options = [sevenzip_path, 'u', base] + options + [
            '-u-', '-up0q3r2x2y2z0w2!' + output, '.']
    else:
        options = [sevenzip_path, 'a', output] + options + ['.']

    os.chdir(args.src)
    sys.exit(subprocess.call(options))
