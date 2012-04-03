##    """Init the Python interpreter when it's used interactively.
##
##    Use the PYTHONSTARTUP envvar to point to this file.
##
##    See:
##        http://docs.python.org/tutorial/interpreter.html#the-interactive-startup-file
##
##    Notes:
##    - This docstring is commented to prevented assignment
##      to the top level of the interpreter.
##    - Don't use 'print' for messages: it needs import print_function
##      for Py2/3 compatibility and that leaks into the interactive prompt.
##    """

# import frequently used modules
import os
import re
import sys


# useful introspective utilities
from pprint import pprint as pp
try:
    from see import see
except ImportError:
    sys.stderr.write('startup.py: could not load see()\n')


# clipboard text get/set
try:
    from clipboard import cb
except ImportError:
    sys.stderr.write('startup: could not load cb()\n')


# URL reader
try:
    from webutil import wget
except ImportError:
    sys.stderr.write('startup: could not load wget()\n')


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


# text encoding fix
def untangle(text, encoding='mbcs'):
    """Fix text that was incorrectly saved as Latin-1."""
    return text.encode('latin1').decode(encoding)
