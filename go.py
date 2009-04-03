# gah! this only works with batch files :o)

import os
import sys


entries = (
    (   'scr,script',
        'Switch to "scripts" folder.',
        'CD /D D:\\docs\\scripts'),
    (   'prj,proj',
        'Switch to "projects" folder.',
        'CD /D E:\\Projects'),
    (   'tst,test',
        'Switch to "projects/test/test/debug" folder.',
        'CD /D E:\\Projects\\test\\test\\debug'),
    (   'py,python',
        'Switch to "F:/temp/python" folder.',
        'CD /D F:\\temp\\python'),
    (   'opt',
        'Switch to "opt/debug" folder and add a line to PROMPT.',
        'CD /D C:\\DOCUME~1\\Elias\\Desktop\\TESTPR~1\\opt\\Debug',
        'PROMPT ' + (78*'-') + '$_$G$S'),
    (   'rasmon',
        'Switch to "rasmon/debug" folder.',
        'CD /D C:\\DOCUME~1\\Elias\\Desktop\\TESTPR~1\\rasmon\\Debug'),
)


def showHelp():
    print "Batch-within-a-batch script."
    print ""
    print "  GO [id]"
    print ""
    print "Registered IDs:"
    cols = max(len(entry[0]) for entry in entries)
    for entry in entries:
        print '  ' + entry[0].ljust(cols) + '  ' + entry[1]


def run(cmds):
    pass


def main(args):
    if not args or '/?' in args:
        showHelp()
        return
    if len(args) > 1:
        print 'Only 1 argument is required.'
        return
    id = args[0].lower()
    for entry in entries:
        if id in entry[0].lower().split(','):
            run(entry[2:])
            return
    print 'invalid id: "%s"' % id


main(sys.argv[1:])
os.system('prompt ^^^^')
