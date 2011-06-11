"""Get external IP via whatismyip.com.

Call without arguments to display IP.
Call with a filename (env.vars accepted) to append local time and IP to it.
"""

import urllib2
import time
import sys
import os


#QUERY_URL = 'http://www.whatismyip.com/automation/n09230945.asp'
QUERY_URL = 'http://automation.whatismyip.com/n09230945.asp'  # new URL as of May 25, 2011


def query():
    """Get IP as a string.

    As per the whatismyip.com automation rules, this function should not
    be called more ofter than every 5 minutes.
    """
    return urllib2.urlopen(QUERY_URL).read()


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) > 1:
        raise SystemExit('too many parameters')
    if not args:
        print query()
    else:
        ok = True
        try:
            ip = query()
        except urllib2.URLError as x:
            ok = False
            ip = '<' + str(x) + '>'
        fn = os.path.expandvars(args[0])
        with open(fn, 'a') as f:
            print >>f, time.ctime(), '-', ip
        if not ok:
            sys.exit(1)
