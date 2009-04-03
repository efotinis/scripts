# 2008.07.24  created (tokenize func)


import re


TOKENIZE_CMD_RX = re.compile(r'''
    "(.*?)(?:"|$)   # a quoted string (closing quote optional at EOS)
    |               # -or-
    ([^\s"]+)       # a string of non-spaces and non-quotes
    ''', re.VERBOSE)


def tokenize(s):
    """Split a string like CommandLineToArgvW does and
    return a 3-tuple for each token (start, end and contents).
    Automatically handle double-quotes and adjacent (quoted) tokens."""
    a = []
    for m in TOKENIZE_CMD_RX.finditer(s):
        token = ''.join(m.groups(''))  # the single matching string
        if a and a[-1][1] == m.start():
            # adjacent to previous; merge
            prevBeg, prevEnd, prevToken = a[-1]
            a[-1] = (prevBeg, m.end(), prevToken + token)
        else:
            # append new
            a += [(m.start(), m.end(), token)]
    return a
        

def test_tokenizeCmd(s):
    s1, s2 = '', ''
    for beg, end, match in tokenize(s):
        spaces = beg - len(s1)
        if spaces > 0:
            s1 += ' ' * spaces
            s2 += ' ' * spaces
        size = end - beg
        s1 += '-' * size
        s2 += match.center(size)
    print
    print 'source: ', s
    print ' spans: ', s1
    print 'tokens: ', s2


if __name__ == '__main__':
    test_tokenizeCmd('')
    test_tokenizeCmd('foo')
    test_tokenizeCmd('simple  ""   " quoted " sin"gle "token"')
