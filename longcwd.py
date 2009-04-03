import os
import sys
import win32api

if '/?' in sys.argv:
  print 'Prints the long-name version of the current directory. [EF 2007.03.01]'
else:
  l = os.getcwd().split('\\')
  curPath = l.pop(0) + '\\'  # drive; must add '\' for join()
  while l:
    s = os.path.join(curPath, l.pop(0))
    info = win32api.FindFiles(s)[0]  # get the one and only list element
    curPath = os.path.join(curPath, info[8])  # add long name
  print curPath
