"""Write clipboard text to STDOUT.

Will fail if there's no text in the clipboard.
"""

import sys
import win32console
import clipboard

text = clipboard.gettext()
if text is None:
    raise SystemExit('no text in clipboard')

encoding = 'cp' + str(win32console.GetConsoleOutputCP())
sys.stdout.write(text.encode(encoding, 'replace'))
