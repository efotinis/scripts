"""Find non-ASCII characters in clipboard text."""

import sys
import getopt
import clipboard


try:
    opts, args = getopt.gnu_getopt(sys.argv[1:], '?')
    opts = dict(opts)
    if args:
        raise getopt.GetoptError('no params allowed')
except getopt.GetoptError as x:
    sys.exit(str(x))

if '-?' in opts:
    print 'Finds non-ASCII chars in the clipboard\'s text.'
    print ''
    print 'Options:'
    print '  -?  This help.'
    sys.exit()

text = clipboard.gettext()
if text is None:
    sys.exit('no text in clipboard')

a = sorted(c for c in set(text) if not 32 <= ord(c) <= 127)
if not a:
    sys.exit('no non-ASCII chars found')

for c in a:
    print ord(c)
