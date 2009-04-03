import os
import sys


def main(args):
    if '/?' in args:
        dispHelp()
        sys.exit(0)
    if len(args) <> 2:
        errLine('Two paths are required.')
        sys.exit(2)
    try:
        src = getFileLines(args[0])
        dst = getFileLines(args[1])
    except IOError, x:
        errLine(str(x))
        sys.exit(2)
    if len(src) <> len(dst):
        errLine('The specified files do not have the same number of lines.')
        sys.exit(2)
    filesProcessed = 0
    failures = 0
    for i in range(len(src)):
        filesProcessed += 1
        try:
            os.rename(src[i], dst[i])
            print 'Renamed "' + src[i] + '" to "' + dst[i] + '".'
        except OSError, x:
            errLine('Could not rename "' + src[i] +
                    '" to "' + dst[i] + '". ' + str(x))
            failures += 1
    print
    print 'Files processed:', filesProcessed
    print 'Failed:', failures
    if failures == 0:
        sys.exit(0)
    else:
        sys.exit(1)


def dispHelp():
    print """\
Renames files using names from two text files.

LISTREN src dst

  src,dst  Text files containing the source and destination names.
           Each file from line N of 'src' is renamed as line N from 'dst'.
           Both files must have the same number of lines.

Returns:
  0  Success.
  1  Some files could not be renamed.
  2  Parameter error."""


def errLine(s):
    sys.stderr.write('ERROR: ' + s + '\n')


def getFileLines(path):    
    return [s.rstrip('\n') for s in open(path).readlines()]


main(sys.argv[1:])
