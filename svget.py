import os
import sys
import re
import getopt
import string
import urllib2
import socket
import pickle
import collections

import webdir
import CommonTools

TIMEOUT = 10  # timeout in seconds for urllib2's blocking operations
TIMEOUT_RETRIES = 3  # times to retry timeouts


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
            return self.pages[url]
        except KeyError:
            data = urllib2.urlopen(url, timeout=TIMEOUT).read()
            self.pages[url] = data
            return data

def makeCachedReader(cache):
    def reader(url):
        return cache[url]
    return reader

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

Actions:
  -l            Display listing.
  -g ORDER      Display extension groups info (count/size).
                Order is one of:
                    n: name(default), c: count, s: size
                and (optionally):
                    +: ascending(default), -: descending
  -d            Download files.

Filters:
  -x EXT_LIST   List of extensions to process, separated by ';'.
                Leading dot is optional. Default is all.
                Multiple values are accumulated.
  -m / -M       Missing (not downloaded or incomplete) or existing files.
'''[1:-1] % locals()

Options = collections.namedtuple('Options',
    'help topurl outdir cachefile extensions listing groups groupsorder download missing')

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
        'missing':None}

    # use gnu_getopt to allow switches after first param
    try:
        switches, params = getopt.gnu_getopt(args, '?o:c:x:lg:dmM')
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

    if not opt['cachefile']:
        opt['cachefile'] = os.path.join(opt['outdir'], 'pagecache.dat')

    opt['extensions'] = frozenset(
        ext if (ext and ext.startswith('.')) else '.'+ext
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


def operation_with_retry(opname, retries, func, args=(), kwargs=None):
    while True:
        try:
            return func(*args, **(kwargs or {}))
        except socket.timeout:
            print opname + ' timed-out...',
            if retries > 0:
                print 'retrying'
                retries -= 1
            else:
                print 'aborting'
                raise


def read_with_retry(conn, size, retries):
    return operation_with_retry('read', retries, conn.read, (size,), {})


def open_with_retry(url_or_req, timeout, retries):
    return operation_with_retry('open', retries, urllib2.urlopen, (url_or_req,), {'timeout':timeout})


def download_resumable_file(src, dst):
    partial_dst = dst + '.PARTIAL'
    if os.path.exists(partial_dst):
        start = os.path.getsize(partial_dst)
        f = open(partial_dst, 'a+b')
    else:
        start = 0
        f = open(partial_dst, 'ab')
    req = urllib2.Request(src, headers={'Range':'bytes=%d-'%start})
    conn = open_with_retry(req, TIMEOUT, TIMEOUT_RETRIES)
    while True:
        try:
            s = read_with_retry(conn, 4096, TIMEOUT_RETRIES)
        except socket.timeout:
            return
        if not s: break
        f.write(s)
    f.close()
    os.rename(partial_dst, dst)
            

##url = 'http://kietouney.free.fr/accueil.JPG'
##dst = r'c:\users\elias\desktop\test.jpg'
##download_resumable_file(url, dst)
##sys.exit()

try:
    opt = getoptions(sys.argv[1:])
except getopt.error as x:
    print >>sys.stderr, str(x)
    sys.exit(2)

if opt.help:
    showhelp()
    sys.exit()

cachedir = os.path.dirname(opt.cachefile)
if not os.path.exists(cachedir):
    os.makedirs(cachedir)
cache = Cache(opt.cachefile)

print 'getting listings...'
totalsize = 0
totalfiles = 0
exts = collections.defaultdict(lambda: [0,0])
try:
    for url, dirs, files in webdir.walk(opt.topurl, makeCachedReader(cache)):
        relpath = url[len(opt.topurl):]
        print urllib2.unquote(url)
        for f in files:
            ext = os.path.splitext(f.name)[1].lower()
            if not opt.extensions or ext in opt.extensions:
                dst = safename(urllib2.unquote(os.path.join(opt.outdir, relpath + f.name)))
                exists = os.path.exists(dst)
                if opt.missing is None or opt.missing != exists:
                    exts[ext][0] += 1
                    exts[ext][1] += f.size
                    totalfiles += 1
                    totalsize += f.size
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
print 'size: %.0f MiB' % (totalsize/2**20,)

if opt.groups:
    GroupItem = collections.namedtuple('GroupItem', 'name count size')
    items = [GroupItem(ext, cnt, size) for ext, (cnt, size) in exts.iteritems()]
    items.sort(key=opt.groupsorder[0], reverse=not opt.groupsorder[1])
    for item in items:
        print '  %-10s  %4d  %4d MiB' % (item.name, item.count, item.size/2**20)

if opt.download:
    cursize = 0
    print 'getting files...'
    for url, dirs, files in webdir.walk(opt.topurl, makeCachedReader(cache)):
        relpath = url[len(opt.topurl):]
        curoutdir = safename(urllib2.unquote(os.path.join(opt.outdir, relpath)))
        for f in files:
            ext = os.path.splitext(f.name)[1].lower()
            if not opt.extensions or ext in opt.extensions:
                dst = safename(urllib2.unquote(os.path.join(opt.outdir, relpath + f.name)))
                exists = os.path.exists(dst)
                if opt.missing is None or opt.missing != exists:
                    if not os.path.exists(curoutdir):
                        os.makedirs(curoutdir)
                    src = url + f.name
                    CommonTools.uprint('%s %s [%.0f KiB]' % (
                        percent(cursize, totalsize),
                        src,
                        f.size/(2.0**10)))
                    if not os.path.exists(dst):
                        download_resumable_file(src, dst)
                    cursize += f.size
