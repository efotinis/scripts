#!python3
"""Update file containing WAN IP from ADSL connection log.

Can be used to update a Dropbox file with my home IP.
"""

import os
import re
import sys


LOGFILE = os.path.expandvars('%LOCALAPPDATA%\\adsl.log')


def last_line(path):
    """Get last line of a text file, including EOL if it exists."""
    with open(path) as f:
        for s in f:
            pass
        return s


def is_ip(s):
    """Test whether string is IP in 'n.n.n.n' format."""
    return re.match(r'^\d+\.\d+\.\d+\.\d+$', s) is not None


def get_ip():
    """Get IP (or None) from ADSL log."""
    line = last_line(LOGFILE).rstrip('\n')
    time, sep, info = line.partition(' ')
    ip = info.split(',', 1)[0]
    return ip if is_ip(ip) else None


def update(path, ip):
    """Write WAN IP to file if it's different."""
    try:
        with open(path) as f:
            previous = f.read()
    except OSError:
        previous = ''
    if ip != previous:
        with open(path, 'w') as f:
            f.write(ip)


if __name__ == '__main__':
    path, = sys.argv[1:]
    ip = get_ip()
    if ip:
        update(path, ip)
