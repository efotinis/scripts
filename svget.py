import os
import sys
import re
import optparse
import urllib2
import socket
import pickle
import collections
import win32api
import time
import win32console
import random

import webdir
import efutil
import mathutil
import console_stuff

# FIXME: handle non-resumable downloads ('accept-ranges: none'; e.g. Coral Cache files)

TIMEOUT = 20  # timeout in seconds for urllib2's blocking operations
TIMEOUT_RETRIES = 5  # times to retry timeouts
PARTIAL_SUFFIX = '.PARTIAL'  # appended to partial downloads
DEF_CACHEFILE = 'PAGECACHE'
DEF_BUFSIZE_KB = 4
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










def parse_cmdline():
    parser = optparse.OptionParser(usage='%prog [options] URL', description='Server dir scraper.', add_help_option=False,
                                   epilog='Multiple filter regexps are allowed and they are processed in the order they were specified.')

    parser.add_option('-o', dest='outdir', default='.', metavar='DIR', help='Output directory. Default is "%default".')
    parser.add_option('-c', dest='cachefile', metavar='FILE', help='Page cache file. Default is "<output dir>\%s".' % DEF_CACHEFILE)
    parser.add_option('-a', dest='beep', action='store_true', help='Beep when downloading completes.')
    parser.add_option('-b', dest='bufsize', type='int', default=DEF_BUFSIZE_KB, help='Read buffer size in KB. Default is %default.')
    parser.add_option('--ile', dest='ignorelisterrors', action='store_true', help='Ignore listing errors.')
    parser.add_option('--shuffle', dest='shuffle', action='store_true', help='Download files in random order (default is listing order).')
    parser.add_option('--all', dest='includeall', action='store_true', help='Include these directories, which are normally ignored: ' + ', '.join(IGNORE_DIRS))
    parser.add_option('-?', action='help', help='This help.')

    group = optparse.OptionGroup(parser, 'Actions')
    group.add_option('-t', dest='showtree', action='store_true', help='Display tree structure.')
    group.add_option('-l', dest='listing', action='store_true', help='Display file listing.')
    group.add_option('-g', dest='groupsorder', metavar='ORDER', help='Display extension groups info (count/size). Order can be "n", "c" or "s" for ascending name, count or size, and "N", "C", or "S" for descending.')
    group.add_option('-d', dest='download', action='store_true', help='Download files.')
    parser.add_option_group(group)

    group = optparse.OptionGroup(parser, 'Filters')
    group.add_option('-x', dest='extensions', action='append', metavar='LIST', help='List of extensions to process, separated by ";". Leading dot is optional. Default is all. Multiple options are allowed.')
    group.add_option('-D', dest='downloadstatus', metavar='STATUS', help='Download status. One or more of: "d" (fully downloaded), "p" (partial), "n" (not downloaded). Default is all ("dpn").')
    group.add_option('--iri', dest='regexps', type='str', action='callback', callback=_rx_opt_callback, callback_kwargs={'_include':True, '_ignorecase':True}, metavar='RX', help='Name include regexp (ignore case).')
    group.add_option('--irc', dest='regexps', type='str', action='callback', callback=_rx_opt_callback, callback_kwargs={'_include':True, '_ignorecase':False}, metavar='RX', help='Name include regexp (match case).')
    group.add_option('--xri', dest='regexps', type='str', action='callback', callback=_rx_opt_callback, callback_kwargs={'_include':False, '_ignorecase':True}, metavar='RX', help='Name exclude regexp (ignore case).')
    group.add_option('--xrc', dest='regexps', type='str', action='callback', callback=_rx_opt_callback, callback_kwargs={'_include':False, '_ignorecase':False}, metavar='RX', help='Name exclude regexp (match case).')
    parser.add_option_group(group)
    parser.set_defaults(regexps=[])

    opts, args = parser.parse_args()

    if len(args) != 1:
        parser.error('exactly one param required')
    opts.topurl = args[0]

    opts.bufsize *= 1024
    if opts.bufsize <= 0:
        parser.error('invalid buffer size')

    if opts.extensions:
        extlist = (';'.join(opts.extensions)).split(';')
        sanitize_ext = lambda s: s if (not s or s.startswith('.')) else '.' + s
        opts.extensions = frozenset(sanitize_ext(s).lower() for s in extlist)

    if opts.groupsorder is not None:
        try:
            opts.groupsorder = GroupsOrdering(opts.groupsorder)
        except ValueError:
            parser.error('invalid groups order: "%s"' % opts.groupsorder)

    try:
        opts.downloadstatus = DownloadStateFilter(opts.downloadstatus)
    except ValueError:
        parser.error('invalid download status: "%s"' % opts.downloadstatus)

    if not opts.cachefile:
        opts.cachefile = os.path.join(opts.outdir, DEF_CACHEFILE)

    return opts        

        
class GroupsOrdering(object):

    def __init__(self, patt):
        try:
            attr = {'n':'name', 'c':'count', 's':'size'}[patt.lower()]
            self.key = operator.attrgetter(self.attrname)
        except KeyError:
            raise ValueError('invalid group ordering pattern')
        self.reverse = not patt.islower()

    def sort(self, a):
        a.sort(key=self.key, reverse=self.reverse)


