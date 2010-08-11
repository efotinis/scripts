"""Use two RGB images to create an RGBA image.

Can be used to create RGBA PNGs of Aero windows (glass & shadow).

The input images are the target area blended over a white and a black
background, respectively.
"""

from __future__ import division

import os
import sys
import itertools
from PIL import Image


def grayscale(rgb, mode):
    """Convert an RGB triple (0..255) to a single grayscale value.

    Available modes:
    - 'avg':        average                     (r + g + b) / 3
    - 'luma':       ITU-R 601-2 luma transform  0.299*r + 0.587*g + 0.114*b
    - 'luma_g':     GIMP desaturate option      0.21*r + 0.71*g + 0.08*b
    - 'lightness':  GIMP desaturate option      (min(r,g,b) + max(r,g,b)) / 2
    """
    if mode == 'avg':
        return int(round(sum(rgb) / 3))
    elif mode == 'luma':
        return int(round(0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2]))
    elif mode == 'luma_g':
        return int(round(0.21*rgb[0] + 0.71*rgb[1] + 0.08*rgb[2]))
    elif mode == 'lightness':
        return int(round((min(rgb) + max(rgb)) / 2))
    else:
        raise ValueError('invalid grayscale mode')


def calc_rgba(rgb_white, rgb_black,
              grayfunc=lambda rgb: grayscale(rgb, 'avg')):
    """Calculate an RGBA pixel from two RGB input pixels.

    All pixel components are in [0,255].

    Algorithm with normalized components:
        Inputs:
            (r1,g1,b1): pixel value blended on a *white* background
            (r2,g2,b2): pixel value blended on a *black* background
        Output:
            (r,g,b,a): the original RGBA pixel
        Solution:
            Assuming the images were blended using linear interpolation
            (showing red component only; green and blue are similar):
                r1 = 1*(1-a) + r*a
                r2 = r*a
            These give:
                a = 1 - r1 + r2
                r = r2/a
            Opacity is combined from all components, so it becomes:
                a = 1 - F(r1,g1,b1) + F(r2,g2,b2)
            where F() is a grayscale function.
            Any grayscale function used gives acceptable results; it would be
            possible to determine the exact one experimentally, but an average
            or luminosity function seems OK.
    """
    a = 255 - grayfunc(rgb_white) + grayfunc(rgb_black)
    r = int(round(rgb_black[0] * 255 / a)) if a else 0
    g = int(round(rgb_black[1] * 255 / a)) if a else 0
    b = int(round(rgb_black[2] * 255 / a)) if a else 0
    return (r, g, b, a)


def crop_transparent(im):
    """Crop the fully transparent area around an image."""
    opacity = im.split()[im.getbands().index('A')]
    bbox = opacity.getbbox()
    if bbox is None:
        raise ValueError('whole image is transparent')
    im = im.crop(bbox)
    im.load()
    return im


def convert(input_white, input_black, output, outfmt):
    """Create an RGBA image from two RGB images."""
    im_white = Image.open(input_white)
    im_black = Image.open(input_black)
    size = im_white.size
    if size != im_black.size:
        raise ValueError('input images have different sizes')
    out = Image.new('RGBA', size)
    input_pixels = itertools.izip(im_white.getdata(), im_black.getdata())
    out.putdata(list(calc_rgba(p1, p2) for p1, p2 in input_pixels))
    out = crop_transparent(out)
    out.save(output, outfmt)


if __name__ == '__main__':
    import sys
    input1, input2, output, outfmt = sys.argv[1:]
    convert(input1, input2, output, outfmt)
