"""DLL utilities."""

import ctypes


def _dllfunc(dll, name, ret, args):
    """Get a func from a loaded DLL and setup ret/arg types."""
    func = dll[name]
    func.restype = ret
    func.argtypes = args
    return func


def cfunc(dll, name, ret, args):
    """Load a func from a C DLL."""
    return _dllfunc(ctypes.cdll[dll], name, ret, args)


def olefunc(dll, name, ret, args):
    """Load a func from an OLE DLL."""
    return _dllfunc(ctypes.oledll[dll], name, ret, args)


def winfunc(dll, name, ret, args):
    """Load a func from a Windows DLL."""
    return _dllfunc(ctypes.windll[dll], name, ret, args)


def pyfunc(dll, name, ret, args):
    """Load a func from a Python DLL."""
    return _dllfunc(ctypes.pydll[dll], name, ret, args)


class BaseDLL(object):
    """Base for various DLL type classes.

    Allows loading of functions via call operator.
    """
    def __init__(self, dll):
        self.dll = dll
        
    def __call__(self, name, ret, args):
        """Load a function by specifying its name, return type, and list of arg types."""
        func = self.dll[name]
        func.restype = ret
        func.argtypes = args
        return func


class CDLL(BaseDLL):
    def __init__(self, name):
        BaseDLL.__init__(self, ctypes.cdll[name])


class OleDLL(BaseDLL):
    def __init__(self, name):
        BaseDLL.__init__(self, ctypes.oledll[name])


class WinDLL(BaseDLL):
    def __init__(self, name):
        BaseDLL.__init__(self, ctypes.windll[name])


class PyDLL(BaseDLL):
    def __init__(self, name):
        BaseDLL.__init__(self, ctypes.pydll[name])

