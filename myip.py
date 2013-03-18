"""Get external IP via the Internet IP service du jour.

Call without arguments to display IP.
Call with a filename (env.vars accepted) to append local time and IP to it.

Old services used:
- whatismyip.com; stopped offering free scripting support at the beginning of 2013;
  see http://forum.whatismyip.com/showpost.php?p=9092&postcount=6
"""

import urllib2
import time
import sys
import os


def query():
    """Get IP as a string."""
    # http://rackerhacker.com/icanhazip-com-faq/
    return urllib2.urlopen('http://icanhazip.com/').read().rstrip('\n')


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
