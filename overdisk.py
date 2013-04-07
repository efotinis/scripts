# TODO: store scan errors and add a cmd for showing them
# TODO: add a filter function (extensions, regexps, size/date ranges, attribs) to restrict operations
# TODO: allow optional traversal of junctions and soft-linked dirs
# TODO: allow command switches and replace "LO","DO","EO" with configurable default switches
# TODO: replace single order flags with multiple flags (lowercase:ascending, uppercase:descensing)
# TODO: detect hardlinks (no need to match; just use link count)
# TODO: detect namespace cycles (e.g. junctions)
# TODO: allow multiple roots (e.g. different drives or dirs); should allow setting an alias for each root
# TODO: option to display uncompressed long names
# TODO: option to display full attribs
# TODO: option to display numbers/sizes as percentage of total
# TODO: head/tail support for listings (nice)
# TODO: some kind of indicators (possibly before or after the prompt) for active filters ('f'), head/tail restriction ('...'), etc
# TODO: allow cmd aliases (to implement the short cmds)

import os
import re
import sys
import operator
import time
import collections
import argparse
import fnmatch
import itertools
import string

import win32file

import AutoComplete
import FindFileW
import console_stuff
import CommonTools

uprint = CommonTools.uprint


# string alignment types mapped to functions
STR_ALIGN = {'l': string.ljust, 'r': string.rjust, 'c': string.center, '': lambda s, n: s}


class PathError(Exception):
    """Path traversing error."""
    pass


class CmdError(Exception):
    """Command line error."""
    pass


class ListStats(object):
    """Directory statistics."""
    def __init__(self):
        self.dirs = 0
        self.files = 0
        self.bytes = 0


class ExtStats(object):
    """Extension statistics."""
    def __init__(self):
        self.files = 0
        self.bytes = 0


class Item(object):
    """Base directory item."""
    
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
                    self.size = None
                    self.attr = None
                    self.mdate = None
                    self.cdate = None
                    return
                else:
                    uprint('FATAL: could not get info for "%s"' % path)
                    raise SystemExit(-1)
        self.size = info.size
        self.attr = info.attr
        self.mdate = CommonTools.wintime_to_pyseconds(info.modify)
        self.cdate = CommonTools.wintime_to_pyseconds(info.create)


class File(Item):
    """File item."""
    
    def __init__(self, path, status=None):
        Item.__init__(self, path)
            
    def addListStats(self, stats, filter_obj):
        if filter_obj.test(self.name):
            stats.files += 1
            stats.bytes += self.size
        
    def addExtStats(self, statsDict, filter_obj):
        if filter_obj.test(self.name):
            ext = os.path.splitext(self.name)[1].lower()
            stats = statsDict[ext]
            stats.files += 1
            stats.bytes += self.size


class Dir(Item):        
    """Directory item."""
    
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
        """Return an immediate subdir."""
        if name in ('', '.'):
            return self
        for c in self.children:
            if c.name.lower() == name.lower():
                return c
        else:
            raise PathError('no child named "%s"' % name)
        
    def getSubPath(self, path):
        """Return a subdir, 1 or more levels deeper, but never higher.
        "path" must be relative, without any ".." tokens."""
        if not path:
            return self
        if os.path.sep in path:
            s1, s2 = path.split(os.path.sep, 1)
            return self.getSubDir(s1).getSubPath(s2)
        else:
            return self.getSubDir(path)
        
    def getListStats(self, filter_obj):
        """Return total dir, files and bytes recursively."""
        stats = ListStats()
        self.addListStats(stats, filter_obj)
        return stats
    
    def addListStats(self, stats, filter_obj):
        stats.dirs += 1
        for c in self.children:
            c.addListStats(stats, filter_obj)
            
    def addExtStats(self, statsDict, filter_obj):
        for c in self.children:
            c.addExtStats(statsDict, filter_obj)


