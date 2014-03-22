"""Telnet management of WBR6600 router."""

import re
import telnetlib


PROMPT = 'WBR-6600>'


class Telnet(object):

    def __init__(self, ip, user, password):
        self.conn = telnetlib.Telnet(ip)
        self.conn.read_until('login: ')
        self.conn.write(user + '\n')
        self.conn.read_until('Password: ')
        self.conn.write(password + '\n')
        self.conn.read_until('Copyright (c) 2001 - 2004 ADSL Company\r\n')
        self.conn.read_until(PROMPT)

    def close(self):
        self.conn.close()

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def communicate(self, cmd):
        """Send command and return response."""
        cmd += '\n'
        self.conn.write(cmd)
        s = self.conn.read_until(PROMPT).replace('\r', '')
        if s.endswith(PROMPT):
            s = s[:-len(PROMPT)]
        return s

    def parseInfoDict(self, s):
        """Return dict from a string of "key : value\n" lines."""
        return {m.group(1):m.group(2)
                for m in re.finditer(r'(.*?)\s*:\s*(.*)\n', s)}

    def getWanProtoStatus(self):
        """Return dict.
        Sample response:
            Encapsulation: PPPoE LLC
            VPI / VCI: 8 / 35
            IP address: 62.1.129.107
            Netmask: 255.255.255.255
            Gateway: 213.16.246.21
        Sample response during "Authentication Fail":
            Encapsulation: PPPoE LLC
            VPI / VCI: 8 / 35
            IP address:
            Netmask:
            Gateway:
        """
        return self.parseInfoDict(self.communicate('wan proto status'))

    def getWanAdslChandata(self):
        """Return dict.
        Sample response:
            near-end interleaved channel bit rate: 0 kbps
            near-end fast channel bit rate: 5048 kbps
            far-end interleaved channel bit rate: 0 kbps
            far-end fast channel bit rate: 1023 kbps
        """
        return self.parseInfoDict(self.communicate('wan adsl chandata'))

    def getWanAdslChandataSummary(self):
        """Return "<DOWN>/<UP> kbps up/down [<fast/interleaved>]" string."""
        d = self.getWanAdslChandata()
        speed_rx = re.compile(r'^(\d+)\s+kbps$', re.IGNORECASE)
        fastDown = speed_rx.match(d['near-end fast channel bit rate']).group(1)
        fastUp = speed_rx.match(d['far-end fast channel bit rate']).group(1)
        ilDown = speed_rx.match(d['near-end interleaved channel bit rate']).group(1)
        ilUp = speed_rx.match(d['far-end interleaved channel bit rate']).group(1)
        if (fastDown, fastUp) != ('0', '0'):
            return '%s/%s kbps up/down fast' % (fastDown, fastUp)
        elif (ilDown, ilUp) != ('0', '0'):
            return '%s/%s kbps up/down interleaved' % (ilDown, ilUp)
        else:
            return '0/0 kbps up/down'

    def getWanAdslOpmode(self):
        """Return dict.
        Sample response:
            operational mode:ITU G.992.5(ADSL2Plus)
        """
        return self.parseInfoDict(self.communicate('wan adsl opmode'))

    def getSysLog(self):
        """Return string."""
        return self.communicate('sys log')

    def getNoise(self):
        """Return dict.
        Sample response:
            Noise Margin (Upstream)   : 11.5 db
            Noise Margin (Downstream) : 7.5 db
            Attenuation (Upstream)    : 22.7 db
            Attenuation (Downstream)  : 41.6 db
        """
        return self.parseInfoDict(self.communicate('wan adsl shownoise'))

    def getNoiseSummary(self):
        """Return "noise margin <N>/<N> dB up/down, attenuation <N>/<N> dB up/down" string."""
        d = self.getNoise()
        noise_rx = re.compile(r'^([\d\.]+)\s+db$', re.IGNORECASE)
        marginUp = noise_rx.match(d['Noise Margin (Upstream)']).group(1)
        marginDown = noise_rx.match(d['Noise Margin (Downstream)']).group(1)
        attenUp = noise_rx.match(d['Attenuation (Upstream)']).group(1)
        attenDown = noise_rx.match(d['Attenuation (Downstream)']).group(1)
        return 'noise margin %s/%s dB up/down, attenuation %s/%s dB up/down' % (
            marginUp, marginDown, attenUp, attenDown)

    def getSysUptime(self):
        # returns: '6 days,  3 hours 03 minutes'
        return self.communicate('sys uptime').splitlines()[1]

    def getAdslUptime(self):
        # returns: '1 day 21 hr 20 min 25 sec'
        s = self.communicate('wan adsl uptime').splitlines()[1]
        prefix = 'ADSL uptime:'
        if s.startswith(prefix):
            s = s[len(prefix):].strip()
        return s
