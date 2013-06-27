"""Single file incremental backup.

Useful for all those programs that habitually munge up their config or stat
files (hello Minecraft... hello Opera extensions...).

A new copy of the source file with a UTC timestamp name is created when its
contents change (checked by their MD5 hash). An entry is added to a version log
whenever the backup runs (whether a file copy is made or not). The log contains
the source file's creation and modification times (Unix UTC timestamp), the
MD5 hash, and the name of the stored file.

Notes:
- Only the file contents are saved. All attributes and metadata are lost.
  However, the file times can be retrieved from the log.
- The actual data files are not needed (only the log is checked), so they can
  be archived.
"""

import argparse
import hashlib
import os
import time
##DEST_DIR = r'D:\backups\to-read sites Opera ext'
##SRC_FILE = os.path.expandvars(r'%LocalAppData%\Opera\Opera\widgets\wuid-4d2bd7bd-8287-0731-0242-55eae1724136\pstorage\00\04\00000000')


class EmptyLogError(Exception):
    pass


def get_last_log_entry(f):
    """Return (time created, time modified, MD5 sig, name)."""
    s = ''
    for s in log:
        pass
    if not s:
        raise EmptyLogError
    ctime, mtime, sig, name = s.split(None, 3)
    return float(ctime), float(mtime), sig, name


def get_current_timestamp_utc():
    """'YYYYMMDD-hhmmssxx'"""
    sec = round(time.time(), 2)  # round to 1/100ths of a second
    sec, fract = divmod(sec, 1)  # split int & fractional seconds
    s1 = time.strftime('%Y%m%d-%H%M%S', time.gmtime(sec))
    s2 = '%02d' % (fract * 100)
    return s1 + s2


def parse_args():
    ap = argparse.ArgumentParser(
        description='backup a single file incrementally')
    add = ap.add_argument
    add('source', help='source file path')
    add('destdir', help='distination directory')
    return ap.parse_args()


if __name__ == '__main__':
    args = parse_args()
    if not os.path.exists(args.source):
        sys.exit('source file does not exist')
    if not os.path.exists(args.destdir):
        os.makedirs(args.destdir)

    # get current info
    cur_ctime = os.path.getctime(args.source)
    cur_mtime = os.path.getmtime(args.source)
    cur_data = open(args.source, 'rb').read()
    cur_sig = hashlib.md5(cur_data).hexdigest()
    cur_name = get_current_timestamp_utc()

    log = open(os.path.join(args.destdir, 'version.log'), 'a+')

    # determine if file has changed and log current info
    try:
        last_ctime, last_mtime, last_sig, last_name = get_last_log_entry(log)
        changed = cur_sig.lower() != last_sig.lower()
    except EmptyLogError:
        changed = True
    print >>log, cur_ctime, cur_mtime, cur_sig, cur_name

    # make copy if needed
    if not changed:
        print 'no changes detected'
    else:
        with open(os.path.join(args.destdir, cur_name), 'wb') as f:
            f.write(cur_data)
        print 'changed file saved'
