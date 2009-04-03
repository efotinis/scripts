import os, win32file

def settimes(f, create=None, modify=None, access=None):
    h = win32file.CreateFile(f, win32file.GENERIC_WRITE, 0, None, win32file.OPEN_EXISTING, 0, None)
    win32file.SetFileTime(h, create, access, modify)
    win32file.CloseHandle(h)

##import os
##a = os.listdir('.')
##for i, s in enumerate(a):
##    settimes(s, create=(2008,10,14+i,12,0,0), modify=(2008,10,27-i,12,0,0))
