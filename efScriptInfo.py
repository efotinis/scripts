import os
import sys


def getName():
    s = sys.argv[0]
    s = os.path.split(s)[1]
    s = os.path.splitext(s)[0]
    return s
