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

import webdir
import CommonTools
import console_stuff

TIMEOUT = 20  # timeout in seconds for urllib2's blocking operations
TIMEOUT_RETRIES = 5  # times to retry timeouts
PARTIAL_SUFFIX = '.PARTIAL'  # appended to partial downloads
DEF_CACHEFILE = 'PAGECACHE'


def safename(s):
    """Replace invalid filename chars with '_'."""
    return re.sub(r'[*?:<>|"]', '_', s)


class Cache(object):

    def __init__(self, fpath):
        self.fpath = fpath
        try:
            self.pages = pickle.load(open(self.fpath, 'rb'))
        except IOError:
            self.pages = {}

    def clear(self):
        self.pages = {}

    def flush(self):
        pickle.dump(self.pages, open(self.fpath, 'wb'), pickle.HIGHEST_PROTOCOL)

    def __getitem__(self, url):
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


def percent(cur, total):
    total = total or 1
    return str(int(round(100.0 * cur / total))) + '%'

def showhelp():
    scriptname = CommonTools.scriptname()
    defcachefile = DEF_CACHEFILE
    print '''
Server dir scraper.

%(scriptname)s [options] URL

  -o OUTDIR     Output directory (default '.')
  -c CACHEFILE  Page cache file (default '<OUTDIR>\%(defcachefile)s')
  -a            Beep when downloading completes.
  -b            Read buffer size in KB (default=4).

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

        regex_casesens = False    

        # use gnu_getopt to allow switches after first param
        switches, params = getopt.gnu_getopt(args,
            '?o:c:x:lg:datD:b:',
            'irx= erx= rxcs rxci'.split())

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
        ext = os.path.splitext(fname)[1].lower()
        return (not self.extensions or ext in self.extensions) and \
            self._test_regexps(fname) and \
            self._test_existance(relpath, fname)

    def _test_regexps(self, fname):
        for must_match, rx in self.regexps:
            matched = bool(rx.search(fname))
            if matched != must_match:
                return False
        # all checks succeeded or no checks specified; it's a match
        return True

    def _test_existance(self, relpath, fname):
        dst = safename(urllib2.unquote(os.path.join(self.outdir, relpath + f.name)))
        return existstate(dst) in opt.downloadstatus


class MovingAverage:
    def __init__(self, winsize):
        self.winsize = winsize
        self.data = []
    def add(self, x, t):
        self.data.insert(0, (x, t))
    def get(self):
        xsum, tsum = 0, 0
        for i, (x, t) in enumerate(self.data):
            xsum += x
            tsum += t
            if tsum >= self.winsize:
                break
        self.data[i+1:] = []
        return xsum/tsum if tsum else 0


def download_resumable_file(src, dst, bufsize):
    retries_left = TIMEOUT_RETRIES
    partial_dst = dst + PARTIAL_SUFFIX
    completed = False
    # It seems that when a socket read times out
    # and we retry the read, the data gets out of sync.
    # So, on read timeouts, we reopen the connection.
    while not completed:
        if os.path.exists(partial_dst):
            start = os.path.getsize(partial_dst)
            f = open(partial_dst, 'a+b')
        else:
            start = 0
            f = open(partial_dst, 'ab')
        spo = console_stuff.SamePosOutput(fallback=True)

        try:
            req = urllib2.Request(src, headers={'Range':'bytes=%d-'%start})
            conn = urllib2.urlopen(req, timeout=TIMEOUT)
            #print conn.headers.dict

            s = conn.headers['content-range']
            m = re.match(r'^(\w+) (?:(\d+)-(\d+)|(\*))/(\d+|\*)$', s)
            assert m, 'invalid HTTP header: content-range = %s' % s
##            print m.groups()
##            spo.reset()
            unit, first, last, unspecified_range, length = m.groups()
            assert unit == 'bytes' and length != '*'

            bytes_total = int(length)
            bytes_downloaded = start
        
            movavg = MovingAverage(30)
            while True:
                dt = time.clock()
                s = conn.read(bufsize)
                dt = time.clock() - dt
                if not s:
                    completed = True
                    break
                bytes_downloaded += len(s)
                movavg.add(len(s), dt)
                spo.restore(eolclear=True)

                speed = movavg.get()

                eta = (bytes_total - bytes_downloaded) / speed if speed else 0
                sec, min, hr = CommonTools.splitunits(eta, (60,60))
                eta = '%d:%02d:%02d' % (hr, min, sec)
                
                print '  %s of %s - %.1f KB/s - ETA %s' % (
                    CommonTools.prettysize(bytes_downloaded),
                    CommonTools.prettysize(bytes_total),
                    speed/1024,
                    eta)
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
                sys.exit(1)
            if isinstance(err, urllib2.URLError) and not isinstance(err.reason, socket.timeout):
                # some error other than timeout
                print err
                return
            spo.restore(eolclear=True)
            print '  timeout...',
            if retries_left > 0:
                print 'retry'
                retries_left -= 1
                spo.reset()
            else:
                print 'abort'
                return
        finally:
            f.close()
            spo.restore(eolclear=True)
    os.rename(partial_dst, dst)
            



def no_dups(a):
    st = set()
    ret = []
    for x in a:
        if x not in st:
            ret += [x]
            st.add(x)
    return ret

Dir = collections.namedtuple('Dir', 'name children'.split())

def add(tree, parts):
    if parts:
        for child in tree.children:
            if child.name == parts[0]:
                break
        else:
            child = Dir(parts[0], [])
            tree.children.append(child)
        add(child, parts[1:])

EMPTY_IDENT = '    '
FULL_IDENT = '|   '
CHILD = '+-- '
LAST_CHILD = '*-- '

EMPTY_IDENT = u'    '
FULL_IDENT = u'\u2502   '
CHILD = u'\u251c\u2500\u2500 '
LAST_CHILD = u'\u2514\u2500\u2500 '


def dump(children, idents):
    for child in children:
        islast = child is children[-1]
        s = ''
        s += ''.join([FULL_IDENT, EMPTY_IDENT][i] for i in idents)
        s += LAST_CHILD if islast else CHILD
        s += urllib2.unquote(child.name)
        CommonTools.uprint(s)
        dump(child.children, idents[:] + [islast])


def test(dirs):
    if dirs[0] == '':
        dirs = dirs[1:]

    tree = Dir('', [])
    for d in dirs:
        parts = [s for s in d.split('/') if s]
        add(tree, parts)

    dump(tree.children, [])



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

def myhandler(cache, spo):
    def handler(err, url):
        spo.restore(eolclear=True)
        CommonTools.uprint(url)
        print ' ', err
        spo.reset()
    return handler

try:
    totalsize = 0
    totalfiles = 0
    filtered_items = []

    spo = console_stuff.SamePosOutput(fallback=True)
    conwidth = console_stuff.consolesize()[0]
    try:
        for url, dirs, files in webdir.walk(opt.topurl, reader=myreader(cache), handler=myhandler(cache, spo)):
            relpath = url[len(opt.topurl):]
            spo.restore(eolclear=True)
            squeezeprint('reading: ', urllib2.unquote(url), conwidth)
            for f in files:
                if opt.filter(relpath, f.name):
                    totalfiles += 1
                    totalsize += f.size
                    filtered_items += [(relpath, f)]
    finally:
        cache.flush()
        spo.restore(eolclear=True)

    if opt.showtree:
        print
        print '---- Tree ----'
        print opt.topurl
        dirs = [relpath for relpath, item in filtered_items]
        dirs = no_dups(dirs)
        test(dirs)

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
                f.date,
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

        GroupItem = collections.namedtuple('GroupItem', 'name count size')
        items = [GroupItem(ext, cnt, size) for ext, (cnt, size) in exts.iteritems()]
        items.sort(key=opt.groupsorder[0], reverse=not opt.groupsorder[1])
        for item in items:
            CommonTools.uprint('%-12s  %4d  %9s (%12d bytes)' % (item.name, item.count, CommonTools.prettysize(item.size), item.size))

    print
    print '---- Summary ----'
    print 'files: %d' % (totalfiles,)
    print 'size: %s (%d bytes)' % (CommonTools.prettysize(totalsize), totalsize)

    if opt.download:
        cursize = 0
        print 'getting files...'
        try:
            for relpath, f in filtered_items:
                curoutdir = safename(urllib2.unquote(os.path.join(opt.outdir, relpath)))
                if not os.path.exists(curoutdir):
                    os.makedirs(curoutdir)
                src = opt.topurl + relpath + f.name
                dst = safename(urllib2.unquote(os.path.join(opt.outdir, relpath + f.name)))
                CommonTools.uprint('%s %s [%s]' % (
                    percent(cursize, totalsize),
                    src,
                    CommonTools.prettysize(f.size)))
                if not os.path.exists(dst):
                    download_resumable_file(src, dst, opt.bufsize)
                cursize += f.size
        finally:
            if opt.beep:
                win32api.MessageBeep(-1)
            
except KeyboardInterrupt:
    print 'Cancelled by user.'
