# 2008.07.14  created
# 2008.07.22  added ExtCnt function

# TODO: factor out common code


import os
import re
import sys
import operator
import time
from collections import defaultdict

import win32file

import win32time
import AutoComplete
import FindFileW
from console_stuff import SamePosOutput
from CommonTools import uprint


class PathError(ValueError):
    '''Path traversing error.'''
    def __init__(self, *args):
        ValueError.__init__(self, *args)


class CmdError(ValueError):
    '''Command line error.'''
    def __init__(self, *args):
        ValueError.__init__(self, *args)


class ListStats:
    '''Directory statistics.'''
    def __init__(self):
        self.dirs = 0
        self.files = 0
        self.bytes = 0


class ExtStats:
    '''Extension statistics.'''
    def __init__(self):
        self.files = 0
        self.bytes = 0


# FILETIME of Python (and C) epoch
PY_EPOCH = win32time.pythonEpochToFileTime().getvalue()
# factor to convert FILETIME to seconds
TIME_SCALE = 1 / 10000000.0


def winToPyTime(n):
    '''Convert a FindFileW.Info date (FILETIME int64)
    to Python seconds since the epoch.'''
    return (n - PY_EPOCH) * TIME_SCALE


class Item:
    '''Base directory item.'''
    def __init__(self, path):
        self.name = os.path.basename(path)
        # os.path.getmtime and family fail with non-ACP chars
        info = FindFileW.getInfo(path)
        if info is None:
            # goddamn securom... (names with trailing space)
            info = FindFileW.getInfo('\\\\?\\' + path)
            if info is None:
                if not self.name:
                    # root dirs have no info
                    self.attr = None
                    self.mdate = None
                    self.cdate = None
                    return
                else:
                    uprint('FATAL: could not get info for "%s"' % path)
                    raise SystemExit(-1)
        self.attr = info.attr
        self.mdate = winToPyTime(info.modify)
        self.cdate = winToPyTime(info.create)


class File(Item):
    '''File item.'''
    def __init__(self, path, status=None):
        Item.__init__(self, path)
        try:
            # getsize fails on some SecuROM files with trailing spaces
            self.size = os.path.getsize(path)
        except OSError:
            # even FindFirstFileW will fail, unless we turn off path parsing
            # with \\?\
            self.size = FindFileW.getInfo('\\\\?\\' + path).size
    def addListStats(self, stats):
        stats.files += 1
        stats.bytes += self.size
    def addExtStats(self, statsDict):
        ext = os.path.splitext(self.name)[1].lower()
        stats = statsDict[ext]
        stats.files += 1
        stats.bytes += self.size


class Dir(Item):        
    '''Directory item.'''
    def __init__(self, path, status=None):
        Item.__init__(self, path)
        if status:
            status.update(path)
        self.getChildren(path, status)
    def getChildren(self, path, status=None):
        self.children = []
        try:
            # some folders (like "System Volume Information") cannot be listed
            items = os.listdir(path)
        except WindowsError as x:
            msg = 'WANRING: could list contents of "%s"; reason: %s' % (path, x.strerror)
            status.staticprint(msg)
            return
        for s in items:
            childPath = os.path.join(path, s)
            factory = Dir if os.path.isdir(childPath) else File
            self.children += [factory(childPath, status)]
    def getSubDir(self, name):
        '''Return an immediate subdir.'''
        if name in ('', '.'):
            return self
        for c in self.children:
            if c.name.upper() == name.upper():
                return c
        else:
            raise PathError('no child named "%s"' % name)
    def getSubPath(self, path):
        '''Return a subdir, 1 or more levels deeper, but never higher.
        "path" must be relative, without any ".." tokens.'''
        if not path:
            return self
        if os.path.sep in path:
            s1, s2 = path.split(os.path.sep, 1)
            return self.getSubDir(s1).getSubPath(s2)
        else:
            return self.getSubDir(path)
    def getListStats(self):
        '''Return total dir, files and bytes recursively.'''
        stats = ListStats()
        self.addListStats(stats)
        return stats
    def addListStats(self, stats):
        stats.dirs += 1
        for c in self.children:
            c.addListStats(stats)
    def addExtStats(self, statsDict):
        for c in self.children:
            c.addExtStats(statsDict)
            
        
        
