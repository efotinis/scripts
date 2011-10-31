"""Produce sounds using the Windows MessageBeep() API."""

import sys
import time
import argparse
import winsound


SOUNDS = {
    'ok': winsound.MB_OK,
    'i': winsound.MB_ICONASTERISK,
    'w': winsound.MB_ICONEXCLAMATION,
    'e': winsound.MB_ICONHAND,
    'q': winsound.MB_ICONQUESTION,
    's':  -1,
}


def parse_args():
    ap = argparse.ArgumentParser(
        description='play a Windows sound',
        add_help=False)
    ap.add_argument('sound', metavar='SOUND', choices=SOUNDS, default='ok', nargs='?',
                    help='sound type: ok (default), i (info, asterisk), '
                         'w (warning, exclamation), e (error, hand, stop), q (question), '
                         '-1 (speaker beep; obsoleted since Vista)')
    group = ap.add_mutually_exclusive_group()
    group.add_argument('-l', dest='loop', action='store_true',
                       help='loop until interrupted by user')
    group.add_argument('-r', dest='repeats', type=int, default=1,
                       help='number of repetitions; default: %(default)s')
    ap.add_argument('-d', dest='delay', type=float, default=1.0,
                    help='delay in seconds between repeats; default: %(default)s')
    ap.add_argument('-?', action='help',
                    help='this help')
    args = ap.parse_args()
    args.sound = SOUNDS[args.sound]
    if args.repeats < 1:
        ap.error('repeat count must be >= 1')
    if args.delay < 0:
        ap.error('delay must be >= 0')
    return args


if __name__ == '__main__':
    args = parse_args()

    try:
        first = True
        while True:
            if first:
                first = False
            else:
                time.sleep(args.delay)

            winsound.MessageBeep(args.sound)

            if args.loop:
                continue
            args.repeats -= 1
            if args.repeats <= 0:
                break

    except KeyboardInterrupt:
        sys.exit('canceled by user')
