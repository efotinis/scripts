import win32api
import win32file


def getDriveRoots(types=None):
    """Return a list of drive roots ('X:\\'), optionally filtered by type.

    'types' can be used to filter the returned drives.
    It can be a win32con.DRIVE_* const (or a sequence of them).
    """
    # get a list of all drive roots
    a = win32api.GetLogicalDriveStrings()[:-1].split('\0')
    if types is None:
        return a
    # filter them
    if isinstance(types, int):
        types = [types]
    return [s for s in a if win32file.GetDriveType(s) in types]


