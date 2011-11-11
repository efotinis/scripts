# File hash calculator.
#
# TODO: only allow DOS-style wildcards by default (add switch -g for explicit globbing)
# - Add a switch for strict error checking (exit on first range or file error).
# TODO: report glob patterns that match no files (currently they are silently ignored)

import os
import sys
import hashlib
import binascii
import struct
import re
import glob
import itertools
import argparse
import copy

import console_stuff
import fileutil
import CommonTools
import optparseutil


HASH_TYPES = set(hashlib.algorithms + ('crc32',))
DEFAULT_HASH_TYPE = 'md5'
DEFAULT_BUFFER_SIZE = 64 * 1024


def size_param(s):
    """Custom 'size' type checker for argparse.

    Parses a string of a float with an optional size prefix and returns a truncated int.
    """
    UNITS = 'kmgtpezy'
    if not s:
        raise argparse.ArgumentTypeError('empty size value')

    unit = UNITS.find(s[-1].lower())
    if unit == -1:
        number, factor = s, 1
    else:
        number, factor = s[:-1], 1024 ** (unit + 1)

    try:
        return int(float(number) * factor)
    except ValueError:
        raise argparse.ArgumentTypeError('bad size value: "%s"' % number)


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
        epilog='size and offset values can be a float with an SI unit suffix',
        add_help=False)

    add = parser.add_argument
    add('files', metavar='FILE', nargs='+',
        help='input file (glob pattern)')
    add('-t', dest='hashFactory', choices=HASH_TYPES,
        default=DEFAULT_HASH_TYPE, metavar='TYPE',
        help='hash type; one of ' + ','.join(sorted(HASH_TYPES)) + '; '
             'default: %(default)s')
    add('-o', dest='offset', type=size_param, default=0,
         help='starting file offset; default: %(default)s')
    add('-l', dest='length', type=size_param, default=-1,
         help='number of bytes to process (or -1 for all); default: %(default)s')
    add('-b', dest='buflen', type=size_param, default=DEFAULT_BUFFER_SIZE,
         help='read buffer size; default: %(default)s')
    add('-u', dest='ucase', action='store_true',
         help='output uppercase hex digits')
    add('-i', dest='invert', action='store_true',
         help='invert output by displaying the file name first; '
              'useful for creating SFV files')
    add('-v', dest='verify', 
         help='list of comma-separated hashes to check against the specified files')
    add('--np', dest='progress', action='store_false', default=True,
         help='do not display progress indicator; '
              'set automatically when STDOUT is not a console')
    add('-?', action='help', help='this help')

    args = parser.parse_args()

    if not console_stuff.iscon():
        args.progress = False

    if args.offset < 0:
        parser.error('offset must be >= 0')
    if args.length < -1:
        parser.error('number of bytes must be >= -1')
    if args.buflen <= 0:
        parser.error('buffer size must be > 0')

    if args.hashFactory == 'crc32':
        args.hashFactory = Crc32
    else:
        args.hashFactory = lambda s=args.hashFactory: hashlib.new(s)

    if args.verify:
        strsize = args.hashFactory().digest_size * 2
        a = []
        for s in args.verify.split(','):
            if len(s) != strsize:
                parser.error('invalid verify hash size: "%s"' % s)
            try:
                a += [int(s, 16)]
            except ValueError:
                parser.error('invalid verify hash: "%s"' % s)
        args.verify = a

    args.files = [unicode(s, 'mbcs') for s in args.files]
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


def fileSig(s, opt, verify=None):
    """Calculate and print file hash.

    If 'verify' is set, tests and prints whether hash matches.
    """
    try:
        f = open(s, 'rb')
        if opt.progress:
            progressBytesToRead = calc_read_size(fileutil.fsize(f), opt.offset, opt.length)
            progressBytesRead = 0
            spinner = itertools.cycle('/-\\|')
            print s, '... ',
            spo = console_stuff.SamePosOutput()
        f.seek(opt.offset)
        d = opt.hashFactory()
        bytesToGo = opt.length
        while bytesToGo != 0:
            buf = f.read(opt.buflen)
            if buf == '': break
            if bytesToGo != -1 and len(buf) > bytesToGo:
                buf = buf[:bytesToGo]
            d.update(buf)
            if opt.progress:
                progressBytesRead += len(buf)
                spo.restore()
                percent = (progressBytesRead*100/progressBytesToRead
                           if progressBytesToRead else 0)
                print str(percent) + '%', spinner.next()
            if bytesToGo != -1:
                bytesToGo = bytesToGo - len(buf)
        if opt.progress:
            spo.pos.X = 0
            spo.restore(True)
        if bytesToGo > 0:
            print 'Reached EOF while reading "%s"' % s
        else:
            digest = d.hexdigest()
            if opt.ucase:
                digest = digest.upper()
            # the empty write() prevents SamePosOutput from
            # accidentally printing at col 1 (instead of 0)
            sys.stdout.write('')

            if verify:
                digest = '   OK   ' if verify == int(digest, 16) else '**FAIL**'
            
            if opt.invert:
                print s, digest
            else:
                print digest, s
    except IOError as x:
        fname = x.filename
        if fname is None:
            fname = s
        CommonTools.errln(x.strerror + ': ' + s)


def files_gen(patterns, not_matched_handler=None):
    """Generate file paths from list of file glob patterns."""
    for patt in patterns:
        matched_something = False
        for s in glob.glob(patt):
            if os.path.isfile(s):
                yield s
                matched_something = True
        if not matched_something and not_matched_handler is not None:
            not_matched_handler(patt)


def not_matched_handler(patt):
    print >>sys.stderr, 'WARNING: no matches for "%s"' % patt
        

if __name__ == '__main__':
    args = parse_args()
##    print args
##    sys.exit()

    # TODO: notify user if a pattern has no matches
    filepaths = list(files_gen(args.files, not_matched_handler))

    if args.verify:
        if len(args.verify) != len(filepaths):        
            sys.exit('number of specified verify hashes does not match file count')
        for s, sig in zip(filepaths, args.verify):
            fileSig(s, args, verify=sig)
    else:
        for s in filepaths:
            fileSig(s, args)
