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

import webdir
import CommonTools

TIMEOUT = 20  # timeout in seconds for urllib2's blocking operations
TIMEOUT_RETRIES = 5  # times to retry timeouts


def safename(s):
    """Replace invalid filename chars with '_'."""
    return re.sub(r'[*?:<>|"]', '_', s)


class Cache(object):

    class Error(object):
        def __init__(self, httperror):
            self.code = httperror.code
            self.msg = httperror.msg
            self.str = str(httperror)
        def __str__(self):
            return self.str

    def __init__(self, fpath):
        self.fpath = fpath
        try:
            self.pages = pickle.load(open(self.fpath, 'rb'))
            for url, data in self.pages.iteritems():
                if isinstance(data, tuple):
                    self.pages[url] = webdir.PageError(data)
        except IOError:
            self.pages = {}

    def clear(self):
        self.pages = {}

    def flush(self):
        pages = self.pages.copy()
        for url, data in pages.iteritems():
            if isinstance(data, webdir.PageError):
                pages[url] = (str(data), data.url, data.code, data.msg)
        pickle.dump(pages, open(self.fpath, 'wb'), pickle.HIGHEST_PROTOCOL)

    def __getitem__(self, url):
        try:
            x = self.pages[url]
            if isinstance(x, webdir.PageError):
                raise x
            else:
                return x
        except KeyError:
            try:
                data = urllib2.urlopen(url, timeout=TIMEOUT).read()
                self.pages[url] = data
                return data
            except urllib2.HTTPError as err:
                err = webdir.PageError(err)
                self.pages[url] = err
                raise err


def makeCachedReader(cache):
    def reader(url):
        return cache[url]
    return reader

def makeCachedHandler(cache):
    def handler(err):
        print err.url
        print ' ', err
    return handler

def percent(cur, total):
    total = total or 1
    return str(int(round(100.0 * cur / total))) + '%'

def showhelp():
    scriptname = CommonTools.scriptname()
    print '''
Server dir scraper.

%(scriptname)s [options] URL

  -o OUTDIR     Output directory (default '.')
  -c CACHEFILE  Page cache file (default '<OUTDIR>\pagecache.dat')
  -a            Beep when downloading completes.

                ---- Actions ----
  -l            Display listing.
  -g ORDER      Display extension groups info (count/size).
                Order is one of:
                    n: name(default), c: count, s: size
                and (optionally):
                    +: ascending(default), -: descending
  -d            Download files.

                ---- Filters ----
  -x EXTLIST    List of extensions to process, separated by ';'.
                Leading dot is optional. Default is all.
                Multiple values are accumulated.
  -m            Missing (not downloaded or incomplete) files.
  -M            Existing files.
  --irx RX      Regexp of names to include.
  --erx RX      Regexp of names to exclude.
                Multiple regexps are accumulated.
  --rxcs        Subsequent regexps are case-sensitive.
  --rxci        Subsequent regexps are case-insensitive (default).
                    
'''[1:-1] % locals()

Options = collections.namedtuple('Options',
    'help topurl outdir cachefile extensions listing '
    'groups groupsorder download missing regexps beep')

def getoptions(args):
    opt = {
        'help': False,
        'topurl': None,
        'outdir': '.',
        'cachefile': None,
        'extensions': [],
        'listing': False,
        'groups': False,
        'groupsorder': parse_groups_order('n+'),
        'download': False,
        'missing': None,
        'regexps': [],
        'beep': False}

    regex_casesens = False    

    # use gnu_getopt to allow switches after first param
    try:
        switches, params = getopt.gnu_getopt(args,
            '?o:c:x:lg:dmMa',
            'irx= erx= rxcs rxci'.split())
    except getopt.error as x:
        x.msg += '; use -? for help'
        raise x

    if len(params) != 1:
        raise getopt.error('exactly one param required')
    opt['topurl'] = params[0]

    for sw, val in switches:
        if sw == '-?':
            opt['help'] = True
        elif sw == '-o':
            opt['outdir'] = val
        elif sw == '-c':
            opt['cachefile'] = val
        elif sw == '-x':
            opt['extensions'].extend(val.split(';'))
        elif sw == '-l':
            opt['listing'] = True
        elif sw == '-g':
            opt['groups'] = True
            opt['groupsorder'] = parse_groups_order(val)
        elif sw == '-d':
            opt['download'] = True
        elif sw == '-m':
            opt['missing'] = True
        elif sw == '-M':
            opt['missing'] = False
        elif sw in ('--irx', '--erx'):
            try:
                opt['regexps'] += [(
                    sw == '--irx',
                    re.compile(val, 0 if regex_casesens else re.I))]
            except re.error:
                raise getopt.error('invalid regexp: "%s"' % val)
        elif sw == '--rxcs':
            regex_casesens = True
        elif sw == '--rxci':
            regex_casesens = False
        elif sw == '-a':
            opt['beep'] = True

    if not opt['cachefile']:
        opt['cachefile'] = os.path.join(opt['outdir'], 'pagecache.dat')

    opt['extensions'] = frozenset(
        ext if (not ext or ext.startswith('.')) else '.'+ext
        for ext in map(string.lower, opt['extensions']))

    return Options(**opt)


