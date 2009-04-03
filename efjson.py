class error(Exception):
    def __init__(self, s):
        Exception.__init__(self, s)


class StringStream:

    def __init__(self, s):
        self.data = s
        self.pos = 0

    def empty(self):
        return self.pos >= len(self.data)

    def getnext(self, n=1):
        ret = self.data[self.pos:self.pos+n]
        self.pos += n
        return ret

    def peeknext(self):
        return self.data[self.pos]

    def skipws(self):
        while not self.empty() and self.peeknext().isspace():
            self.pos += 1


class JsonStream(StringStream):

    escaped = {'"':'"', '\\':'\\', '/':'/',
               'b':'\b', 'f':'\f', 'n':'\n', 'r':'\r', 't':'\t'}
    literals = {'true':True, 'false':False, 'null':None}

    def __init__(self, s):
        StringStream.__init__(self, s)
        self.skipws()

    def parse_value(self):
        c = self.peeknext()
        if c == '{':
            return self.parse_object()
        elif c == '[':
            return self.parse_array()
        elif c == '"':
            return self.parse_string()
        elif c.isdigit() or c == '-':
            return self.parse_number()
        else:
            return self.parse_literal()

    def parse_string(self):
        ret = ''
        self.getnext() # skip '"'
        while not self.empty():
            c = self.getnext()
            if c == '"':
                break
            elif c == '\\':
                if self.empty():
                    raise error('unexpected EOF')
                c = self.getnext()
                if c in self.escaped:
                    ret += self.escaped[c]
                elif c == 'u':
                    ret += unichr(int(self.getnext(4), 16))
                else:
                    raise error('invalid escape')
            elif ord(c) < 32:
                raise error('found control char in string')
            else:
                ret += c
        else:
            raise error('unexpected EOF')
        return ret

    def parse_number(self):
        """
        number 
            int [frac] [exp]
        int 
            [-] digit
            [-] digit1-9 digits 
        frac 
            . digits 
        exp 
            e digits 
        digits 
            digit
            digit digits 
        e 
            e
            e+
            e-
            E
            E+
            E-
        """
        raise error('numbers not yet supported')

    def parse_literal(self):
        s = ''
        while not self.empty() and self.peeknext().isalpha():
            s += self.getnext()
        try:
            return self.literals[s]
        except KeyError:
            raise error('invalid literal')

    def parse_object(self):
        self.getnext() # skip '{'
        items = self.parse_list(self.member_parser, '}')
        self.getnext() # skip '}'
        ret = {}
        for name, value in items:
            ret[name] = value
        return ret

    def parse_array(self):
        self.getnext() # skip '['
        items = self.parse_list(self.element_parser, ']')
        self.getnext() # skip ']'
        return items

    def parse_list(self, item_parser, stop_char):
        ret = []
        self.skipws()
        if self.peeknext() == stop_char:
            return ret
        while True:
            ret += [item_parser()]
            self.skipws()
            c = self.peeknext()
            if c == ',':
                self.getnext()
                self.skipws()
            elif c == stop_char:
                return ret
            else:
                raise error('expected "," or "%s"' % stop_char)

    def member_parser(self):
        name = self.parse_string()
        self.skipws()
        if self.peeknext() <> ':':
            raise error('expected ":"')
        self.getnext()
        self.skipws()
        value = self.parse_value()
        return name, value

    def element_parser(self):
        return self.parse_value()


s = r"""
{
    "a": "true",
    "b": null,
    "d": [
        "sd\t\u072"
        ]
}
"""

try:
    print JsonStream(s).parse_value()
except error, x:
    print 'ERROR:', str(x)
    



lyrics - white and nerdy
clipper / vfp : avax
json python impl,