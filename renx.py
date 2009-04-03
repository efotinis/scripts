import os
import sys
import re
import collections


# script exit values (errorlevel)
EXIT_OK = 0
EXIT_RENAME_FAILURE = 1
EXIT_BAD_PARAM = 2

# types of help requests (can be combined)
HELP_NORMAL = 0x1
HELP_REGEXP = 0x2

# items to rename
TYPE_FILES = 0
TYPE_DIRS = 1
TYPE_FILES_AND_DIRS = 2

# part of filename affected
PART_WHOLE = 0
PART_BASE = 1
PART_EXT = 2


def main(args):
    helpReq = getHelpFlags(args)
    if helpReq:
        showHelp(helpReq)
        return EXIT_OK
    
    try:
        args = Args()
    except Args.Error, x:
        errLn(str(x))
        return EXIT_BAD_PARAM

    ###################################
    ##     CHECKING STOPPED HERE     ##
    ###################################

    flags = 0
    if not args.caseSens:
        flags |= re.IGNORECASE
    if args.localeSpec:
        flags |= re.LOCALE
        
    try:
        srcRx = re.compile(args.src, flags)
    except re.error, x:
        errLn('Invalid src regex: ' + str(x))
        sys.exit(2)
        
    filesProcessed = 0
    failures = 0
    for s in os.listdir(args.dir):
        m = srcRx.match(s)
        if m:
            filesProcessed += 1
            try:
                s2 = m.expand(args.dst)
            except re.error, x:
                errLn('Invalid dst pattern.')
                sys.exit(2)
            if args.test:
                print s
                print s2
                print
            else:
                try:
                    os.rename(s, s2)
                    if args.verbose:
                        print '"' + s + '" => "' + s2 + '"'
                except OSError, x:
                    errLn('Could not rename "' + s +
                            '" to "' + s2 + '". ' + str(x))
                    failures += 1

    print 'Files processed:', filesProcessed
    print 'Failed:', failures
    if failures == 0:
        sys.exit(0)
    else:
        sys.exit(1)


def getHelpFlags(args):
    """Scan arg list for help switches and return help flags."""
    ret = 0
    if '/?' in args:
        ret |= HELP_NORMAL
    if '/??' in args:
        ret |= HELP_REGEXP
    return ret
        

def showHelp(flags):
    """Display the help items specified in 'flags'."""
    if flags & HELP_NORMAL:
        pass  # ...
    if flags & HELP_REGEXP:
        pass  # ...
##def dispHelp():
##    print r"""Renames files using regular expressions.
##
##RENX [/C] [/L] [/V] [/T] [dir] src dst
##
##  dir  The directory to work in (a normal string). Default is current dir.
##  src  The pattern of the files to rename. Use /?? for more help.
##  dst  The new name pattern. This should include match groups from the 'src'
##       pattern. A group can be specified by "\N" (where N is 1-99),
##       or by "\g<N>" (to avoid group number ambiguity).
##  /C   Perform case-sensitive match.
##  /L   Use current-locale-specific versions of \w, \W, \b, \B, \s and \S.
##  /M
##  /V   Verbose output: Show files successfully renamed.
##  /T   Test mode: Show source and destination names, without actually renaming
##       any files.
##  /??  Display regular expression syntax.
##
##Returns:
##  0  Success.
##  1  Some files could not be renamed.
##  2  Parameter error."""
##
##
##def dispRegExHelp():
##    print r"""Regular expression help:
##  .         Matches any char.
##  ^ $       Matches the start/end of the string.
##  * + ?     Matches 0+/1+/0-1 items (greedy).
##  *? +? ??  Non-greedy variants.
##  {m}       Matches 'm' items.
##  {m,n}     Matches 'm' to 'n' items (greedy). 'm' defaults to 0, 'n' to inf.
##  {m,n}?    Non-greedy variant.
##  \         Escape special chars.
##  [...]     Set matching any of the contained chars.
##  [^...]    Set matching any but the contained chars.
##            Sets can contain individual chars or ranges between two chars
##            (separated by "-"). Special chars are not active inside sets.
##  X|Y       Matches either X or Y (any expression). Checks expressions
##            left-to-right and always matches the first found (non-greedy).
##  (...)     Matches the enclosed expression and defines a group.
##
##Extensions (don't generate a group, except "(?P...)":
##  (?iLmsux)    Sets one or more regex flags. Better avoid using these.
##  (?...)       Non-grouping version of regular parentheses.
##  (?P<id>...)  Same as "(...)" but also gives the match a symbolic name
##               (along with a number index). Name must be unique in the regex.
##  (?P=id)      Matches the text that was matched by an earlier group.
##  (?#...)      Comment; the contents are ignored.
##  (?=...)      Lookahead assertion. Matches if ... matches next, but doesn't
##               consume any of the string.
##  (?!...)      Negative lookahead assertion. Matches if ... doesn't match next.
##  (?<=...)     Positive lookbehind assertion.
##  (?<!...)     Negative lookbehind assertion.
##  (?(N/id)yes-patt|no-patt)  Optional match, depending on the existance of N/id.
##                             no-patt is optional.
##Special:
##  \A \Z  Matches the start/end of the string.
##  \b \B  Matches "", but only at (or not at) the beginning or end of a word.
##  \d \D  Matches any decimal digit (or anything but that).
##  \s \S  Matches any whitespace char (or anything but that).
##  \w \W  Matches any alphanumeric char or the underscore (or anything but that).
##  \a \b \f \n \r \t \v \x \\  C-style char literals."""
##
##

    
def isList(x):
    """Return whether the argument is a list."""
    return isinstance(x, list)


