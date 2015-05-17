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
# TODO: make commands case-sensitive
# TODO: allow multiple dir params to commands that it make sense (e.g. extcnt, scan, and go)

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
import console_stuff
import efutil
import winfiles
import six

uprint = efutil.uprint


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
    
    def __init__(self, path, data):
        self.name = data.name
        self.size = data.size
        self.attr = data.attr
        self.mdate = data.modify
        self.cdate = data.create


class File(Item):
    """File item."""
    
    def __init__(self, path, data, status=None):
        Item.__init__(self, path, data)
            
    def add_list_stats(self, stats, filter_obj):
        if filter_obj.test(self.name):
            stats.files += 1
            stats.bytes += self.size
        
    def add_ext_stats(self, stats_dict, filter_obj):
        if filter_obj.test(self.name):
            ext = os.path.splitext(self.name)[1].lower()
            stats = stats_dict[ext]
            stats.files += 1
            stats.bytes += self.size


class Dir(Item):        
    """Directory item."""
    
    def __init__(self, path, data, status=None):
        Item.__init__(self, path, data)
        if status:
            status.update(path)
        self.get_children(path, status)
        
    def get_children(self, path, status=None):
        self.children = []
        try:
            for data in winfiles.find(os.path.join(path, '*'), times='unix'):
                child_path = os.path.join(path, data.name)
                factory = Dir if winfiles.is_dir(data.attr) else File
                self.children += [factory(child_path, data, status)]
        except WindowsError as x:
            msg = 'WARNING: could not list contents of "%s"; reason: %s' % (path, x.strerror)
            status.static_print(msg)
            return
            
    def get_sub_dir(self, name):
        """Return an immediate subdir."""
        if name in ('', '.'):
            return self
        for c in self.children:
            if c.name.lower() == name.lower():
                return c
        else:
            raise PathError('no child named "%s"' % name)
        
    def get_sub_path(self, path):
        """Return a subdir, 1 or more levels deeper, but never higher.
        "path" must be relative, without any ".." tokens."""
        if not path:
            return self
        if os.path.sep in path:
            s1, s2 = path.split(os.path.sep, 1)
            return self.get_sub_dir(s1).get_sub_path(s2)
        else:
            return self.get_sub_dir(path)
        
    def get_list_stats(self, filter_obj):
        """Return total dir, files and bytes recursively."""
        stats = ListStats()
        self.add_list_stats(stats, filter_obj)
        return stats
    
    def add_list_stats(self, stats, filter_obj):
        stats.dirs += 1
        for c in self.children:
            c.add_list_stats(stats, filter_obj)
            
    def add_ext_stats(self, stats_dict, filter_obj):
        for c in self.children:
            c.add_ext_stats(stats_dict, filter_obj)


def cmd_help(state, params):
    if params:
        raise CmdError('no params required')
    print '''
Commands:
  ROOT [dir]    Set (or show) root directory.
  CHDIR [dir]   Set (or show) current directory. As a shortcut, "\\" and ".."
                can be used without the command name.
  DIR [dir]     Show directory contents.
  LIST [dir]    Show directory entry statistics.
  EXTCNT [dir]  Show directory extension statistics (files only).
  SCAN [dir]    Rescan directory.
  GO [dir]      Open directory in Explorer.
  FILTER [flt]  Set (or show) filename filter. Use "*" to include all.
                Filtering affects DIR, LIST, and EXTCNT.
                Param is a sequence of glob patterns to include.
                Prepending a pattern with "/" will exclude matches.
  TAIL [n]      Set (or show) tail count for listings.
                0: all, >0: last n, <0: first n
                Affects LIST and EXTCNT output.
  DIRORDER [dircol]
  LISTORDER [listcol]
  EXTORDER [extcol]
                Set (or show) sort order for DIR, LIST and EXTCNT.
  UNIT [unit]   Set (or show) size unit. One of "bkmgtpe*".
  ALIAS [name[=[value]]]
                Set (or show) one or more simply command aliases.
                No params show all aliases, 'name' shows aliases starting
                with name, 'name=' deletes and 'name=value' sets an alias.
  COLSEP [sep]  Set (or show) the string used to separate table columns.
  CLS           Clear screen.
  HELP          Show help.
  QUIT          Exit.

DIR, LIST, EXTCNT and SCAN default to current directory.

Order flags (lowercase is ascending; use uppercase for descending):
  listcol      dircol         extcol
  -----------  -------------  -----------
  d dirs       m modify date  f files
  f files      s size         s size
  s size       a attributes   n name
  n name       n name         * unordered
  * unordered  * unordered

Dir display extra attribute flags (hex):
  01 temporary      10 offline
  02 sparse file    20 not content indexed
  04 reparse point  40 encrypted
  08 compressed
'''[1:-1]


