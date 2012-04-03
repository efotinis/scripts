"""App Paths registry key utility.

Info:
No docs in MSDN...

HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths
    program.exe                     allows program.exe to be found without a dir path (works in Start-Run, but not in a console)
        @="c:\dir\program.exe"      can be used to map to a different program (e.g. pbrush -> mspaint)
        "Path"="C:\dir1;C:\dir2"    PATH-like string that takes precedence in the DLL search order
        "useURL"="1"                ??? used for most Office apps (app accepts URLs?)
        "SaveURL"="1"               ??? used for some Office apps (app saves to URLs?)


http://www.codeguru.com/cpp/w-p/dll/article.php/c99
Application Specific Paths for DLL Loading

http://www.windowskb.com/Uwe/Forum.aspx/windowsxp/187194/Associate-Program-with-Start-Run
Associate Program with Start>Run
    ;Informs the shell that the program accepts URLs.
    ;"useURL"="1"

http://support.microsoft.com/kb/871001    
You may receive an HTTP: error message when you try to open a Visio 2003 file or a Visio 2002 SR-1 file by using FrontPage 2003
    (using "SaveURL" to bypass error)

http://web.archive.org/web/20050812083519/http://msdn.microsoft.com/library/en-us/dnwue/html/ch11c.asp
Using the Registry
    The system will automatically update the path and default entries
    if the user moves or renames the application's executable file
    using the system shell user interface.

http://blogs.msdn.com/oldnewthing/archive/2004/09/01/223936.aspx
How to find the Internet Explorer binary
    (much info)

"""

import os
import collections
import operator
import efRegistry

appsPath = r'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths'
valCounts = collections.defaultdict(int)
subkeys = efRegistry.getRegSubkeys(appsPath)
for keyName in subkeys:
    for valName in efRegistry.getRegValueNames(os.path.join(appsPath, keyName)):
        valCounts[valName] += 1
##        if valName.lower() == 'RunAsOnNonAdminInstall'.lower():
##            print keyName
        efRegistry.get

print 'keys count:', len(subkeys)
for name, count in sorted(valCounts.items(), key=operator.itemgetter(1), reverse=True):
    print '%5d x "%s"' % (count, name)


'''
SaveURL
    Excel.exe
    PowerPnt.exe
    Winword.exe

useURL
    Excel.exe
    frontpg.exe
    MSACCESS.EXE
    MsoHtmEd.exe
    PowerPnt.exe
    Winword.exe
'''