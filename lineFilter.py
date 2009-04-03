import sys


def showHelp():
    print """Filters lines from STDIN to STDOUT.

LINEFILTER [/N] [/S] [line ...]

  line  A line number to print. First line is number 0. Multiple lines can be
        specified and they will be printed in the specified order.
  /N    Do not count empty lines.
  /S    Strict indexing. Out of range line numbers (<0 or >=max lines) will be
        treated as an error. If omitted, empty lines are printed instead.
"""


def main(args):
    if '/?' in args:
        showHelp()
        return 0
    skipEmpty = False
    strictRange = False
    linesList = []
    for s in args:
        if s[0:1] == '/':
            c = s[1:2].upper()
            if c == 'N':
                skipEmpty = True
            elif c == 'S':
                strictRange = True
            else:
                errLn('Invalid switch: ' + s)
                return 1
        else:
            try:
                linesList.append(int(s, 10))
            except ValueError:
                errLn('Invalid line number: ' + s)
                return 1
    neededLines = {}
    i = 0
    while True:
        s = sys.stdin.readline()
        if not s:
            break
        if skipEmpty and not s.rstrip('\n'):
            continue
        if i in linesList:
            neededLines[i] = s.rstrip('\n')
        i += 1
    for i in linesList:
        try:
            print neededLines[i]
        except KeyError:
            if not strictRange:
                pass
            else:
                errLn('Line number ' + str(i) + ' does not exist.')
                return 1
    return 0


def errLn(s):
    sys.stderr.write('ERROR: ' + s + '\n')
    

sys.exit(main(sys.argv[1:]))
