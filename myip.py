"""Get external IP via whatismyip.com.

Call without arguments to display IP.
Call with a filename (env.vars accepted) to append local time and IP to it.
"""

import urllib2
import time
import sys
import os


QUERY_URL = 'http://www.whatismyip.com/automation/n09230945.asp'


def query():
    """Get IP as a string.

    As per the whatismyip.com automation rules, this function should not
    be called more ofter than every 5 minutes.
    """
    return urllib2.urlopen(QUERY_URL).read()


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print query()
    elif len(args) == 1:
        fn = os.path.expandvars(args[0])
        with open(fn, 'a') as f:
            print >>f, time.ctime(), '-', query()
    else:
        raise SystemExit('too many parameters')
