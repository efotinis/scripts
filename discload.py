import sys, bz2, pickle, CommonTools


def disphelp():
    script = CommonTools.scriptname().upper()
    print 'usage: %s <infile>' % script


def countdata(a):
    dircnt, filecnt = 0, 0
    for item in a:
        if len(item) == 5:
            filecnt += 1
        else:
            dircnt += 1
            subdirs, subfiles = countdata(item[5])
            dircnt += subdirs
            filecnt += subfiles
    return dircnt, filecnt


def main(args):
    if '/?' in args:
        disphelp()
        raise SystemExit
    if len(args) != 1:
        raise SystemExit('ERROR: 1 parameter required')

    try:
        f = open(args[0], 'rb')
    except IOError:
        raise SystemExit('ERROR: could not open file')

    s = f.read(8)
    if s != 'EFDDMP00':
        raise SystemExit('ERROR: bad magic')
    s = f.read()
    s = bz2.decompress(s)
    d = pickle.loads(s)

    print 'name:', d['name']
    print 'volume:', d['label']
    print 'serial: %08x' % d['serial']
    print 'notes:', d['notes']
    dircnt, filecnt = countdata(d['data'])
    print 'dirs:', dircnt
    print 'files:', filecnt


main(sys.argv[1:])
