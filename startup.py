"""Init the Python interpreter when it's used interactively.

Use the PYTHONSTARTUP envvar to point to this file.

See:
    http://docs.python.org/tutorial/interpreter.html#the-interactive-startup-file
"""

# import frequently used modules
import os
import re
import sys


# useful introspective utilities
from pprint import pprint as pp
try:
    from see import see
except ImportError:
    pass


# clipboard text get/set
try:
    import clipboard
    def cb(s=None):
        """Get/set clipboard text."""
        if s is None:
            return clipboard.gettext()
        else:
            clipboard.settext(s)
except ImportError:
    pass


# URL reader
try:
    # Python 2.x
    import urllib2 as _urllib
except ImportError:
    # Python 3.x
    import urllib.request as _urllib
def wget(url):
    """Read a Web resource."""
    # add user agent, because some sites (e.g. Wikipedia)
    # forbid access to unknown/blank user-agents
    req = _urllib.Request(url, headers={'User-Agent':'Opera'})
    return _urllib.urlopen(req).read()


# add the Python version to the main frame's title
import win32ui
try:
    win32ui.GetApp().frame.SetWindowText(
        'PythonWin/' + '{0.major}.{0.minor}'.format(sys.version_info))
except AttributeError:
    # "'PyCWinApp' object has no attribute 'frame'"
    # when running in the console
    pass
