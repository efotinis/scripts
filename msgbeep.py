import sys
import win32api
from win32con import MB_OK, MB_ICONINFORMATION, MB_ICONWARNING, MB_ICONERROR, MB_ICONQUESTION


def showhelp():
    print '''
Play a Windows sound.

BEEP [-?] [<sound>]

Accepted sounds:
    ok         Default Beep sound (MB_OK). This is the default.
    i[nfo]     Asterisk sound (MB_ICONINFORMATION/MB_ICONASTERISK)
    w[arn]     Exclamation sound (MB_ICONWARNING/MB_ICONEXCLAMATION)
    e[rr[or]]  Critical Stop sound (MB_ICONERROR/MB_ICONHAND/MB_ICONSTOP)
    q, ask     Question sound (MB_ICONQUESTION)
    s[imple]   Simple beep (uses speaker if no sound card is available)
'''[1:-1]


args = sys.argv[1:]
if '-?' in args:
    showhelp()
    sys.exit()
if len(args) > 1:
    print >>sys.stderr, 'only one parameter is accepted'
    sys.exit(2)
if not args:
    args = ['ok']

options = {
    'ok': MB_OK,
    'i': MB_ICONINFORMATION,
    'info': MB_ICONINFORMATION,
    'w': MB_ICONWARNING,
    'warn': MB_ICONWARNING,
    'e': MB_ICONERROR,
    'err': MB_ICONERROR,
    'error': MB_ICONERROR,
    'q': MB_ICONQUESTION,
    'ask': MB_ICONQUESTION,
    's': -1,
    'simple': -1}

try:
    sound = options[args[0].lower()]
except KeyError:
    sys.exit('invalid sound: "%s"' % args[0])
win32api.MessageBeep(sound)
