import os
import sys
from PIL import Image


SRC, ROWS, COLS = sys.argv[1:]
ROWS, COLS = int(ROWS), int(COLS)

im = Image.open(SRC)
width, height = im.size

i = 0
for row in range(ROWS):
    for col in range(COLS):
        x1, y1 = width * col // COLS, height * row // ROWS
        x2, y2 = width * (col + 1) // COLS, height * (row + 1) // ROWS
        imnew = Image.new('RGB', (x2-x1, y2-y1))
        imnew.paste(im.copy().crop((x1, y1, x2, y2)))
        outpath = os.path.splitext(SRC)[0] + ('_%04d' % i) + '.bmp'
        imnew.save(outpath, 'BMP')
        i += 1
