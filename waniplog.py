#!python3
"""Update file containing WAN IP.

Can be used to update a Dropbox file with my home IP.
"""

import sys

import myip
import tdw8970


def get_ip(psw):
    """Get current external WAN IP.

    Try the router's telnet interface and fallback to a web service.
    """
    try:
        psw = psw.encode('ascii')
        with tdw8970.Telnet(password=psw, timeout=5) as t:
            for d in t.wan_services():
                if d['Proto'] == 'PPPoE':
                    return d['IP']
        print('IP not found using telnet', file=sys.stderr)
    except Exception as x:
        print('telnet session failed:', x, file=sys.stderr)
    return myip.query()


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
    psw, path = sys.argv[1:]
    update(path, get_ip(psw))
