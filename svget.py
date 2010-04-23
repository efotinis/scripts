import os
import sys
import re
import getopt
import string
import urllib2
import socket
import pickle
import collections
import win32api
import time
import win32console
import random

import webdir
import CommonTools
import console_stuff

TIMEOUT = 20  # timeout in seconds for urllib2's blocking operations
TIMEOUT_RETRIES = 5  # times to retry timeouts
PARTIAL_SUFFIX = '.PARTIAL'  # appended to partial downloads
DEF_CACHEFILE = 'PAGECACHE'
IGNORE_DIRS = ['_vti_cnf/']


def safename(s):
    """Make a path safe for local filesystem.

    Changes:
        - '/' -> '\\'
        - invalid chars -> '_'
        - trim surrounding whitespace from individual path elements
    """
    s = s.replace('/', '\\')
    s = re.sub(r'[*?:<>|"]', '_', s)
    return '\\'.join(part.strip() for part in s.split('\\'))


class Cache(object):
    """Load/create an HTML page cache.

    This is a mapping of URLs to HTML strings.
    URLs that fail to load raise webdir.Error.
    """

    def __init__(self, fpath):
        self.fpath = fpath
        try:
            self.pages = pickle.load(open(self.fpath, 'rb'))
        except IOError:
            self.pages = {}

    def clear(self):
        """Clear cache."""
        self.pages = {}

    def flush(self):
        """Write to disk."""
        pickle.dump(self.pages, open(self.fpath, 'wb'), pickle.HIGHEST_PROTOCOL)

    def __getitem__(self, url):
        """Get cached page (load if necessary). May throw webdir.Error."""
        try:
            x = self.pages[url]
            if isinstance(x, webdir.Error):
                raise x
            return x
        except KeyError:
            try:
                data = urllib2.urlopen(url, timeout=TIMEOUT).read()
                self.pages[url] = data
                return data
            except urllib2.HTTPError as err:
                err = webdir.LoadError(str(err))
                self.pages[url] = err
                raise err
            # Note that when urlopen times out, we get this (not an HTTPError):
            # ...
            #   File "C:\Program Files\Python26\lib\urllib2.py", line 1105, in do_open
            #     raise URLError(err)
            # urllib2.URLError: <urlopen error timed out>


def percent(value, total):
    """Int percent string of value over total.

    Example:
    >>> percent(10, 50)
    '20%'
    """
    total = total or 1
    return str(int(round(100.0 * value / total))) + '%'


def showhelp():
    """Print help."""
    scriptname = CommonTools.scriptname()
    defcachefile = DEF_CACHEFILE
    ignoredirs = ', '.join(IGNORE_DIRS)
    print '''
Server dir scraper.

%(scriptname)s [options] URL

  -o OUTDIR     Output directory (default '.').
  -c CACHEFILE  Page cache file (default '<OUTDIR>\%(defcachefile)s').
  -a            Beep when downloading completes.
  -b            Read buffer size in KB (default=4).
  --ile         Ignore listing errors.
  --shuffle     Download files in random order (default is listing order).
  --all         Include these directories, which are normally ignored:
                    %(ignoredirs)s

                ---- Actions ----
  -t            Display tree structure.
  -l            Display file listing.
  -g ORDER      Display extension groups info (count/size).
                Order is one of:
                    n: name(default), c: count, s: size
                and:
                    +: ascending(default), -: descending
  -d            Download files.

                ---- Filters ----
  -x EXTLIST    List of extensions to process, separated by ';'.
                Leading dot is optional. Default is all.
                Multiple values are accumulated.
  -D STATUS     Download status. One or more of:
                    d: fully downloaded, p: partial, n: not downloaded.
  --irx RX      Regexp of names to include.
  --erx RX      Regexp of names to exclude.
                Multiple regexps are accumulated.
  --rxcs        Subsequent regexps are case-sensitive.
  --rxci        Subsequent regexps are case-insensitive (default).
                    
'''[1:-1] % locals()


def existstate(path):
    """Get file exist state: 'd': downloaded, 'p': partial, 'n': missing."""
    if os.path.exists(path):
        return 'd'
    elif os.path.exists(path + PARTIAL_SUFFIX):
        return 'p'
    else:
        return 'n'


