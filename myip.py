"""Get external IP via the Internet IP service du jour.

Old services used:
- whatismyip.com; stopped offering free scripting support at the beginning of 2013;
  see http://forum.whatismyip.com/showpost.php?p=9092&postcount=6
"""

from __future__ import print_function
import os
import sys
import time
import argparse

from six.moves.urllib.request import urlopen
from six.moves.urllib_error import URLError


def query():
    """Get IP as a string."""
    # http://rackerhacker.com/icanhazip-com-faq/
    s = urlopen('http://icanhazip.com/').read()
    return s.decode('utf-8').rstrip('\n')


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
    except URLError as x:
        ip, error = None, str(x)

    if args.logfile:
        result = ip or ('<' + error + '>')
        with open(args.logfile, 'a') as f:
            print(time.ctime(), '-', result, file=f)
    else:
        if ip:
            print(ip)
        else:
            sys.exit(error)
