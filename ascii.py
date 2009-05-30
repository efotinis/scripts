"""Print ASCII chars in 32-255 range."""

import sys
import getopt
import CommonTools


def help():
    scriptname = CommonTools.scriptname().upper()
    print """
Print an ASCII map of the characters in the 32-255 range.

%(scriptname)s options

  -n  Narrow map (16x14). Default is wide (32x7).
"""[1:-1] % locals()
    raise SystemExit


ROWSIZE = 32

try:
    opt, args = getopt.getopt(sys.argv[1:], '?hn')
    for sw, val in opt:
        if sw == '-n':
            ROWSIZE = 16
        elif sw == '-?' or sw == '-h':
            help()
except getopt.GetoptError as err:
    raise SystemExit(err)

for i in range(32, 256, ROWSIZE):
    print ''.join(chr(c) for c in range(i, i+ROWSIZE))
