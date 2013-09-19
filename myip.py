"""Get external IP via the Internet IP service du jour.

Old services used:
- whatismyip.com; stopped offering free scripting support at the beginning of 2013;
  see http://forum.whatismyip.com/showpost.php?p=9092&postcount=6
"""

import os
import sys
import time
import urllib2
import argparse


def query():
    """Get IP as a string."""
    # http://rackerhacker.com/icanhazip-com-faq/
    return urllib2.urlopen('http://icanhazip.com/').read().rstrip('\n')


def parse_args():
    ap = argparse.ArgumentParser(
        description='show WAN external IP')
    ap.add_argument('-l', dest='logfile',
        help='append date/IP to file, instead of printing to stdout')
    return ap.parse_args()


if __name__ == '__main__':
    args = parse_args()

    try:
        ip, error = query(), None
    except urllib2.URLError as x:
        ip, error = None, str(x)

    if args.logfile:
        result = ip or ('<' + error + '>')
        with open(args.logfile, 'a') as f:
            print >>f, time.ctime(), '-', result
    else:
        if ip:
            print ip
        else:
            sys.exit(error)
