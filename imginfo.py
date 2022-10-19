"""Output image file information in JSON."""

import argparse
import glob
import json
import os
import sys

from PIL import Image


def parse_args():
    p = argparse.ArgumentParser(
        description='Get image file information. Output format is JSON.',
        epilog='''
Note for Windows 7 with PowerShell 5: To properly accept Unicode file paths via
the pipeline, set $OutputEncoding to UTF-8 and enable Python\'s UTF-8 mode:
  PS> $OutputEncoding = [System.Text.UTF8Encoding]::new($false)  # no BOM
  PS> $Env:PYTHONUTF8 = 1  # or run script with "py -X utf8"
  PS> ls ... | % FullName | imginfo.py -'''[1:],
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        'input',
        metavar='FILE',
        nargs='*',
        help='Input file paths. Recursive glob patterns allowed. '
            'Use "-" to read literal file paths from STDIN (see note below).'
    )
    p.add_argument(
        '-G',
        dest='no_glob',
        action='store_true',
        help='Disable glob matching for input parameters.'
    )
    return p.parse_args()


def output_image_info_json(path):
    try:
        with Image.open(path) as im:
            print(json.dumps({
                'width': im.width,
                'height': im.height,
                'format': im.format,
                'mime': im.get_format_mimetype(),
                'mode': im.mode,
                'path': path
            }))
    except OSError:
        print(f'Could not get image info: {path!r}', file=sys.stderr)


def process_input_arg(s, no_glob):
    if s == '-':
        yield from map(lambda s: s.rstrip('\n'), sys.stdin)
    elif no_glob:
        yield s
    else:
        no_match = True
        for path in glob.iglob(s, recursive=True):
            no_match = False
            yield path
        if no_matched:
            print(f'Pattern matched nothing: {s!r}', file=sys.stderr)


def main(args):
    for s in args.input:
        for path in process_input_arg(s, args.no_glob):
            output_image_info_json(path)


if __name__ == '__main__':
    main(parse_args())