def showHelp():
    print '''
   R | ROOT [dir]    Set (or show) root directory.
  CD | CHDIR [dir]   Set (or show) current directory.
   D | DIR [dir]     Show directory contents.
   L | LIST [dir]    Show directory entry statistics.
   E | EXTCNT [dir]  Show directory extension statistics (files only).
   S | SCAN [dir]    Rescan directory.
  DO | DIRORDER [dircol][dirctn]
  LO | LISTORDER [listcol][dirctn]  
  EO | EXTORDER [extcol][dirctn]
                     Set (or show) sort order for DIR, LIST and EXTCNT.
   U | UNIT [unit]   Set (or show) size unit. One of "B", "K", "M", "G".
   ? | HELP          Show help.
   Q | QUIT          Exit.

DIR, LIST, EXTCNT and SCAN default to current directory.

Order flags:
  listcol      dircol         extcol       dirctn
  -----------  -------------  -----------  ------------
  D dirs       M modify date  F files      + ascending
  F files      S size         S size       - descending
  S size       A attributes   N name       
  N name       N name         * unordered
  * unordered  * unordered    

Dir display extra attribute flags (hex):
  01 temporary      10 offline
  02 sparse file    20 not content indexed
  04 reparse point  40 encrypted
  08 compressed
'''[1:-1]


def showUsage():
    print '''
Interactive cmdline OverDisk variant.

OVERDISK [root]

    root  Initial root dir. "." if omitted.
'''[1:-1]
    

RX_CMD = re.compile(
    r'''^
        \s*             # optional leading space
        (\w+|\?)        # alnum word or "?"
        (?:
            \s+(.*)     # optional params with leading space
        )?
    $''',
    re.IGNORECASE | re.VERBOSE)


class State:
    '''Global program state.'''
    def __init__(self):
        self.root = None        # root Dir object
        self.rootPath = ''      # root dir path (must be unicode -> listdir bug)
        self.relPath = ''       # current relative dir path
        self.listOrder = '*+'   # list sorting
        self.dirOrder = '*+'    # dir sorting
        self.extOrder = '*+'    # extcnt sorting
        self.unit = 'B'         # display size unit


class CmdDispatcher:
    '''Command dispatcher.'''
    def __init__(self, state):
        self.state = state
        self.entries = (
            (('?', 'help'),   lambda dummy1, dummy2: showHelp()),
            (('cd', 'chdir'), cmdCd),
            (('d', 'dir'),    cmdDir),
            (('l', 'list'),   cmdList),
            (('e', 'extcnt'), cmdExtCnt),
            (('r', 'root'),   cmdRoot),
            (('s', 'scan'),   cmdScan),
            (('lo', 'listorder'), cmdListOrder),
            (('do', 'dirorder'),  cmdDirOrder),
            (('eo', 'extorder'),  cmdExtOrder),
            (('u', 'unit'),   cmdUnit)
        )
    def dispatch(self, cmd, params):
        for cmdIds, func in self.entries:
            if cmd.lower() in cmdIds:
                func(self.state, params)
                return
        else:
            raise CmdError('unknown command "%s"' % cmd)


def getCandidatePaths(state, seed):
    head, tail = os.path.split(seed)
    try:
        relPath, dirObj = locateDir(state, head)
    except PathError:
        return []
    if tail:
        tail = tail.upper()
        matches = lambda s: s.upper().startswith(tail)
    else:
        matches = lambda s: True
    a = []
    for item in dirObj.children:
        if isinstance(item, Dir) and matches(item.name):
            #a += [item.name]
            a += [os.path.join(head, item.name)]
    return a


