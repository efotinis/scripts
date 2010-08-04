"""Join multiple images."""

from __future__ import print_function
from __future__ import division

import os
import sys
import re
import optparse
from PIL import Image
import wildcard


Image.init()  # load format drivers
INPUT_FORMATS = Image.OPEN.keys()
#OUTPUT_FORMATS = Image.SAVE.keys()
OUTPUT_FORMATS = 'PCX TIFF JPEG GIF BMP PNG'.split()

# mapping of file extension to image format
EXTENSION_FORMAT = {'PCX':'PCX', 'TIF':'TIFF', 'TIFF':'TIFF', 'JPG':'JPEG',
                    'JPEG':'JPEG', 'GIF':'GIF', 'BMP':'BMP', 'PNG':'PNG'}

ALIGNMENTS = 'tl t tr l c r bl b br'.split()
HORZ_ALIGNMENT = {'tl':0,'t':1,'tr':2,'l':0,'c':1,'r':2,'bl':0,'b':1,'br':2}
VERT_ALIGNMENT = {'tl':0,'t':0,'tr':0,'l':1,'c':1,'r':1,'bl':2,'b':2,'br':2}


def print_error(*x, **y):
    """Print to STDERR."""
    print(*x, file=sys.stderr, **y)


def gen_file_paths(masks):
    """Generate file paths from wildcard masks.

    Prints an error line if a mask doesn't match enything.
    A single path may be generated more than once if it matches multiple masks.
    """
    for mask in masks:
        head, tail = os.path.split(mask)
        matches = [os.path.join(head, s) for s in wildcard.listdir(tail, head)]
        matches = [s for s in matches if os.path.isfile(s)]
        if not matches:
            print_error('warning: no files matched with "{0}"'.format(mask))
        for s in matches:
            yield s


COLOR_FORMATS = (
    # '#RRGGBB'
    (   re.compile(r'^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$', re.IGNORECASE),
        lambda a: tuple(int(s, 16) for s in a)),
    # '#RGB'
    (   re.compile(r'^#([0-9a-f])([0-9a-f])([0-9a-f])$', re.IGNORECASE),
        lambda a: tuple(17 * int(s, 16) for s in a)),
    # 'r,g,b'
    (   re.compile(r'^(\d+),(\d+),(\d+)$', re.IGNORECASE),
        lambda a: tuple(int(s) for s in a)))


def parse_color(s):
    """Convert a color string to an RGB tuple.

    Allowed formats: '#RGB', '#RRGGBB' (hex), and 'r,g,b' (dec).
    """
    try:
        for regex, convert in COLOR_FORMATS:
            m = regex.match(s)
            if not m:
                continue
            ret = convert(m.groups())
            if all(0 <= n <= 255 for n in ret):
                return ret
    except ValueError:
        pass
    raise ValueError('invalid color value: "{0}"'.format(s))


def parse_cmdline():
    loadformats = ', '.join(INPUT_FORMATS)
    saveformats = ', '.join(OUTPUT_FORMATS)
    op = optparse.OptionParser(
        usage='%prog [options] INPUTS OUTPUT',
        description='Join multiple images.',
        epilog='Supported input formats: {0}. '
               'Supported output formats: {1}.'.format(loadformats, saveformats),
        add_help_option=False)

    add = op.add_option
    add('-v', dest='vertical', action='store_true', 
        help='Vertical layout. Default is horizontal.')
    add('-b', dest='breaknum', type='int', default=0, metavar='NUM',
        help='Number of images per row (or column if layout is vertical). '
             'Use this to create a table. Default is 0, which means no break '
             '(a single row/column).')
    add('-p', dest='packed', action='store_true', 
        help='Pack images together, i.e. don\'t use max width/height. '
             'Ignored when -b is used.')
    add('-f', dest='fillcolor', default='0,0,0', metavar='CLR',
        help='Background fill color. Specify as red, green and blue components '
             '(range 0-255), separated by commas, or as CSS colors (#RRGGBB, #RGB). '
             'Default is %default.')
    add('-a', dest='align', choices=ALIGNMENTS, default='c',
        help='Alignment of individual images. Accepted values: ' + ','.join(ALIGNMENTS) +
             '. Default is "%default".')
    add('-o', dest='outformat', metavar='FMT', choices=OUTPUT_FORMATS,
        help='Output image format. The default depends on the output extension.')
    add('-q', dest='quality', type='int', metavar='NUM', default=0,
        help='Output image quality. Used only for formats that support variable quality, like JPEG. '
             'Range is 1..100. Default is 0, which maps to a default quality setting.')
    add('-?', action='help',
        help=optparse.SUPPRESS_HELP)
    opt, args = op.parse_args()

    if len(args) >= 2:
        opt.inputs, opt.output = args[:-1], args[-1]
    else:
        op.error('at least 2 params are required')
    if not opt.outformat:
        opt.outformat = EXTENSION_FORMAT[os.path.splitext(args[-1])[1].lstrip('.').upper()]
    if opt.outformat not in OUTPUT_FORMATS:
        op.error('unsupported output format: "{0}"'.format(opt.outformat))
    if opt.breaknum < 0:
        op.error('invalid break value: {0}'.format(opt.breaknum))
    try:
        opt.fillcolor = parse_color(opt.fillcolor)
    except ValueError as err:
        op.error(str(err))
    if not 0 <= opt.quality <= 100:
        op.error('quality value out of range')

    return opt


