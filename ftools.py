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


####RX = re.compile(r'^(\d+)\. (.*) \((\d{8})\) \[((?:\w|-)+)\]\.mp4$')
####def parse_ydl_name(s):
####    """(index,name,date,id) from 'index. name (date) [id].mp4'."""
####    return RX.match(s).groups()
##
##RX = re.compile(r'^\[(\d{8})\] (.*) \[((?:\w|-)+)\]\.mp4$')
##def parse_ydl_name(s):
##    """(date,name,id) from '[date] name [id].mp4'."""
##    return RX.match(s).groups()
##
##if __name__ == '__main__':
##    (DIR,) = sys.argv[1:]
##    for s in os.listdir(DIR):
##        p = os.path.join(DIR, s)
##        date, name, id_ = parse_ydl_name(s)
##        duration = fmt_hhmmss(get_duration(p))
##        print(date, id_, duration, name)


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


VIDEO_EXTS = set('.' + s for s in 'avi wmv mp4 m4v mov mpeg mpg rm flv ogm mkv ram asf'.split())


def is_video(fp):
    """Test if path has a video extension."""
    return fp.suffix.lower() in VIDEO_EXTS


def get_first_stream(info, type_):
    """Get first video/audio stream or None.

    type_ can be 'video' or 'audio'.
    A weird WMV had 3 video streams, but the last 2 had an avg_frame_rate=0/0.
    """
    a = [stream for stream in info['streams'] if stream['codec_type'] == type_]
    return a[0] if a else None


def get_video_size(info):
    """Video (width,height).

    Tries the format info first and then the first video stream.
    """
    try:
        return int(info['format']['width']), int(info['format']['height'])
    except KeyError:
        vid = get_first_stream(info, 'video')
        if not vid:
            raise ValueError('no video streams')
        return int(vid['width']), int(vid['height'])


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
                    info = avprobe(str(f))
                    duration = float(info['format']['duration'])
                    bitrate_kbps = round(float(info['format']['bit_rate']) / 1000)
                    video = get_first_stream(info, 'video')
                    audio = get_first_stream(info, 'audio')
                    print(
                        efutil.timefmt(duration),
                        '{:4d}x{:<4d}'.format(video['width'], video['height']) if video else '----x----',
                        '{:5.2f}'.format(int_ratio(video['avg_frame_rate'])) if video else '-----',
                        '{:4.0f}k'.format(float(video.get('bit_rate', '-1')) / 1000) if video else '----',
                        f)
                    durations += [duration]
                except subprocess.CalledProcessError:
                    print('could not get media info: "{}"'.format(str(f)), file=sys.stderr)
    print('total videos:', len(durations))
    print('duration:')
    print('  total:', efutil.timefmt(sum(durations)))
    print('  average:', efutil.timefmt(stats.amean(durations)))
    print('  stddev:', efutil.timefmt(stats.stddev(durations)))
    


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
