"""Display current time and Internet IP (via whatismyip.com)."""

import urllib2
import time

WHATISMYIP_URL = 'http://www.whatismyip.com/automation/n09230945.asp'

ip = urllib2.urlopen(WHATISMYIP_URL).read()

print time.ctime(), '-', ip
