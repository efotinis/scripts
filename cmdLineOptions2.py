class Parser:
    self.switchEscapeNext = '/'  # a token that causes the next one to be parsed as a non-switch, even if it looks like a switch; e.g. 'FINDSTRING / /0' ('/' is ignored and '/0' is parsed as a positional arg)
    self.switchEscapeRest = '//' #
    # the default for the above two must be None (not '')
    self.options = []  # list of Option objects used to parse
    

# option flags 
OPT_COMBINABLE = 1 << 0  # 
OPT_CASESENS = 1 << 1  #

class Option:
    def __init__(self, name):
        self.name = name  # used to refer to this option; e.g. hasOpt('foo')
        self.ids = []  # list of ids; e.g.  I, IGN, IGNORE


class Id:
    self.




def hasSwitch(opt, sw):
    

# switch name matching
MATCH_FULL = 0          # 'X' can match '/X[:Y]'
MATCH_PARTIAL = 1       # 'XYZ' with min len 1 can match '/X[Y[Z]][:abc]'
MATCH_OPTIONALCOLON = 2 # 'X' can match '/X[[:]Y]'

caseSens = Yes | No
valueSep = Always | Never | Optional
minLen   = 1..len(s)  (0 means len(s))


class Error(Exception):
    def __init__(self):
        Exception.__init__(self, 'cmdLineOptions error.')

class ArgError(Error):
    def __init__(self, s):
        Exception.__init__(self, s)


ID_CASESENS        = 0x1

ID_VALSEP_OPTIONAL = 0x0
ID_VALSEP_ALWAYS   = 0x2
ID_VALSEP_NEVER    = 0x4


class Id:
    def __init__(self, name, flags=0, minMatch=0):
        if not name:
            raise ArgError('Created Id with empty name.')
        self.name = name
        self.caseSens = bool(flags & ID_CASESENS)
        valueSepMask = ID_VALSEP_ALWAYS | ID_VALSEP_NEVER
        self.valueSep = flags & valueSepMask
        if self.valueSep == valueSepMask:
            raise ArgError('Created Id with invalid VALSEP flags.')
        if not (0 <= minMatch <= len(name))
            raise ArgError('Created Id with invalid minMatch.')
        self.minLen = minMatch
        if self.minLen == len(name):
            self.minLen = 0


SW_VAL_OPTIONAL = 0x0
SW_VAL_ALWAYS   = 0x1
SW_VAL_NEVER    = 0x2


class Switch:
    def __init__(self, flags, ids):
        self.ids = ids
        self.val = SW_VAL_OPTIONAL
        valMask = SW_VAL_ALWAYS | SW_VAL_NEVER
        self.val = flags & valMask
        if self.val == valMask:
            raise ArgError('Created Switch with invalid VAL flags.')


Switch(SW_VAL_NEVER, [Id('M')], Id('MOUNT')])
Switch(SW_VAL_NEVER, [Id('U')], Id('UMOUNT')], Id('UNMOUNT')]))
Switch(SW_VAL_NEVER, [Id('S')], Id('STATUS')]))
Switch(SW_VAL_NEVER, [Id('RO')]))
Switch(SW_VAL_NEVER, [Id('CD')]))



def test(switches, args)



class CmdLineOptions:
    def __init__(self, args=None):
        self.clear()
        if args:
            self.add(args)

        /o
        /o:n
        /on
        /O
        /O:n
        /On

partial matching (one of):
    - none
    - match head without colon, eg. '/xy123' => ('xy', '123')
    - match partial con-conflicting: eg. '/inc:xyz' => ('include', 'xyz')
        a minimum char count should be specified, eg. with 3, 'EXCLUDE' can match 'EXC', but not 'E'


switches = [switchData, ...]
switchData = [switchAttr, [switchName, ...]]
switchName = [nameStr, nameAttr]

switches = [
    [
        'Directories to exclude.'
        EMPTYVAL,
        [
            ['X', FULLMATCH],
            ['EXCLUDE', FULLMATCH]
        ]
    ],
    [
        'Sort order.',
        REQVAL,
        [
            ['O', HEADMATCH]
        ]
    ]
]




        addSwitch((('m', '), ('mount')))

## there should be switch attributes and switch-alias attributes ... :b
##
##        

    def clear(self):
        self.items = []

    def add(self, args):
        self.items += parseRaw(args)

    def regPartialMatch(self, switch):
        self.regSwitches += switch  # str or str list
    

make a list of registered switch attribs:
    [
        ['X', attribs],
        ['Y', attribs],
        ...
    ]

another list of aliases (NOTE: what about case/partiality?):
    [
        ['i', 'include'],
        ['d', 'delete'],
        ...
    ]


##  a switch can have multiple names, e.g. ('i', 'inc', 'include')
##
##  switch attributes (in groups of mutual exclusion):
##        
##      pos: order within cmdline with other 'pos' items is important
##      ----> perhaps not needed;
##          we can/should just scan switches sequencially
##
##      case: matches case sensitively
##        
##      head: if there's a partial match at the beginning, the rest becomes the value
##          eg. normally '/X12' is parsed as ('X12', '')
##              but, if 'head' is on for 'X', it becomes ('X', '12')
##        
##      value: optional | mandatory | not-allowed
##        
##      concat: multiple values are concatenated into a single string value
##          eg. '/X:foo /X:bar' => ('X', 'foobar')
##      list: multiple values are grouped in a list (which becomes the switch's value)
##          eg. '/X:foo' => ('X', ['foo'])
##              '/X:foo /X:bar' => ('X', ['foo', 'bar'])
##      ---->  these could be replaced by special funcs:
##          opt.get('X')        # return first or last value (string)
##          opt.getlist('X')    # return list of all 'X' string values
##          opt.getlist('X').join(delim)  # return a single string
##
##  instance methods:
##      getUnexpectedSwitches() => list of undeclared switches (without duplicates)
##      getCollisions(mutExcl) => list of mutually excl. switches found
##          eg. for cmdline '/A /X /Z', getCollisions(['X', 'Y', 'Z']) => ['X', 'Z']
##          the return can be used to inform the user, eg. print 'Incompatible switches:', ret
##
##      getCount(id) => num
##      getFirst(id) => single
##      getLast(id) => single
##      getAll(id) => list
##      removeAll(id)
##
##      getCount() => num of all items (switches & params)
##      get(n) => get by index



##def parseKeyed(args, acceptMultiples, switchCase=0):
##    named = {}
##    unnamed = []
##    for sw, val in parseRaw(args):
##        if not sw:
##            unnamed += val
##        else:
##            
##    return named, unnamed
