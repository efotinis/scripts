"""Fix non-Unicode sys.argv on Windows Python 2.x.

Importing this module will replace sys.argv with a list of proper
Unicode strings. On other platforms/versions, importing does nothing.
"""

import sys
if sys.platform == 'win32' and sys.version_info.major < 3:
    import wincmdline
    a = wincmdline.get_argv()[1:]  # strip the actual interpreter
    sys.argv = a or ['']  # add empty module path if none was specified
