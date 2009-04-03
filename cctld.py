import os, sys

def showhelp():
    print '''
Display country name (and maybe some info) of 2-letter TLDs.

CCTLD [tld ...]

  tld  A 2-letter TLD. Leading dots are ignored.
'''[1:-1]

def readdata():
    """Read data file and return mapping of 2-letter code to country/note pair."""
    d = {}
    for s in open(os.path.splitext(sys.argv[0])[0] + '.txt'):
        row = s.decode('utf8').rstrip('\n').split('\t')
        row += [''] * (3 - len(row))
        d[row[0]] = row[1:]
    return d

def main(args):
    if '/?' in args:
        showhelp()
        return 0
    if not args:
        return 0
    d = readdata()
    args = [s.lower().lstrip('.') for s in args]
    allok = True
    for s in args:
        print s + ':',
        try:
            country, note = d[s]
            print country
            if note:
                print '   ', note.encode('mbcs')
        except KeyError:
            print 'UNUSED'
            allok = False
    return 0 if allok else 1
            
sys.exit(main(sys.argv[1:]))
