"""Directory utilities."""

import os


def uniquepath(path):
    """Generate a unique path, like Windows Explorer.

    Uses increasing numbers (starting at 2) in parens before the extension.

    NOTE: Subject to race conditions.
    """
    i = 1
    base, ext = os.path.splitext(path)
    while os.path.exists(path):
        i += 1
        path = base + ' (' + str(i) + ')' + ext
    return path


