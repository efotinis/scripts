"""Print the PATH entries."""

import os
import sys
import getopt


try:
    opt, args = getopt.gnu_getopt(sys.argv[1:], '?')
    opt = dict(opt)
    if args:
        raise getopt.GetoptError('no params needed')
except getopt.GetoptError as err:
    raise SystemExit('ERROR: ' + str(err))

if '-?' in opt:
    print 'Display a list of the PATH entries.'
    raise SystemExit

for s in os.environ['PATH'].split(os.path.pathsep):
    print s
