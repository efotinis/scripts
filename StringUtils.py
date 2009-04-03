# Misc string utilities.
#
# 2008.03.08  Created


def findall(s, sub):
    """Offsets list of all occurences of a string."""
    ret = []
    start = 0
    while True:
        found = s.find(sub, start)
        if found == -1:
            break
        ret += [found]
        start = found + 1
    return ret
