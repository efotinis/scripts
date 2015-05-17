"""Print router status for the WBR-6600 router.

Currently prints one line showing:
- system local time
- external WAN IP
- link speeds
- channel mode
- noise summary (margin/attenuation)

Can optionally write the router sys log to a directory.
"""

import os
import sys
import time
import getpass
import argparse
import wbr6600
import efutil


def parse_args():
    ap = argparse.ArgumentParser(
        description='WBR-6600 router status')
    ap.add_argument('-l', dest='logdir',
                    help='directory to save sys log; uses UTC timestamp for name')
    ap.add_argument('cookie', nargs='?', help='cooked admin password; '
                    'if omitted, it must be entered interactively')
    args = ap.parse_args()
    if args.cookie:
        args.cookie = str(args.cookie.decode('base64').decode('rot13'))
    return args


if __name__ == '__main__':
    args = parse_args()
    if not args.cookie:
        args.cookie = getpass.getpass('password: ')

    with wbr6600.Telnet('192.168.0.1', 'admin', args.cookie) as t:
        timestamp = time.ctime()
        ip = t.getWanProtoStatus()['IP address']
        chan = t.getWanAdslChandataSummary()
        opmode = t.getWanAdslOpmode().get('operational mode', 'n/a')
        try:
            noise = t.getNoiseSummary()
        except KeyError:
            noise = 'n/a'
        sys_uptime = t.getSysUptime()
        adsl_uptime = t.getAdslUptime()

        if args.logdir:
            syslog_timestamp = efutil.get_timestamp(compact=True, utc=True)
            syslog_text = t.getSysLog()

    print '%s - %s, %s, %s, %s, uptime (sys/adsl): %s / %s' % (
        timestamp, ip, chan, opmode, noise, sys_uptime, adsl_uptime)

    if args.logdir:
        if not os.path.exists(args.logdir):
            os.makedirs(args.logdir)
        logpath = os.path.join(args.logdir, syslog_timestamp + '.log')
        with open(logpath, 'w') as f:
            f.write(syslog_text)