def split_cmd(s):
    """Split a param string like a shell does.

    Handles adjacent tokens and double quotes (incl. missing closing quote).
    """
    # find: spaces, quoted, and unquoted tokens
    a = re.findall(r'(\s+)|"(.*?)(?:"|(\s+)$)|([^\s"]+)', s)

    # replace spaces with None and combine the rest of the string tokens;
    # s1 is a quoted token, minus s2, which is the closing quote or
    # the trailing space of an non-terminated quoted token;
    # s3 is an unquoted token
    a = [None if space else s1+s2+s3 for space, s1, s2, s3 in a]

    # remove trailing space; the leading space, if any, is needed
    if a and a[-1] is None:
        del a[-1]
        
    # combine consequtive strings, adding a new one when None is found
    ret = []
    for s in a:
        if s is None:
            ret += ['']
        elif ret:
            ret[-1] += s
        else:
            ret = [s]
    return ret


def test_split_cmd():
    f = split_cmd

    # empty
    assert(f('') == [])
    assert(f(' ') == [])
    assert(f('     ') == [])

    # single
    assert(f('a') == ['a'])
    assert(f(' a') == ['a'])
    assert(f('a ') == ['a'])
    assert(f(' a ') == ['a'])

    # quoted
    assert(f('"a"') == ['a'])
    assert(f('"a" b') == ['a', 'b'])

    # multiple
    assert(f('a b') == ['a', 'b'])
    assert(f('a  b') == ['a', 'b'])
    assert(f('"a" "b"') == ['a','b'])

    # adjacent
    assert(f('"a"b') == ['ab'])
    assert(f('"a""b"') == ['ab'])

    # missing end quote
    assert(f('"a""b') == ['ab'])
    assert(f('"a" "b') == ['a','b'])
    assert(f('"a" "b ') == ['a','b '])


class Filter(object):
    """File filtering object."""

    def __init__(self, rule_strings):
        self.rules = []
        for s in rule_strings:
            include = True
            if s[:1] == '/':
                include = False
                s = s[1:]
            if s:
                patt = fnmatch.translate(s)
                # TODO: make case-matching depend on platfrom and/or configurable
                self.rules += [(include, re.compile(patt, re.IGNORECASE))]
        self.initial = (self.rules[0][0] == False) if self.rules else True
        self.pattern_string = ' '.join('"'+s+'"' if ' ' in s else s
                                       for s in rule_strings)

    def __str__(self):
        return self.pattern_string

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
        self.root = None            # root Dir object
        self.root_path = ''         # root dir path (must be unicode -> listdir bug)
        self.rel_path = ''          # current relative dir path
        self.list_order = '*'       # list sorting
        self.dir_order = '*'        # dir sorting
        self.ext_order = '*'        # extcnt sorting
        self.unit = 'b'             # display size unit
        self.filter = Filter(['*']) # filename filter
        self.tail_count = 0         # listing tail count
        self.aliases = {            # simple command aliases
            '?': 'help', 'cd': 'chdir', 'd': 'dir', 'l': 'list', 'e': 'extcnt',
            'r': 'root', 's': 'scan', 'g': 'go', 'f': 'filter', 't': 'tail',
            'lo': 'listorder', 'do': 'dirorder', 'eo': 'extorder', 'u': 'unit',
            'cs': 'colsep', 
            'a': 'alias', 'q': 'quit'
        }
        self.colsep = '  '          # table column separator


