#!python
"""File hash calculator."""

from __future__ import print_function
import argparse
import binascii
import glob
import hashlib
import itertools
import os
import struct
import sys

try:
    from itertools import izip
except ImportError:
    izip = zip

import efutil
import console_stuff
import fileutil


HASH_TYPES = hashlib.algorithms_available | set(['crc32'])
DEFAULT_HASH_TYPE = 'md5'
DEFAULT_BUFFER_SIZE = 64 * 1024


class Crc32:
    """CRC32 digest using the hashlib interface."""
    digest_size = 4
    def __init__(self, data=''):
        self.value = binascii.crc32(data)
    def update(self, data):
        self.value = binascii.crc32(data, self.value)
    def digest(self):
        return struct.pack('>L', self.value & 0xffffffff)
    def hexdigest(self):
        return binascii.hexlify(self.digest())
    def copy(self):
        # the only state of CRC32 is its current value
        ret = Crc32()
        ret.value = self.value
        return ret


##def get_hash_object(name, string=''):
##    if name == 'crc32':
##        return Crc32(string)
##    else:
##        return hashlib.new(name, string)


def parse_args():
    parser = argparse.ArgumentParser(
        description='calculate file hashes',
        epilog='size and offset values can be a float with an SI unit suffix')

    add = parser.add_argument

    add('files', metavar='FILE', nargs='+',
        help='input file (glob pattern)')
    add('-t', dest='hash_type', choices=HASH_TYPES,
        default=DEFAULT_HASH_TYPE, metavar='TYPE',
        help='hash type; one of ' + ','.join(sorted(HASH_TYPES)) + '; '
             'default: %(default)s')
    add('-o', dest='offset', type=efutil.size_arg, default=0,
         help='starting file offset; default: %(default)s')
    add('-l', dest='length', type=efutil.size_arg, default=-1,
         help='number of bytes to process (or -1 for all); default: %(default)s')
    add('-b', dest='buflen', type=efutil.size_arg, default=DEFAULT_BUFFER_SIZE,
         help='read buffer size; default: %(default)s')
    add('-u', dest='uppercase', action='store_true',
         help='output hashes in uppercase')
    add('-i', dest='invert', action='store_true',
         help='invert output by displaying the file name first; '
              'useful for creating SFV files')
    add('-v', dest='verify', 
         help='list of comma-separated hashes to check against the specified files')
    add('-P', dest='progress', action='store_false', default=True,
         help='do not display progress indicator; '
              'set automatically when STDOUT is not a console')
    add('-G', dest='glob', action='store_false', default=True,
         help='disable globbing of input paths')

    args = parser.parse_args()

    if not console_stuff.iscon():
        args.progress = False

    if args.offset < 0:
        parser.error('offset must be >= 0')
    if args.length < -1:
        parser.error('number of bytes must be >= -1')
    if args.buflen <= 0:
        parser.error('buffer size must be > 0')

    if args.hash_type == 'crc32':
        args.hash_type = Crc32
    else:
        args.hash_type = lambda s=args.hash_type: hashlib.new(s)

    if args.verify:
        strsize = args.hash_type().digest_size * 2
        a = []
        for s in args.verify.split(','):
            s = s.strip().lower()
            if len(s) != strsize:
                parser.error('invalid verify hash size: "%s"' % s)
            try:
                int(s, 16)
            except ValueError:
                parser.error('invalid verify hash value: "%s"' % s)
            a += [s]
        args.verify = a

    return args


def calc_read_size(fsize, offset, length):
    """Calculate the actual byte count given the file size and read offset/length."""
    if offset < 0:
        offset = 0
    if offset > fsize:
        offset = fsize
    if length < 0:
        length = fsize - offset
    end = offset + length
    if end > fsize:
        end = fsize
    return end - offset


class ProgressIndicator(object):
    """Temporary progress indicator with percent value and spinner."""
    def __init__(self, name, total):
        self.current = 0
        self.total = total
        self.spinner = itertools.cycle('/-\\|')
        # NOTE: if name is too long, SamePosOutput will only erase the last row
        print(name, '... ', end='')
        self.spo = console_stuff.SamePosOutput()
    def update(self, n):
        self.current += n
        self.spo.restore()
        percent = (100.0 * self.current / self.total if self.total else 0)
        print('%.0f%% %s' % (percent, next(self.spinner)))
    def clear(self):
        self.spo.pos.X = 0  # include the name
        self.spo.restore(True)
        sys.stdout.write('')  # softspace kludge


def calc_hash(fp, offset, size, hash, buflen, progress):
    """Calculate stream data digest. May raise IOError or EOFError."""
    try:
        fp.seek(offset)
        bytes_left = size
        while bytes_left > 0:
            buf = fp.read(min(buflen, bytes_left))
            if buf == '':
                raise EOFError('no enough data')
            hash.update(buf)
            if progress:
                progress.update(len(buf))
            bytes_left -= len(buf)
    finally:
        if progress:
            progress.clear()
    return hash.hexdigest()


class EmptyGlobHandler(object):
    def __init__(self):
        self.occured = False
    def __call__(self, patt):
        print('no matches for "%s"' % patt, file=sys.stderr)
        self.occured = True
        

def files_gen(patterns, empty_handler=None):
    """Generate file paths from a list of glob patterns.

    If specified, empty_handler is called with a single argument,
    which represents a pattern with no matches.
    """
    for patt in patterns:
        emtpy = True
        for s in glob.glob(patt):
            if os.path.isfile(s):
                yield s
                emtpy = False
        if emtpy and empty_handler:
            empty_handler(patt)


def main(args):
    # FIXME: iscon() still returns True if running on console with stdout redirected.
    # It only returns False on PythonWin.
##    if console_stuff.iscon(sys.stdout.fileno()):
##        import win32api
##        win32api.MessageBeep()
##    
##    sys.exit()

    empty_globs = EmptyGlobHandler()
    filepaths = files_gen(args.files, empty_globs) if args.glob else args.files

    if args.verify:
        # check for length match early
        filepaths = list(filepaths)
        if len(filepaths) != len(args.verify):
            sys.exit('number of specified verify hashes does not match file count')

    error_occured = False
    expected_hashes = args.verify or itertools.repeat(None)

    for (path, expected_hash) in izip(filepaths, expected_hashes):
        try:
            fp = open(path, 'rb')
            hashobj = args.hash_type()
            total = calc_read_size(fileutil.fsize(fp), args.offset, args.length)
            progress = ProgressIndicator(path, total) if args.progress else None
            hash = calc_hash(fp, args.offset, total, hashobj, args.buflen, progress)
            if not expected_hash:
                if args.uppercase:
                    hash = hash.upper()
                if args.invert:
                    print(path, hash)
                else:
                    print(hash, path)
            else:
                if hash != expected_hash:
                    print('FAIL ', path)
                    print('hash mismatch for "%s": expected %s, got %s' % (path, expected_hash, hash),
                          file=sys.stderr)
                    error_occured = True
                else:
                    print('OK   ', path)
        except (IOError, EOFError) as x:
            print('error while hashing "%s": %s' % (path, x), file=sys.stderr)

    if empty_globs.occured:
        error_occured = True

    sys.exit(1 if error_occured else 0)


if __name__ == '__main__':
    try:
        main(parse_args())
    except KeyboardInterrupt:
        sys.exit('cancelled')
