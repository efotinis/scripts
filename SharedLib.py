"""DLL func load utilities.

Example:
    import SharedLib, ctypes
    from ctypes.wintypes import BOOL, UINT, PVOID
    SystemParametersInfo = SharedLib.winfunc(
        'user32', 'SystemParametersInfo', BOOL, [UINT,UINT,LPVOID,UINT])
    - or -
    user = SharedLib.WinLib('user32')
    SystemParametersInfo = user('SystemParametersInfo', BOOL, [UINT,UINT,LPVOID,UINT])

2008.01.27  Created.
"""


import ctypes


def _libfunc(lib, name, ret, args):
    """Get a func from a loaded DLL and setup ret/arg types."""
    func = lib[name]
    func.restype = ret
    func.argtypes = args
    return func


def cfunc(lib, name, ret, args):
    """Load a func from a C DLL."""
    return _libfunc(ctypes.cdll[lib], name, ret, args)


def olefunc(lib, name, ret, args):
    """Load a func from an OLE DLL."""
    return _libfunc(ctypes.oledll[lib], name, ret, args)


def winfunc(lib, name, ret, args):
    """Load a func from a Windows DLL."""
    return _libfunc(ctypes.windll[lib], name, ret, args)


def pyfunc(lib, name, ret, args):
    """Load a func from a Python DLL."""
    return _libfunc(ctypes.pydll[lib], name, ret, args)


class _Lib:
    """Load a func by calling with name, ret and arg types."""
    def __call__(self, name, ret, args):
        func = self.lib[name]
        func.restype = ret
        func.argtypes = args
        return func

class CLib(_Lib):
    def __init__(self, name):
        self.lib = ctypes.cdll[name]

class OleLib(_Lib):
    def __init__(self, name):
        self.lib = ctypes.oledll[name]

class WinLib(_Lib):
    def __init__(self, name):
        self.lib = ctypes.windll[name]

class PyLib(_Lib):
    def __init__(self, name):
        self.lib = ctypes.pydll[name]

