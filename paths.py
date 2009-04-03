import os
import sys

if '/?' in sys.argv:
    print 'Displays a list of the %PATH% items.'
else:
    print '\n'.join(os.environ['PATH'].split(';'))

## This PY script replaces my old BAT:
##
##    ---- PATHS.BAT ----
##    @ECHO %PATH% | txtops brl ;
##    -------------------

