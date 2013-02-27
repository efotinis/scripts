"""Download a list of URLs."""

import os
import sys
import argparse
import urllib2
import urlparse
import random
import time

import CommonTools


def parse_args():
    ap = argparse.ArgumentParser(
        description='Download a list of URLs.',
        epilog='Multiple URL parameters, list files, and input from STDIN are allowed and will be added in that order.',
        add_help=False)
    _add = ap.add_argument

    _add('urls', nargs='*', metavar='URL',
         help='input URLs')
    _add('-l', dest='listfiles', action='append',
         help='text file with input URLs (one per line)')
    _add('-L', dest='stdinfiles', action='store_true',
         help='read input URLs from STDIN (one per line)')
    _add('-o', dest='outdir', default='.',
         help='output dir; default is "%(default)s"')
    _add('-s', dest='shuffle', action='store_true',
         help='shuffle input URLs order before downloading')
    _add('-?', action='help',
        help='this help')

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


if __name__ == '__main__':
    args = parse_args()

    okcount = skipcount = errcount = 0
    time_sec = time.time()
    bytes = 0

    try:
        for i, url in enumerate(args.urls):
            print '(%d/%d) %s ...' % (i + 1, len(args.urls), url),
            local = os.path.basename(urlparse.urlsplit(url).path)
            local = os.path.join(args.outdir, local)
            if os.path.exists(local):
                print 'SKIP'
                skipcount += 1
            else:
                try:
                    data = urllib2.urlopen(url).read()
                    open(local, 'wb').write(data)
                    bytes += len(data)
                except (urllib2.URLError, IOError) as err:
                    print 'ERROR'
                    print >>sys.stderr, 'could not get "%s"; dest: "%s"; reason: "%s"' % (url, local, err)
                    errcount += 1
                else:
                    print 'OK'
                    okcount += 1
    except KeyboardInterrupt:
        print 'canceled by user'

    time_sec = time.time() - time_sec

    print
    print 'downloaded:', okcount
    print '   skipped:', skipcount
    print '    errors:', errcount
    print '     total:', len(args.urls)
    print '      time: %.0f s' % time_sec
    print '      size: %s' % CommonTools.prettysize(bytes)
    print '     speed: %s/s' % CommonTools.prettysize(bytes / time_sec if time_sec else 0)

    sys.exit(1 if errcount else 0)
