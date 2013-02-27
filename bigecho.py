"""Print using large letters. Inspired by BIGECHO.COM."""

from PIL import Image
import iterutil
import CommonTools

UPPER_HALF = unichr(0x2580)
LOWER_HALF = unichr(0x2584)
FULL_BLOCK = unichr(0x2588)


# TODO: add height param to Font's init, so that we can specify bitmaps
#       with multiple rows of chars
# TODO: save to and load from file (optionally support image files for bitmaps)


def expand(s, n):
    return ''.join(c*n for c in s)


def chars_from_image(path, cell, spacing):
    """
        cell        (width,height) of char cells
        spacing     (x,y) spacing between cells
    """
    im = Image.open(path)
    for y in range(0, im.size[1], cell[1] + spacing[1]):
        for x in range(0, im.size[0], cell[0] + spacing[0]):
            data = list(im.crop((x, y, x + cell[0], y + cell[1])).getdata())
            data = [FULL_BLOCK if x == (0,0,0,255) else ' ' for x in data]
            yield list(''.join(x) for x in iterutil.grouper(cell[0], data))

def chars_from_string(data, cell, spacing):
    lines = [t for t in data.splitlines() if t]
    for i in range(0, len(lines[0]), cell + spacing):
        yield [line[i:i+cell] for line in lines]


class Font(object):

##    def __init__(self, charset, bitmap, width, spacing=1, weight=1):
##        """Create font."""
##        lines = [t for t in bitmap.splitlines() if t]
##        self.width = width
##        self.height = len(lines)
##        self.spacing = spacing
##        self.chars = {}
##        for (i, c) in enumerate(charset):
##            i *= self.width + self.spacing
##            self.chars[c] = [line[i:i+self.width] for line in lines]
##        if ' ' not in self.chars:
##            self.chars[' '] = [' ' * self.width for i in range(self.height)]
##        if weight > 1:
##            for (c, lines) in self.chars.items():
##                lines[:] = [expand(s, weight) for s in lines]
##            self.width *= weight

    def __init__(self, charset, bitmaps, width, height, spacing=1, weight=1):
        """Create font."""
        self.width = width
        self.height = height
        self.spacing = spacing
        self.chars = {char:data for char,data in zip(charset, bitmaps)}
            
        if ' ' not in self.chars:
            self.chars[' '] = [' ' * self.width for i in range(self.height)]

        if weight > 1:
            for (c, lines) in self.chars.items():
                lines[:] = [expand(s, weight) for s in lines]
            self.width *= weight

    def render(self, s):
        """Render text into list of scan lines."""
        spacechar = self.chars[' ']
        a = [[] for i in range(self.height)]
        for c in s:
            charlines = self.chars.get(c, spacechar)
            for (line, cline) in zip(a, charlines):
                line.append(cline)
        joiner = ' ' * self.spacing
        return [joiner.join(line) for line in a]

    def uprint(self, s):
        CommonTools.uprint('\n'.join(self.render(s)))


if __name__ == '__main__':
    import os
    import sys
    from textwrap import dedent

##    s = dedent('''
##        XXX  X  XXX XXX X X XXX XXX XXX XXX XXX         
##        X X XX    X   X X X X   X     X X X X X      X  
##        X X  X  XXX XXX XXX XXX XXX  X  XXX XXX         
##        X X  X  X     X   X   X X X X   X X   X      X  
##        XXX XXX XXX XXX   X XXX XXX X   XXX XXX  X      
##        ''')
##    bitmaps = chars_from_string(s.replace('X', FULL_BLOCK), 3, 1)
##    font = Font('0123456789.:', bitmaps, 3, 5, weight=2)

    font_image = os.path.join(os.path.dirname(__file__), 'bigecho-5x5.png')
    bitmaps = chars_from_image(font_image, (5,5), (1,1))
    charset = ''.join(chr(n) for n in range(32,128))
    font = Font(charset, bitmaps, 5, 5, spacing=1)

    for s in sys.argv[1:]:
        print
        font.uprint(s)
