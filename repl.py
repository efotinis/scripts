import os
import sys
import shutil
import re

SCRIPT_NAME = os.path.splitext(os.path.basename(sys.argv[0]))[0].upper()

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_BAD_PARAM = 2


def showHelp():
    print """Replace text in files.

%s [/I] [/R] [/S] [/B] [/A] from to files[...]

  /I     Ignore case.
  /R     Use regular expressions.
  /S     Recurse dirs.
  /B     Create backups.
  /A     Abort on the first error. If omitted, operation continues with the
         next file or directory.
  from   The source string or regexp.
  to     The destination string. If /R is used, this may contain regexp refs.
  files  A list of files. Wildcards are allowed.

Exit codes:
  0  Success.
  1  At least one file error occured.
  2  Argument error.""" % SCRIPT_NAME

    
def main(args):
    if '/?' in args:
        showHelp()
        return EXIT_OK
    try:
        opt = Options(args)
    except Options.Error, x:
        errLn(str(x))
        return EXIT_BAD_PARAM
    fileSet = set()
    for x in opt.fileFilters:
        func = processFile if isinstance(x[1], basestring) else processDir
        if not func(x[0], x[1], fileSet, opt) and opt.abortOnError:
            return EXIT_ERROR
    return EXIT_OK


class Options:

	// TODO: make these instance vars    
    findExpr = None
    replExpr = None
    fileFilters = []
    backup = False
    recurse = False
    abortOnError = False
    
    class Error(Exception):
        def __init__(self, x):
            Exception.__init__(self, x)
            
    def __init__(self, args):
        useRegexps = False
        ignoreCase = False
        params = []
        forceNextNotSwitch = False
        for s in args:
            if s[:1] == '/' and not forceNextNotSwitch:
                swtch = s[1:].upper()
                if swtch == '':
                    forceNextNotSwitch = True
                elif swtch == 'I':
                    ignoreCase = True
                elif swtch == 'R':
                    useRegexps = True
                elif swtch == 'S':
                    self.recurse = True
                elif swtch == 'B':
                    self.backup = True
                elif swtch == 'A':
                    self.abortOnError = True
                else:
                    raise Options.Error('Invalid switch: "%s"' % s)
            else:
                params += [s]
                if forceNextNotSwitch:
                    forceNextNotSwitch = False
        if len(params) < 3:
            raise Options.Error('Missing parameter.')
        regexpFlags = 0
        if ignoreCase:
            regexpFlags |= re.IGNORECASE
        if useRegexps:
            try:
                self.findExpr = re.compile(params[0], regexpFlags)
            except re.error, x:
                raise Options.Error('Bad regexp: "%s": %s' % (params[0], str(x)))
        else:
            self.findExpr = re.compile(re.escape(params[0]), regexpFlags)
        self.replExpr = params[1]
        for s in params[2:]:
            self.fileFilters += [self.parseFileFilter(s)]
            
    def parseFileFilter(self, s):
        if s.endswith(('\\', '/')):
            s = s[:-1]
        if os.path.isdir(s):
            raise Options.Error('A dir was specified ("%s"). '
                                 'Append a "*" mask if that was intended.' % s)
        dir, mask = os.path.split(s)
        if '*' in mask or '?' in mask:
            return dir, dosWildToRegexp(mask)
        else:
            return dir, mask


def processFile(dir, fname, fileSet, opt):
    fpath = os.path.join(dir, fname)
    if fpath.upper() in fileSet:
        return True
    else:
        fileSet.add(fpath.upper())

##    print os.path.join(dir, fname)
##    return

    try:        
        with file(fpath) as f:
            s1 = f.read()
        s2 = opt.findExpr.sub(opt.replExpr, s1)
        if s1 != s2:
            if opt.backup:
                bakfpath = os.path.join(dir, getUniqueBackupName(dir, fname))
                shutil.copyfile(fpath, bakfpath)
            with file(fpath, 'w') as f:
                f.write(s2)
    except (IOError, OSError), x:
        errLn(str(x))
        if opt.abortOnError:
            return False

    return True        
    

def processDir(dir, fileRegexp, fileSet, opt):
    try:
        dirList = os.listdir(dir)
    except OSError, x:
        errLn(str(x))
        return False
    # use a list to collect subdirs, so that
    # they are processed after this dir's files
    subdirs = []
    # process files and optionally collect subdirs
    for s in dirList:
        if os.path.isdir(os.path.join(dir, s)):
            if opt.recurse:
                subdirs += [s]
        elif fileRegexp.match(s):
            if not processFile(dir, s, fileSet, opt) and opt.abortOnError:
                return False
    # then process subdirs
    for s in subdirs:
        ok = processDir(os.path.join(dir, s), fileRegexp, fileSet, opt)
        if not ok and opt.abortOnError:
            return False
    return True


def getUniqueBackupName(dir, fname):
    base, ext = os.path.splitext(fname)
    i = 1
    while True:
        test = '%s(%d)%s' % (base, i, ext)
        if not os.path.exists(os.path.join(dir, test)):
            return test
        i += 1


def errLn(s):
    sys.stderr.write('ERROR: ' + s + '\n')


def dosWildToRegexp(s):
    ret = ''
    for c in s:
        ret += '.*' if c == '*' else '.' if c == '?' else re.escape(c)
    return re.compile('^' + ret + '$', re.I)


sys.exit(main(sys.argv[1:]))
