"""Join multiple images into one."""

import sys
import re
import optparse

from PIL import Image

import CommonTools


Image.init()  # load format drivers
INPUT_FORMATS = Image.OPEN.keys()
OUTPUT_FORMATS = Image.SAVE.keys()


def parse_color(s):
    """Convert 'r,g,b' string to number triple. Each element must be in 0-255."""
    m = re.match(r'^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$', s)
    try:
        if not m:
            raise ValueError
        ret = map(int, m.groups())
        if not all(0 <= n <= 255 for n in ret):
            raise ValueError
        return ret
    except ValueError:
        raise ValueError('invalid color value: "%s"' % s)


def parse_cmdline():
    loadformats = ','.join(INPUT_FORMATS)
    saveformats = ','.join(OUTPUT_FORMATS)
    op = optparse.OptionParser(
        usage='%prog [options] INPUTS OUTPUT',
        description='Join multiple images.',
        epilog='Supported input formats: %(loadformats)s. '
               'Supported output formats: %(saveformats)s.' % locals(),
        add_help_option=False)

    add = op.add_option
    add('-v', dest='vertical', action='store_true', 
        help='Vertical layout. Default is horizontal.')
    add('-b', dest='breaknum', type='int', default=0, 
        help='Number of images per row (or column if layout is vertical). '
             'Use this to create a table. Default is 0, which means no break '
             '(a single row/column). [NOT SUPPORTED YET]')
    add('-f', dest='fillcolor', default='0,0,0', 
        help='Background fill color. Specify as red, green and blue components '
             '(range 0-255), separated by commas. Default is %default.')
    add('-o', dest='outformat', default='PNG', 
        help='Output image format. Default is %default.')
    add('-?', action='help',
        help=optparse.SUPPRESS_HELP)
    opt, args = op.parse_args()

    if len(args) < 2:
        op.error('at least 2 params are required')
    opt.outformat = opt.outformat.upper()
    if opt.outformat not in OUTPUT_FORMATS:
        op.error('unsupported output format: "%s"' % opt.outformat)
    if opt.breaknum < 0:
        opt.breaknum = 0
    if opt.breaknum > 0:
        op.error('-b not supported yet')
    try:
        opt.fillcolor = parse_color(opt.fillcolor)
    except ValueError as err:
        op.error(str(err))

    return opt, args[:-1], args[-1]


def boxes_gen(dims, vertical):
    """Generate box coords from a list of dimensions."""
    x, y = 0, 0
    for w, h, in dims:
        yield x, y, x+w, y+h
        if vertical:
            y += h
        else:
            x += w


def getbounds(boxes):
    """Calc smallest bounding box from list of boxes."""
    minx = min(t[0] for t in boxes)
    miny = min(t[1] for t in boxes)
    maxx = max(t[2] for t in boxes)
    maxy = max(t[3] for t in boxes)
    return minx, miny, maxx, maxy


if __name__ == '__main__':
    opt, inputs, output = parse_cmdline()
    try:
        imgs = [Image.open(s) for s in inputs]
        dims = [im.size for im in imgs]
        boxes = list(boxes_gen(dims, opt.vertical))
        bounds = getbounds(boxes)
        assert bounds[:2] == (0,0)
        outimg = Image.new('RGB', bounds[2:], opt.fillcolor)
        for im, box in zip(imgs, boxes):
            outimg.paste(im, box)
        outimg.save(output, opt.outformat)
    except Exception as err:
        CommonTools.exiterror(str(err))