class ScanStatus:
    def __init__(self, root):
        self.spo = SamePosOutput(fallback=True)
        self.root = root
    def update(self, s):
        self.spo.restore(True)
        s = s[len(self.root):]  # trim root
        uprint(s[:79])  # TODO: use a better trimming func, removing middle path elements
    def cleanup(self):
        self.spo.restore(True)
    def staticprint(self, s):
        """Print a static line and continue updates to the next line."""
        self.spo.restore(True)
        print s
        self.spo.reset()


def main(args):
    if '/?' in args:
        showUsage()
        return 0
    if len(args) > 1:
        uprint('ERROR: no more than 1 param needed')
        return 2
    if not args:
        args = [os.getcwd()]

    state = State()
    cmdDispatcher = CmdDispatcher(state)

    state.rootPath = os.path.abspath(unicode(args[0]))
    if not os.path.isdir(state.rootPath):
        uprint('ERROR: not a dir: ""' % state.rootPath)
        return 2

    uprint('scanning "%s" ...' % state.rootPath)
    status = ScanStatus(state.rootPath)
    state.root = Dir(state.rootPath, status)
    status.cleanup()

    acmgr = AutoComplete.Manager()

    while True:
        try:
            prompt = ':: ' + os.path.join(
                state.rootPath, state.relPath).rstrip(os.path.sep) + '>'

            if 0:
                s = raw_input(prompt).strip()
            else:
                acmgr.completer = lambda s: getCandidatePaths(state, s)
                s = acmgr.input(prompt)

            if not s:
                continue
            m = RX_CMD.match(s)
            if not m:
                uprint('ERROR: invalid cmd line')
                continue
            cmd, params = m.groups()
            cmd = cmd.lower()
            params = params or ''
            if cmd in ('q', 'quit'):
                break
            cmdDispatcher.dispatch(cmd, params)
        except (CmdError, PathError) as x:
            uprint('ERROR: ' + str(x))
        finally:
            uprint('')


def walkPath(state, curRelPath, parts):
    '''Walk directories starting from a current relative path
    and using a list of token parts (incl. "." and "..").
    Underflowing ".." tokens (trying to go above state.root) are ignored.
    Returns resulting relative path or throws PathError.'''
    a = curRelPath.split(os.path.sep) if curRelPath else []
    for s in parts:
        if s == '.':
            continue
        elif s == '..':
            del a[-1:]
        else:
            try:
                state.root.getSubPath(os.path.join(*(a + [s])))
                a += [s]
            except PathError:
                raise
    return os.path.join(*a) if a else ''


def setupDirChange(state, newPath):
    '''Return initial relative path and list of item tokens to walk
    during a dir change. Tokens may contain "." and ".." items.'''
    parts = os.path.normpath(newPath).split(os.path.sep)  # len >= 1
    if parts[0] == '':
        # new path is absolute
        return '', parts[1:]
    else:
        # new path is relative
        return state.relPath, parts


def locateDir(state, newPath):
    '''Find dir by following "newPath" (absolute or relative)
    and return its relative path and Dir object.'''
    if not newPath:
        relPath = state.relPath
    else:
        relPath = walkPath(state, *setupDirChange(state, newPath))
    return relPath, state.root.getSubPath(relPath)
    

def dateStr(n):
    a = list(time.localtime(n))[:5]
    a[0] %= 100
    return '%02d%02d%02d-%02d%02d' % tuple(a)


def attrStr(n):
    extra = (n & 0xff00) >> 8
    s = '%02x' % extra if extra else '..'
    s += '-'
    s += 'A' if n & win32file.FILE_ATTRIBUTE_ARCHIVE   else '.'
    s += 'D' if n & win32file.FILE_ATTRIBUTE_DIRECTORY else '.'
    s += 'S' if n & win32file.FILE_ATTRIBUTE_SYSTEM    else '.'
    s += 'H' if n & win32file.FILE_ATTRIBUTE_HIDDEN    else '.'
    s += 'R' if n & win32file.FILE_ATTRIBUTE_READONLY  else '.'
    return s