def showHelp():
    print '''
   R | ROOT [dir]    Set (or show) root directory.
  CD | CHDIR [dir]   Set (or show) current directory.
   D | DIR [dir]     Show directory contents.
   L | LIST [dir]    Show directory entry statistics.
   E | EXTCNT [dir]  Show directory extension statistics (files only).
   S | SCAN [dir]    Rescan directory.
   G | GO [dir]      Open directory in Explorer.
   F | FILTER [flt]  Set (or show) filename filter. Use "*" to include all.
                     Filtering affects DIR, LIST, and EXTCNT.
                     Param is a sequence of glob patterns to include.
                     Prepending a pattern with "/" will exclude matches.
  HT | HEADTAIL [n]  Set (or show) listing head/tail count. Listing rows shown:
                     all (n=0), first n (n>0), last n (n<0)
                     Affects LIST and EXTCNT output.
  DO | DIRORDER [dircol][dirctn]
  LO | LISTORDER [listcol][dirctn]  
  EO | EXTORDER [extcol][dirctn]
                     Set (or show) sort order for DIR, LIST and EXTCNT.
   U | UNIT [unit]   Set (or show) size unit. One of "bkmgt*".
       CLS           Clear screen.
   ? | HELP          Show help.
   Q | QUIT          Exit.

DIR, LIST, EXTCNT and SCAN default to current directory.

Order flags:
  listcol      dircol         extcol       dirctn
  -----------  -------------  -----------  ------------
  d dirs       m modify date  f files      + ascending
  f files      s size         s size       - descending
  s size       a attributes   n name       
  n name       n name         * unordered
  * unordered  * unordered    

Dir display extra attribute flags (hex):
  01 temporary      10 offline
  02 sparse file    20 not content indexed
  04 reparse point  40 encrypted
  08 compressed
'''[1:-1]


RX_CMD = re.compile(
    r'''^
        \s*             # optional leading space
        (\w+|\?|\.\.)        # alnum word, "?", or ".."
        (?:
            \s+(.*)     # optional params with leading space
        )?
    $''',
    re.IGNORECASE | re.VERBOSE)


class Filter(object):
    """File filtering object."""

    def __init__(self, rule_str):
        self.pattern = rule_str
        self.rules = []
        for s in rule_str.split():
            include = True
            if s[:1] == '/':
                include = False
                s = s[1:]
            if s:
                patt = fnmatch.translate(s)
                # TODO: make case-matching depend on platfrom and/or configurable
                self.rules += [(include, re.compile(patt, re.IGNORECASE))]
        self.initial = (self.rules[0][0] == False) if self.rules else True

    def test(self, s):
        ret = self.initial
        for include, rx in self.rules:
            if ret != include:
                if include and rx.match(s):
                    ret = True
                elif not include and rx.match(s):
                    ret = False
        return ret


class State(object):
    """Global program state."""
    def __init__(self):
        self.root = None        # root Dir object
        self.rootPath = ''      # root dir path (must be unicode -> listdir bug)
        self.relPath = ''       # current relative dir path
        self.listOrder = '*+'   # list sorting
        self.dirOrder = '*+'    # dir sorting
        self.extOrder = '*+'    # extcnt sorting
        self.unit = 'b'         # display size unit
        self.filter = Filter('*')  # filename filter
        self.headTailCount = 0  # listing head/tail count


class CmdDispatcher(object):
    """Command dispatcher."""
    
    def __init__(self, state):
        self.state = state
        self.entries = (
            (('?', 'help'),   lambda dummy1, dummy2: showHelp()),
            (('cd', 'chdir'), cmdCd),
            (('..',),         lambda state, params: cmdCd(state, '..')),
            (('d', 'dir'),    cmdDir),
            (('l', 'list'),   cmdList),
            (('e', 'extcnt'), cmdExtCnt),
            (('r', 'root'),   cmdRoot),
            (('s', 'scan'),   cmdScan),
            (('g', 'go'),     cmdGo),
            (('f', 'filter'), cmdFilter),
            (('ht', 'headtail'), cmdHeadTail),
            (('lo', 'listorder'), cmdListOrder),
            (('do', 'dirorder'),  cmdDirOrder),
            (('eo', 'extorder'),  cmdExtOrder),
            (('u', 'unit'),   cmdUnit),
            (('cls',),         lambda dummy1, dummy2: cmdCls()),
        )
        
    def dispatch(self, cmd, params):
        for cmdIds, func in self.entries:
            if cmd.lower() in cmdIds:
                func(self.state, params)
                return
        else:
            raise CmdError('unknown command "%s"' % cmd)


