"""File utilities."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import os

import efutil
import fsutil
from PIL import Image
import stats

from status import Status


AVPROBE = 'c:/tools/libav/usr/bin/avprobe.exe'
if not os.path.isfile(AVPROBE):
    sys.exit('missing dependency: {}'.format(AVPROBE))


Image.init()  # maybe preinit() instead?


class Error(Exception):
    pass


def files(dp, recurse=False):
    """Get Path file objects of specified dir (optionally recursively)."""
    #return (x for x in dp.iterdir() if x.is_file())
    for x in dp.iterdir():
        if x.is_file():
            yield x
        elif recurse:
            yield from files(x, recurse)

def dirs(dp):
    """Get Path dir objects of specified dir."""
    return (x for x in dp.iterdir() if x.is_dir())

def is_image(fp):
    """Test if path has an image extension."""
    return fp.suffix.lower() in Image.EXTENSION

def verify_image(fp):
    """Test if image can be opened."""
    try:
        Image.open(str(fp))
        return True
    except OSError:
        return False

def avprobe(fp):
    """Media container/streams info."""
    s = subprocess.check_output(
        [AVPROBE, '-show_format', '-show_streams', '-of', 'json', str(fp)],
        stderr=subprocess.DEVNULL,
        shell=True)
    try:
        return json.loads(str(s, 'utf-8'))  # avprobe outputs UTF-8, apparently
    except UnicodeError:
        efutil.conerr('could not decode result of "{}"'.format(str(fp)))
        return json.loads(str(s, 'utf-8', 'replace'))

def move(items, target):
    """Move items to target dir."""
    for src in items:
        src.rename(target / src.name)


def parse_args():
    parser = argparse.ArgumentParser(description='file utilities')
    subs = parser.add_subparsers(dest='cmd')

    ap = subs.add_parser('v', help='list video durations')
    add = ap.add_argument
    add('dirs', metavar='DIR', type=Path, nargs='+', help='dir containing videos')
    add('-r', dest='recurse', action='store_true', help='recurse subdirs')
    add('-b', dest='bare', action='store_true', help='omit footer totals')
    add('-t', dest='totals', action='store_true',
        help='output totals only: count, time, avg, sd')

    ap = subs.add_parser('i', help='list corrupt images')
    add = ap.add_argument
    add('dirs', metavar='DIR', type=Path, nargs='+', help='dir containing images')
    add('-o', dest='outdir', type=Path, help='output dir to move images')

    return parser.parse_args()


class VideoInfo:
    """Video file information."""
    def __init__(self, path):
        self.info = avprobe(path)

    def resolution(self):
        """Get (width,height) of video.

        If the container data does not contain resolution info, the video
        streams are checked. Multiple video streams with different sizes
        (or no video streams at all) raise an error.
        """
        # check container first
        try:
            fmt = self.info['format']
            return int(fmt['width']), int(fmt['height'])
        except KeyError:
            pass
        # check video streams
        resolutions = set((int(s['width']), int(s['height']))
                          for s in self._vid_streams())
        if not resolutions:
            raise Error('no video streams')
        if len(resolutions) > 1:
            raise Error('multiple video stream resolutions')
        return resolutions.pop()

    def duration(self):
        """Get duration in seconds."""
        try:
            return float(self.info['format']['duration'])
        except KeyError:
            raise Error('could not determine duration')

    def bitrate(self):
        """Get total rate in bits per second."""
        try:
            return float(self.info['format']['bit_rate'])
        except KeyError:
            raise Error('could not determine bitrate')

    def framerate(self):
        """Get rate in frames per second."""
        framerates = set(int_ratio(s['avg_frame_rate'])
                         for s in self._vid_streams())
        if not framerates:
            raise Error('no video streams')
        if len(framerates) > 1:
            raise Error('multiple video stream framerates')
        return framerates.pop()

    def _vid_streams(self):
        """Generate video streams (excluding apparent thumbnails)."""
        for s in self.info['streams']:
            # FIXME: some videos streams (WMV) do have avg_frame_rate == 0/0
            if s['codec_type'] == 'video' and s['avg_frame_rate'] != '0/0':
                yield s


VIDEO_EXTS = set('.' + s for s in 'avi wmv mp4 m4v mov mpeg mpg rm flv ogm mkv ram asf webm'.split())


def is_video(fp):
    """Test if path has a video extension."""
    return fp.suffix.lower() in VIDEO_EXTS


def int_ratio(s):
    """Float ratio from 'x/y' string."""
    x, sep, y = s.partition('/')
    return int(x) / int(y)


def do_videos(args):
    durations = []
    for d in args.dirs:
        for f in files(d, args.recurse):
            if is_video(f):
                try:
                    info = VideoInfo(str(f))
                    width, height = info.resolution()
                    duration = info.duration()
                    durations += [duration]
                    if not args.totals:
                        efutil.conout('{} {:4d}x{:<4d} {:5.2f} {:5.0f}k {}'.format(
                            efutil.timefmt(duration),
                            width, height,
                            info.framerate(),
                            info.bitrate() / 1000,
                            f))
                    else:
                        print(len(durations), end='\r', flush=True)
                except subprocess.CalledProcessError:
                    efutil.conerr('could not get info for "{}"'.format(str(f)))
                except Error as x:
                    efutil.conerr('could not get info for "{}" ({})'.format(str(f), x))
    if args.totals:
        print('{:4} {} {} {} {}'.format(
            len(durations),
            efutil.timefmt(sum(durations)),
            efutil.timefmt(stats.amean(durations) if durations else 0),
            efutil.timefmt(stats.stddev(durations) if durations else 0),
            ', '.join('"{}"'.format(d) for d in args.dirs)
        ))
    elif not args.bare:
        print('total videos:', len(durations))
        print('duration:')
        print('  total:', efutil.timefmt(sum(durations)))
        print('    avg:', efutil.timefmt(stats.amean(durations) if durations else 0))
        print('     sd:', efutil.timefmt(stats.stddev(durations) if durations else 0))
    

def do_images(args):
    if args.outdir and not args.outdir.is_dir():
        args.outdir.mkdir(parents=True)
    with Status() as st:
        st.update('scanning images...')
        images = [f for d in args.dirs for f in files(d) if is_image(f)]
        for i, p in enumerate(images, 1):
            st.update('{}/{}'.format(i, len(images)))
            if not verify_image(p):
                if args.outdir:
                    p.rename(args.outdir / p.name)
                else:
                    with st.hide():
                        print(p)


if __name__ == '__main__':
    args = parse_args()
    try:
        if args.cmd == 'v':
            do_videos(args)
        elif args.cmd == 'i':
            do_images(args)
        else:
            print('unknown cmd:', args.cmd, file=sys.stderr)
    except KeyboardInterrupt:
        sys.exit('cancelled')
