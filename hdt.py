import os, sys, re, subprocess, efutil


SMARTCTL_PATH = r'C:\\Program Files\\smartmontools\\bin\\smartctl.exe'
TEMP_FILE = os.path.join(os.environ['TEMP'], '~hdtemp.$$$')
DEVICE_PARAM_RX = re.compile(r'^(hd[a-z])|(\d+)$')
SMART_RAWVALUE_OFFSET = 87
errln = efutil.errln


def checkdevice(dev):
    # send SMARTCTL output to a file (note: SMARTCTL never uses STDERR)
    cmdline = '"%s" -A %s' % (SMARTCTL_PATH, dev)
    with open(TEMP_FILE, 'w') as f:
        p = subprocess.Popen(cmdline, stdout=f, shell=True)
        exitcode = p.wait()
    if exitcode:
        errln('smartctl call failed for ' + dev)
        return False
    for s in open(TEMP_FILE):
        if 'temperature_celsius' in s.lower():
            degrees = (s + ' ')[SMART_RAWVALUE_OFFSET:].split()[0]
            print '%s: %s oC' % (dev, degrees)
            break
    else:
        errln('no temperature (in Celcius) found in SMART attributes of "%s"' % dev)
        return False
    return True


def parsedeviceid(s):
    """Check for a valid device id and return in "/dev/hd?" format."""
    m = DEVICE_PARAM_RX.match(s)
    if not m:
        raise ValueError
    if m.group(1):
        return '/dev/' + m.group(1)
    else:
        n = int(m.group(2))
        if not 0 <= n <= 25:
            raise ValueError
        return '/dev/hd' + chr(ord('a') + n)


def showhelp():
    s = '''
Display drive temperatures using SMARTCTL.

%s [drives]

  drives  The list of drives to check. Valid formats:
          - hda ... hdz
          - 0 ... 25
'''[1:-1]
    print s % efutil.scriptname().upper()


def main(args):
    if '/?' in args:
        showhelp()
        return 0
    args = [s for s in args if not s.startswith('/')]  # ignore switches
    errors = False
    if not os.path.exists(SMARTCTL_PATH):
        errln('program missing: "%s"' % SMARTCTL_PATH)
        return 1
    try:
        for s in args:
            try:
                s = parsedeviceid(s)
            except ValueError:
                errln('invalid device: "%s"' % s)
                errors = True
                continue
            if not checkdevice(s):
                errors = True
    finally:
        if os.path.exists(TEMP_FILE):
            os.unlink(TEMP_FILE);
    return 1 if errors else 0


sys.exit(main(sys.argv[1:]))