class Options(object):
    """Script options."""

    def __init__(self, args):
        self.help = False
        self.topurl = None
        self.outdir = '.'
        self.cachefile = None
        self.extensions = []
        self.listing = False
        self.groups = False
        self.groupsorder = self._parse_groups_order('n+')
        self.download = False
        self.regexps = []
        self.beep = False
        self.showtree = False
        self.downloadstatus = self._parse_download_status('dpn')
        self.bufsize = 4 * 1024
        self.ignorelisterrors = False
        self.shuffle = False
        self.includeall = False

        regex_casesens = False    

        # use gnu_getopt to allow switches after first param
        switches, params = getopt.gnu_getopt(args,
            '?o:c:x:lg:datD:b:',
            'irx= erx= rxcs rxci ile shuffle all'.split())

        if len(params) != 1:
            raise getopt.error('exactly one param required')
        self.topurl = params[0]

        for sw, val in switches:
            if sw == '-?':
                self.help = True
            elif sw == '-o':
                self.outdir = val
            elif sw == '-c':
                self.cachefile = val
            elif sw == '-x':
                self.extensions.extend(val.split(';'))
            elif sw == '-l':
                self.listing = True
            elif sw == '-g':
                self.groups = True
                self.groupsorder = self._parse_groups_order(val)
            elif sw == '-d':
                self.download = True
            elif sw in ('--irx', '--erx'):
                try:
                    self.regexps += [(
                        sw == '--irx',
                        re.compile(val, 0 if regex_casesens else re.I))]
                except re.error:
                    raise getopt.error('invalid regexp: "%s"' % val)
            elif sw == '--rxcs':
                regex_casesens = True
            elif sw == '--rxci':
                regex_casesens = False
            elif sw == '-a':
                self.beep = True
            elif sw == '-t':
                self.showtree = True
            elif sw == '-D':
                self.downloadstatus = self._parse_download_status(val)
            elif sw == '-b':
                try:
                    self.bufsize = int(val)
                    if self.bufsize < 1:
                        raise ValueError
                    self.bufsize *= 1024
                except ValueError:
                    raise getopt.error('invalid buffer size: "%s"' % val)
            elif sw == '--ile':
                self.ignorelisterrors = True
            elif sw == '--shuffle':
                self.shuffle = True
            elif sw == '--all':
                self.includeall = True

        if not self.cachefile:
            self.cachefile = os.path.join(self.outdir, DEF_CACHEFILE)

        self.extensions = frozenset(
            ext if (not ext or ext.startswith('.')) else '.'+ext
            for ext in map(string.lower, self.extensions))

    @staticmethod
    def _parse_groups_order(s):
        fields = {
            'n': lambda x: x.name,
            'c': lambda x: x.count,
            's': lambda x: x.size}
        orders = {
            '+': True,
            '-': False}
        field = fields['n']
        order = orders['+']
        for c in s:
            if c in fields:
                field = fields[c]
            elif c in orders:
                order = orders[c]
            else:
                raise getopt.error('invalid groups order: "%s"' % s)
        return field, order

    @staticmethod
    def _parse_download_status(s):
        ret = frozenset(s)
        if ret.issubset(frozenset('dpn')):
            return ret
        else:
            raise getopt.error('invalid download status: "%s"' % s)

    def filter(self, relpath, fname):
        """Test filename against all filters."""
        fname = urllib2.unquote(fname)  # BUGFIX: needed to make filtering regexps work (need to rethink url quoting and filtering)
        ext = os.path.splitext(fname)[1].lower()
        return (not self.extensions or ext in self.extensions) and \
            self._test_regexps(fname) and \
            self._test_existance(relpath, fname)

    def _test_regexps(self, fname):
        """Test filename against all regexps."""
        for must_match, rx in self.regexps:
            matched = bool(rx.search(fname))
            if matched != must_match:
                return False
        # all checks succeeded or no checks specified; it's a match
        return True

    def _test_existance(self, relpath, fname):
        """Test filename against exist flags."""
        dst = safename(urllib2.unquote(os.path.join(self.outdir, relpath + f.name)))
        return existstate(dst) in opt.downloadstatus


class MovingAverage:
    """Moving avarage (unweighted) calculator."""
    
    def __init__(self, winsize):
        self.winsize = winsize
        self.data = []
        
    def add(self, x, t):
        """Add data."""
        self.data.insert(0, (x, t))
        
    def get(self):
        """Get current average."""
        xsum, tsum = 0, 0
        i = 0  # init in case data is empty
        for i, (x, t) in enumerate(self.data):
            xsum += x
            tsum += t
            if tsum >= self.winsize:
                break
        # discard data outside window
        self.data[i+1:] = []
        return xsum/tsum if tsum else 0


