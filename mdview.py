"""Convert a Markdown file and open resulting temp HTML file.

Can be used as an Explorer context menu handler.
"""

import argparse
import os
import sys
import time
import traceback
import webbrowser

import win32api
from win32con import MB_ICONEXCLAMATION
import markdown


# HTML output template
TEMPLATE = '''<!doctype html><html>
<head><meta charset="utf-8">
<title>{title}</title></head>
<body>{body}</body></html>'''

# delete temp files older than this
DELETE_AGE_SEC = 24 * 60 * 60


def parse_args():
    ap = argparse.ArgumentParser(
        description='convert and view Markdown files')
    add = ap.add_argument

    add('inputs', metavar='FILE', nargs='+',
        help='input file')
    add('-g', dest='guimode', action='store_true',
        help='GUI mode; use MessageBox for user interaction')

    return ap.parse_args()


class TempDir(object):
    """Temp directory holding converted files."""
    def __init__(self):
        self.tmpdir = os.path.expandvars('%Temp%\\mdview')
        if not os.path.exists(self.tmpdir):
            os.makedirs(self.tmpdir)
    def add(self, srcpath, html):
        """Store item and return its path."""
        name = os.path.splitext(os.path.basename(srcpath))[0]
        tmppath = os.path.join(self.tmpdir, name + '.htm')
        with open(tmppath, 'w') as f:
            f.write(html)
        return tmppath
    def close(self):
        if self.tmpdir is not None:
            self._cleanup()
            self.tmpdir = None
    def _cleanup(self):
        """Delete old files."""
        now = time.time()
        for s in os.listdir(self.tmpdir):
            s = os.path.join(self.tmpdir, s)
            if now - os.path.getmtime(s) > DELETE_AGE_SEC:
                os.unlink(s)
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def convert(path):
    """Convert Markdown file to HTML source."""
    with open(path) as f:
        html = markdown.markdown(f.read().decode('utf-8'))  # "assuming" UTF-8
    name = os.path.splitext(os.path.basename(path))[0]
    return TEMPLATE.format(title=name.encode('utf-8'), body=html.encode('utf-8'))


def error(msg, guimode):
    if args.guimode:
        win32api.MessageBox(0, msg, sys.argv[0], MB_ICONEXCLAMATION)
    else:
        print >>sys.stderr, msg


def main(args):
    with TempDir() as tmp:
        for s in args.inputs:
            try:
                output = tmp.add(s, convert(s))
                webbrowser.open_new_tab(output)
            except Exception as x:
                msg = 'could not convert "%s": %s' % (s, x)
                error(msg, args.guimode)


if __name__ == '__main__':
    try:
        args = parse_args()
        main(args)
    except Exception as x:
        if args.guimode:
            msg = traceback.format_exc()
            title = os.path.basename(sys.argv[0])
            win32api.MessageBox(0, msg, title, MB_ICONEXCLAMATION)
            sys.exit(1)
        else:
            raise
