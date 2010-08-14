"""Compiled Windows resource utilities."""

import ctypes
import struct
import contextlib
from ctypes.wintypes import WORD, DWORD, LPVOID, LPCWSTR, HRSRC, HMODULE, HGLOBAL

import win32api

import dllutil


# winbase.h constants
LOAD_LIBRARY_AS_IMAGE_RESOURCE = 0x00000020
LOAD_LIBRARY_AS_DATAFILE_EXCLUSIVE = 0x00000040	


kernel32 = dllutil.WinDLL('kernel32')
FindResourceEx = kernel32('FindResourceExW', HRSRC, [HMODULE, LPCWSTR, LPCWSTR, WORD])
LoadResource = kernel32('LoadResource', HGLOBAL, [HMODULE, HRSRC])
LockResource = kernel32('LockResource', LPVOID, [HGLOBAL])
SizeofResource = kernel32('SizeofResource', DWORD, [HMODULE, HRSRC])


@contextlib.contextmanager
def Module(path, flags=0):
    """Context manager for loading a DLL."""
    module = win32api.LoadLibraryEx(path, 0, flags)
    try:
        yield module
    finally:
        win32api.FreeLibrary(module)


@contextlib.contextmanager
def UpdateResource(fname, clear=False):
    """Context manager for resource updating.

    If 'clear' is True, existing resources are deleted.
    Caller can raise a DiscardUpdate exception to exit, discarding updates.
    """
    h = win32api.BeginUpdateResource(fname, delete)
    discard = False
    try:
        yield h
    except DiscardUpdate:
        discard = True
    finally:
        win32api.EndUpdateResource(h, discard)


class DiscardUpdate(Exception):
    """Raise within an UpdateResource context to discard changes."""
    pass


def _enum_filter(value, cond):
    if cond is None:
        return True
    try:
        return cond(value)
    except TypeError:
        pass
    try:
        return value in cond
    except TypeError:
        return value == cond


def enum_resources(module, type_=None, name=None, lang=None):
    """Generate resources (type/name/lang triples) with optional filtering.

    The filters can be:
    - None: everything matches
    - single value: single match
    - sequence: match any value in sequence
    - function: accepts a value and returns boolean match
    """
    for r_type in win32api.EnumResourceTypes(module):
        if _enum_filter(r_type, type_):
            for r_name in win32api.EnumResourceNames(module, r_type):
                if _enum_filter(r_name, name):
                    for r_lang in win32api.EnumResourceLanguages(module, r_type, r_name):
                        if _enum_filter(r_lang, lang):
                            yield r_type, r_name, r_lang


def read_resource(module, type_, name, lang):
    """Get the raw bytes of a resource."""
    res = FindResourceEx(module, LPCWSTR(type_), LPCWSTR(name), lang)
    mem = LoadResource(module, res)
    ptr = LockResource(mem)
    size = SizeofResource(module, res)
    buf = ctypes.create_string_buffer(size)
    ctypes.memmove(buf, ptr, size)
    return buf.raw


def build_menu_item(flags, idnum, text):
    """Construct a raw menu item resource."""
    POPUP = 0x0010
    if flags & POPUP:
        raise ValueError('POPUP flag not allowed')
    return (struct.pack('HH', flags, idnum) + unicode(text + '\0').encode('utf_16_le'))