class CmdDispatcher(object):
    """Command dispatcher."""
    
    def __init__(self, state):
        self.state = state
        self.entries = {
            'help': cmd_help,
            'chdir': cmd_cd,
            '..': lambda state, params: cmd_cd(state, ['..']),
            '\\': lambda state, params: cmd_cd(state, ['\\']),
            'dir': cmd_dir,
            'list': cmd_list,
            'extcnt': cmd_extcnt,
            'root': cmd_root,
            'scan': cmd_scan,
            'go': cmd_go,
            'filter': cmd_filter,
            'tail': cmd_tail,
            'listorder': cmd_listorder,
            'dirorder': cmd_dirorder,
            'extorder': cmd_extorder,
            'unit': cmd_unit,
            'alias': cmd_alias,
            'colsep': cmd_colsep,
            'cls': cmd_cls,
            'quit': cmd_quit,
        }
        
    def dispatch(self, cmd, params):
        func = self.entries.get(cmd.lower())
        if func is None:
            raise CmdError('unknown command "%s"' % cmd)
        func(self.state, params)


def tail_filter(seq, count):
    """Yield seq items, restricting their number.

    Items returned for count=N:
        N=0  all
        N>0  last N
        N<0  first N
    """
    # NOTE: we can't use itertools.islice, since it doesn't support negative indices
    if count == 0:
        for x in seq:
            yield x
    elif count < 0:
        for i, x in enumerate(seq):
            if i < -count:
                yield x
            else:
                break
    else:  # count > 0
        a = []
        for x in seq:
            a += [x]
            a = a[-count:]
        for x in a:
            yield x


TableColumn = collections.namedtuple('TableColumn', 'caption alignment formatter')


def pad_table_row(a, alignments, widths, joiner):
    """Pad and join row cells."""
    a = [STR_ALIGN[alignment](s, width) for (s, alignment, width) in zip(a, alignments, widths)]
    return joiner.join(a)


def output_table(cols, data, colsep, footer=0):
    """Generate table rows, given a list of TableColumn objects and a 2D list of cell values."""
    rows = [[col.formatter(x, a) for (x, col) in zip(a, cols)]
            for a in data]
    captions = [c.caption for c in cols]
    max_widths = [max(len(row[i]) for row in itertools.chain([captions], rows))
                  for i in range(len(cols))]
    alignments = [c.alignment for c in cols]

    yield pad_table_row(captions, alignments, max_widths, colsep)
    yield pad_table_row(['-' * n for n in max_widths], alignments, max_widths, colsep)
    if footer > 0:
        rows, footer_rows = rows[:-footer], rows[-footer:]
    else:
        rows, footer_rows = rows, []
    for row in rows:
        yield pad_table_row(row, alignments, max_widths, colsep)
    if footer_rows:
        yield pad_table_row(['-' * n for n in max_widths], alignments, max_widths, colsep)
        for row in footer_rows:
            yield pad_table_row(row, alignments, max_widths, colsep)


def get_candidate_paths(state, seed):
    head, tail = os.path.split(seed)
    try:
        rel_path, dir_obj = locate_dir(state, head)
    except PathError:
        return []
    if tail:
        tail = tail.lower()
        matches = lambda s: s.lower().startswith(tail)
    else:
        matches = lambda s: True
    a = []
    for item in dir_obj.children:
        if isinstance(item, Dir) and matches(item.name):
            #a += [item.name]
            a += [os.path.join(head, item.name)]
    return a


class ScanStatus(object):
    """Manage temporary status output during dir scanning."""

    def __init__(self, root):
        self.spo = console_stuff.SamePosOutput(fallback=True)
        self.root = root
        self.last_update = time.time()

    def update(self, s):
        t = time.time()
        # update only every 250ms; speeds up scanning
        # and gives user time to read the status
        if t - self.last_update < 0.25:
            return
        self.last_update = t
        self.spo.restore(True)
        s = s[len(self.root):]  # trim root
        uprint(s[:79])  # TODO: use a better trimming func, removing middle path elements

    def cleanup(self):
        self.spo.restore(True)

    def static_print(self, s):
        """Print a static line and continue updates to the next line."""
        self.spo.restore(True)
        print s
        self.spo.reset()

    def __enter__(self):
##        self._start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
##        t = time.time() - self._start_time
##        self.static_print('[scan time: %.2f s]' % t)
        self.cleanup()


def walk_path(state, cur_rel_path, parts):
    """Walk directories starting from a current relative path
    and using a list of token parts (incl. "." and "..").
    Underflowing ".." tokens (trying to go above state.root) are ignored.
    Returns resulting relative path or throws PathError."""
    a = cur_rel_path.split(os.path.sep) if cur_rel_path else []
    for s in parts:
        if s == '.':
            continue
        elif s == '..':
            del a[-1:]
        else:
            try:
                state.root.get_sub_path(os.path.join(*(a + [s])))
                a += [s]
            except PathError:
                raise
    return os.path.join(*a) if a else ''


