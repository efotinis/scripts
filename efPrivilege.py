##
##    Use PrivilegeElevator to enable a privilege temporarily, e.g.
##
##        with PrivilegeElevator(win32security.SE_BACKUP_NAME):
##            # do something that requires BACKUP privilege (e.g. RegSaveKeyEx)
##

import win32api
import win32security


def _makeseq(x):
    if not isinstance(x, (list, tuple)):
        ret = []
        ret.append(x)
        return ret


class Privileges:

    def __init__(self, process=win32api.GetCurrentProcess()):
        """Manage a process's privileges."""
        self.process = process

    def adjust(self, privs, attr):
        """Adjust one or more privileges."""
        token = None
        try:
            token = win32security.OpenProcessToken(
                self.process,
                win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY)
            tokprivs = []
            for priv in _makeseq(privs):
                privval = win32security.LookupPrivilegeValue(None, priv)
                tokprivs += [(privval, attr)]
            return win32security.AdjustTokenPrivileges(token, False, tokprivs)
        finally:
            if token: token.Close()

    def enable(self, privs):
        """Enable one or more privileges."""
        return self.adjust(privs, win32security.SE_PRIVILEGE_ENABLED)

    def disable(self, privs):
        """Disable one or more privileges."""
        return self.adjust(privs, 0)


class PrivilegeElevator:

    def __init__(self, privs):
        """Temporarily enable one or more privileges."""
        self.privs = privs
        # TODO: save return and use it for 'close' (maybe privs were already enabled)
        Privileges().enable(self.privs)

    def __del__(self):
        self.close()

    def close(self):        
        Privileges().disable(self.privs)

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        pass