def parse_groups_order(s):
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


def download_resumable_file(src, dst):
    retries_left = TIMEOUT_RETRIES
    partial_dst = dst + '.PARTIAL'
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
        try:
            req = urllib2.Request(src, headers={'Range':'bytes=%d-'%start})
            conn = urllib2.urlopen(req, timeout=TIMEOUT)
            while True:
                s = conn.read(4096)
                if not s:
                    completed = True
                    break
                f.write(s)
        except (socket.timeout, urllib2.URLError) as err:
            # urlopen raises urllib2.URLError(reason=socket.timeout),
            # while conn.read raises socket.timeout
            if isinstance(err, urllib2.URLError) and not isinstance(err.reason, socket.timeout):
                # some error other than timeout
                print err
                return
            print '  timeout...',
            if retries_left > 0:
                print 'retry'
                retries_left -= 1
            else:
                print 'abort'
                return
        finally:
            f.close()
    os.rename(partial_dst, dst)
            

def test_regexps(regexps, s):
    for must_match, rx in regexps:
        matched = bool(rx.search(s))
        if matched != must_match:
            return False
    # all checks succeeded or no checks specified; it's a match
    return True


os.chdir(r'C:\Users\Elias\Desktop\server_scrape')
sys.argv[1:] = 'http://nfig.hd.free.fr/util/ -gn'.split()


try:
    opt = getoptions(sys.argv[1:])
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

try:
    print 'getting listings...'
    totalsize = 0
    totalfiles = 0
    exts = collections.defaultdict(lambda: [0,0])
    filtered_items = []
    try:
        for url, dirs, files in webdir.walk(opt.topurl, reader=makeCachedReader(cache), handler=makeCachedHandler(cache)):
            relpath = url[len(opt.topurl):]
            print urllib2.unquote(url)
            for f in files:
                ext = os.path.splitext(f.name)[1].lower()
                if not opt.extensions or ext in opt.extensions:
                    if test_regexps(opt.regexps, f.name):
                        dst = safename(urllib2.unquote(os.path.join(opt.outdir, relpath + f.name)))
                        exists = os.path.exists(dst)
                        if opt.missing is None or opt.missing != exists:
                            exts[ext][0] += 1
                            exts[ext][1] += f.size
                            totalfiles += 1
                            totalsize += f.size
                            filtered_items += [(relpath, f)]
                            if opt.listing:
                                partial = not exists and os.path.exists(dst + '.PARTIAL')
                                CommonTools.uprint('  %s %10s %c %s' % (
                                    f.date,
                                    f.size,
                                    '*' if exists else '%' if partial else ' ',
                                    urllib2.unquote(f.name)))
    finally:
        cache.flush()

    print 'files: %d' % (totalfiles,)
    print 'size: %s (%d bytes)' % (CommonTools.prettysize(totalsize), totalsize)

    if opt.groups:
        GroupItem = collections.namedtuple('GroupItem', 'name count size')
        items = [GroupItem(ext, cnt, size) for ext, (cnt, size) in exts.iteritems()]
        items.sort(key=opt.groupsorder[0], reverse=not opt.groupsorder[1])
        for item in items:
            print '  %-10s  %4d  %8s (%12d bytes)' % (item.name, item.count, CommonTools.prettysize(item.size), item.size)

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
                    download_resumable_file(src, dst)
                cursize += f.size
        finally:
            if opt.beep:
                win32api.MessageBeep(-1)
            
except KeyboardInterrupt:
    print 'Cancelled by user.'
