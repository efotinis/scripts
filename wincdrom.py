"""Windows CD-ROM type drive operations.

Inspired by http://code.activestate.com/recipes/180919/ (r2)

Terminology used in this module:
    'X'       drive letter
    'X:'      drive
    'X:\\'    drive root
"""

import os
import time
import string
import contextlib
import win32file
import win32api
from win32con import DRIVE_CDROM, GENERIC_READ, FILE_SHARE_READ, OPEN_EXISTING
from winioctlcon import IOCTL_STORAGE_LOAD_MEDIA, IOCTL_STORAGE_EJECT_MEDIA


def system_drives():
    """Generate the logical drives ('X:') of type DRIVE_CDROM."""
    for c in string.ascii_uppercase:
        if win32file.GetDriveType(c + ':\\') == DRIVE_CDROM:
            yield c + ':'


def _get_drive(s):
    """Convert a single letter or a path with a drive spec to a drive string ('X:')."""
    if not s or len(s) > 1 and s[1] != ':' or s[0] not in string.ascii_letters:
        raise ValueError('bad drive format: "{0}"'.format(s))
    return s[0].upper() + ':'


def _get_drive_device(drive):
    """Open a handle to a drive device."""
    return win32file.CreateFile('\\\\.\\' + drive, GENERIC_READ,
        FILE_SHARE_READ, None, OPEN_EXISTING, 0, 0)


class Cdrom:
    """A Win32 CD-ROM type drive."""

    def __init__(self, drive):
        """Init with a drive letter or path containing a drive spec."""
        self.drive = _get_drive(drive)

    def load(self):
        """Close the drive door."""
        with contextlib.closing(_get_drive_device(self.drive)) as dev:
            win32file.DeviceIoControl(dev, IOCTL_STORAGE_LOAD_MEDIA, None, 0, None)
        
    def eject(self):
        """Open the drive door."""
        with contextlib.closing(_get_drive_device(self.drive)) as dev:
            win32file.DeviceIoControl(dev, IOCTL_STORAGE_EJECT_MEDIA, None, 0, None)

    def is_ready(self):
        """Test whether the loaded media is ready for access."""
        try:
            win32api.GetVolumeInformation(self.drive + '\\')
            return True
        except win32api.error:
            return False

    def wait_ready(self, timeout, interval=1):
        """Poll the drive until it's ready and return True.

        If the timeout period expires, False is returned.
        The polling interval can also be specified.
        """
        endtime = time.time() + timeout
        while time.time() < endtime:
            if self.is_ready():
                return True
            time.sleep(interval)
        return False


if __name__ == '__main__':
    print 'System CD-ROM drives: ' + ', '.join(system_drives())
    try:
        drive = raw_input('Enter CD-ROM drive to test (Ctrl-C to exit): ')
    except KeyboardInterrupt:
        raise SystemExit
    cd = Cdrom(drive)

    print
    
    print 'opening...',
    cd.eject()
    print 'OK'

    print 'ready status:', cd.is_ready()    

    print 'closing...',
    cd.load()
    print 'OK'

    print 'ready status:', cd.is_ready()    

    print 'waiting 2 sec to become ready...',
    print cd.wait_ready(2, 0.25)

    print 'ready status:', cd.is_ready()    

    print 'waiting another 10 sec to become ready...',
    print cd.wait_ready(10, 1)

    print 'ready status:', cd.is_ready()    
