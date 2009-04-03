import os
import sys
import re


def main(args):
    if '/?' in args:
        dispHelp()
        sys.exit(0)
    args = parseArgs(args)  # may exit(2)

    for srcDir, rx in args.paths:
        for s in os.listdir(srcDir):
            spec = os.path.join(srcDir, s)
            if not os.path.isfile(spec):
                continue
            if rx.match(s):
                newSpec = os.path.join(args.dir, s)
                try:
                    os.rename(spec, newSpec)
                except OsError, x:
                    ....................................






argh..........  how can we split() a path with a reg ex?????
since the regex may contain \\\\\\\\\'s ???????????





...............................                    
        
    dir = r'D:\616\__New Folder\new pcmn files\other\photo\folder'
    for s in os.listdir(dir):
        path = os.path.join(dir, s)
        if not os.path.isfile(path):
            continue
        if len(s) > 64:
            os.rename(path, os.path.join(dir, 'x', s))


def dispHelp():
    print r"""Moves files with long names.

MOVELONG len dir [/G:]path[...]

  len   The minimum name length of files to be moved.
  dir   The target directory.
  path  The file(s) to move. Multiple paths and DOS wildcards are allowed.
  /R    Modifies the next 'path' to match using regular expressions."""


class Args:
	__init__
		paths = []
		len = 0
		dir = 0

    
def parseArgs(args):
    ret = Args()

    if len(args) < 3:
        errLn('At least 3 parameters are required.')
        sys.exit(2)

    try:
        ret.len = int(args[0], 10)
    except ValueError:
        errLn('Invalid length: "' + s + '".')
        sys.exit(2)

    ret.dir = args[1]

    switchRx = re.compile(r'/([^:]+)(?::(.*))?', re.I)
    for s in args:
        m = switchRx.match(s)
        if not m:
            pathAndMask = os.path.split(s)
            pathAndMask[1] = dosWildToRegEx(pathAndMask[1])
            ret.paths.append(pathAndMask)
        elif m.group(1).upper() == 'R':
            try:
                pathAndMask = os.path.split(m.group(2))
                pathAndMask[1] = re.compile(pathAndMask[1], re.I)
                ret.paths.append(pathAndMask)
            except re.error:
                errLn('Invalid regular expression: "' + m.group(2) + '".')
                sys.exit(2)

    return ret                
        

def dosWildToRegEx(s):
    rx = ''
    for c in s:
        if c == '*':
            rx += '.*'
        elif c == '?':
            rx += '.+'
        else:
            rx += re.escape(c)
    return re.compile(rx)

    
def errLn(s):
    sys.stderr.write('ERROR: ' + s + '\n')

    
main(sys.argv[1:])