def trimName(s, n):
    '''Replace some chars before the ext with '<..>'
    if needed to restrict size of file name.
    Append a single '>' if name or ext is too long.'''
    if len(s) <= n:
        return s
    name, ext = os.path.splitext(s)
    if len(ext) >= n or n-len(ext)-4 <= 0:
        return s[:n-1] + '>'
    return name[:n-len(ext)-4] + '<..>' + ext


def cmdRoot(state, params):
    if not params:
        uprint(state.rootPath)
        return
    if params[:1] == params[-1:] == '"':
        params = params[1:-1]
    newRootPath = os.path.abspath(unicode(params))
    if not os.path.isdir(newRootPath):
        raise PathError('not a dir: "%s"' % newRootPath)
    status = ScanStatus(newRootPath)
    state.root = Dir(newRootPath, status)
    status.cleanup()
    state.rootPath = newRootPath
    state.relPath = ''


def cmdCd(state, params):
    if not params:
        uprint(os.path.join(state.rootPath, state.relPath))
        return
    if params[:1] == params[-1:] == '"':
        params = params[1:-1]
    state.relPath = walkPath(state, *setupDirChange(state, params.strip()))


def cmdDir(state, params):
    if params[:1] == params[-1:] == '"':
        params = params[1:-1]
    relPath, dir = locateDir(state, params.strip())
    dirRows, fileRows = [], []
    for item in dir.children:
        if isinstance(item, Dir):
            dirRows += [(item.mdate, 0, item.attr, item.name)]
        else:
            fileRows += [(item.mdate, item.size, item.attr, item.name)]
    orderIndexMap = {'M':0, 'S':1, 'A':2, 'N':3, '*':None}
    orderIndex = orderIndexMap[state.dirOrder[0]]
    if orderIndex is not None:
        dirRows.sort(
            key=operator.itemgetter(orderIndex),
            reverse=(state.listOrder[1] == '-')
        )
        fileRows.sort(
            key=operator.itemgetter(orderIndex),
            reverse=(state.listOrder[1] == '-')
        )
    modifyDispSize = {
        'B': lambda n: n,
        'K': lambda n: int(round(n / 2.0 ** 10)),
        'M': lambda n: int(round(n / 2.0 ** 20)),
        'G': lambda n: int(round(n / 2.0 ** 30)),
    }[state.unit]
    NAME_LEN = 44
    for a in dirRows:
        uprint('%11s %-12s %8s  %s' % (
            dateStr(a[0]), '<DIR>', attrStr(a[2]), trimName(a[3], NAME_LEN)))
    for a in fileRows:
        uprint('%11s %12s %8s  %s' % (
            dateStr(a[0]), modifyDispSize(a[1]), attrStr(a[2]), trimName(a[3], NAME_LEN)))