def setup_dir_change(state, new_path):
    """Return initial relative path and list of item tokens to walk
    during a dir change. Tokens may contain "." and ".." items."""
    parts = os.path.normpath(new_path).split(os.path.sep)  # len >= 1
    if parts[0] == '':
        # new path is absolute
        return '', parts[1:]
    else:
        # new path is relative
        return state.rel_path, parts


def locate_dir(state, new_path):
    """Find dir by following "new_path" (absolute or relative)
    and return its relative path and Dir object."""
    if not new_path:
        rel_path = state.rel_path
    else:
        rel_path = walk_path(state, *setup_dir_change(state, new_path))
    return rel_path, state.root.get_sub_path(rel_path)
    

def date_to_str(n):
    a = list(time.localtime(n))[:5]
    a[0] %= 100
    return '%02d%02d%02d-%02d%02d' % tuple(a)


def attr_to_str(n):
    extra = (n & 0xff00) >> 8
    s = '%02x' % extra if extra else '..'
    s += '-'
    s += 'A' if n & win32file.FILE_ATTRIBUTE_ARCHIVE   else '.'
    s += 'D' if n & win32file.FILE_ATTRIBUTE_DIRECTORY else '.'
    s += 'S' if n & win32file.FILE_ATTRIBUTE_SYSTEM    else '.'
    s += 'H' if n & win32file.FILE_ATTRIBUTE_HIDDEN    else '.'
    s += 'R' if n & win32file.FILE_ATTRIBUTE_READONLY  else '.'
    return s


def trim_name(s, n):
    """Replace some chars before the ext with '<..>'
    if needed to restrict size of file name.
    Append a single '>' if name or ext is too long."""
    if len(s) <= n:
        return s
    name, ext = os.path.splitext(s)
    if len(ext) >= n or n-len(ext)-4 <= 0:
        return s[:n-1] + '>'
    return name[:n-len(ext)-4] + '<..>' + ext


def cmd_root(state, params):
    if len(params) > 1:
        raise CmdError('at most one param required')
    if not params:
        uprint(state.root_path)
        return
    if params[:1] == params[-1:] == '"':
        params = params[1:-1]
    new_root_path = os.path.abspath(six.text_type(params[0]))
    if not os.path.isdir(new_root_path):
        raise PathError('not a dir: "%s"' % new_root_path)
    with ScanStatus(new_root_path) as status:
        data = winfiles.find(new_root_path).next()
        state.root = Dir(new_root_path, data, status)
    state.root_path = new_root_path
    state.rel_path = ''


def cmd_cd(state, params):
    if len(params) > 1:
        raise CmdError('at most one param required')
    if not params:
        uprint(os.path.join(state.root_path, state.rel_path))
        return
    (target,) = params
    state.rel_path = walk_path(state, *setup_dir_change(state, target))


def size_title_and_formatter(unit):
    """Return the title and formatting func for a specific size unit."""
    if unit == 'b':
        return 'bytes', lambda n: '{:,}'.format(n)
    elif unit == 'k':
        return 'KB', lambda n: '{:,.0f}'.format(n / 2.0**10)
    elif unit == 'm':
        return 'MB', lambda n: '{:,.0f}'.format(n / 2.0**20)
    elif unit == 'g':
        return 'GB', lambda n: '{:,.0f}'.format(n / 2.0**30)
    elif unit == 't':
        return 'TB', lambda n: '{:,.0f}'.format(n / 2.0**40)
    elif unit == 'p':
        return 'PB', lambda n: '{:,.0f}'.format(n / 2.0**50)
    elif unit == 'e':
        return 'EB', lambda n: '{:,.0f}'.format(n / 2.0**60)
    elif unit == '*':
        return 'size', lambda n: efutil.prettysize(n)
    else:
        raise ValueError('bad unit', unit)


