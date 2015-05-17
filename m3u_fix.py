"""Fix M3U/M3U8 playlists when files are moved around."""

from __future__ import print_function
import argparse
import codecs
import io
import os
import sys

import six


def parse_args():
    ap = argparse.ArgumentParser(
        description='fix M3U/M3U8 playlists when files are moved around',
        epilog='files are matched using just the base name, since M3U '
        'playlists contain no other info; files that are not found remain '
        'unchanged (a warning is printed); exit codes: 0=ok, 1=error, '
        '2=bad param, 3=some files not found')
    
    add = ap.add_argument
    add('-d', dest='lookupDirs', action='append', default=['.'],
        help='directory to search files into (recursively); '
        'multiple switches are allowed; default is "."')
    add('-s', dest='silent', action='store_true',
        help='silent mode; select a random file when multiple are found '
        'with the same name, instead of asking user')
    add('-D', dest='noSummary', action='store_true',
        help='do not print summary details')
    add('--bom', dest='bom', action='store_true',
        help='write BOM in M3U8 output; some players require it, '
        'others ignore it, and others choke on it')
    add('source', help='input playlist')
    add('dest', nargs='?', help='output playlist; if omitted, output is '
        'written to STDOUT; if the extension is M3U8, UTF-8 encoding is used')
    args = ap.parse_args()
    args.lookupDirs = map(six.text_type, args.lookupDirs)
    for s in args.lookupDirs:
        if not os.path.isdir(s):
            ap.error('bad lookup dir: ' + s)
    return args


def process(playlist, lookupDirs, notFoundHandler, multipleFoundHandler):
    """Process a playlist; return new playlist and number of files not found."""
    baseNames = {}
    for s in playlist:
        baseNames[os.path.basename(s).lower()] = []
    for d in lookupDirs:
        for dpath, dirs, files in os.walk(d):
            for s in files:
                base = os.path.basename(s).lower()
                if base in baseNames:
                    baseNames[base] += [os.path.join(dpath, s)]
    notFoundCnt = 0
    for i in range(len(playlist)):
        base = os.path.basename(playlist[i]).lower()
        a = baseNames[base]
        if not a:
            playlist[i] = notFoundHandler(playlist[i])
            notFoundCnt += 1
        elif len(a) == 1:
            playlist[i] = a[0]
        else:
            playlist[i] = multipleFoundHandler(playlist[i], a)
    return playlist, notFoundCnt


def hasUtf8Bom(path):
    with open(path, 'rb') as f:
        if f.read(3) == codecs.BOM_UTF8:
            return True
    return False


def read_input(source):
    """Read playlist items."""
    ext = os.path.splitext(source)[1]
    utf8 = ext.lower() == '.m3u8' or hasUtf8Bom(source)
    with io.open(source, encoding='utf-8' if utf8 else 'mbcs') as f:
        return [s.rstrip('n') for s in f]


def write_output(dest, writeBom, playlist):
    """Write playlist items."""
    if dest is None:
        outName = '<STDOUT>'
        utf8 = False
        f = sys.stdout
    else:
        outName = dest
        utf8 = os.path.splitext(outName)[1].lower() == '.m3u8'
        f = io.open(outName, 'w', encoding='utf-8' if utf8 else 'mbcs')
    if utf8 and writeBom:
        f.write(u'\uFEFF')
    for s in playlist:
        print(s, file=f)
    if f is not sys.stdout:
        f.close()


if __name__ == '__main__':
    args = parse_args()

    try:
        read_input(args.source)
    except IOError as x:
        sys.exit('could not read source; %s' % x)

    def notFound(s):
        print('no match for "%s"' % s)
        return s
    def multipleFoundChoose(s, a):
        print('multiple matches for "%s"' % s)
        for i, fpath in enumerate(a):
            print('  %d: %s' % (i+1, fpath))
        print('  0: leave unchanged')
        while True:
            s = raw_input('choose:')
            try:
                answer = int(s)
                if answer == 0:
                    return s
                elif 1 <= answer <= len(a):
                    return a[answer - 1]
            except ValueError:
                pass
    def multipleFoundPickRandom(s, a):
        return a[0]

    multFnd = multipleFoundPickRandom if args.silent else multipleFoundChoose 
    playlist, notFoundCnt = process(playlist, args.lookupDirs, notFound, multFnd)

    try:
        write_output(args.dest, args.bom, playlist)
    except IOError as x:
        sys.exit('could not write output; %s' % x)

    if not args.noSummary:
        print('entries: %d' % len(playlist))
        print('not found: %d' % notFoundCnt)

    sys.exit(3 if notFoundCnt else 0)
