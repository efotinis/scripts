#!python3
"""Download a list of URLs."""

import argparse
import contextlib
import os
import random
import sys
import urllib.parse
import warnings

import urllib3

import dlmgr
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
    add('-V', '--no-verify', dest='noverify', action='store_true',
        help='skip server certificate validation')

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


def output_result_line(path, status):
    """Replace previous console line with nicely formatted result."""
    os.system('d:/projects/eatlines.exe 1')
    print(status.rjust(8), path)


@contextlib.contextmanager
def disable_ssl_warnings():
    """Source: https://stackoverflow.com/a/69434599"""
    import warnings
    import urllib3
    with warnings.catch_warnings():
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        yield


if __name__ == '__main__':
    args = parse_args()

    okcount = skipcount = errcount = 0
    counters = dlmgr.Counters()

    try:
        for i, url in enumerate(args.urls, 1):
            print('[%d/%d] %s' % (i, len(args.urls), url))
            local = os.path.basename(urllib.parse.urlsplit(url).path)
            local = os.path.join(args.outdir, local)
            try:
                with warnings.catch_warnings():
                    if args.noverify:
                        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                    kwargs = {
                        'counters': counters,
                        'verify': not args.noverify
                    }
                    if dlmgr.download_with_resume(url, local, dlmgr.Status(), **kwargs):
                        output_result_line(url, 'done')
                        okcount += 1
                    else:
                        output_result_line(url, 'skipped')
                        skipcount += 1
            except Exception as err:
                output_result_line(url, 'failed')
                print('could not get "%s"; dest: "%s"; reason: "%s"' % (url, local, err), file=sys.stderr)
                errcount += 1
    except KeyboardInterrupt:
        print('cancelled')

    print()
    print('      done:', okcount)
    print('   skipped:', skipcount)
    print('    failed:', errcount)
    print(' cancelled:', len(args.urls) - (okcount + skipcount + errcount))
    print('     total:', len(args.urls))

    speed = counters.bytes / counters.seconds if counters.seconds else 0
    print('downloaded: {} in {} ({}/s)'.format(
        efutil.prettysize(counters.bytes),
        efutil.timefmt(counters.seconds),
        efutil.prettysize(speed)))

    sys.exit(1 if errcount else 0)
