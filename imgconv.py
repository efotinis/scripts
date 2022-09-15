"""Convert image format."""

import argparse
import os
import sys

from PIL import Image

import string

def parse_args():
    valid_formats = Image.SAVE.keys()

    p = argparse.ArgumentParser(
        description='Convert images to different format and remove original files.',
        epilog=f'Supported output formats: {", ".join(valid_formats)}.'
    )

    p.add_argument(
        '-f',
        dest='format', 
        metavar='FORMAT', 
        type=lambda s: s.upper(),
        choices=valid_formats,
        help='Output format. Must be specified if it cannot be infered '
             'from the output extension.'
    )
    p.add_argument(
        dest='extension', 
        metavar='OUTEXT', 
        type=lambda s: s if s.startswith('.') else '.' + s,
        help='Output extension, with optional leading dot. If possible, '
             'it will be used to infer the output format.'
    )
    p.add_argument(
        dest='source', 
        metavar='SRC', 
        nargs='+', 
        help='Input image path.'
    )
    p.add_argument(
        '-q', 
        dest='quality', 
        nargs=1, 
        default=75, 
        help='Target quality (where needed). Valid range: 0-100. Default: %(default)s.'
    )

    args = p.parse_args()

    if args.format is None:
        args.format = Image.EXTENSION.get(args.extension.lower())
        if args.format is None:
            p.error(f'Cannot infer format from extension: {args.extension}. Use -f.')
    
    if not 0 <= args.quality <= 100:
        p.error('Quality must be 0-100.')

    return args


def main(args):
    for path in args.source:
        stem, ext = os.path.splitext(path)
        deduced_format = Image.EXTENSION.get(ext.lower())
        if deduced_format is None:
            print(f'unknown extension format: {ext}', file=sys.stderr)
        elif deduced_format == args.format:
            print(f'skipping: {path}')
        else:
            try:
                im = Image.open(path)
                dest = stem + args.extension
                im.save(dest, args.format, quality=args.quality)
                print(f'converted: {path}')
            except Exception as x:
                print(f'could not convert: {path}; reason: {x}', file=sys.stderr)
            else:
                os.remove(path)


if __name__ == '__main__':
    Image.init()
    main(parse_args())

