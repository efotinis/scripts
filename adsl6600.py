"""Print ADSL connection status for the WBR-6600 router.

Currently prints one line showing:
- system local time
- external WAN IP
- link speeds
- channel mode
- noise summary (margin/attenuation)
"""

import os
import sys
import time
import getpass
import wbr6600


if __name__ == '__main__':
    router_ip, user, token = sys.argv[1:]
    if token:
        token = str(token.decode('base64').decode('rot13'))
    else:
        token = getpass.getpass()

    with wbr6600.Telnet(router_ip, user, token) as t:
        timestamp = time.ctime()
        ip = t.getWanProtoStatus()['IP address']
        chan = t.getWanAdslChandataSummary()
        opmode = t.getWanAdslOpmode().get('operational mode', 'n/a')
        try:
            noise = t.getNoiseSummary()
        except KeyError:
            noise = 'n/a'

    print '%s - %s, %s, %s, %s' % (timestamp, ip, chan, opmode, noise)
