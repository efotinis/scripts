import os
import sys
import time

import cmdLine

ERR_NO_SPACE_LEFT_ON_DEVICE = 28
ERR_PERMISSION_DENIED = 13


def fillFAT(drive):
    if drive[-1:] not in '\\/':
        drive += '\\'
    try:
        i = 0
        while True:
            s = os.path.join(drive, '%08d' % i)
            if not os.path.exists(s):
                file(s, 'wb').close()
            print i,
            i += 1
    except IOError, x:
        if x.errno == ERR_PERMISSION_DENIED:
            print 'No space left'
        else:
            raise

    return 0


class FileNameGen:
    def __init__(self, dir):
        self.dir = dir
        self.nextIndex = 0
    def next(self):
        while True:
            s = os.path.join(self.dir, '%08d' % self.nextIndex)
            self.nextIndex += 1
            if not os.path.exists(s):
                return s

    
def sizeFmtX(decimals=0):
    pass


def fillFile(drive, fileCnt, fileLen, bufSize, bufPatt):
    if drive[-1:] not in '\\/':
        drive += '\\'

    # make buffer
    buf = bufPatt
    while len(buf) < bufSize:
        buf *= 2
    buf = buf[:bufSize]
        
    KB = 1024

    fnameGen = FileNameGen(drive)
    totalBytesWritten = 0

    speedBytes = 0
    speedStartSec = time.time()
    printIntervalSec = 10

    try:
        for i in xrange(fileCnt):
            curFileBytesWritten = 0
            f = file(fnameGen.next(), 'wb')
            while True:
                f.write(buf)
                totalBytesWritten += len(buf)
                curFileBytesWritten += len(buf)
                speedBytes += len(buf)
                # print speed if needed            
                dt = time.time() - speedStartSec
                if dt >= printIntervalSec:
                    print 'Written: %5d KB - Speed: %6.2f KB/sec' % (totalBytesWritten / KB, float(speedBytes) / KB / dt)
                    speedBytes = 0
                    speedStartSec = time.time()
                if fileLen != -1 and curFileBytesWritten >= fileLen:
                    break
            f.close()
    except IOError, x:
        if x.errno == ERR_NO_SPACE_LEFT_ON_DEVICE:
            print 'No space left'
        else:
            raise
    
    return 0


def help():
    print """\
Disk burn-tester. By Elias Fotinis 2006-01-30.

FILLDISK drive /FAT
FILLDISK drive /FILE [/N:count] [/S:size] [/B:size] [/P:patt]

  drive  The target drive, e.g. "A:"
  /FAT   Fill FAT(s) by continuously creating many 0-size files.
  /FILE  Fill data area by continuously writting to a file.
  /N     File count. Default is 1.
  /S     File size. Default is -1, meaning unlimited.
  /B     Write buffer size. Default is 4K.
  /P     Pattern to use for writing. C-style string escapes can be used.
         It is repeated or truncated to fit the buffer size. Default is "\0".
"""
    return 0


def printErr(s):
    sys.stderr.write(s + '\n')


def main():
    opt = cmdLine.Options(sys.argv[1:])
    if '?' in opt:
        return help()
    
    if 'FAT' in opt and 'FILE' in opt:    
        printErr('Cannot specify both FAT and FILE switches.')
        return 1

    drives = opt.getAll('')
    opt.erase('')
    if not drives:
        printErr('No drive specified.')
        return 1
    elif len(drives) > 1:
        printErr('More than one drive specified.')
        return 1
    else:
        drive = os.path.splitdrive(drives[0])[0]

    if 'FAT' in opt:
        opt.erase('FAT')
        invalid = opt.switchSet()
        if invalid:
            printErr('Invalid switches: ' + ','.join(invalid))
            return 1
        return fillFAT(drive)
    elif 'FILE' in opt:
        opt.erase('FILE')
        try:
            fileCnt = cmdLine.parseSize(opt.getLast('N', '1'))
            if fileCnt < 0:
                fileCnt = 0
            fileLen = cmdLine.parseSize(opt.getLast('S', '-1'))
            if fileLen < -1:
                fileLen = -1
            bufSize = cmdLine.parseSize(opt.getLast('B', '4K'))
            if bufSize < 1:
                bufSize = 4096
        except cmdLine.SizeParamError, x:
            print x
            return 1
        bufPatt = opt.getLast('P', '\\0')
        if not bufPatt:
            bufPatt = '\0'
        opt.erase(['N', 'S', 'B', 'P'])
        invalid = opt.switchSet()
        if invalid:
            printErr('Invalid switches: ' + ','.join(invalid))
            return 1
        return fillFile(drive, fileCnt, fileLen, bufSize, bufPatt)
    else:        
        printErr('No function selected.')
        return 1


sys.exit(main())