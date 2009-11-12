"""Security utilities."""

import contextlib

import win32api
import win32security


class ProcessPrivileges:
    """Manage a process's privileges."""

    def __init__(self, process=win32api.GetCurrentProcess()):
        self.process = process

    def adjust(self, names, attr):
        """Adjust one or more privileges."""
        access = win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
        with contextlib.closing(win32security.OpenProcessToken(self.process, access)) as token:
            newstate = [(win32security.LookupPrivilegeValue(None, name), attr) for name in names]
            return win32security.AdjustTokenPrivileges(token, False, newstate)

    def enable(self, names):
        """Enable one or more privileges."""
        return self.adjust(names, win32security.SE_PRIVILEGE_ENABLED)

    def disable(self, names):
        """Disable one or more privileges."""
        return self.adjust(names, 0)


@contextlib.contextmanager
def privilege_elevation(privileges):
    """Temporarily enable privileges of the current process.

    Example:
    >>> with privilege_elevation(win32security.SE_BACKUP_NAME):
    ...     pass  # something that requires BACKUP privilege (e.g. RegSaveKeyEx)
    """
    p = ProcessPrivileges()
    # TODO: save return and use it for 'close' (in case privileges were already enabled)
    p.enable(privileges)
    try:
        yield
    finally:
        p.disable(privileges)
