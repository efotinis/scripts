"""Parse text databases.

Useful for human-readable databases, where special lines define sections.
Examples are INI files and their variants.
"""


class TextDB(object):
    """Base class defining the characteristics of text database.

    The pre/section/entry/post functions can be overriden to match
    a specific file format that will be consumed by parse(). See parse()
    for information about function calling order.

    See IniFile for an example implementation.
    """
                
    def pre(self, s):
        """Proprocess line. Can remove comments and whitespace."""
        return s

    def section(self, s):
        """Section name or None."""
        return None

    def entry(self, s):
        """Entry object or None."""
        return None

    def post(self, s):
        """Handle unmatched lines. By default, non-whitespace is an error."""
        if s.strip() != '':
            raise Error('unmatched line')

    def parse(self, lines, index=1):
        """Generate sections as (name, list_of_items) tuples.

        Note that the pre/section/entry/post functions are called in order and
        a successful section or entry match stops the call chain.

        The starting line index is used for exception messages.
        """
        current = None
        for i, s in enumerate(lines, index):
            try:
                s = self.pre(s.rstrip('\n'))
                name = self.section(s)
                if name is not None:
                    if current is not None:
                        yield current
                    current = name, []
                    continue
                item = self.entry(s)
                if item is not None:
                    if current is None:
                        raise Error('item before any section')
                    current[1].append(item)
                    continue
                self.post(s)
            except Error as x:
                x.line = i
                x.text = s
                raise
        if current is not None:
            yield current


class Error(Exception):
    """Generic error."""
    def __init__(self, msg, text=None, line=None):
        self.msg = msg
        self.text = text
        self.line = line
    def __str__(self):
        s = ''
        if self.line is not None:
            s += 'line %d: ' % self.line
        s += self.msg
        if self.text is not None:
            s += ' %r' % self.text
        return s


class IniFile(TextDB):
    """Sample INI file parser, implemented as a dict or dicts."""

    def __init__(self, path):
        self.sections = {}
        with open(path, 'rt') as f:
            for name, items in self.parse(f):
                self.sections[name] = {key:value for key, value in items}

    def pre(self, s):
        s = s.partition(';')[0]  # strip comments
        return s.strip()  # strip whitespace

    def section(self, s):
        if s[:1] != '[':
            return None
        if s[-1:] != ']':
            raise Error('missing closing bracket')
        return s[1:-1].strip()

    def entry(self, s):
        if not s:
            return None
        key, sep, value = s.partition('=')
        return key.strip(), value.strip()


class IndentedDB(TextDB):
    """Another sample of an indentation based database.

    Sections are defined by names that start at the beginning of the line
    and contain items that are indented by whitespace, e.g.:

        section 1
            item 1a
            item 1b
        
        section 2
            item 2a
            item 2b
    """
    def __init__(self, path):
        with open(path, 'rt') as f:
            self.items = {name:items for name,items in self.parse(f)}
    def section(self, s):
        return s.rstrip() if s and s[0] not in ' \t' else None
    def entry(self, s):
        return s.strip() or None
