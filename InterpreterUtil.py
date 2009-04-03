import sys


def _del(d, keep):
    for s in d.keys():
            if s[:2] != '__' and s not in keep:
                del d[s]

def nukeglobs():
    i = 0
    while True:
        fo = sys._getframe(i)
        if fo.f_globals['__name__'] == '__main__':
            _del(fo.f_globals, ('pywin',))
            break
        i += 1
