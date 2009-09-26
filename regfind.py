import sys
import _winreg
import ctypes

from winerror import ERROR_ACCESS_DENIED, ERROR_NO_MORE_ITEMS

from ctypes.wintypes import BYTE, LONG, DWORD, LPWSTR, LPCWSTR, HKEY
REGSAM = DWORD
FILETIME = DWORD * 2
LPDWORD = ctypes.POINTER(DWORD)
PHKEY = ctypes.POINTER(HKEY)
PFILETIME = ctypes.POINTER(FILETIME)
LPBYTE = ctypes.POINTER(BYTE)


RegOpenKeyExW = ctypes.windll.advapi32.RegOpenKeyExW
RegOpenKeyExW.restype = LONG
RegOpenKeyExW.argtypes = [HKEY, LPCWSTR, DWORD, REGSAM, PHKEY]

RegCloseKey = ctypes.windll.advapi32.RegCloseKey
RegCloseKey.restype = LONG
RegCloseKey.argtypes = [HKEY]

RegEnumKeyExW = ctypes.windll.advapi32.RegEnumKeyExW
RegEnumKeyExW.restype = LONG
RegEnumKeyExW.argtypes = [HKEY, DWORD, # key, index
                          LPWSTR, LPDWORD, # nameBuf, nameBufLen
                          LPDWORD, # reserved (0)
                          LPWSTR, LPDWORD, # classBuf, classBufLen
                          PFILETIME] # lastWriteTime

RegEnumValueW = ctypes.windll.advapi32.RegEnumValueW
RegEnumValueW.restype = LONG
RegEnumValueW.argtypes = [HKEY, DWORD, # key, index
                          LPWSTR, LPDWORD, # nameBuf, nameBufLen
                          LPDWORD, # reserved (0)
                          LPDWORD, # type
                          LPBYTE, LPDWORD] # dataBuf, dataBufLen

RegQueryValueExW = ctypes.windll.advapi32.RegEnumValueW
RegQueryValueExW.restype = LONG
RegQueryValueExW.argtypes = [HKEY,
                             LPCWSTR, # name
                             LPDWORD, # reserved (0)
                             LPDWORD, # type
                             LPBYTE, LPDWORD] # dataBuf, dataBufLen


def errLn(s):
    sys.stderr.write('ERROR: ' + s + '\n')


class RegKey:

    class Error(WindowsError):
        def __init__(self, n):
            WindowsError.__init__(self)
            self.winerror = n

    def __init__(self, root, path, sam=_winreg.KEY_READ):
        self.h = HKEY(0)
        self.open(root, path, sam)

    def isOpen(self):
        return bool(self.h.value)

    def open(self, root, path, sam=_winreg.KEY_READ):
        self.close()
        n = RegOpenKeyExW(root, path, 0, sam, ctypes.byref(self.h))
        if n:
            raise self.Error(n)

    def close(self):
        if self.isOpen():
            n = RegCloseKey(self.h)
            if n:
                raise self.Error(n)
            n = HKEY(0)

    def enumKey(self, i):
        buf = ctypes.create_unicode_buffer(260)
        bufLen = DWORD(len(buf))
        n = RegEnumKeyExW(self.h, i, buf, ctypes.byref(bufLen),
                          None, None, None, None)
        if n:
            return u''
        return buf.value
        
    def getKeys(self):
        ret = []
        i = 0
        while True:
            s = self.enumKey(i)
            if not s:
                break
            ret.append(s)
            i += 1
        return ret
        
    def enumValue(self, i):
        buf = ctypes.create_unicode_buffer(260)
        bufLen = DWORD(len(buf))
        n = RegEnumValueW(self.h, i, buf, ctypes.byref(bufLen),
                          None, None, None, None)
        if n:
            return u''
        return buf.value

    def getValues(self):
        ret = []
        i = 0
        while True:
            s = self.enumValue(i)
            if not s:
                break
            ret.append(s)
            i += 1
        return ret

    def getValueType(self, id):
        type = DWORD()
        if isinstance(id, basestring):
            n = RegQueryValueExW(self.h, id, None, ctypes.byref(type),
                                 None, None)
        else:
            n = RegEnumValueW(self.h, id, None, None, None, ctypes.byref(type),
                              None, None)
        if n:
            return None
        return type.value

    def getValueData(self, id):
        pass
        

##def traverse1(key, sub):
##    try:
##        rk = RegKey(key, sub)
##    except RegKey.Error, x:
##        if x.winerror == ERROR_ACCESS_DENIED:
##            return 0
##        else:
##            raise
##    i = 0
##    subCnt = 0
##    while True:
##        s = rk.enumKey(i)
##        if not s:
##            break
##        subCnt += traverse1(rk.h, s)
##        i += 1
##    rk.close()
##    return i + subCnt
##
##
##def traverse2(key, sub):
##    try:
##        rk = RegKey(key, sub)
##    except RegKey.Error, x:
##        if x.winerror == ERROR_ACCESS_DENIED:
##            return 0
##        else:
##            raise
##    subCnt = 0
##    keys = rk.getKeys()
##    for s in keys:
##        subCnt += traverse2(rk.h, s)
##    rk.close()
##    return len(keys) + subCnt
##
##
##
##from time import time
##
##root = HKEY(_winreg.HKEY_CLASSES_ROOT)
###root = HKEY(_winreg.HKEY_CURRENT_USER)
##
##t1 = 1e+99
##t2 = 1e+99
##while True:
##
##    t = time()
##    traverse1(root, u'')
##    t = time() - t
##    if t < t1:
##        t1 = t
##
##    t = time()
##    traverse2(root, u'')
##    t = time() - t
##    if t < t2:
##        t2 = t
##
##    print '%6.2f, %6.2f' % (t1, t2)


"""
enum keys:
(1) ret '' on end
(2) throw exception on end

  (1)     (2)
 2.38,   2.84  (HKCU)
12.91,  14.61  (HKLM)
"""

root = HKEY(_winreg.HKEY_CURRENT_USER)


##def traverse2(key, sub):
##    try:
##        rk = RegKey(key, sub)
##    except RegKey.Error, x:
##        if x.winerror == ERROR_ACCESS_DENIED:
##            return 0
##        else:
##            raise
##    subCnt = 0
##    keys = rk.getKeys()
##    for s in keys:
##        subCnt += traverse2(rk.h, s)
##    rk.close()
##    return len(keys) + subCnt
