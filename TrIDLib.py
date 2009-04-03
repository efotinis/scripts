"""Python wrapper for Marco Pontello's TrIDLib.

(C) 2008 Elias Fotinis
TrIDLib is (C) 2003-06 Marco Pontello
"""
import os, ctypes


# constants for the free version
#
TRID_GET_RES_NUM         = 1     # Get the number of results available
TRID_GET_RES_FILETYPE    = 2     # Filetype descriptions
TRID_GET_RES_FILEEXT     = 3     # Filetype extension
TRID_GET_RES_POINTS      = 4     # Matching points
#
TRID_GET_VER             = 1001  # TrIDLib version (major * 100 + minor)
TRID_GET_DEFSNUM         = 1004  # Number of filetypes definitions loaded

# additional constants for the full version
#
TRID_GET_DEF_ID          = 100   # Get the id of the filetype's definition for a given result
TRID_GET_DEF_FILESCANNED = 101   # Various info about that def
TRID_GET_DEF_AUTHORNAME  = 102   #     "
TRID_GET_DEF_AUTHOREMAIL = 103   #     "
TRID_GET_DEF_AUTHORHOME  = 104   #     "
TRID_GET_DEF_FILE        = 105   #     "
TRID_GET_DEF_REMARK      = 106   #     "
TRID_GET_DEF_RELURL      = 107   #     "
TRID_GET_DEF_TAG         = 108   #     "
TRID_GET_DEF_MIMETYPE    = 109   #     "
#
TRID_GET_ISTEXT          = 1005  # Check if the submitted file is text or binary one


DLL_NAME = 'TrIDLib.dll'
BUF_SIZE = 4096


class Error(Exception):
    """TrIDLib error."""
    def __init__(self, s):
        Exception.__init__(self, s)


class TrIDLib:

    def __init__(self, dllpath='', defsdir=''):
        """Load library and (optionally) definitions."""
        if not dllpath:
            dllpath = DLL_NAME
        elif os.path.isdir(dllpath):
            dllpath = os.path.join(dllpath, DLL_NAME)
        try:
            self.dll = ctypes.WinDLL(dllpath)
            INT, PCHAR = ctypes.c_int, ctypes.c_char_p
            self.pLoadDefsPack = self._getproc('TrID_LoadDefsPack', INT, [PCHAR])
            self.pSubmitFileA = self._getproc('TrID_SubmitFileA', INT, [PCHAR])
            self.pAnalyze = self._getproc('TrID_Analyze', INT, [])
            self.pGetInfo = self._getproc('TrID_GetInfo', INT, [INT,INT,PCHAR])
            self.buf = ctypes.create_string_buffer(BUF_SIZE)
        except (WindowsError, AttributeError):
            raise Error('could not load dll')
        if defsdir:
            self.loaddefs(defsdir)

    def close(self):
        """Force library to unload.
        Normally, the garbage collector will unload it eventually."""
        self.dll = None
        self.pAnalyze = None
        self.pGetInfo = None
        self.pLoadDefsPack = None
        self.pSubmitFileA = None

    def _getproc(self, name, ret, args):
        """Get DLL func object and set its return and arg types."""
        func = self.dll[name]
        func.restype = ret
        func.argtypes = args
        return func

    def loaddefs(self, defsdir):
        """Load definitions pack from a directory.
        Defpack file name is hardcoded to 'TrIDDefs.TRD'."""
        if not self.pLoadDefsPack(defsdir):
            raise Error('could not load defs pack from "%s"' % defsdir)

    def submit(self, fname):
        if not self.pSubmitFileA(fname):
            raise Error('file submit failed for "%s"' % fname)

    def analyze(self):
        if not self.pAnalyze():
            raise Error('could not analyze file')

    def getinfo(self, type, index = 0):
        ret = self.pGetInfo(type, index, self.buf)
        return ret, self.buf.value

    def version(self):
        """Library version (pair of major/minor numbers)."""
        n = self.getinfo(TRID_GET_VER)[0]
        return n / 100, n % 100

    def defsnum(self):
        """Number of definitions in loaded defpack."""
        return self.getinfo(TRID_GET_DEFSNUM)[0]

    def results(self):
        """Get list of (type, extensions, points) results."""
        matches = self.getinfo(TRID_GET_RES_NUM)[0]
        return list(
            (
                self.getinfo(TRID_GET_RES_FILETYPE, i)[1],
                self.getinfo(TRID_GET_RES_FILEEXT, i)[1].split('/'),
                self.getinfo(TRID_GET_RES_POINTS, i)[0]
            )
            for i in range(1, matches+1)
        )

    def istext(self):
        """Report if analyzed files looks like text (FULL VERSION ONLY)."""
        return self.getinfo(TRID_GET_ISTEXT)[0]

    def idresults(self):
        """Get result defpack IDs (FULL VERSION ONLY)."""
        matches = self.getinfo(TRID_GET_RES_NUM)[0]
        return tuple(self.getinfo(TRID_GET_DEF_ID, i)[0]
                     for i in range(1, matches+1))

    def idinfo(self, i):
        """Get internal defpack ID info tuple (FULL VERSION ONLY).
        It contains: number of files scanned, author name/email/website,
        file type, comment, info URL, tag and MIME type."""
        return (
            self.getinfo(TRID_GET_DEF_FILESCANNED, i)[0],
            self.getinfo(TRID_GET_DEF_AUTHORNAME, i)[1],
            self.getinfo(TRID_GET_DEF_AUTHOREMAIL, i)[1],
            self.getinfo(TRID_GET_DEF_AUTHORHOME, i)[1],
            self.getinfo(TRID_GET_DEF_FILE, i)[1],
            self.getinfo(TRID_GET_DEF_REMARK, i)[1],
            self.getinfo(TRID_GET_DEF_RELURL, i)[1],
            self.getinfo(TRID_GET_DEF_TAG, i)[1],
            self.getinfo(TRID_GET_DEF_MIMETYPE, i)[1])


if __name__ == '__main__':
    DLL_DIR = DEFS_DIR = 'D:\\docs\scripts'  # modify
    trid = TrIDLib(DLL_DIR, DEFS_DIR)
    print 'DLL version: %d.%02d' % trid.version()
    print 'definitions: %d' % trid.defsnum()
    