def cmd_dir(state, params):
    if len(params) > 1:
        raise CmdError('at most one param required')
    rel_path, dir = locate_dir(state, params[0] if params else '')
    data_rows = []
    for item in dir.children:
        if isinstance(item, Dir) or state.filter.test(item.name):
            data_rows += [(item.mdate, item.size, item.attr, item.name)]
    order_index_map = {'m':0, 's':1, 'a':2, 'n':3, '*':None}
    order_index = order_index_map[state.dir_order.lower()]
    if order_index is not None:
        data_rows.sort(
            key=operator.itemgetter(order_index),
            reverse=(not state.list_order.islower())
        )

    is_dir_row = lambda row: bool(row[2] & win32file.FILE_ATTRIBUTE_DIRECTORY)

    # move dirs to beginning
    data_rows.sort(key=is_dir_row, reverse=True)

    size_title, size_fmt = size_title_and_formatter(state.unit)
    size_str = lambda x, row: '<DIR>' if is_dir_row(row) else size_fmt(x)
    date_str = lambda x, row: date_to_str(x)
    attr_str = lambda x, row: attr_to_str(x)
    NAME_LEN = 44  # FIXME: calc from console if possible
    name_str = lambda x, row: trim_name(x, NAME_LEN)

    cols = [
        TableColumn('date', 'l', date_str),
        TableColumn(size_title, 'r', size_str),
        TableColumn('attr', 'l', attr_str),
        TableColumn('name', '', name_str),
        ]
    for s in output_table(cols, data_rows, state.colsep):
        uprint(s)


def cmd_list(state, params):
    if len(params) > 1:
        raise CmdError('at most one param required')
    rel_path, dir = locate_dir(state, params[0] if params else '')
    data_rows = []
    total_stats = [0, 0, 0]
    file_stats = [0, 0, 0]
    for item in dir.children:
        try:
            stats = item.get_list_stats(state.filter)
            data_rows += [(stats.dirs, stats.files, stats.bytes, item.name)]
            total_stats[0] += stats.dirs
            total_stats[1] += stats.files
            total_stats[2] += stats.bytes
        except AttributeError:
            # it's a File
            if state.filter.test(item.name):
                file_stats[1] += 1
                file_stats[2] += item.size
                total_stats[1] += 1
                total_stats[2] += item.size
    order_index_map = {'d':0, 'f':1, 's':2, 'n':3, '*':None}
    order_index = order_index_map[state.list_order.lower()]
    if order_index is not None:
        data_rows.sort(
            key=operator.itemgetter(order_index),
            reverse=(not state.list_order.islower())
        )

    data_rows = list(tail_filter(data_rows, state.tail_count))
    data_rows += [file_stats + ['<files>']] + \
                [total_stats + ['<total>']]

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
    for s in output_table(cols, data_rows, state.colsep, 2):
        uprint(s)


def cmd_extcnt(state, params):
    if len(params) > 1:
        raise CmdError('at most one param required')
    rel_path, dir = locate_dir(state, params[0] if params else '')
    stats_dict = collections.defaultdict(lambda: ExtStats())
    for item in dir.children:
        item.add_ext_stats(stats_dict, state.filter)
    data_rows = []
    total_files, total_size = 0, 0
    for ext, stats in stats_dict.iteritems():
        data_rows += [(stats.files, stats.bytes, ext)]
        total_files += stats.files
        total_size += stats.bytes
    order_index_map = {'f':0, 's':1, 'n':2, '*':None}
    order_index = order_index_map[state.ext_order.lower()]
    if order_index is not None:
        data_rows.sort(
            key=operator.itemgetter(order_index),
            reverse=(not state.ext_order.islower())
        )

    data_rows = list(tail_filter(data_rows, state.tail_count))
    data_rows += [[total_files, total_size, '<total>']]

    size_title, size_fmt = size_title_and_formatter(state.unit)
    number_str = lambda x, row: '{:,}'.format(x)
    size_str = lambda x, row: size_fmt(x)
    identity = lambda s, row: s

    cols = [
        TableColumn('files', 'r', number_str),
        TableColumn(size_title, 'r', size_str),
        TableColumn('ext', '', identity),
        ]
    for s in output_table(cols, data_rows, state.colsep, 1):
        uprint(s)


def cmd_scan(state, params):
    if len(params) > 1:
        raise CmdError('at most one param required')
    rel_path, dir = locate_dir(state, params[0] if params else '')
    abs_path = os.path.join(state.root_path, rel_path)
    uprint('scanning "%s" ...' % os.path.join(state.root_path, abs_path))
    with ScanStatus(abs_path) as status:
        dir.get_children(abs_path, status)


