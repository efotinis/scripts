# TODO: add flags for mask interpretation (-w:wildcard(def), -g:glob, [-r:regexp])
# TODO: add warning output when a mask doesn't match anything
# TODO: add negotiation to check for already tranferred files (either whole or partial);
#       before getting data, the client should send the size and hash of the an existing file
# TODO: encryption (possibly with pycrypto)
# TODO: add move option (delete source on successful send)
# TODO: add custom socket timeout

import os
import sys
import copy
import optparse
import time
import contextlib
import ctypes
import socket
import struct
import contextlib
import glob

import optparseutil
import win32file
import dllutil
import CommonTools
import mathutil
import console_stuff
import quantizer

from ctypes.wintypes import BOOL, DWORD, HANDLE, FILETIME, LARGE_INTEGER
LPDWORD = ctypes.POINTER(DWORD)
LPFILETIME = ctypes.POINTER(FILETIME)
PLARGE_INTEGER = ctypes.POINTER(LARGE_INTEGER)


DEFAULT_PORT = 14580
DEFAULT_BUFLEN = 1024 * 32  # used to be 4K, but that caused congestion


# ====================================================================================


'''
Stream Format
=============

stream:
    file0, file1, ..., fileN

file:
    size    type    descr
    ----    ----    -----
       4    uint    path name size
       *    str     path name (utf-8); should be relative for security reasons
       4    uint    attributes
       8    uint    creation time (FILETIME, UTC)
       8    uint    modification time (FILETIME, UTC)
       8    uint    file size
       *    str     file data

Notes:
- integers are little-endian
- hash field has been removed, since the socket type used (SOCKET_STREAM) is "reliable"

'''

'''
Stream Format (New)
===================

legend:
    [S]     server
    [C]     client
    <...>   data sent

structs:
    TOTALS_INFO     info about number of files/firs, total size, max path size


Protocol selection:
    [S] <PROTO_LIST>
    [C] (select protocol or close)

Protocol 0:
    [S] <TOTALS_INFO>
    [C] if accept:
            <REPLY("ack")>
        else:
            <REPLY("nak", "reason")>
            close()
    [S] for f in files:
            <file path/size>
    [C]     (send existing size & data hash for data up to min(client size, server size))
    [S]     (verify existing client data)




'''


# utilities ==========================================================================


kernel32 = dllutil.WinDLL('kernel32')
GetFileTime = kernel32('GetFileTime', BOOL, [HANDLE, LPFILETIME, LPFILETIME, LPFILETIME])
SetFileTime = kernel32('SetFileTime', BOOL, [HANDLE, LPFILETIME, LPFILETIME, LPFILETIME])
GetFileSizeEx = kernel32('GetFileSizeEx', BOOL, [HANDLE, PLARGE_INTEGER])


FILE_READ_ATTRIBUTES = 0x0080
FILE_WRITE_ATTRIBUTES = 0x0100
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000  # to allow opening handles to directories


def getFileTime(path):
    access = FILE_READ_ATTRIBUTES
    sharing = win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE | win32file.FILE_SHARE_DELETE
    flags = FILE_FLAG_BACKUP_SEMANTICS
    h = win32file.CreateFileW(path, access, sharing, None, win32file.OPEN_EXISTING, flags, None)
    with contextlib.closing(h):
        created, accessed, modified = FILETIME(), FILETIME(), FILETIME()
        if not GetFileTime(h.handle, created, accessed, modified):
            raise ctypes.WinError()
        return created, accessed, modified
        
    
def setFileTime(path, created, accessed, modified):
    access = FILE_WRITE_ATTRIBUTES
    sharing = win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE | win32file.FILE_SHARE_DELETE
    flags = FILE_FLAG_BACKUP_SEMANTICS
    h = win32file.CreateFileW(path, access, sharing, None, win32file.OPEN_EXISTING, flags, None)
    with contextlib.closing(h):
        if not SetFileTime(h.handle, created, accessed, modified):
            raise ctypes.WinError()


def getFileAttr(path):
    return win32file.GetFileAttributesW(path)


def setFileAttr(path, n):
    return win32file.SetFileAttributesW(path, n)


