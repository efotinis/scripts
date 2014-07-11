"""Windows INI file utilities.

tags: windows, files
"""

import collections


def read(path):
    """Read INI file as a dict of dicts.

    Example:
    >>> ini = read_ini('test.ini')
    >>> value = ini[section][name]
    """
    ret = collections.defaultdict(dict)
    section = None
    for s in open(path, 'rt'):
        s = s.strip()
        if not s or s[0] == ';':
            continue
        if s[0] == '[' and s[-1] == ']':
            section = ret[s[1:-1]]
        else:
            name, _, value = s.partition('=')
            section[name] = value
    return ret
