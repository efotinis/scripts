#!python3
"""Download a list of URLs."""

import os
import sys
import argparse
import urllib.request
import urllib.parse
import random
import time

import efutil


def parse_args():
    ap = argparse.ArgumentParser(
        description='Download a list of URLs.',
        epilog='Multiple URL parameters, list files, and input from STDIN '
        'are allowed and will be added in that order.')
    add = ap.add_argument
    add('urls', nargs='*', metavar='URL',
        help='input URLs')
    add('-l', dest='listfiles', action='append',
        help='text file with input URLs (one per line)')
    add('-L', dest='stdinfiles', action='store_true',
        help='read input URLs from STDIN (one per line)')
    add('-o', dest='outdir', default='.',
        help='output dir; default is "%(default)s"')
    add('-s', dest='shuffle', action='store_true',
        help='shuffle input URLs order before downloading')

    args = ap.parse_args()

    # add URLs from list files
    for fn in args.listfiles or []:
        try:
            args.urls += [s.rstrip('\n') for s in open(fn)]
        except IOError:
            ap.error('could not read listfile: "%s"' % fn)
    del args.listfiles

    # add URLs from STDIN
    if args.stdinfiles:
        for s in sys.stdin:
            args.urls += [s.rstrip('\n')]

    # shuffle urls
    if args.shuffle:
        random.shuffle(args.urls)
    del args.shuffle

    return args


class DownloadMeter:
    def __init__(self, total=-1):
        self.totalbytes = total
        self.donebytes = 0
        self.starttime = time.monotonic()
    def add(self, n):
        self.donebytes += n
    def __str__(self):
        if self.totalbytes >= 0:
            ratio = self.donebytes / self.totalbytes if self.totalbytes else 0
            dt = time.monotonic() - self.starttime
            speed = self.donebytes / dt if dt else 0
            eta = (self.totalbytes - self.donebytes) / speed if speed else 0
            return '{}, {:.0%}, ETA: {}'.format(efutil.prettysize(self.donebytes), ratio, efutil.timefmt(eta))
        else:
            return '{}'.format(efutil.prettysize(self.donebytes))


if __name__ == '__main__':
    args = parse_args()

    okcount = skipcount = errcount = 0
    time_sec = time.time()
    bytes = 0

    try:
        for i, url in enumerate(args.urls):
            print('(%d/%d) %s ...' % (i + 1, len(args.urls), url), end=' ', flush=True)
            local = os.path.basename(urllib.parse.urlsplit(url).path)
            local = os.path.join(args.outdir, local)
            if os.path.exists(local):
                print('SKIP')
                skipcount += 1
            else:
                try:
##                    data = urllib.request.urlopen(url).read()
##                    open(local, 'wb').write(data)
##                    bytes += len(data)
                    BLOCKSIZE = 65536
                    status = ''
                    with urllib.request.urlopen(url) as resp, open(local, 'wb') as f:
                        total = int(resp.headers['Content-Length'])
                        dm = DownloadMeter(int(resp.headers.get('Content-Length', '-1')))
                        while True:
                            block = resp.read(BLOCKSIZE)
                            if not block:
                                break
                            f.write(block)
                            bytes += len(block)
                            #status = '{} ({:.0%})'.format(efutil.prettysize(bytes), bytes / total)
                            #print(status + '\b'*len(status), end='', flush=True)
                            dm.add(len(block))
                            print(dm, end='\r', flush=True)
                    print(' '*len(status)+'\b'*len(status), end='')
                except (urllib.request.URLError, IOError) as err:
                    print('ERROR')
                    print('could not get "%s"; dest: "%s"; reason: "%s"' % (url, local, err), file=sys.stderr)
                    errcount += 1
                else:
                    print('OK')
                    okcount += 1
    except KeyboardInterrupt:
        print('canceled by user')

    time_sec = time.time() - time_sec

    print()
    print('downloaded:', okcount)
    print('   skipped:', skipcount)
    print('    errors:', errcount)
    print('     total:', len(args.urls))
    print('      time: %.0f s' % time_sec)
    print('      size: %s' % efutil.prettysize(bytes))
    print('     speed: %s/s' % efutil.prettysize(bytes / time_sec if time_sec else 0))

    sys.exit(1 if errcount else 0)