def getFileSize64(path):
    access = FILE_READ_ATTRIBUTES
    sharing = win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE | win32file.FILE_SHARE_DELETE
    flags = FILE_FLAG_BACKUP_SEMANTICS
    h = win32file.CreateFileW(path, access, sharing, None, win32file.OPEN_EXISTING, flags, None)
    with contextlib.closing(h):
        li = LARGE_INTEGER()
        if not GetFileSizeEx(h.handle, li):
            raise ctypes.WinError()
        return li.value


# server =============================================================================


def server_filestream(fpath, buflen):
    created, _, modified = getFileTime(fpath)
    attr = getFileAttr(fpath)
    size = getFileSize64(fpath)

    #print 'LOG:', 'sending ' + fpath
    
    s = fpath.encode('utf-8')
    s = struct.pack('<L', len(s)) + s
    s += struct.pack('<LLLLLQ',
                     attr,
                     created.dwLowDateTime, created.dwHighDateTime,
                     modified.dwLowDateTime, modified.dwHighDateTime,
                     size)
    yield s
    #print 'LOG:', 'header (%d)' % len(s)

    with open(fpath, 'rb') as f:
        while True:
            s = f.read(buflen)
            if not s:
                break
            yield s
            #print 'LOG:', 'data (%d)' % len(s)


def run_server(listenport, buflen, files):
    print 'files to be sent:', len(files)

    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as ssoc:
        #ssoc.bind((socket.gethostname(), listenport))
        #--------------------------------------------------------
        # Using the above bind() we end up binding to the IP of one of the virtual VMware
        # networks, 192.168.193.1 (can be seen with 'netstat -anp tcp | find "14580"').
        #
        # I don't know why this IP is used, but I've noticed that it comes up as the first
        # IP4 address in getaddrinfo()'s results:
        #
        #   >>> socket.getaddrinfo(socket.gethostname(), None)
        #   [(23, 0, 0, '', ('fe80::a172:9160:3ac7:54c4%13', 0, 0, 13)),
        #    (23, 0, 0, '', ('fe80::78f6:b6c5:3690:834f%15', 0, 0, 15)),
        #    (23, 0, 0, '', ('fe80::60:da63:dd6e:2b66%11', 0, 0, 11)),
        #    (23, 0, 0, '', ('fe80::1cb0:2667:c1fe:57f2%20', 0, 0, 20)),
        #    (2, 0, 0, '', ('192.168.193.1', 0)),          # <-- this is what we get
        #    (2, 0, 0, '', ('192.168.93.1', 0)),
        #    (2, 0, 0, '', ('192.168.1.4', 0)),            # <-- this is what we want
        #    (23, 0, 0, '', ('2001:0:5ef5:79fd:1cb0:2667:c1fe:57f2', 0, 0, 0))]
        #
        # I've also noticed that gethostbyname_ex() returns the preferred IP first, so we
        # use that to get a numeric IP instead of passing the host name directly to bind().
        #
        # Networking is hard... :(
        #--------------------------------------------------------
        ip = socket.gethostbyname_ex(socket.gethostname())[2][0]
        ssoc.bind((ip, listenport))
        ssoc.listen(1)

        print 'waiting for client on port %d ...' % listenport
        csoc, address = ssoc.accept()
        with contextlib.closing(csoc):
            print 'got connection:', address
            try:
                for fp in files:
                    for data in server_filestream(fp, buflen):
                        csoc.sendall(data)
            except socket.error as err:
                print 'ERROR:', str(err)


# client =============================================================================


