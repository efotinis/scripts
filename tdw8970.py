"""Telnet management of TD-W8970 router."""

import re
import telnetlib


PROMPT = b'TP-LINK(conf)#'


class Telnet(object):

    def __init__(self, ip='192.168.1.1', user=b'admin', password=b'admin', timeout=None):
        self.conn = telnetlib.Telnet(host=ip, timeout=timeout)

        self.conn.read_until(b'username:')
        self.conn.write(user + b'\n')
        self.conn.read_until(b'password:')
        self.conn.write(password + b'\n')

        # tricky part: we must send a newline and read twice, otherwise 
        # no comunication works afterwards; this also happens with telnetlib's
        # interactive(), but not with Windows' telnet command
        # (I dare not delve in the arcane machinations of the dark TeLNeT 
        # protocol that lies in front of me, staring into my very soul with...
        # *screams* *crunching bones* *incoherent sounds* *silence*)
        self.conn.write(b'\n')
        self.conn.read_until(b'TP-LINK(conf)#')
        self.conn.read_until(b'TP-LINK(conf)#')

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
        self.conn.write(cmd + b'\n')
        s = self.conn.read_until(PROMPT)
        if s.endswith(PROMPT):
            s = s[:-len(PROMPT)]
        return s.decode('ascii').replace('\r\n', '\n').replace('\r', '\n')

##    def __getitem__(self, cmd):
##        return self.communicate(cmd.encode('ascii'))

    @staticmethod
    def _response_lines(resp):
        """Generate response lines (without EOLs).

        Strips first (command) and empty lines, and stops at ending success line.
        """
        gotfirst = False
        for s in resp.splitlines():
            if not gotfirst:
                gotfirst = True
                continue
            if s == 'cmd:SUCC':
                break
            yield s
        else:
            raise ValueError('no success code in response')

    def wan_services(self):
        lines = list(self._response_lines(self.communicate(b'wan show service')))
        if lines[0] == lines[-1]:
            del lines[-1]
        else:
            raise ValueError('table header/footer mismatch')
        fields, lines = lines[0].split(), lines[1:]
        for s in lines:
            yield dict(zip(fields, s.split()))
