"""Join multiple images into one."""

import sys, re
import Image
import DosCmdLine, CommonTools


'''
os.chdir(r'D:\work\scans\PENDING\music cds')
i1,i2 = Image.open('a.bmp'), Image.open('b.bmp')
i12 = Image.new('RGB', (2552*2, 3508))
i = i12
del i12
i.paste(i1, (0,0,2552, 3508))
i.paste(i2, (2552,0,2552*2, 3508))
i.save('ab.bmp')
'''

OUTPUT_FORMATS = 'BMP PNG GIF JPG'.split()


def buildswitches():
    """Create cmdline switches info."""
    Flag = DosCmdLine.Flag
    Swch = DosCmdLine.Switch
    return [
        Flag('V', 'vertical',
             'Vertical layout, Default is horizontal.'),
        Swch('B', 'breaknum',
             'Number of images per row (or column if layout is vertical). '
             'Use this to create a table. Default is 0, which means no break '
             '(a single row/column). [NOT SUPPORTED YET]',
             0, converter=int),
        Swch('F', 'fillcolor',
             'Background fill color. Specify as red, green and blue components '
             '(range 0-255), separated by commas. Default is black (0,0,0).',
             (0,0,0), converter=parse_optcolor),
        Swch('O', 'outformat',
             'Output image format. Supported formats: %s. '
             'Default is BMP.' % ', '.join(OUTPUT_FORMATS),
             'BMP', converter=parse_optformat)]


def parse_optcolor(s):
    m = re.match(r'^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$', s)
    try:
        if not m:
            raise ValueError
        return map(int, m.groups())
    except ValueError:
        raise DosCmdLine.Error('invalid color format: "%s"' % s)


def parse_optformat(s):
    ret = s.upper()
    if ret not in OUTPUT_FORMATS:
        raise DosCmdLine.Error('unsupported output format: "%s"' % s)
    return ret


def showhelp(switches):
    name = CommonTools.scriptname().upper()
    options = '\n'.join(DosCmdLine.helptable(switches))
    print '''
Join multiple images.

%s [/V] [/B:breaknum] [/F:fillcolor] [/O:outformat] inputs... output

%s
'''[1:-1] % (name, options)


def main(args):
    switches = buildswitches()
    if '/?' in args:
        showhelp(switches)
        sys.exit()
    try:
        opt, params = DosCmdLine.parse(args, switches)
        if not params:
            raise DosCmdLine.Error('no images specified')
        inputs, output = params[:-1], params[-1]
        if not inputs:
            raise DosCmdLine.Error('no input images specified')
        if opt.breaknum > 0:
            raise DosCmdLine.Error('/B not supported yet')
    except DosCmdLine.Error, err:
        CommonTools.errln(str(err))
        sys.exit(2)

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
    except Exception, err:
        CommonTools.errln(str(err))
        sys.exit(1)
    

def boxes_gen(dims, vert):
    x, y = 0, 0
    for w, h, in dims:
        yield x, y, x+w, y+h
        if vert:
            y += h
        else:
            x += w


def getbounds(boxes):
    """Cacl smallest bounding box from list of boxes."""
    minx = min(t[0] for t in boxes)
    miny = min(t[1] for t in boxes)
    maxx = max(t[2] for t in boxes)
    maxy = max(t[3] for t in boxes)
    return minx, miny, maxx, maxy


main(sys.argv[1:])
