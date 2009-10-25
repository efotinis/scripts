"""Filter for aligning names in C variable declarations.

Works only for simple cases.

Example:
    input:
        char* foo;
        string bar;
        SomeStruct baz;
    output:
        char*      foo;
        string     bar;
        SomeStruct baz;
"""

import sys


def get_tokens(s):
    """Split type and name."""
    s = s.lstrip()
    i = s.find(' ')
    if i == -1:
        return '', s
    else:
        return s[:i], s[i:].lstrip()


input = sys.stdin
output = sys.stdout

items = [get_tokens(s.rstrip('\n')) for s in input]
maxlen = max(len(item[0]) for item in items)

for item in items:
    output.write(item[0].ljust(maxlen + 1) + item[1] + '\n')
