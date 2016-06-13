"""File utilities."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

import efutil
import fsutil
from PIL import Image
import stats

from status import Status


AVPROBE = 'c:/prg/libav/usr/bin/avprobe.exe'


Image.init()  # maybe preinit() instead?


class Error(Exception):
    pass


def files(dp):
    """Get Path file objects of specified dir."""
    return (x for x in dp.iterdir() if x.is_file())

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
    return json.loads(str(s, 'mbcs'))

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
        for f in files(d):
            if is_video(f):
                try:
                    info = VideoInfo(str(f))
                    width, height = info.resolution()
                    print('{} {:4d}x{:<4d} {:5.2f} {:5.0f}k {}'.format(
                        efutil.timefmt(info.duration()),
                        width, height,
                        info.framerate(),
                        info.bitrate() / 1000,
                        f))
                    durations += [info.duration()]
                except subprocess.CalledProcessError:
                    print('could not get media info: "{}"'.format(str(f)), file=sys.stderr)
    print('total videos:', len(durations))
    print('duration:')
    print('  total:', efutil.timefmt(sum(durations)))
    print('    avg:', efutil.timefmt(stats.amean(durations)))
    print('     sd:', efutil.timefmt(stats.stddev(durations)))
    

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
