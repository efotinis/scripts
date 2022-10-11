"""Generate and show simple fractal image.

tags: demo, graphics, fractal
"""

from __future__ import division
from PIL import Image


def mandelbrot(z, c):
    """The classic Mandelbrot set. <http://en.wikipedia.org/wiki/Mandelbrot_set>"""
    return z * z + c


def burning_ship(z, c):
    """The Burning Ship. <http://en.wikipedia.org/wiki/Burning_Ship_fractal>"""
    z = complex(abs(z.real), abs(z.imag))
    return z * z + c


def pixel_to_point(xy, image_size, view_center, view_size):
    """Convert image pixel coords to viewport complex number."""
    return complex((xy[0] / image_size[0] - 0.5) * view_size[0] + view_center[0],
                   (xy[1] / image_size[1] - 0.5) * view_size[1] + view_center[1])


def loop(c, equation, max_iters):
    """Calculate the fractal point."""
    z = 0
    for i in range(max_iters):
        z = equation(z, c)
        if abs(z) > 2:
            return i
    return max_iters


if __name__ == '__main__':
    MAX_ITERS = 30
    IMAGE_SIZE = (400, 400)
    VCENTER = (-0.5, 0.0)
    VSIZE = (3.0, 3.0)

    img = Image.new('I', IMAGE_SIZE)

    for y in range(IMAGE_SIZE[1]):
        for x in range(IMAGE_SIZE[0]):
            c = pixel_to_point((x,y), IMAGE_SIZE, VCENTER, VSIZE)
            i = loop(c, mandelbrot, MAX_ITERS)
            img.putpixel((x,y), 0 if i == MAX_ITERS else int(i / MAX_ITERS * 255))

    img.show()
