#!python3
"""Downlad manager utilities."""

import contextlib
import os
import sys
import time

import requests

import efutil


'''

can     remote  local
resume  size    size
        (nr)    (nl)
======  ======  ======
x       x       --      create file; get [0,nr)
x       x       =       already downloaded
x       x       <       open file; get [nl,nr)
x       x       >       truncate?

x       --      --      create file; get all
x       --      ?       open file; get [nl,)

--      x       --      create file; get all
--      x       =       already downloaded
--      x       <       restart; create file; get all
--      x       >       truncate?

--      --      --      create file; get all
--      --      ?       restart; create file; get all


'''

class Status:

    def __init__(self):
        self.lastdisplen = 0
        self.lastupdate = time.monotonic()

    def begin(self, canresume, remotesize, localsize):
##        print('size (remote/local): ', remotesize, localsize)
##        print('resumable:', canresume)
        pass

    def update(self, start, cur, total, elapsed):
        t = time.monotonic()
        if t - self.lastupdate < 1.0:
            return
        self.lastupdate = t
        if total is not None:
            ratio = cur / total if total else 0
            downloaded = cur - start
            pending = total - cur
            speed = downloaded / elapsed if elapsed else 0
            eta = pending / speed if speed else 0
            msg = '{} ({:.0%}) of {} at {}/s; ETA {}'.format(
                efutil.prettysize(cur),
                ratio,
                efutil.prettysize(total),
                efutil.prettysize(speed),
                efutil.timefmt(eta))
        else:
            msg = '{}'.format(
                efutil.prettysize(cur))
        displen = len(msg)
        print(msg.ljust(self.lastdisplen), end='\r', flush=True)
        self.lastdisplen = displen

    def end(self, msg):
        print(msg.ljust(self.lastdisplen))


def download_with_resume(remote, local, status, blocksize=65536, allow_restart=False, allow_truncate=False):
    """Download web resource with resume support."""

    if os.path.exists(local):
        status.end('already downloaded')
        return True

    TIMEOUT = None

    with contextlib.closing(requests.head(remote, stream=True, timeout=TIMEOUT)) as r:
        canresume = 'bytes' in r.headers.get('Accept-Ranges', '')
        remotesize = int(r.headers['Content-Length']) if 'Content-Length' in r.headers else None

    local_partial = local + '.part'
    localsize = os.path.getsize(local_partial) if os.path.exists(local_partial) else None

    status.begin(canresume, remotesize, localsize)

    if localsize is not None and remotesize is not None:
        if localsize == remotesize:
            status.end('already downloaded')
            os.rename(local_partial, local)
            return True
        if localsize > remotesize:
            if not allow_truncate:
                status.end('local file is larger than remote')
                return False
            with open(local_partial, 'r+b') as f:
                f.truncate(remotesize)
            status.end('truncated existing')
            os.rename(local_partial, local)
            return True

    f = None
    try:
        if canresume and remotesize is not None:
            #print('resuming range {} ... {}'.format(localsize or 0, remotesize))
            f = open(local_partial, 'w+b' if localsize is None else 'r+b')
            h = {'Range': 'bytes={}-{}'.format(localsize or 0, remotesize)}
        elif canresume and remotesize is None and localsize is not None:
            #print('resuming range {} ... ?'.format(localsize))
            f = open(local_partial, 'r+b')
            h = {'Range': 'bytes={}-'.format(localsize)}
        else:
            #print('starting download')
            f = open(local_partial, 'w+b')
            h = {}
        localsize = localsize or 0

        with contextlib.closing(requests.get(remote, headers=h, stream=True, timeout=TIMEOUT)) as r:
            f.seek(0, os.SEEK_END)
            startpos = localsize
            starttime = time.monotonic()
            status.update(startpos, localsize, remotesize, time.monotonic() - starttime)
            for block in r.iter_content(blocksize):
                f.write(block)
                localsize += len(block)
                status.update(startpos, localsize, remotesize, time.monotonic() - starttime)
    except KeyboardInterrupt:    
        status.end('cancelled')
        return False
    finally:
        if f:
            f.close()

    status.end('done')
    os.rename(local_partial, local)
    return True


if __name__ == '__main__':
    url, path = sys.argv[1:]
    download_with_resume(url, path, Status())