def cmd_go(state, params):
    if len(params) > 1:
        raise CmdError('at most one param required')
    rel_path, dir = locate_dir(state, params[0] if params else '')
    abs_path = os.path.join(state.root_path, rel_path)
    os.startfile(abs_path)


def cmd_filter(state, params):
    if not params:
        print str(state.filter)
        return
    state.filter = Filter(params)


def cmd_tail(state, params):
    if len(params) > 1:
        raise CmdError('at most one param required')
    if not params:
        print state.tail_count
        return
    try:
        state.tail_count = int(params[0], 10)
    except ValueError:
        raise CmdError('invalid number "%s"' % params)


def cmd_order(state, params, attr, accepted_flags):
    if len(params) > 1:
        raise CmdError('at most one param required')
    cur = getattr(state, attr)
    if not params:
        uprint(cur)
        return
    new_flag = params[0]
    if not new_flag in accepted_flags:
        raise CmdError('invalid order flag "%s"' % new_flag)
    setattr(state, attr, new_flag)


def cmd_listorder(state, params):
    cmd_order(state, params, 'list_order', '*dfsnDFSN')


def cmd_dirorder(state, params):
    cmd_order(state, params, 'dir_order', '*msanMSAN')


def cmd_extorder(state, params):
    cmd_order(state, params, 'ext_order', '*fsnFSN')


def cmd_unit(state, params):
    if len(params) > 1:
        raise CmdError('at most one param required')
    if not params:
        uprint(state.unit)
        return
    unit = params[0]
    if unit not in 'bkmgtpe*':
        raise CmdError('invalid size unit "%s"' % unit)
    state.unit = unit


def cmd_alias(state, params):
    aliases = state.aliases
    keys = sorted(aliases.keys())
    if not params:
        for key in keys:
            uprint(key + '=' + aliases[key])
        return
    for s in params:
        name, sep, value = s.partition('=')
        name, value = name.strip().lower(), value.strip().lower()
        if not name:
            uprint('WARNING: empty alias name: "%s"' % s)
        elif not sep:
            for key in keys:
                if key.startswith(name):
                    uprint(key + '=' + aliases[key])
        elif not value:
            del aliases[name]
        else:
            aliases[name] = value


def cmd_colsep(state, params):
    if len(params) > 1:
        raise CmdError('at most one param required')
    if not params:
        s = state.colsep
        if ' ' in s:
            s = '"' + s + '"'
        uprint(s)
        return
    state.colsep = params[0]


def cmd_cls(state, params):
    if params:
        raise CmdError('no params required')
    console_stuff.cls()


def cmd_quit(state, params):
    if params:
        raise CmdError('no params required')
    raise SystemExit


def parse_args():
    ap = argparse.ArgumentParser(description='interactive OverDisk CLI')
    ap.add_argument('root', nargs='?', metavar='DIR', default='.',
                    help='the initial root dir; default: "%(default)s"')
    args = ap.parse_args()
    args.root = os.path.abspath(six.text_type(args.root))
    if not os.path.isdir(args.root):
        ap.error('not a dir: "%s"' % args.root)
    return args


if __name__ == '__main__':
    args = parse_args()

    state = State()
    state.root_path = args.root
    cmd_dispatcher = CmdDispatcher(state)

    uprint('scanning "%s" ...' % state.root_path)
    with ScanStatus(state.root_path) as status:
        data = winfiles.find(state.root_path).next()
        state.root = Dir(state.root_path, data, status)

    acmgr = AutoComplete.Manager()

    while True:
        try:
            prompt_flags = []
            if str(state.filter) != '*':
                prompt_flags += ['f']
            if state.tail_count:
                prompt_flags += [str(state.tail_count)]
            if 1 or prompt_flags:
                prompt_flags = '[' + ','.join(prompt_flags) + '] '
            else:
                prompt_flags = ''

            prompt = prompt_flags + os.path.join(
                state.root_path, state.rel_path).rstrip(os.path.sep) + '> '

            if 0:
                s = raw_input(prompt).strip()
            else:
                acmgr.completer = lambda s: get_candidate_paths(state, s)
                s = acmgr.input(prompt)

            params = split_cmd(s)
            if not params:
                continue

            cmd, params = params[0].lower(), params[1:]
            cmd = state.aliases.get(cmd, cmd)
            cmd_dispatcher.dispatch(cmd, params)
        except (CmdError, PathError) as x:
            uprint('ERROR: ' + str(x))
        finally:
            uprint('')
