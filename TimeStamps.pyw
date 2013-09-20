"""Display the timestamps of the items passed in the cmdline.

2007.11.28  created
2007.12.02  added Unicode support (cmdline & msgbox)
"""

import os, sys, time, win32api, win32con, winfixargv, MessageBoxW

def scriptname():
    return os.path.splitext(os.path.basename(sys.argv[0]))[0]

def datetimestr(t):
    """Convert time object to system short date & time string."""
    return win32api.GetDateFormat(0,0,t) + ' ' + win32api.GetTimeFormat(0,0,t)

def gettimestamps(s):
    """Get create, modify and last access times of a file/dir."""
    return os.path.getctime(s), os.path.getmtime(s), os.path.getatime(s)

def msgbox(s, flags=0):
    """Popup a message box."""
    return MessageBoxW.MessageBoxW(0, s, scriptname(), flags)

def main(args):
    STAMP_TITLES = ('create', 'modify', 'access')
    INDENT = ' ' * 4
    if not args:
        msgbox('no files specified')
        return
    outputblocks = []
    for item in args:
        a = [item]
        try:
            t = gettimestamps(item)
            a += [INDENT + '%s: %s' % (title, datetimestr(stamp))
                for title, stamp in zip(STAMP_TITLES, t)]
        except (IOError, OSError), x:
            a += [INDENT + str(x)]
        outputblocks += ['\n'.join(a)]
    msgbox('\n\n'.join(outputblocks))

try:
    main(sys.argv[1:])
except Exception, x:
    # not very useful without a trace, but better than no output at all
    msgbox(str(x), win32con.MB_ICONERROR)
