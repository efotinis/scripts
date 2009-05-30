##import os
##import FindFileW
##import WinTime
##import time
##
##
##def attrToStr(attribs, empty=''):
##    flags = 'RHS?DAVNTPXCOIE?'
##    n = 1
##    ret = ''
##    for i in xrange(16):
##        ret += flags[i] if (attribs & n) else empty
##        n *= 2
##    return ret



##FILE_ATTRIBUTE_READONLY            = 1 <<  0
##FILE_ATTRIBUTE_HIDDEN              = 1 <<  1
##FILE_ATTRIBUTE_SYSTEM              = 1 <<  2
##FILE_ATTRIBUTE_DIRECTORY           = 1 <<  4
##FILE_ATTRIBUTE_ARCHIVE             = 1 <<  5
##FILE_ATTRIBUTE_DEVICE              = 1 <<  6
##FILE_ATTRIBUTE_NORMAL              = 1 <<  7
##FILE_ATTRIBUTE_TEMPORARY           = 1 <<  8
##FILE_ATTRIBUTE_SPARSE_FILE         = 1 <<  9
##FILE_ATTRIBUTE_REPARSE_POINT       = 1 << 10
##FILE_ATTRIBUTE_COMPRESSED          = 1 << 11
##FILE_ATTRIBUTE_OFFLINE             = 1 << 12
##FILE_ATTRIBUTE_NOT_CONTENT_INDEXED = 1 << 13
##FILE_ATTRIBUTE_ENCRYPTED           = 1 << 14


##n = 0
##for dir, info in FindFileW.walk('R:\\'):
##    #print os.path.join(dir, info.name)
##    n -= info.size

##a = FindFileW.dirList(r'c:\temp\foo')[0]
##
##ft = WinTime.FILETIME()
##ft.init(a.create)
##ft = WinTime.toLocalFileTime(ft)
##xxxxx = long(ft)
##st = WinTime.SYSTEMTIME()
##WinTime.FileTimeToSystemTime(ft, st)
## 
##print
##print a.name
##print st
##
##x = xxxxx - long(WinTime.pythonEpochToFileTime())
##x /= 10000000
##print time.gmtime(x)
##
### Thursday, 15 March, 2007, 01:02:00


##a = FindFileW.dirList('r:\\')[0]
##print a.name


##for x in FindFileW.dirList('c:\\'):
##    print attrToStr(x.attr, '-'), x.name
##
##    
##
##
##GetDiskFreeSpaceEx(
###win32file.GetDriveType('C:\\')


import sys


def showHelp():
    print """\
params:  srcDir outFile descr"""

    
def errLn(s):
    sys.stderr.write('ERROR: ' + s + '\n')

    
def main(args):
    if '/?' in args:
        showHelp()
        return 0

    return 0    




# sys.exit(main(sys.argv[1:]))



def strEscape(s, specChars, escChar='\\'):
    escChar = escChar[0]
    ret = ''
    if not escChar in specChars:
        specChars += escChar
    for c in s:
        if c in specChars:
            ret += escChar
        ret += c
    return ret


def strUnescape(s, escChar='\\'):
    escChar = escChar[0]
    ret = ''
    unescaped = False
    for c in s:
        if unescaped:
            ret += c
            unescaped = False
        elif c == escChar:
            unescaped = True
        else:
            ret += c
    return ret


def csvJoin(a):
    ret = ''
    for s in a:
        if ret:
            ret += ','
        if ',' in s or s[:1] == '"':
            ret += strEscape(s, ',', '


"""
abc     abc
a,bc    "a,bc"


"""
import csv                             