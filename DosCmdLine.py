"""A module to handle DOS-style cmdline arguments.

2007.09.20 [EF] created... finally :)
"""

import textwrap


class Error(Exception):
    def __init__(self, s):
        Exception.__init__(self, s)


class Switch:

    def __init__(self, ids, name, descr, init, **params):
        """Object describing a switch.

        'ids' is either a single string or a tuple of string ids.
        'name' is the variable to hold the switch value.
            Note: If this evals to false, the object is not an actual switch,
            but a the description of a param. No variable is created for such
            an object; only 'ids' and 'descr' are used when displaying a usage
            listing.
        'descr' is a string to be used in a usage listing.
            Note: If this evals to false, this object is not included in a usage
            listing.
        'init' is the initial value of the switch variable.
        'params' holds additional information depending on the switch type:
            - If there is a 'value', the switch is a '/X' style switch and
              when found sets the switch var to that 'value'.
            - If there is an 'accumulator' or a 'converter' the switch is
              either a '/X:Y' or '/X[:Y]' style one.
              If there's an 'value_opt' and it tests True,
              the ':Y' part is optional.

        params['accumulator'] is a function taking the switch value,
        and the current switch variable's value and returning a new var value.
            e.g. init = []
                 accumulator = lambda s,a: a+[int(s)]
                 defines a switch that stores an int list
        params['converter'] is a function taking only the switch value and
        returning a new var value.
            e.g. init = 0
                 converter = lambda s: int(s, 0)
                 defines a switch that is by default 0 and can accept any C-style
                 int literal.
        The switch value is either a string or None (if optional and not specified).
        """
        self.ids = tuple([ids]) if isinstance(ids, basestring) else ids
        self.name = name
        self.descr = descr
        self.init = init
        self.params = params

    def parse(self, switch, value, options):
        """Parse a switch/value pair and return whether it was processed."""
        if not self.name or not self.match(switch):
            return False
        if 'value' in self.params:  # /X type
            if value is not None:
                raise Error('switch "%s" doesn\'t accept a value' % switch)
            setattr(options, self.name, self.params['value'])
        else:  # /X:Y or /X[:Y] type
            if value is None and self.params.get('value_opt') != True:
                raise Error('switch "%s" requires a value' % switch)
            accum = self.params.get('accumulator')
            conv = self.params.get('converter')
            try:
                if accum:
                    newvalue = accum(value, getattr(options, self.name))
                elif conv:
                    newvalue = conv(value)
                else:
                    newvalue = value
                setattr(options, self.name, newvalue)
            except Error:  # let our types of errors pass verbatim
                raise
            except Exception, x:  # translate all other errors to our type
                raise Error('could not process value "%s" of switch "%s": %s' %
                            (value, switch, x))
        return True  # processed

    def match(self, switch):
        """Test for a match on any one of the switch's ids."""
        for id in self.ids:
            if switch.lower() == id.lower():
                return True
        return False


class Flag(Switch):
    def __init__(self, ids, name, descr, **params):
        """A simple flag switch."""
        Switch.__init__(self, ids, name, descr, init=False, value=True, **params)

    
def split(s):
    """Split a cmdline arg to a switch/value pair.

    '/X'   -> ('X', None)    switch without value
    '/X:Y' -> ('X', 'Y')     switch with value
    'xyz'  -> (None, 'xyz')  not a switch, i.e. a param
    """
    if not s or s[0] != '/':
        return None, s
    s = s[1:]  # strip '/'
    if ':' in s:
        return s.split(':', 1)  # note: caller should handle a '' switch id
    else:
        return s, None


class Options:
    """Dummy class; stores switch variables and allows dot-notation access."""
    def dump(self):
        """Print all members and their values; for debugging."""
        for s in dir(self):
            if s != 'dump' and not s.startswith('__') and not s.endswith('__'):
                print s + ': ' + str(getattr(self, s))


def parse(args, switches):
    """Parse an arg list, using a list of switches and return options and params."""
    params = []
    # create option object and set initial values
    options = Options()
    for sw in switches:
        # NEW: 2007.09.26 [EF] added 'and getattr() is None'
        # so that multiple switches can affect a single var,
        # needing only one default val (the first non-None).
        # This seems better that specifying the same default val
        # in each switch.
        if sw.name and getattr(options, sw.name, None) is None:
            setattr(options, sw.name, sw.init)
    for s in args:
        switch, value = split(s)
        if switch is None:
            params += [value]
        else:  # process switch
            for sw in switches:
                if sw.parse(switch, value, options):
                    break
            else:
                raise Error('invalid switch: "%s"' % switch)
    return options, params

    
def helptable(switches, outwidth=80):
    """Return a str list of switches/params and descriptions."""
    table = []
    for sw in switches:
        if sw.descr:
            pfx = '/' if sw.name else ''  # add slash to real switches
            ids = ','.join(pfx + id for id in sw.ids)
            table += [(ids, sw.descr)]
    if not table:  # BUGFIX: 2007.09.24 [EF] early exit; max() fails on empty seq
        return []
    INDENT = 2
    SEP = 2
    leftColW = max(len(cols[0]) for cols in table) + SEP
    ret = []
    for title, descr in table:
        a = textwrap.wrap(descr, (outwidth - 1) - leftColW - INDENT)
        a = a or ['']
        for i, s in enumerate(a):
            ret += [INDENT*' ' + (title if i==0 else '').ljust(leftColW) + s]
    return ret


def showlist(switches, outwidth=80):
    """Print the list returned by helptable()."""
    for s in helptable(switches, outwidth):
        print s


if __name__ == '__main__':
    switches = [
        Flag  (('?','h'), 'help',  'Show this help.'),
        Switch('m',       'mode',  'Set mode of operation',
               0, converter=int, value_opt=True),
        Flag  ('q',       'quiet', 'Don\'t display any messages'),
        Switch('n',       'names', 'Name to use. Multiple switches are accumulated',
               [], accumulator=(lambda s,l:l+[s])),
    ]
    args = '/? /n:foo /m:5 /n:bar'.split()
    opt, params = parse(args, switches)
    opt.dump()
    