def countNonLists(a):
    """Return number of non-list elements in a list."""
    ret = 0
    for x in a:
        if not isList(x):
            ret += 1
    return ret


def dosWildToRegExp(s):
    """Convert a DOS-style wildcard to a regexp string."""
    ret = ''
    map = { '*':'.*', '?':'.' }  # regexp equivalents of '*' and '?'
    for c in s:
        ret += (map[c] if c in map else re.escape(c))
    return ret
    

class Transform(object):
    def __init__(self):
        pass
    def apply(self, s):
        return s
    class Error(Exception):
        pass
    

class Convert(Transform):
    def __init__(self, pattern, template):
        Transform.__init__(self)
        self.pattern = pattern
        self.template = template
    def apply(self, s):
        mo = self.pattern.search(s)
        if mo:
            s = mo.expand(self.template)
        return s
        

class Replace(Transform):
    def __init__(self, ranges, pattern, template):
        Transform.__init__(self)
        self.ranges = ranges
        self.pattern = pattern
        self.template = template
    def apply(self, s):
##        mo = self.pattern.search(s)
##        if mo:
##            s = mo.expand(self.template)
        return s
        

class Args:
    self.dir = ''
    self.recurseDirs = False
    self.maskRx = None
    self.processType = TYPE_FILES
    self.processPart = PART_WHOLE
    self.caseSens = False
    self.localeSpec = False
    self.verbose = False
    self.test = False
    self.tranforms = []

    class Error(Exception):
        def __init__(self, x):
            Exception.__init__(self, x)

    def parse(self, argv):
        # regexp for '/switch[:[value]]'
        switchRx = re.compile(r'^/([^:]+)(?::(.*))?$', re.I)
        
        # 'params' will be a string list, containing
        # nested, 1-element lists where '/R' was found
        params = []
        for s in argv:
            mo = switchRx.match(s)
            if mo:
                self.parseSwitch(mo.group(1), mo.group(2), params)
            else:
                params.append(s)

        self.collectSwitchParams(params)
        self.checkSwitchParams(params):

    def parseSwitch(self, sw, val, params):
        sw = sw.upper()
        simpleSwitches = {
            'C': ('caseSens',    True),
            'L': ('localeSpec',  True),
            'V': ('verbose',     True),
            'T': ('test',        True),
            'B': ('processPart', PART_BASE),
            'E': ('processPart', PART_EXT),
            'D': ('processType', TYPE_DIRS),
            'A': ('processType', TYPE_FILES_AND_DIRS),
            'S': ('recurseDirs', True),
            }
        if sw in simpleSwitches:
            self.ensureNoVal(sw, val)
            attr, value = simpleSwitches[sw]
            self[attr] = value
        elif sw == 'R':
            params.append(ReplaceParamGroup(parseRanges(val)))
        else:
            raise Error, 'Unknown switch: "' + sw + '"'

    class SwitchParams(object):  # ABC
        def __init__(self, switch, maxParams):
            self.switch = switch
            self.params = []
            self.maxParams = maxParams
        def tryAdd(self, x):
            if self.isComplete():
                return false
            self.params.append(x)
            return true
        def isComplete(self):
            return len(self.params) >= self.maxParams

    class ModifyParams(SwitchParams):
        def __init__(self):
            SwitchParams.__init__(self, 'M', 2)

    class ReplaceParams(SwitchParams):
        def __init__(self):
            SwitchParams.__init__(self, 'R', 3)

    def collectSwitchParams(params):
        tmp = []
        for x in params:
            if isinstance(x, SwitchParams) or not tmp or \
               not isinstance(tmp[-1], SwitchParams) or not tmp[-1].tryAdd(x):
                tmp.append(x)
        params[:] = tmp

    def checkSwitchParams(params):
        switchCounts = collections.defaultdict(lambda:0)
        for x in params:
            if isinstance(x, SwitchParams):
                switchCounts[x.switch] += 1
                if not x.isComplete():
                    raise Error, 'Missing argument of /' + x.switch + \
                          ' switch #' + str(switchCounts[x.switch]) + '.'
            
    def parseFilter(self, s):
        REGEXP_SEP = '\\\\'
        if REGEXP_SEP in s:
            dir, rx = s.split(REGEXP_SEP, 1)
            ...
        else:
            dir, file = os.path.split(s)
            if '*' in file or '?' in file:
                ...
            else:
                ...
            

    def parseRanges(self, s):
        ret = []
        for range in s.split(','):
            a = range.split(':')
            if len(a) == 0:
                ok
            == 1
                ok
            == 2
                ok
            == 3
                ok
            else
                not ok







            if not m:
                params.append(s)
                if len(params) > 3:
                    raise Error, 'Too many parameters.'
                
                
                
            else:
                raise Error, 'Invalid switch: "' + s + '"'
            
        if len(params) < 2:
            raise Error, 'Too few parameters.'
        elif len(params) == 2:
            self.src, self.dst = params
        else:  # len(params) == 3
            self.dir, self.src, self.dst = params
        return

    def ensureNoVal(self, sw, val):
        if val:
            raise Error, '/' + sw + ' does not accept a value.'
            


def buildName(matchObj, dstList):
    matchCnt = matchObj.groups


def errLn(s):
    sys.stderr.write('ERROR: ' + s + '\n')


# remove script name from 'argv', call main and return its result
sys.exit(main(sys.argv[1:]))
