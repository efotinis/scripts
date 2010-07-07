"""File system (and path) utilities."""

import contextlib


@contextlib.contextmanager
def preserve_cwd(path=None):
    """Context manager to preserve (and optionally set) the current directory."""
    orgpath = os.getcwd()
    if path is not None:
        os.chdir(path)
    try:
        yield
    finally:
        os.chdir(orgpath)
