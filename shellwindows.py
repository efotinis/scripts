"""Print the HWND and URL of the opened Shell windows.

The URL of virtual folders is empty.
Example:
    0x00000000004609c0 file:///D:/scripts
    0x000000000046093a file:///C:/Users/Public
"""

import ctypes
import win32com.client
#import win32com.client.constants
from ctypes.wintypes import LPVOID


PTRSIZE = ctypes.sizeof(LPVOID)


shapp = win32com.client.Dispatch('Shell.Application')
wnds = shapp.Windows()  # get the ShellWindows object
# traverse the InternetExplorer objects
for i in range(wnds.Count):
    print '0x%0*x %s' % (PTRSIZE * 2, int(wnds(i).HWND), wnds(i).LocationURL)
