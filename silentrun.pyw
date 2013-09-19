"""Run a CLI program without displaying a console."""


import sys
import subprocess


if __name__ == '__main__':
    sys.exit(subprocess.call(sys.argv[1:], shell=True))