class DownloadStateFilter(object):

    def __init__(self, patt=None):
        if patt is None:
            patt = 'dpn'
        self.states = frozenset(patt)
        if not self.states:
            raise ValueError('no download status flags specified')
        if not self.states.issubset(set('dpn')):
            raise ValueError('invalid download status: "%s"' % s)

    @staticmethod
    def getstate(path):
        """Get file state: 'd': downloaded, 'p': partial, 'n': missing."""
        if os.path.exists(path):
            return 'd'
        elif os.path.exists(path + PARTIAL_SUFFIX):
            return 'p'
        else:
            return 'n'

    def test(self, path):
        return self.getstate(path) in self.states

    def __repr__(self):
        return 'DownloadStateFilter(%r)' % ''.join(self.states)
        

def _parse_download_status(s):
    ret = frozenset(s)
    if not ret.issubset(set('dpn')):
        raise ValueError('invalid download status: "%s"' % s)
    return ret


def _rx_opt_callback(option, opt, value, parser, _include, _ignorecase):
    flags = re.IGNORECASE if _ignorecase else 0
    try:
        parser.values.regexps.append(NameRegexpFilter(_include, value, flags))
    except re.error:
        parser.error('invalid filter regexp: "%s"' % value)


class NameRegexpFilter(object):

    def __init__(self, include, patt, flags=0):
        self.include = include
        self.rx = re.compile(patt, flags)
        # patt and flags stored just for __repr__()
        self.patt = patt
        self.flags = flags

    def test(self, s):
        return self.include == bool(self.rx.search(s))

    def __repr__(self):
        return 'NameRegexpFilter(%s, %r, %s)' % (self.include, self.patt, self.flags)


def filter_item(relpath, fname, opts):
    """Determine whether an item will be processed, based on filter options."""
    fname = urllib2.unquote(fname)  # BUGFIX: needed to make filtering regexps work (need to rethink url quoting and filtering)
    # extension
    ext = os.path.splitext(fname)[1].lower()
    if opts.extensions and ext not in opts.extensions:
        return False
    # name regexps
    if not all(rx.test(fname) for rx in opts.regexps):
        return False
    # download state
    dst = safename(urllib2.unquote(os.path.join(opts.outdir, relpath + f.name)))
    if not opts.downloadstatus.test(dst):
        return False
    return True    


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
    return efutil.prettysize(n, iec).replace('bytes', '').rstrip('B').replace(' ', '')


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
    # and we retry the read, the data stream gets out of sync.
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
                hr, min, sec = mathutil.multi_divmod(file_eta, 60, 60)
                file_eta = '%d:%02d:%02d' % (hr, min, sec)

                total_eta = (totalsize - totaldone) / speed if speed else 0
                if total_eta < 0: total_eta = 0
                hr, min, sec = mathutil.multi_divmod(total_eta, 60, 60)
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
                    total_eta),

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
            print
            
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
    s = '%9s in %-5d  ' % (efutil.prettysize(dirobj.size), dirobj.count)
    s += ''.join((EMPTY_IDENT, FULL_IDENT)[i] for i in idents[:-1])
    if idents:
        s += (LAST_CHILD, CHILD)[idents[-1]]
    s += urllib2.unquote(dirobj.name)
    efutil.uprint(s)

    for sub in dirobj.subs:
        printtree(sub, idents + [sub is not dirobj.subs[-1]])


def squeezeprint(pfx, sfx, conwidth):
    maxsfxlen = conwidth - 1 - len(pfx) - 3  # 3 for '...', 1 to avoid wrapping
    if len(sfx) > maxsfxlen:
        sfx = '...' + sfx[-maxsfxlen:]
    efutil.uprint(pfx + sfx)

def myreader(cache):
    def reader(url):
        return cache[url]
    return reader

def myhandler(cache, spo, ignore):
    def handler(err, url):
        if not ignore:
            spo.restore(eolclear=True)
            efutil.uprint(url)
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


if __name__ == '__main__':
    opt = parse_cmdline()

##    # debug #########
##    from pprint import pprint as pp
##    pp(dict(opt.__dict__.items()))  # get a real dict for pretty-printing
##    raise SystemExit
##    # ###############

    cachedir = os.path.dirname(opt.cachefile)
    if not os.path.exists(cachedir):
        os.makedirs(cachedir)
    cache = Cache(opt.cachefile)

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
                    if filter_item(relpath, f.name, opt):
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
                    efutil.uprint(opt.topurl + relpath)
                    currelpath = relpath
                dst = safename(urllib2.unquote(os.path.join(opt.outdir, relpath + f.name)))
                exists = os.path.exists(dst)
                partial = not exists and os.path.exists(dst + PARTIAL_SUFFIX)
                efutil.uprint('  %s %10s %c %s' % (
                    compressdate(f.date),
                    f.size,
                    '*' if exists else '%' if partial else ' ',
                    urllib2.unquote(f.name)))

        if opt.groupsorder:
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
            groupsorder.sort(items)
            for item in items:
                clrout.write(0, extclrs.get(item.name.lstrip('.').lower(), 0), '  ')
                sys.stdout.write(' ')
                efutil.uprint('%-12s  %4d  %9s (%12d bytes)' % (item.name, item.count, efutil.prettysize(item.size), item.size))

        print
        print '---- Summary ----'
        print 'files: %d' % (totalfiles,)
        print 'size: %s (%d bytes)' % (efutil.prettysize(totalsize), totalsize)

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
                    efutil.uprint(safename(urllib2.unquote(relpath + f.name)))
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
                        efutil.uprint('  ' + s)
                if opt.beep:
                    win32api.MessageBeep(-1)
                
    except KeyboardInterrupt:
        print 'Cancelled by user.'