def head_tail_filter(seq, count):
    """Yield seq items, restricting their number.

    Items returned for count=N:
        N=0  all
        N>0  first N
        N<0  last N
    """
    if count == 0:
        for x in seq:
            yield x
    elif count > 0:
        for i, x in enumerate(seq):
            if i < count:
                yield x
            else:
                break
    else:  # count < 0
        a = []
        for x in seq:
            a += [x]
            a = a[count:]
        for x in a:
            yield x


TableColumn = collections.namedtuple('TableColumn', 'caption alignment formatter')


def pad_table_row(a, alignments, widths, joiner):
    """Pad and join row cells."""
    a = [STR_ALIGN[alignment](s, width) for (s, alignment, width) in zip(a, alignments, widths)]
    return joiner.join(a)


def output_table(cols, data, footer=0):
    """Generate table rows, given a list of TableColumn objects and a 2D list of cell values."""
    rows = [[col.formatter(x, a) for (x, col) in zip(a, cols)]
            for a in data]
    captions = [c.caption for c in cols]
    max_widths = [max(len(row[i]) for row in itertools.chain([captions], rows))
                  for i in range(len(cols))]
    alignments = [c.alignment for c in cols]
    joiner = '  '

    yield pad_table_row(captions, alignments, max_widths, joiner)
    yield pad_table_row(['-' * n for n in max_widths], alignments, max_widths, joiner)
    if footer > 0:
        rows, footer_rows = rows[:-footer], rows[-footer:]
    else:
        rows, footer_rows = rows, []
    for row in rows:
        yield pad_table_row(row, alignments, max_widths, joiner)
    if footer_rows:
        yield pad_table_row(['-' * n for n in max_widths], alignments, max_widths, joiner)
        for row in footer_rows:
            yield pad_table_row(row, alignments, max_widths, joiner)


def getCandidatePaths(state, seed):
    head, tail = os.path.split(seed)
    try:
        relPath, dirObj = locateDir(state, head)
    except PathError:
        return []
    if tail:
        tail = tail.lower()
        matches = lambda s: s.lower().startswith(tail)
    else:
        matches = lambda s: True
    a = []
    for item in dirObj.children:
        if isinstance(item, Dir) and matches(item.name):
            #a += [item.name]
            a += [os.path.join(head, item.name)]
    return a


class ScanStatus(object):
    """Manage temporary status output during dir scanning."""

    def __init__(self, root):
        self.spo = console_stuff.SamePosOutput(fallback=True)
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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


def walkPath(state, curRelPath, parts):
    """Walk directories starting from a current relative path
    and using a list of token parts (incl. "." and "..").
    Underflowing ".." tokens (trying to go above state.root) are ignored.
    Returns resulting relative path or throws PathError."""
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
    """Return initial relative path and list of item tokens to walk
    during a dir change. Tokens may contain "." and ".." items."""
    parts = os.path.normpath(newPath).split(os.path.sep)  # len >= 1
    if parts[0] == '':
        # new path is absolute
        return '', parts[1:]
    else:
        # new path is relative
        return state.relPath, parts


def locateDir(state, newPath):
    """Find dir by following "newPath" (absolute or relative)
    and return its relative path and Dir object."""
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
    """Replace some chars before the ext with '<..>'
    if needed to restrict size of file name.
    Append a single '>' if name or ext is too long."""
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
    with ScanStatus(newRootPath) as status:
        state.root = Dir(newRootPath, status)
    state.rootPath = newRootPath
    state.relPath = ''


