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
  -b  Bare output: no top & side counters.
"""[1:-1] % locals()
    raise SystemExit


rowsize = 32
bareoutput = False

try:
    opt, args = getopt.getopt(sys.argv[1:], '?hnb')
    for sw, val in opt:
        if sw == '-n':
            rowsize = 16
        elif sw == '-b':
            bareoutput = True
        elif sw == '-?' or sw == '-h':
            help()
except getopt.GetoptError as err:
    raise SystemExit(err)

if not bareoutput:
    headerfmt = '%01x' if rowsize <= 16 else '%02x'
    headers = map(''.join, zip(*[headerfmt % i for i in range(rowsize)]))
    for s in headers:
        print '   ' + s
    print '   ' + '-' * rowsize

for i in range(32, 256, rowsize):
    if not bareoutput:
        sys.stdout.write('%02x|' % i)
    print ''.join(chr(c) for c in range(i, i+rowsize))
