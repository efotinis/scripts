"""Print using large letters. Inspired by BIGECHO.COM."""

import CommonTools

UPPER_HALF = unichr(0x2580)
LOWER_HALF = unichr(0x2584)
FULL_BLOCK = unichr(0x2588)


# TODO: add height param to Font's init, so that we can specify bitmaps
#       with multiple rows of chars
# TODO: save to and load from file (optionally support image files for bitmaps)


def expand(s, n):
    return ''.join(c*n for c in s)


class Font(object):

    def __init__(self, charset, bitmap, width, spacing=1, weight=1):
        """Create font."""
        lines = [t for t in bitmap.splitlines() if t]
        self.width = width
        self.height = len(lines)
        self.spacing = spacing
        self.chars = {}
        for (i, c) in enumerate(charset):
            i *= self.width + self.spacing
            self.chars[c] = [line[i:i+self.width] for line in lines]
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
    import sys
    from textwrap import dedent

    s = dedent('''
        XXX  X  XXX XXX X X XXX XXX XXX XXX XXX         
        X X XX    X   X X X X   X     X X X X X      X  
        X X  X  XXX XXX XXX XXX XXX  X  XXX XXX         
        X X  X  X     X   X   X X X X   X X   X      X  
        XXX XXX XXX XXX   X XXX XXX X   XXX XXX  X      
        ''')
    font = Font('0123456789.:', s.replace('X', FULL_BLOCK), 3, weight=2)

    print sys.argv
    for s in sys.argv[1:]:
        print s
        font.uprint(s)
        print


'''
 !"#$%&'()*+,-./
0123456789:;<=>?
@ABCDEFGHIJKLMNO
PQRSTUVWXYZ[\]^_
`abcdefghijklmno
pqrstuvwxyz{|}~

 !"#$%&'()*+,-./
0123456789:;<=>?
@ABCDEFGHIJKLMNO
PQRSTUVWXYZ[\]^_
`{|}~
'''