def cmdCd(state, params):
    if not params:
        uprint(os.path.join(state.rootPath, state.relPath))
        return
    if params[:1] == params[-1:] == '"':
        params = params[1:-1]
    state.relPath = walkPath(state, *setupDirChange(state, params.strip()))


def size_title_and_formatter(unit):
    """Return the title and formatting func for a specific size unit."""
    if unit == 'b':
        return 'bytes', lambda n: '{:,}'.format(n)
    elif unit == 'k':
        return 'KB', lambda n: '{:,}'.format(n / 2**10)
    elif unit == 'm':
        return 'MB', lambda n: '{:,}'.format(n / 2**20)
    elif unit == 'g':
        return 'GB', lambda n: '{:,}'.format(n / 2**30)
    elif unit == 't':
        return 'TB', lambda n: '{:,}'.format(n / 2**40)
    elif unit == '*':
        return 'size', lambda n: CommonTools.prettysize(n)
    else:
        raise ValueError('bad unit', unit)


def cmdDir(state, params):
    if params[:1] == params[-1:] == '"':
        params = params[1:-1]
    relPath, dir = locateDir(state, params.strip())
    dataRows = []
    for item in dir.children:
        if isinstance(item, Dir) or state.filter.test(item.name):
            dataRows += [(item.mdate, item.size, item.attr, item.name)]
    orderIndexMap = {'m':0, 's':1, 'a':2, 'n':3, '*':None}
    orderIndex = orderIndexMap[state.dirOrder[0]]
    if orderIndex is not None:
        dataRows.sort(
            key=operator.itemgetter(orderIndex),
            reverse=(state.listOrder[1] == '-')
        )

    is_dir_row = lambda row: bool(row[2] & win32file.FILE_ATTRIBUTE_DIRECTORY)

    # move dirs to beginning
    dataRows.sort(key=is_dir_row, reverse=True)

    size_title, size_fmt = size_title_and_formatter(state.unit)
    size_str = lambda x, row: '<DIR>' if is_dir_row(row) else size_fmt(x)
    date_str = lambda x, row: dateStr(x)
    attr_str = lambda x, row: attrStr(x)
    NAME_LEN = 44  # FIXME: calc from console if possible
    name_str = lambda x, row: trimName(x, NAME_LEN)

    cols = [
        TableColumn('date', 'l', date_str),
        TableColumn(size_title, 'r', size_str),
        TableColumn('attr', 'l', attr_str),
        TableColumn('name', '', name_str),
        ]
    for s in output_table(cols, dataRows):
        uprint(s)


def cmdList(state, params):
    if params[:1] == params[-1:] == '"':
        params = params[1:-1]
    relPath, dir = locateDir(state, params.strip())
    dataRows = []
    totalStats = [0, 0, 0]
    fileStats = [0, 0, 0]
    for item in dir.children:
        try:
            stats = item.getListStats(state.filter)
            dataRows += [(stats.dirs, stats.files, stats.bytes, item.name)]
            totalStats[0] += stats.dirs
            totalStats[1] += stats.files
            totalStats[2] += stats.bytes
        except AttributeError:
            # it's a File
            if state.filter.test(item.name):
                fileStats[1] += 1
                fileStats[2] += item.size
                totalStats[1] += 1
                totalStats[2] += item.size
    orderIndexMap = {'d':0, 'f':1, 's':2, 'n':3, '*':None}
    orderIndex = orderIndexMap[state.listOrder[0]]
    if orderIndex is not None:
        dataRows.sort(
            key=operator.itemgetter(orderIndex),
            reverse=(state.listOrder[1] == '-')
        )

    dataRows = list(head_tail_filter(dataRows, state.headTailCount))
    dataRows += [fileStats + ['<files>']] + \
                [totalStats + ['<total>']]

    size_title, size_fmt = size_title_and_formatter(state.unit)
    number_str = lambda x, row: '{:,}'.format(x)
    size_str = lambda x, row: size_fmt(x)
    identity = lambda s, row: s

    cols = [
        TableColumn('dirs', 'r', number_str),
        TableColumn('files', 'r', number_str),
        TableColumn(size_title, 'r', size_str),
        TableColumn('name', '', identity),
        ]
    for s in output_table(cols, dataRows, 2):
        uprint(s)