def prettysize_compact(n, iec=False):
    return CommonTools.prettysize(n, iec).replace('bytes', '').rstrip('B').replace(' ', '')


def download_resumable_file(src, dst, bufsize, totalsize, totaldone, movavg):
    """Download file with resume support.

    Returns a 3-tuple of sizes:
        - initial partial size (may be 0)
        - bytes downloaded (equal to filesize below if completed)
        - exact filesize from HTTP headers (None if connection could not be opened)
    """
    retries_left = TIMEOUT_RETRIES
    partial_dst = dst + PARTIAL_SUFFIX

    ret_start = None
    ret_done = None
    ret_size = None

    # It seems that when a socket read times out
    # and we retry the read, the data gets out of sync.
    # So, on read timeouts, we reopen the connection.
    completed = False
    while not completed:
        if os.path.exists(partial_dst):
            start = os.path.getsize(partial_dst)
            f = open(partial_dst, 'a+b')
        else:
            start = 0
            f = open(partial_dst, 'ab')
        if ret_start is None:
            ret_start = start
            ret_done = start

        spo = console_stuff.SamePosOutput(fallback=True)

        try:
            req = urllib2.Request(src, headers={'Range':'bytes=%d-'%start})
            conn = urllib2.urlopen(req, timeout=TIMEOUT)

            # get total size from header
            s = conn.headers['content-range']
            m = re.match(r'^(\w+) (?:(\d+)-(\d+)|(\*))/(\d+|\*)$', s)
            assert m, 'invalid HTTP header: content-range = %s' % s
            unit, first, last, unspecified_range, length = m.groups()
            assert unit == 'bytes' and length != '*'

            filesize = int(length)
            filedone = start
            ret_size = filesize
        
            while True:
                speed = movavg.get()

                file_eta = (filesize - filedone) / speed if speed else 0
                if file_eta < 0: file_eta = 0
                sec, min, hr = CommonTools.splitunits(file_eta, (60,60))
                file_eta = '%d:%02d:%02d' % (hr, min, sec)

                total_eta = (totalsize - totaldone) / speed if speed else 0
                if total_eta < 0: total_eta = 0
                sec, min, hr = CommonTools.splitunits(total_eta, (60,60))
                total_eta = '%d:%02d:%02d' % (hr, min, sec)

                spo.restore(eolclear=True)
                print '  %.1f KB/s, File: %s/%s (%s) %s, Total: %s/%s (%s) %s' % (
                    speed/1024,
                    prettysize_compact(filedone),
                    prettysize_compact(filesize),
                    percent(filedone, filesize),
                    file_eta,
                    prettysize_compact(totaldone),
                    prettysize_compact(totalsize),
                    percent(totaldone, totalsize),
                    total_eta)

                dt = time.clock()
                s = conn.read(bufsize)
                dt = time.clock() - dt
                if not s:
                    completed = True
                    break

                filedone += len(s)
                totaldone += len(s)
                ret_done += len(s)

                movavg.add(len(s), dt)

                f.write(s)

        except (socket.timeout, urllib2.URLError) as err:
            # urlopen raises urllib2.URLError(reason=socket.timeout),
            # while conn.read raises socket.timeout
            # (also got an httplib.BadStatusLine once, which didn't show up
            # when retrying the download; should we retry on that too or
            # on all httplib.HTTPExceptions?)
            if isinstance(err, urllib2.HTTPError):
                # FIXME: also got some HTTPErrors (no reason member);
                #        just print it to see what's it all about
                print '*' * 40
                print err
                print '*' * 40
                return ret_start, ret_done, ret_size
            if isinstance(err, urllib2.URLError) and not isinstance(err.reason, socket.timeout):
                # some error other than timeout
                print err
                return ret_start, ret_done, ret_size
            spo.restore(eolclear=True)
            print '  timeout...',
            if retries_left > 0:
                print 'retry'
                spo.reset()
                retries_left -= 1
            else:
                print 'abort'
                spo.reset()
                return ret_start, ret_done, ret_size
        finally:
            f.close()
            spo.restore(eolclear=True)
    os.rename(partial_dst, dst)
    return ret_start, ret_done, ret_size
            



