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
