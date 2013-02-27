"""Print external IP address. Can be used to detect dropped Net connection."""

import re
import sys
import wbr6600

with wbr6600.Telnet('192.168.0.1', 'admin', 'fooker') as t:
    ip = t.getWanProtoStatus()['IP address']
    m = re.match(r'^\d+\.\d+\.\d+\.\d+$', ip)
    if m:
        print m.group()
    else:
        sys.exit('no external IP address detected')
