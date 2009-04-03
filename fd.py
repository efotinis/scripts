import sys
import subprocess
import string

import cmdLineOptions


exePath = 'C:\\Program Files\\filedisk\\filedisk.exe'
driveLetters = string.ascii_uppercase[2:]  # 'C'..'Z'


##filedisk /mount  <devicenumber> <filename> [size[k|M|G] | /ro | /cd] <drive:>
##filedisk /umount <drive:>
##filedisk /status <drive:>
##
##filename formats:
##  c:\path\filedisk.img
##    \Device\Harddisk0\Partition1\path\filedisk.img
##      \\server\share\path\filedisk.img
##
##      example:
##      filedisk /mount  0 c:\temp\filedisk.img 8M f:
##      filedisk /mount  1 c:\temp\cdimage.iso /cd i:
##      filedisk /umount f:
##      filedisk /umount i:
##
##
## /M drive deviceNo image [opt]
## /U [drives ... ]  if 'drives' ommited, *prompt* to unmount all
## /UA              unmount all
## /S [drives ...]  if 'drives' ommited, return status for all mounted images
##
##
##
##
##
##

def main():
    args = cmdLineOptions.parseRaw(sys.argv[1:])
    for i in range(len(args)):
        args[i][0] = args[i][0].upper()

    if '/?' in args:
        help()
        sys.exit(0)
    action = extractAction(args)
    actionDict = {
        'M': actionMount,
        'U': actionUnmount,
        'S': actionStatus
    }
    actionDict[action](args)


def printErrLn(x):
    sys.stderr.write(x)
    sys.stderr.write('\n')


def help():
    print """\
FILEDISK wrapper.

FD /M
FD /M
FD /M
"""


def filedisk(options):
    try:
        sp = subprocess.Popen(exePath + ' ' + options, -1, None, None, subprocess.PIPE, subprocess.PIPE)
    except OSError, x:
        printErrLn(x)
        return (-1, '', str(x))
    sp.wait()
    out, err = sp.communicate()
    return (sp.returncode, out, err)


def getDriveStatus(drive):
    if drive[-1:] != ':':
        drive += ':'
    result = filedisk('/status ' + drive)
    if result[0] == 0:
        return parseMountedStatus(result[1])
    return None


# Return list of mounted images' status.
def getAllMountedDrivesStatus():
    ret = []
    for c in driveLetters:
        result = filedisk('/status ' + c + ':')
        if result[0] == 0:
            ret += [parseMountedStatus(result[1].rstrip('\r\n'))]
    return ret


# Split a FILEDISK mounted image status line to its components
# e.g. this string:
#   Z: \??\f:\test.img Size: 1474560 bytes, ReadOnly
#   -- ---------------       -------        --------
#  drive    image              size        flags (opt)
# becomes:
#   ('Z:', '\??\f:\test.img', 1474560, 'ReadOnly')
def parseMountedStatus(s):
    s = s.rstrip('\r\n')

    # find size delimiters
    markers = (' Size: ', ' bytes')
    offsets = [-1, -1]
    offsets[0] = s.find(markers[0])
    offsets[1] = s.find(markers[1], offsets[0])
    if -1 in offsets:
        return ret

    ret = [
        s[:2],
        s[3:offsets[0]],
        int(s[offsets[0] + len(markers[0]):offsets[1]]),
        s[offsets[1] + len(markers[1]):]
    ]
    if ret[3][:2] == ', ':
        ret[3] = ret[3][2:]
    return tuple(ret)

    
def extractAction(args):
    actions = tuple('MUS')
    existFlags = [0, 0, 0]
    for i in range(len(args)):
        s = args[i].upper()
        for j in range(len(actions)):
            if s == '/' + actions[j]:
                existFlags[j] = 1
    sum_ = sum(existFlags)
    if sum_ == 0:
        return 'S'
    elif sum_ == 1:
        return actions[existFlags.index(1)]
    else:
        printErrLn('/M, /U, and /S are mutually exclusive.')
        sys.exit(1)


def actionMount(args):
    pass


def actionUnmount(args):
    pass


def actionStatus(args):
    if 'ALL' in [s.upper() for s in args]:
        statList = getAllMountedDrivesStatus()
        for stat in statList:
            printStatus(stat)
    else:
        for s in args



main()

