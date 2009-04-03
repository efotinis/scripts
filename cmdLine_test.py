##import getopt
##import optparse
##
##
##import platform
##
##def test(x=[]):
##    print x
##    x.append(42)
##    print x
##    print
##
##print
##test()
##test([])
##test([69])
##test([])
##test()
##
##parser.opt('a').combine()
##    lambda x,y: return x  -->  keep first
##    lambda x,y: return y  -->  keep last
##    lambda x,y: return x+y  -->  append
##    lambda x,y: raise Error  -->  not allowed


"""
parseInt


store           attr = value
store_const     attr = const
store_true      attr = True
store_false     attr = False
append          if attr is None:
                    attr = []
                attr += [value]
append_const    if attr is None:
                    attr = []
                attr += [const]
count           if attr is None:
                    attr = 0 if def is None else def
                attr += 1
                    
"""


class Switch():
    MULTI_STR_CONCAT = 0
    MULTI_LIST_CONCAT = 1
    MULTI_ERROR = 2
    MULTI_KEEP_FIRST = 3
    MULTI_KEEP_LAST = 4
    MULTI_DONT_PARSE = 5

    NONE = 0
    OPT = 1
    REQ = 2

    def __init__(self, s):
        a = s.split(';')
        self.names = self.parseNames(a[0])
        self.multi = self.parseMulti(a[1])
        self.valueReq = self.sepReq = self.parseValueSepReq(a[2])
        self.type = self.parseType(a[3])

    @staticmethod
    def parseNames(s):
        ret = []
        for name in s.split(','):
            if '(' in name:
                i = name.index('(')
                j = name.index(')')
                ret.append((name[:i], name[i+1:j]))
            else:
                ret.append(name)
        return ret

    @staticmethod
    def parseMulti(s):
        x = {
            '+': MULTI_STR_CONCAT,
            '*': MULTI_LIST_CONCAT,
            'X': MULTI_ERROR,
            '1': MULTI_KEEP_FIRST,
            '$': MULTI_KEEP_LAST,
            '-': MULTI_DONT_PARSE,
            }
        return x[s.upper()]

    @staticmethod
    def parseValueSepReq(s):
        valReq = REQ if 'V' in s else OPT if 'v' in s else NONE
        sepReq = REQ if 'S' in s else OPT if 's' in s else NONE
        return (valReq, sepReq)

    @staticmethod
    def parseType(s):
        """
        b   bool
        i   signed int (allow dec or hex)
        u   unsigned int (allow dec or hex)
        f   float
        t   text
        s   size (with optional prefix)
        """
        
"""

names
multiple





teminology
----------
program /switch:value argument


switch ids
==========
X       single letter (stackable?)      'D,X?'
ABC     word (partial match?)           'DEL,DE(LETE)'
        (case?)

value rules
===========
val     sep     syn
-------------------
none    -       /X                      '  '
req     none    /XY                     ' V'
req     req     /X:Y                    'SV'
req     opt     /X[:]Y                  'sV'
opt     none    /X[Y]                   ' v'
opt     req     /X[:Y]                  'Sv'
opt     opt     /X[[:]Y]                'sv'

multiplicity rules
==================
occurencies     action
----------------------
0               -
1               -
2+              keepFirst               '1'
2+              keepLast                'N'
2+              keepAllConcat           '+'
2+              keepAllList             '*'

value types
===========
bool
str
int
float


valueFilter(callableObj)
    def callableObj(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

value   type
---------------
no      -
yes     str
yes     str list


parser.add_option("-n", type="int", dest="num")

parser.add_option("-n").type("int").dest("num")


foo /a

"""
