"""Compiled Windows resource utilities."""

import win32api


# winbase.h constants
LOAD_LIBRARY_AS_DATAFILE = 0x00000002
LOAD_LIBRARY_AS_IMAGE_RESOURCE = 0x00000020
LOAD_LIBRARY_AS_DATAFILE_EXCLUSIVE = 0x00000040	


class Module(object):
    """Resource module."""
    def __init__(self, path, exclusive=False):
        flags = LOAD_LIBRARY_AS_IMAGE_RESOURCE | \
                LOAD_LIBRARY_AS_DATAFILE_EXCLUSIVE if exclusive else LOAD_LIBRARY_AS_DATAFILE
        self.handle = win32api.LoadLibraryEx(path, 0, flags)
    def close(self):
        if self.handle:
            win32api.FreeLibrary(self.handle)
            self.handle = 0
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    def read(self, type_, name, lang):
        """Get raw resource bytes."""
        return win32api.LoadResource(type_, name, lang)
    def __iter__(self):
        """Generate (type,name,lang) of resources."""
        for type_ in win32api.EnumResourceTypes(self.handle):
            for name in win32api.EnumResourceNames(self.handle, type_):
                for lang in win32api.EnumResourceLanguages(self.handle, type_, name):
                    yield type_, name, lang


class Update(object):
    """Resource update operation."""
    def __init__(self, path, clear=False):
        self.handle = win32api.BeginUpdateResource(path, clear)
    def close():
        if self.handle:
            win32api.EndUpdateResource(self.handle, True)
            self.handle = 0
    def commit(self):
        """Commit any changes made."""
        win32api.EndUpdateResource(self.handle, False)
        self.handle = 0
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    def set(self, type_, name, lang, data):
        """Create or modify resource."""
        win32api.UpdateResource(self.handle, type_, name, data, lang)
    def remove(self, type_, name, lang):
        """Delete resource."""
        self.set(self, type_, name, lang, None)