def bounding_box(boxes):
    """Bounding box of a sequence of boxes."""
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def calc_img_cells(sizes, vertical, breaknum, packed):
    """Calculate image cells, i.e. output grid before alignment."""
    if vertical:
        # to avoid code duplication for the vertical layout, we first transpose
        # the image sizes on entry and then re-transpose the returned boxes on exit
        sizes = [(s[1], s[0]) for s in sizes]
    max_width = max(s[0] for s in sizes)
    max_height = max(s[1] for s in sizes)
    ret = []
    if not breaknum and packed:
        # single, packed row
        x = 0
        for s in sizes:
            ret.append([x, 0, x + s[0], max_height])
            x += s[0]
    else:
        # table
        x, y, n = 0, 0, 0
        for s in sizes:
            ret.append([x, y, x + max_width, y + max_height])
            x += max_width
            n += 1
            if n == breaknum:
                x = 0
                y += max_height
                n = 0
    if vertical:
        # see similar 'if' at function top
        ret = [(r[1], r[0], r[3], r[2]) for r in ret]
    return ret


def calc_img_boxes(cells, sizes, alignment):
    """Calculate subimage boxes by aligning into output grid cells."""
    ret = []
    for cell, size in zip(cells, sizes):
        cell_w, cell_h = cell[2] - cell[0], cell[3] - cell[1]
        assert cell_w >= size[0] and cell_h >= size[1], 'calculated cell too small'
        x1, x2 = align(cell[0], cell_w, size[0], HORZ_ALIGNMENT[alignment])
        y1, y2 = align(cell[1], cell_h, size[1], VERT_ALIGNMENT[alignment])
        ret.append([x1, y1, x2, y2])
    return ret


def align(cell_orig, cell_size, size, alignment):
    """Align a single dimension (size) to an ouput segment (cell_orig, cell_size).

    Alignment can be: 0=start, 1=middle, 2=end.
    """
    assert cell_size >= size
    if alignment == 0:
        return cell_orig, cell_orig + size
    elif alignment == 1:
        beg = cell_orig + (cell_size - size) // 2
        return beg, beg + size
    elif alignment == 2:
        end = cell_orig + cell_size
        return end - size, end
    else:
        raise ValueError('invalid alignment')
        


if __name__ == '__main__':
    opt = parse_cmdline()

    # get input images
    opt.inputs = list(gen_file_paths(opt.inputs))
    if not opt.inputs:
        raise ValueError('no input images')
    print('joining {0} image(s)...'.format(len(opt.inputs)))

    # load images and calc output grid
    imgs = [Image.open(s) for s in opt.inputs]
    img_sizes = [im.size for im in imgs]
    img_cells = calc_img_cells(img_sizes, opt.vertical, opt.breaknum, opt.packed)

    # allocate and init ouput image
    bounds = bounding_box(img_cells)
    assert bounds[:2] == (0,0)
    outimg = Image.new('RGB', bounds[2:], opt.fillcolor)

    # paste images into grid with proper alignment
    img_boxes = calc_img_boxes(img_cells, img_sizes, opt.align)
    for im, box in zip(imgs, img_boxes):
        outimg.paste(im, box)

    outimg.save(opt.output, opt.outformat, quality=opt.quality)