class Dir(object):
    def __init__(self, name):
        self.name = name
        self.count = 0
        self.size = 0
        self.subs = []
    def __getitem__(self, relpath):
        if not relpath:
            return self
        s1, s2 = relpath.split('/', 1)
        for sub in self.subs:
            if sub.name == s1:
                break
        else:
            sub = Dir(s1)
            self.subs += [sub]
        return sub[s2]

EMPTY_IDENT = '    '
FULL_IDENT = '|   '
CHILD = '+-- '
LAST_CHILD = '*-- '

EMPTY_IDENT = u'    '
FULL_IDENT = u'\u2502   '
CHILD = u'\u251c\u2500\u2500 '
LAST_CHILD = u'\u2514\u2500\u2500 '


def printtree(dirobj, idents):
    s = '%9s in %-5d  ' % (CommonTools.prettysize(dirobj.size), dirobj.count)
    s += ''.join((EMPTY_IDENT, FULL_IDENT)[i] for i in idents[:-1])
    if idents:
        s += (LAST_CHILD, CHILD)[idents[-1]]
    s += urllib2.unquote(dirobj.name)
    CommonTools.uprint(s)

    for sub in dirobj.subs:
        printtree(sub, idents + [sub is not dirobj.subs[-1]])


try:
    opt = Options(sys.argv[1:])
except getopt.error as x:
    print >>sys.stderr, str(x)
    sys.exit(2)

if opt.help:
    showhelp()
    sys.exit(0)

cachedir = os.path.dirname(opt.cachefile)
if not os.path.exists(cachedir):
    os.makedirs(cachedir)
cache = Cache(opt.cachefile)

def squeezeprint(pfx, sfx, conwidth):
    maxsfxlen = conwidth - 1 - len(pfx) - 3  # 3 for '...', 1 to avoid wrapping
    if len(sfx) > maxsfxlen:
        sfx = '...' + sfx[-maxsfxlen:]
    CommonTools.uprint(pfx + sfx)

def myreader(cache):
    def reader(url):
        return cache[url]
    return reader

def myhandler(cache, spo, ignore):
    def handler(err, url):
        if not ignore:
            spo.restore(eolclear=True)
            CommonTools.uprint(url)
            print ' ', err
            spo.reset()
    return handler

rxdate = re.compile(r'^(\d{2})-([a-z]{3})-(\d{4}) (\d{2}):(\d{2})$', re.IGNORECASE)
months = dict(zip('jan feb mar apr may jun jul aug sep oct nov dec'.split(), range(1,13)))

def compressdate(s):
    """Convert date string from 'dd-MMM-yyyy hh:mm' to 'yyyyMMdd-hhmm'."""
    d,mo,y,h,m = rxdate.match(s).groups()
    return '%s%02d%s-%s%s' % (y, months[mo.lower()], d, h, m)
    

def getdownloadedsize(fpath):
    """Get size of downloaded file or current partial size."""
    if os.path.exists(fpath):
        return os.path.getsize(fpath)
    elif os.path.exists(fpath + PARTIAL_SUFFIX):
        return os.path.getsize(fpath + PARTIAL_SUFFIX)
    else:
        return 0


class ColorOutput(object):
    def __init__(self):
        self.buf = win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)
    def close(self):
        self.buf.Close()
    def write(self, fg, bg, text):
        oldattr = self.buf.GetConsoleScreenBufferInfo()['Attributes']
        self.buf.SetConsoleTextAttribute(fg + bg*16)
        self.buf.WriteConsole(text)
        self.buf.SetConsoleTextAttribute(oldattr)
    def writeln(self, fg, bg, text):
        self.write(fg, bg, text + '\n')


