import re
import types

import six


def parseRaw(args):
    """Parse cmdline values and switches (in the form of '/switch[:value]').

    Returns a list of (switch,value) tuples.
    If 'switch' is '', 'value' is a non-switch value.
    """
    ret = []

    switchRx = re.compile(r'/([^:]+)(?::(.*))?', re.I)

    for s in args:
        m = switchRx.match(s)
        if m:
            ret.append((m.group(1), m.group(2)));
        else:
            ret.append(('', s))

    return ret


def upperSwitches(opt):
    """Convert switches to uppercase."""
    for i in range(len(opt)):
        opt[i][0] = opt[i][0].upper()


def lowerSwitches(opt):
    """Convert switches to lowercase."""
    for i in range(len(opt)):
        opt[i][0] = opt[i][0].lower()


# find a set of any of the specified switches
def findSet(opt, sw):
    optSw = set([x[0] for x in opt if x[0]])  # get non-empty switches
    return optSw & set(sw)


def hasSwitch(opt, s):
    for x in opt:
        if x[0] == s:
            return True
    return False


class SizeParamError(Exception):
    def __init__(self, msg='', src=''):
        Exception.__init__(self)
        self.msg = msg
        self.src = src
    def __str__(self):
        s = self.msg
        if self.src:
            s += ': ' + self.src
        return s
        
        
def parseSize(s):
    """Parse a size string of the format: [basePfx] number [unit].

    basePfx: An optional C-style base prexif.
    number:  Either int or float. The return value is always converted to int.
    unit:    Any of these (case insensitive): 'k','M','G','T','P','E'
    return:  An int.
    raise:   SizeParamError if s is empty, or the number is invalid.
    """
    if not s:
        raise SizeParamError('Empty size param')

    # extract size factor
    factor = 1
    units = 'KMGTPE'
    unitIndex = units.find(s[-1].upper())
    if unitIndex >= 0:
        factor = 1024 ** (1 + unitIndex)
        s = s[:-1]

    try:
        if '.' in s:
            return int(float(s) * factor)
        else:
            return int(int(s, 0) * factor)
    except:
        raise SizeParamError('Invalid size param number', s)


def strimatch(s1, s2):
    return s1.upper() == s2.upper()


class Item:
    def __init__(self, sw='', val=''):
        self.sw = sw
        self.val = val
    def __eq__(self, sw):
        return strimatch(sw, self.sw)
    def __str__(self):
        lst = []
        if self.sw:
            lst += ['/' + self.sw]
        if self.val:
            lst += [self.val]
        return ':'.join(lst)


##def iif(cond, x1, x2):
##    if cond:
##        return x1
##    else:
##        return x2


# switch names are case insensitive
class Options:

    def __init__(self, args=None):
        self.clear()
        if args:
            self.parse(args)

    def clear(self):
        self.options = []

    def parse(self, args):
        lst = parseRaw(args)
        for item in lst:
            self.options += [Item(item[0], item[1])]

    def __len__(self):
        return len(self.options)

    def __getitem__(self, i):
        return self.options[i]

    def __contains__(self, sw):
        for item in self.options:
            if item == sw:
                return True
        return False

    def __nonzero__(self):
        return self is not None

    def getAll(self, sw):
        return [item.val for item in self if item == sw]

    def getFirst(self, sw, default=None):
        lst = self.getAll(sw)
        if lst:
            return lst[0]
        else:
            return default

    def getLast(self, sw, default=None):
        lst = self.getAll(sw)
        if lst:
            return lst[-1]
        else:
            return default

##    def extractAll(self, sw):
##        indexes = self.findAll(sw)
##        ret = self.getAll(sw)
##        self.erase(sw)
##        return ret

    def findAll(self, sw):
        return [i for i in range(len(self)) if self[i] == sw]

    def findFirst(self, sw):
        lst = self.findAll(sw)
        if lst:
            return lst[0]
        else:
            return -1

    def findLast(self, sw):
        lst = self.findAll(sw)
        if lst:
            return lst[-1]
        else:
            return -1

    # x can be int (index), string (switch), or a list of those (even mixed)
    def erase(self, x):
        if isinstance(x, types.IntType):
            del self.options[x]
        elif isinstance(x, six.string_types):
            self.erase(self.findAll(x))
        else:
            # erase in reverse to properly handle indexes (if any)
            for i in reversed(x[:]):
                self.erase(i)

    def switchSet(self):
        return set([item.sw for item in self.options if not item == ''])


def main():
    """Test driver."""
    import sys
    l = parseRaw(sys.argv[1:])
    for sw, val in l:
        if sw == None:
            print 'value: "%s"' % val
        else:
            print 'switch: "%s"  "%s"' % (sw, val)


if __name__ == '__main__':
    main()
    
