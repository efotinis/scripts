import os
import sys
import bz2
import pickle

import win32api

import efutil
import winfiles


def datadump(dpath):
    a = []
    for i in winfiles.find(os.path.join(dpath, '*')):
        a += [[i.name, i.attr, i.create, i.modify, i.size]]
        if winfiles.is_dir(i.attr):
            a[-1] += [datadump(os.path.join(dpath, i.name))]
    return a
    

def getVolSn(s):
    """Volume name and serial number a path's drive."""
    drive = os.path.splitdrive(s)[0] + '\\'
    vol, sn = win32api.GetVolumeInformation(drive)[:2]
    sn &= 0xffffffff
    return vol, sn


def disphelp():
    script = efutil.scriptname().upper()
    print 'usage: %s <drive> <outfile> [<name>] [<notes>]' % script


def main(args):
    if '/?' in args:
        disphelp()
        raise SystemExit
    if not 2 <= len(args) <= 4:
        raise SystemExit('ERROR: 2 to 4 parameters required')

    drive   = args[0]
    outfile = args[1]
    name    = args[2] if len(args) > 2 else ''
    notes   = args[3] if len(args) > 3 else ''

    try:
        volume, serial = getVolSn(drive)
    except win32api.error:
        raise SystemExit('ERROR: invalid drive')

    data = datadump(drive)

    try:
        f = open(outfile, 'wb')
    except IOError:
        raise SystemExit('ERROR: could not open output file')

    d = {
        'name': name,
        'label': volume,
        'serial': serial,
        'notes': notes,
        'data': data
        }

    f.write('EFDDMP00')
    s = pickle.dumps(d, pickle.HIGHEST_PROTOCOL)
    s = bz2.compress(s)
    f.write(s)


main(sys.argv[1:])