def cmdExtCnt(state, params):
    if params[:1] == params[-1:] == '"':
        params = params[1:-1]
    relPath, dir = locateDir(state, params.strip())
    statsDict = collections.defaultdict(lambda: ExtStats())
    for item in dir.children:
        item.addExtStats(statsDict, state.filter)
    dataRows = []
    totalFiles, totalSize = 0, 0
    for ext, stats in statsDict.iteritems():
        dataRows += [(stats.files, stats.bytes, ext)]
        totalFiles += stats.files
        totalSize += stats.bytes
    orderIndexMap = {'f':0, 's':1, 'n':2, '*':None}
    orderIndex = orderIndexMap[state.extOrder[0]]
    if orderIndex is not None:
        dataRows.sort(
            key=operator.itemgetter(orderIndex),
            reverse=(state.extOrder[1] == '-')
        )

    dataRows = list(head_tail_filter(dataRows, state.headTailCount))
    dataRows += [[totalFiles, totalSize, '<total>']]

    size_title, size_fmt = size_title_and_formatter(state.unit)
    number_str = lambda x, row: '{:,}'.format(x)
    size_str = lambda x, row: size_fmt(x)
    identity = lambda s, row: s

    cols = [
        TableColumn('files', 'r', number_str),
        TableColumn(size_title, 'r', size_str),
        TableColumn('ext', '', identity),
        ]
    for s in output_table(cols, dataRows, 1):
        uprint(s)


def cmdScan(state, params):
    if params[:1] == params[-1:] == '"':
        params = params[1:-1]
    relPath, dir = locateDir(state, params.strip())
    absPath = os.path.join(state.rootPath, relPath)
    uprint('scanning "%s" ...' % os.path.join(state.rootPath, absPath))
    with ScanStatus(absPath) as status:
        dir.getChildren(absPath, status)


def cmdGo(state, params):
    if params[:1] == params[-1:] == '"':
        params = params[1:-1]
    relPath, dir = locateDir(state, params.strip())
    absPath = os.path.join(state.rootPath, relPath)
    os.startfile(absPath)


def cmdFilter(state, params):
    if not params:
        print state.filter.pattern
        return
    state.filter = Filter(params)


def cmdHeadTail(state, params):
    if not params:
        print state.headTailCount
        return
    try:
        state.headTailCount = int(params, 10)
    except ValueError:
        raise CmdError('invalid number "%s"' % params)


def cmdOrder(state, params, attr, colFlags):
    cur = getattr(state, attr)
    if not params:
        uprint(cur)
        return
    newCol, newDir = '', ''
    for c in params.lower():
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
    cmdOrder(state, params, 'listOrder', 'dfsn*')


def cmdDirOrder(state, params):
    cmdOrder(state, params, 'dirOrder', 'msan*')


def cmdExtOrder(state, params):
    cmdOrder(state, params, 'extOrder', 'fsn*')


def cmdUnit(state, params):
    if not params:
        uprint(state.unit)
        return
    if len(params) != 1 or params not in 'bkmgt*':
        raise CmdError('invalid size unit "%s"' % params)
    state.unit = params


def cmdCls():
    console_stuff.cls()


def parse_args():
    ap = argparse.ArgumentParser(description='interactive OverDisk CLI')
    ap.add_argument('root', nargs='?', metavar='DIR', default='.',
                    help='the initial root dir; default: "%(default)s"')
    args = ap.parse_args()
    args.root = os.path.abspath(unicode(args.root))
    if not os.path.isdir(args.root):
        ap.error('not a dir: "%s"' % args.root)
    return args


if __name__ == '__main__':
    args = parse_args()

    state = State()
    state.rootPath = args.root
    cmdDispatcher = CmdDispatcher(state)

    uprint('scanning "%s" ...' % state.rootPath)
    with ScanStatus(state.rootPath) as status:
        state.root = Dir(state.rootPath, status)

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
