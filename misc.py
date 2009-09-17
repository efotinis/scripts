import re


def strEscape(s, specChars, escChar='\\'):
    escChar = escChar[0]
    ret = ''
    if not escChar in specChars:
        specChars += escChar
    for c in s:
        if c in specChars:
            ret += escChar
        ret += c
    return ret


def strUnescape(s, escChar='\\'):
    escChar = escChar[0]
    ret = ''
    unescaped = False
    for c in s:
        if unescaped:
            ret += c
            unescaped = False
        elif c == escChar:
            unescaped = True
        else:
            ret += c
    return ret




'''
0   \0  null
7   \a  alert
8   \b  backspace
9   \t  tab
10  \n  newline
11  \v  vertical tab
12  \f  formfeed
13  \r  carriage return
34  \"
39  \'
63  \?
92  \\

\xFF
\uFFFF
'''


ESCAPES = {
    '\0':'0', '\a':'a', '\b':'b', '\t':'t', '\n':'n', '\v':'v',
    '\f':'f', '\r':'r', '"':'"', "'":"'", '?':'?', '\\':'\\'}

UNESCAPES = dict((v,k) for k,v in ESCAPES.items())

HEXSTR = re.compile(r'^[0-9a-f]+$', re.IGNORECASE)


def escape_str(s):
    ret = ''
    for c in s:
        x = ESCAPES.get(c)
        if x:
            ret += '\\' + x
        elif ord(c) < 32:
            ret += '\\x%02x' % ord(c)
        else:
            ret += c
    return ret

def unescape_str(s):
    ret = ''
    slen = len(s)
    i = 0
    while i < slen:
        if s[i] == '\\':
            i += 1
            if i + 1 > slen:
                raise ValueError('escape char at end of string')
            if s[i] == 'x':
                i += 1
                if i + 2 > slen:
                    raise ValueError('insufficient chars after \\x escape')
                xx = s[i:i+2]
                i += 2
                try:
                    if not HEXSTR.match(xx):
                        raise ValueError
                    ret += chr(int(xx, 16))
                except ValueError:
                    raise ValueError('bad chars after \\x escape')
            else:
                xx = UNESCAPES.get(s[i])
                i += 1
                if not xx:
                    raise ValueError('invalid escape at %d' % i)
                ret += xx
        else:
            ret += s[i]
            i += 1
    return ret
