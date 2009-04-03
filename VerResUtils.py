"""Windows version resource utilities."""

# 2008.01.27  Created.


import ctypes, SharedLib


DWORD = ctypes.c_ulong
LPWSTR = ctypes.c_wchar_p
UINT = ctypes.c_uint
BYTE = ctypes.c_byte
WCHAR = ctypes.c_wchar
TCHAR = ctypes.c_wchar
BOOL = ctypes.c_long

MAX_DEFAULTCHAR = 2
MAX_LEADBYTES = 12
MAX_PATH = 260


VerLanguageName = SharedLib.winfunc('kernel32',
    'VerLanguageNameW', DWORD, [DWORD, LPWSTR, DWORD])


class CPINFOEXW(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('MaxCharSize',         UINT),
        ('DefaultChar',         BYTE * MAX_DEFAULTCHAR),
        ('LeadByte',            BYTE * MAX_LEADBYTES),
        ('UnicodeDefaultChar',  WCHAR),
        ('CodePage',            UINT),
        ('CodePageName',        TCHAR * MAX_PATH),
    ]


GetCPInfoExW = SharedLib.winfunc('kernel32',
    'GetCPInfoExW', BOOL, [UINT, DWORD, ctypes.POINTER(CPINFOEXW)])


def verlangname(n):
    """Version resource language name.

    Return u'Language Neutral' if lang is invalid.
    """
    buflen = 100
    buf = ctypes.create_unicode_buffer(buflen)
    VerLanguageName(n, buf, buflen)
    return buf.value


defcodepages = {
    0: 'default system ANSI', # CP_ACP
    1: 'default system OEM',  # CP_OEMCP
    2: 'default system MAC',  # CP_MACCP
    3: 'default thread ANSI'} # CP_THREAD_ACP


def codepagename(n):
    """Version resource codepage name.

    Return u'' if cp is invalid.
    """
    if n == 1200:  # not recognized by GetCPInfoExW
        return u'1200  (UCS-2)'
    cpix = CPINFOEXW()
    GetCPInfoExW(n, 0, ctypes.byref(cpix))
    if n in defcodepages:  # special, mapped codepages
        return defcodepages[n] + ': ' + cpix.CodePageName
    else:
        return cpix.CodePageName
