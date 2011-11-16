"""Write clipboard text to STDOUT.

usage: paste [-?]

Will fail if there's no text in the clipboard.
"""

import sys
import getopt
import win32console
import clipboard

try:
    opts, args = getopt.gnu_getopt(sys.argv[1:], '?')
    opts = dict(opts)
    if '-?' in opts:
        sys.stdout.write(__doc__)
        sys.exit()
    if args:
        raise getopt.GetoptError('no parameters allowed')
except getopt.GetoptError as x:
    sys.stderr.write(str(x) + '\n')
    sys.exit(2)

text = clipboard.get_text()
if text is None:
    sys.exit('no text in clipboard')

encoding = 'cp' + str(win32console.GetConsoleOutputCP())
text = text.encode(encoding, 'replace')
# split lines manually to avoid CRLF->CRCRLF problems
# TODO: can be optimized by splitting iteratively
for s in text.splitlines():
    print s
