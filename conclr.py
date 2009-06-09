"""Clipper-style console color strings."""


COLORCHARS = 'NBGCRMYW'
COLORS = dict(zip(COLORCHARS, range(8)))
INTENSITIES = {'':0, '+':8}


def color(s):
    return (COLORS[s[0].upper()] + INTENSITIES[s[1:]]) if s else 0


def attr(s):
    if '/' in s:
        fore, back = s.split('/', 1)
    else:
        fore, back = s, ''
    return color(fore) | (color(back) << 4)


def fromcolor(n):
    if not 0 <= n < 16:
        raise ValueError('invalid color value')
    return COLORCHARS[n & 7] + ('+' if n >= 8 else '')


def fromattr(n):
    if not 0 <= n < 256:
        raise ValueError('invalid attribute value')
    return fromcolor(n & 15) + '/' + fromcolor(n >> 4)
