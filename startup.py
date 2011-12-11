"""Init the Python interpreter when it's used interactively.

Use the PYTHONSTARTUP envvar to point to this file.

See:
    http://docs.python.org/tutorial/interpreter.html#the-interactive-startup-file
"""

from __future__ import print_function

# import frequently used modules
import os
import re
import sys


# useful introspective utilities
from pprint import pprint as pp
try:
    from see import see
except ImportError:
    print('startup: could not load see()', file=sys.stderr)


# clipboard text get/set
try:
    from clipboard import cb
except ImportError:
    print('startup: could not load cb()', file=sys.stderr)


# URL reader
try:
    from webutil import wget
except ImportError:
    print('startup: could not load wget()', file=sys.stderr)


# add the Python version to the main frame's title
try:
    import win32ui
    try:
        win32ui.GetApp().frame.SetWindowText(
            'PythonWin/' + '{0.major}.{0.minor}'.format(sys.version_info))
    except AttributeError:
        # "'PyCWinApp' object has no attribute 'frame'"
        # when running in the console
        pass
    del win32ui
except ImportError:
    pass


del print_function