def cmdList(state, params):
    if params[:1] == params[-1:] == '"':
        params = params[1:-1]
    relPath, dir = locateDir(state, params.strip())
    dataRows = []
    totalStats = [0, 0, 0]
    fileStats = [0, 0, 0]
    for item in dir.children:
        try:
            stats = item.getListStats()
            dataRows += [(stats.dirs, stats.files, stats.bytes, item.name)]
            totalStats[0] += stats.dirs
            totalStats[1] += stats.files
            totalStats[2] += stats.bytes
        except AttributeError:
            # it's a File
            fileStats[1] += 1
            fileStats[2] += item.size
            totalStats[1] += 1
            totalStats[2] += item.size
    orderIndexMap = {'D':0, 'F':1, 'S':2, 'N':3, '*':None}
    orderIndex = orderIndexMap[state.listOrder[0]]
    if orderIndex is not None:
        dataRows.sort(
            key=operator.itemgetter(orderIndex),
            reverse=(state.listOrder[1] == '-')
        )
    modifyDispSize = {
        'B': lambda n: n,
        'K': lambda n: int(round(n / 2.0 ** 10)),
        'M': lambda n: int(round(n / 2.0 ** 20)),
        'G': lambda n: int(round(n / 2.0 ** 30)),
    }[state.unit]
    fileStats[2] = modifyDispSize(fileStats[2])
    totalStats[2] = modifyDispSize(totalStats[2])
    for data in dataRows:
        a = list(data)
        a[2] = modifyDispSize(a[2])
        uprint('%6d %6d %12d  %s' % tuple(a))
    uprint('%6s %6d %12d  %s' % tuple(['-'] + fileStats[1:] + ['<files>']))
    uprint('%6d %6d %12d  %s' % tuple(totalStats + ['<total>']))


def cmdExtCnt(state, params):
    if params[:1] == params[-1:] == '"':
        params = params[1:-1]
    relPath, dir = locateDir(state, params.strip())
    statsDict = defaultdict(lambda: ExtStats())
    for item in dir.children:
        item.addExtStats(statsDict)
    dataRows = []
    totalFiles, totalSize = 0, 0
    for ext, stats in statsDict.iteritems():
        dataRows += [(stats.files, stats.bytes, ext)]
        totalFiles += stats.files
        totalSize += stats.bytes
    orderIndexMap = {'F':0, 'S':1, 'N':2, '*':None}
    orderIndex = orderIndexMap[state.extOrder[0]]
    if orderIndex is not None:
        dataRows.sort(
            key=operator.itemgetter(orderIndex),
            reverse=(state.extOrder[1] == '-')
        )
    modifyDispSize = {
        'B': lambda n: n,
        'K': lambda n: int(round(n / 2.0 ** 10)),
        'M': lambda n: int(round(n / 2.0 ** 20)),
        'G': lambda n: int(round(n / 2.0 ** 30)),
    }[state.unit]
    totalSize = modifyDispSize(totalSize)
    for data in dataRows:
        a = list(data)
        a[1] = modifyDispSize(a[1])
        uprint('%6d %12d  %s' % tuple(a))
    uprint('%6d %12d  %s' % (totalFiles, totalSize, '<total>'))


def cmdScan(state, params):
    if params[:1] == params[-1:] == '"':
        params = params[1:-1]
    relPath, dir = locateDir(state, params.strip())
    absPath = os.path.join(state.rootPath, relPath)
    uprint('scanning "%s" ...' % os.path.join(state.rootPath, absPath))
    status = ScanStatus(absPath)
    dir.getChildren(absPath, status)
    status.cleanup()


def cmdOrder(state, params, attr, colFlags):
    cur = getattr(state, attr)
    if not params:
        uprint(cur)
        return
    newCol, newDir = '', ''
    for c in params.upper():
        if c in colFlags:
            newCol = c
        elif c in '+-':
            newDir = c
        else:
            raise CmdError('invalid order flag "%s"' % c)
    if newCol:
        cur = newCol + cur[1]
    if newDir:
        cur = cur[0] + newDir
    setattr(state, attr, cur)


def cmdListOrder(state, params):
    cmdOrder(state, params, 'listOrder', 'DFSN*')


def cmdDirOrder(state, params):
    cmdOrder(state, params, 'dirOrder', 'MSAN*')


def cmdExtOrder(state, params):
    cmdOrder(state, params, 'extOrder', 'FSN*')


def cmdUnit(state, params):
    if not params:
        uprint(state.unit)
        return
    params = params.upper()
    if len(params) != 1 or params not in 'BKMG':
        raise CmdError('invalid size unit "%s"' % params)
    state.unit = params


sys.exit(main(sys.argv[1:]))
