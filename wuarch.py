# Inspired by:
# - UninstallRemover.vbs
#   (TODO: find source)
# - Doug Knox's XP_Remove_Hotfix_Backup.exe
#   <http://www.dougknox.com/xp/utils/xp_hotfix_backup.htm>
# - Save Space After Installing Updates
#   <http://www3.telus.net/dandemar/spack.htm>
#
# 2007.06.05  created
# 2007.09.27  replaced optparse with DosCmdLine; added day count in /T output;
#             added /NS
#
# TODO:
# - test on 2000/Vista


import os, sys, re, _winreg, tempfile, time, zipfile, shutil
import win32api
import efRegistry
import DosCmdLine


EXIT_OK = 0
EXIT_ERROR = 1
EXIT_BADPARAM = 2


WINDIR = os.environ['windir']
REG_PATH_UNINST = r'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'
RX_UNINST_DIRNAME = re.compile(r'^\$NtUninstall(KB|Q)(\d{6})(.*)\$$', re.I)
TMPFILE = tempfile.mktemp()


## TODO: put this in the help screen
##
##A ZIP file is created for each update, containing:
##- the uninstall files from "%WINDIR%\$NtUninstall*$"
##- the log file "%WINDIR%\*.log" (if any)
##- the exported uninstall registry key
##  "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*" (if any)


def scriptName():
    return os.path.splitext(os.path.basename(sys.argv[0]))[0]


def errln(s):
    sys.stderr.write('ERROR: ' + s + '\n')


def findLog(parts):
    """Return the full path of the log matching the specified update name parts,
    or '' if not found."""
    s = os.path.join(WINDIR, ''.join(parts)+'.log')
    if os.path.exists(s):
        return s
    s = os.path.join(WINDIR, ''.join(parts[:2])+'.log')
    if os.path.exists(s):
        return s
    return ''


def findKey(parts):
    """Return the full path of the registry key matching the specified update
    name parts, or '' if not found."""
    s = os.path.join(REG_PATH_UNINST, ''.join(parts))
    return s if efRegistry.regKeyExists(s) else ''


def archive(uninstdirname, nameparts, outdir):
    zipname = ''.join(nameparts) + '.zip'
    zipname = os.path.join(outdir, zipname)
    z = zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED)

    uninstdirpath = os.path.join(WINDIR, uninstdirname)

    # write a dir entry in the zip file to preserve the dir's mod date
    dirmoddate = time.localtime(os.path.getmtime(uninstdirpath))[:6]
    info = zipfile.ZipInfo(uninstdirname+'/', dirmoddate)
    info.external_attr = win32api.GetFileAttributes(uninstdirpath)
    z.writestr(info, '')

    # save backup files
    for dir, subs, files in os.walk(uninstdirpath):
        savepath = dir[len(WINDIR)+1:]
        for fname in files:
            s1 = os.path.join(dir, fname)
            s2 = os.path.join(savepath, fname)
            z.write(s1, s2)

    # save log (if it exists)
    logpath = findLog(nameparts)
    if logpath:
        z.write(logpath, os.path.basename(logpath))

    # save reg key (if it exists)
    regpath = findKey(nameparts)
    if regpath and efRegistry.exportRegKey(regpath, TMPFILE):
        s = ''.join(nameparts) + '.reg'
        z.write(TMPFILE, s)

    z.close()

    # we made it; start deleting stuff    
    shutil.rmtree(uninstdirpath)
    if logpath:
        os.unlink(logpath)
    if regpath:
        efRegistry.nukeKey(regpath)


def getBackupDirsInfo():
    """Return the name, mod dates and match parts
    of all update backup dirs in the Windows dir."""
    ret = []
    for s in os.listdir(WINDIR):
        path = os.path.join(WINDIR, s)
        if os.path.isdir(path):
            m = RX_UNINST_DIRNAME.match(s)
            if m:
                ret += [(s, os.path.getmtime(path), m.groups())]
    return ret
    

def getWinVer():
    """Return Windows major and minor version number or (0,0) on error."""
    try:
        return sys.getwindowsversion()[:2]
    except NameError:
        return 0,0


def showHelp(switches):
    name = scriptName().upper()
    table = '\n'.join(DosCmdLine.helptable(switches))
    print """\
Archive and cleanup Windows Update backups.
Elias Fotinis 2007

%s [/O:dir] [/D:days] [/T] [/F]

%s

Exit code: 0=ok, 1=error, 2=bad params""" % (name, table)


def main(args):
    Swch = DosCmdLine.Switch
    Flag = DosCmdLine.Flag
    switches = (
        Swch('O', 'outdir',
             'The directory to place the archives. Default is the current.',
             '.'),
        Swch('D', 'daylimit',
             'Process updates installed at least the specified number '
             'of days ago. (default: 0, meaning all updates)',
             0, converter=int),
        Flag('T', 'test',
             'Display, without actually archiving, the updates that will be '
             'affected. Each update is preceeded by its installation age in '
             'days.'),
        Flag('NS', 'nosummary',
             'Do not display number of items displayed or processed.'),
##        Flag('F', 'force',
##             'Force execution on non-WinXP systems (2000/Vista). '
##             'Use with caution; it has not been.'),
    )
    if '/?' in args:
        showHelp(switches)
        return EXIT_OK
    try:
        opt, params = DosCmdLine.parse(args, switches)
        if params:
            raise DosCmdLine.Error('no arguments are allowed')
        if opt.daylimit < 0:
            raise DosCmdLine.Error('days must be >= 0')
    except DosCmdLine.Error, x:
        errln(str(x))
        return EXIT_BADPARAM

##    if getWinVer() != (5,1) and not opt.force:
##        errln('system is not Windows XP; see help on /F switch for details')
    if getWinVer() != (5,1):
        errln('this script is for Windows XP only')
        return EXIT_ERROR

    # get info
    dirsInfo = getBackupDirsInfo()

    # filter by date
    if opt.daylimit <> 0:
        now = time.time()
        secs = opt.daylimit * 24 * 3600
        dirsInfo = [x for x in dirsInfo if now - x[1] >= secs]

    errcnt = 0
    for name, moddate, nameparts in dirsInfo:
        if opt.test:
            ageInDays = int((time.time()-moddate)/3600/24)
            print '%3d: %s' % (ageInDays, name)
        else:
            print 'Archiving:', name
            try:
                archive(name, nameparts, opt.outdir)
            except (IOError, OSError), x:
                errLn(str(x))
                errcnt += 1

    if not opt.nosummary:
        print 'Items:', len(dirsInfo)
    if not opt.test:
        print 'Errors:', errcnt

    return EXIT_OK if not errcnt else EXIT_ERROR


try:
    sys.exit(main(sys.argv[1:]))
finally:
    if os.path.exists(TMPFILE):
        os.unlink(TMPFILE)