try:
    totalsize = 0
    totaldone = 0  # incl. partial downloads and skipped due to timeouts
    totalfiles = 0
    filtered_items = []

    spo = console_stuff.SamePosOutput(fallback=True)
    conwidth = console_stuff.consolesize()[1]
    try:
        for url, dirs, files in webdir.walk(opt.topurl, reader=myreader(cache), handler=myhandler(cache, spo, opt.ignorelisterrors)):
            relpath = url[len(opt.topurl):]
            spo.restore(eolclear=True)
            squeezeprint('reading: ', urllib2.unquote(url), conwidth)
            for f in files:
                if opt.filter(relpath, f.name):
                    totalfiles += 1
                    totalsize += f.size
                    dst = safename(urllib2.unquote(os.path.join(opt.outdir, relpath + f.name)))
                    totaldone += getdownloadedsize(dst)
                    filtered_items += [(relpath, f)]
            if not opt.includeall:
                # remove ignored dirs so they are not walked into
                for i in range(len(dirs)-1, -1, -1):
                    if dirs[i].name in IGNORE_DIRS:
                        dirs[i:i+1] = []
    finally:
        cache.flush()
        spo.restore(eolclear=True)

    if opt.showtree:
        print
        print '---- Tree ----'
        root = Dir('')
        for relpath, item in filtered_items:
            dir = root[relpath]
            dir.count += 1
            dir.size += item.size
        root.name = opt.topurl
        printtree(root, [])

    if opt.listing:
        print
        print '---- List ----'
        currelpath = None
        for relpath, f in filtered_items:
            # lazy-print path only when it changes
            if currelpath != relpath:
                if currelpath is not None:
                    print
                CommonTools.uprint(opt.topurl + relpath)
                currelpath = relpath
            dst = safename(urllib2.unquote(os.path.join(opt.outdir, relpath + f.name)))
            exists = os.path.exists(dst)
            partial = not exists and os.path.exists(dst + PARTIAL_SUFFIX)
            CommonTools.uprint('  %s %10s %c %s' % (
                compressdate(f.date),
                f.size,
                '*' if exists else '%' if partial else ' ',
                urllib2.unquote(f.name)))

    if opt.groups:
        print
        print '---- Groups ----'
        exts = collections.defaultdict(lambda: [0,0])
        for relpath, f in filtered_items:
            ext = os.path.splitext(f.name)[1].lower()
            exts[ext][0] += 1
            exts[ext][1] += f.size

        BLACK,BLUE,GREEN,CYAN,RED,MAGENTA,YELLOW,GRAY = range(8)

        filetypes = {
            'video':     [BLUE, 'avi mov mpeg mpg wmv'],
            'audio':     [YELLOW, 'm4a mp3 wav wma'],
            'documents': [GREEN, 'doc pdf pps xls'],
            'images':    [RED, 'bmp gif jpeg jpg pcx png tga tif tiff'],
            'archives':  [GRAY, '7z ace bzip gz rar tar zip']}
##        for s in filetypes:
##            filetypes[s][1] = filetypes[s][1].split()
        extclrs = {}
        for clr, extlist in filetypes.values():
            for ext in extlist.split():
                extclrs[ext] = clr

        clrout = ColorOutput()

        GroupItem = collections.namedtuple('GroupItem', 'name count size')
        items = [GroupItem(ext, cnt, size) for ext, (cnt, size) in exts.iteritems()]
        items.sort(key=opt.groupsorder[0], reverse=not opt.groupsorder[1])
        for item in items:
            clrout.write(0, extclrs.get(item.name.lstrip('.').lower(), 0), '  ')
            sys.stdout.write(' ')
            CommonTools.uprint('%-12s  %4d  %9s (%12d bytes)' % (item.name, item.count, CommonTools.prettysize(item.size), item.size))

    print
    print '---- Summary ----'
    print 'files: %d' % (totalfiles,)
    print 'size: %s (%d bytes)' % (CommonTools.prettysize(totalsize), totalsize)

    if opt.download:
        print
        print '---- Download ----'
        if opt.shuffle:
            random.shuffle(filtered_items)
        incomplete = []
        movavg = MovingAverage(30)  # speed counter
        try:
            for relpath, f in filtered_items:
                curoutdir = safename(urllib2.unquote(os.path.join(opt.outdir, relpath)))
                if not os.path.exists(curoutdir):
                    os.makedirs(curoutdir)
                src = opt.topurl + relpath + f.name
                dst = safename(urllib2.unquote(os.path.join(opt.outdir, relpath + f.name)))
                CommonTools.uprint(safename(urllib2.unquote(relpath + f.name)))
                if not os.path.exists(dst):
                    start, done, size = download_resumable_file(src, dst, opt.bufsize, totalsize, totaldone, movavg)
                    if done != size:  # even if size is None
                        incomplete += [dst]
                    # subtract the initial partial size
                    # and add the whole file size (whether completed or not)
                    totaldone -= start
                    totaldone += size or f.size
        finally:
            if incomplete:
                print 'Incomplete files:', len(incomplete)
                for s in incomplete:
                    CommonTools.uprint('  ' + s)
            if opt.beep:
                win32api.MessageBeep(-1)
            
except KeyboardInterrupt:
    print 'Cancelled by user.'