def client_filestream(outdir, reader, buflen):
    n = 0
    try:
        s = reader(4)
        n += len(s)
    except EOFError:
        #print 'LOG:', 'end of stream'
        return False
    (pathsize,) = struct.unpack('<L', s)
    s = reader(pathsize)
    n += len(s)
    fpath = s.decode('utf-8')

    CommonTools.uprint('receiving "%s"' % fpath)

    s = reader(28)
    n += len(s)
    (attr, c_low, c_high, m_low, m_high, size) = struct.unpack('<LLLLLQ', s)
    created = FILETIME(c_low, c_high)
    modified = FILETIME(m_low, m_high)

    #print 'LOG:', 'header (%d)' % n
    #print 'LOG:', 'path:', fpath

    outfile = os.path.join(outdir, fpath)

    # create dirs if needed
    filedir = os.path.dirname(outfile)
    if not os.path.exists(filedir):
        os.makedirs(filedir)

    spo = console_stuff.SamePosOutput()
    #ma = util.MovingAverage(1, 10)
    quant = quantizer.TimeQuantizer(1.0, 30)
    t = time.time()
    with open(outfile, 'wb') as f:
        bytesleft = size
        while bytesleft > 0:
            s = reader(min(buflen, bytesleft))
            f.write(s)
            #ma.add(len(s))
            quant += len(s)
            if time.time() - t >= 1.0:
                spo.restore(eolclear=True)
                gotsize = size - bytesleft
                #speed = ma.calc()
                speed = sum(quant.data) / len(quant.data) if quant.data else 0
                H, M, S = mathutil.multi_divmod(bytesleft / speed if speed else 0, 60, 60)
                print '  got: %s,  speed: %s/s,  ETA: %02d:%02d:%02d' % (
                    CommonTools.prettysize(gotsize),
                    CommonTools.prettysize(speed),
                    H, M, S)
                t = time.time()
            bytesleft -= len(s)
            #print 'LOG:', 'data (%d)' % len(s)
    spo.restore(eolclear=True)

    setFileTime(outfile, created, None, modified)
    setFileAttr(outfile, attr)

    return True


def readerfunc(soc_recv):
    def f(size):
        data = ''
        while len(data) < size:
            s = soc_recv(size - len(data))
            if not s:
                raise EOFError
            data += s
        return data
    return f


def run_client(listenport, buflen, server, outdir):
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as soc:
        soc.settimeout(10)
        try:
            soc.connect((server, listenport))
            while client_filestream(outdir, readerfunc(soc.recv), buflen):
                pass
            print 'done'
        except socket.timeout as err:
            CommonTools.exiterror(str(err))



# ====================================================================================


class CustomOption(optparse.Option):
    """Extended optparse Option class which includes a 'size' type."""
    TYPES = optparse.Option.TYPES + ('size',)
    TYPE_CHECKER = copy.copy(optparse.Option.TYPE_CHECKER)
    TYPE_CHECKER['size'] = optparseutil.check_size


def parse_cmdline():
    parser = optparse.OptionParser(
        option_class=CustomOption,
        usage=None, description='Transfer files using TCP.',
        epilog=None, add_help_option=False)

    _add = parser.add_option

    _add('-r', action='store', dest='receivefrom', metavar='SRV',
         help='Receive from the specified server. The output directory must be specified as an argument. '
         'If this switch is omitted, runs a server and the program arguments specify the files and '
         'directories to send.')
    _add('-p', type='int', dest='port', default=DEFAULT_PORT,
         help='Server port. Default is %default.')
    _add('-b', type='size', dest='buflen', default=DEFAULT_BUFLEN,
         help='Buffer size. Size suffix (K,M,etc) allowed. Default is %default.')
    _add('-?', action='help',
         help='Show this help.')

    opt, args = parser.parse_args()

    if not 1024 <= opt.port <= 65535:
        parser.error('invalid port number; must be 1024..65535')
    if not 1 <= opt.buflen <= 2**20:
        parser.error('invalid buffer size; must be 1..1M')
    if opt.receivefrom is None and not args:
        parser.error('no arguments specified for sending')
    if opt.receivefrom is not None and len(args) != 1:
        parser.error('no output dir specified for receiving')

    return opt, args


if __name__ == '__main__':
    opt, args = parse_cmdline()
    #print opt

    if opt.receivefrom is None:
        masks = [unicode(s) for s in args]
        files = sum((glob.glob(s) for s in masks), [])
        if not files:
            raise SystemExit('no files matched')
        run_server(opt.port, opt.buflen, files)
    else:
        outdir, = args
        run_client(opt.port, opt.buflen, opt.receivefrom, outdir)
