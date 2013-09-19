"""Print table-formatted data.

tags: text

NOTE: None is only used in Column objects to inherit from Table
      (it is never a special setting here)


Table/Column attributes
=======================

    width:{int,str}='fit'
        column width
            >=0     as specified
            <0      proportional; divide available space on all such columns
            '*'     max len of header, footer, and all cells
            'fit'   max len of header, footer, and first cell
            'hide'  hide column (and its colsep); useful to omit data from
                    list rows, while relying on automatic index 'selector'

    colsep:str=' '
        left-hand column separator (ignored for first column)

    headsep:{str,callable}='-'
        header separator
            ''          if all visible column headsep are '', the entire headsep
                        line is omitted
            str         replicate the string enough times to fill the available width
            callable    user-defined function

    footsep:str=''
        footer separator
            (like headsep)

    align:str='l'
        header, footer, and cell alignment
            l   left
            r   right
            c   center

    format:{str,callable}='{}'
        data formatting
            str         format() string pattern
            callable    use-defined formatting function

    overflow:{str,callable}='trim'
        how to handle cell data wider than column
            'ignore'    remove extra chars (left-most if align='r', right-most otherwise)
            'trim'      like 'ignore', but adds a '<'/'>' at the removed chars
            'error'     raise exception
            callable    use-defined trimming function

    pad:{int,str,tuple}=0
        extra padding around cell strings
            int     left/right number of spaces
            str     left/right string
            tuple   separate left and right pad (either can be int or str)


Column attributes
=================

    header:{str,tuple}=''
        column header
            str     single-line header; if all column headers are '', the entire header
                    line is omitted
            tuple   multi-line header

    footer:{str,tuple}=''
        column footer
            (like header)

    selector:{None,int,str,tuple,callable}=None
        data select from each record row
            None        get the n'th item, where n is the column index
                        (including hidden columns)
            int         same as ('item', <int>)
            str         same as ('item', <str>)
            tuple   (type_, x); type can be:
                            'item'  operator.itemgetter(x)
                            'attr'  operator.attrgetter(x)
            callable    user-defined function
"""

from __future__ import print_function
import sys
import itertools
import copy


def _non_none(a, b):
    """a if a is not None else b"""
    return a if a is not None else b


def _normalize_marginals(a, align):
    """Process list of marginals (i.e. headers or footers)."""

    # convert strings to 1-tuples and lists to tuples
    a = [tuple(x) if isinstance(x, (tuple, list)) else (x,) for x in a]

    # pad lines to max size
    max_lines = max(len(t) for t in a)
    a = [_pad_lines(t, max_lines, align) for t in a]

    # remove whole, ''-only lines (note: zip(*a) is a 2-D list transpose)
    return zip(*[t for t in zip(*a) if any(t)])


def _pad_lines(lines, count, valign):
    """Pad lines tuple to size count with 0-length strings.

    valign  one of: 'top', 'bottom'
    """
    pad = ('',) * (count - len(lines))
    return lines + pad if valign == 'top' else pad + lines


def _pad(s, width, align, overflow):
    if align == 'l':
        s = s.ljust(width)
    elif align == 'r':
        s = s.rjust(width)
    else:
        s = s.center(width)
    if len(s) > width:
        if overflow == 'error':
            raise ValueError('cell data wider than column')
        elif overflow == 'ignore':
            s = s[-width:] if align == 'r' else s[:width]
        elif overflow == 'trim':
            s = '<'+s[-width+1:] if align == 'r' else s[:width-1]+'>'
        else:
            raise NotImplementedError('callable cell overflow')
    return s


def _print_marginal_rows(marginals, columns, stream):
    for cells in marginals:
        row = ''
        for i, (c, m) in enumerate(zip(columns, cells)):
            row += c.colsep if i > 0 else ''
            cell = _pad(m, c.width, c.align, 'ignore')
            row += c.pad[0] + cell + c.pad[1]
        print(row, file=stream)


def _print_marginal_seps(which, columns, stream):
    seps = [getattr(c, which) for c in columns]
    if any(seps):
        row = ''
        for i, (c, s) in enumerate(zip(columns, seps)):
            row += c.colsep if i > 0 else ''
            row += (s[:1] or ' ') * (c.width + len(c.pad[0]) + len(c.pad[1]))
        print(row, file=stream)


class Table(object):

    def __init__(self, **kw):
        self.columns = kw.pop('columns', [])

        self.width = kw.pop('width', '*')
        self.colsep = kw.pop('colsep', ' ')
        self.headsep = kw.pop('headsep', '')
        self.footsep = kw.pop('footsep', '')
        self.align = kw.pop('align', 'l')
        self.format = kw.pop('format', '{}')
        self.overflow = kw.pop('overflow', 'trim')
        self.pad = kw.pop('pad', 0)
        self.header = kw.pop('header', '')
        self.footer = kw.pop('footer', '')

        # remove trailing whitespace from all lines
        self.rstrip_lines = kw.pop('rstrip_lines', False)

        # how to align headers/footers with fewer lines than total
        # ('top' or 'bottom')
        self.multi_header_align = kw.pop('multi_header_align', 'bottom')
        self.multi_footer_align = kw.pop('multi_footer_align', 'top')

        # file-like object to send output to
        self.stream = kw.pop('stream', sys.stdout)

        if kw:
            raise ValueError('unexpected keyword arguments', kw.keys())


    def _copy_normalized_visible_columns(self):
        columns = [copy.deepcopy(c) for c in self.columns if c.width != 'hide']
        visible_indices = [i for i, c in enumerate(self.columns) if c.width != 'hide']

        for c, vi in zip(columns, visible_indices):

            # inherit defaults
            c.width = _non_none(c.width, self.width)
            c.colsep = _non_none(c.colsep, self.colsep)
            c.headsep = _non_none(c.headsep, self.headsep)
            c.footsep = _non_none(c.footsep, self.footsep)
            c.align = _non_none(c.align, self.align)
            c.format = _non_none(c.format, self.format)
            c.overflow = _non_none(c.overflow, self.overflow)
            c.pad = _non_none(c.pad, self.pad)
            c.header = _non_none(c.header, self.header)
            c.footer = _non_none(c.footer, self.footer)
            c.selector = vi if c.selector is None else c.selector

            # normalize
            if not callable(c.format):
                c.format = lambda y, format=c.format: format.format(y)
            if isinstance(c.selector, int):
                c.selector = operator.itemgetter(c.selector)
            if not isinstance(c.pad, tuple):
                c.pad = (c.pad, c.pad)
            c.pad = tuple(' ' * x if isinstance(x, int) else x for x in c.pad)

        self._normalize_marginals(columns)
        return columns


    def _normalize_marginals(self, columns):
        headers = _normalize_marginals(
            [c.header for c in columns], self.multi_header_align)
        footers = _normalize_marginals(
            [c.footer for c in columns], self.multi_footer_align)

        if not headers:
            headers = [()] * len(columns)
        if not footers:
            footers = [()] * len(columns)

        for c,h,f in zip(columns, headers, footers):
            c.header = h
            c.footer = f


    def output(self, data):
        columns = self._copy_normalized_visible_columns()
        if not columns:
            return

        cells_rows = ([c.format(c.selector(rec)) for c in columns] for rec in data)

        head_rows = zip(*(c.header for c in columns))
        foot_rows = zip(*(c.footer for c in columns))
        head_widths = [max(len(s) for s in a) for a in zip(*head_rows)] or \
                      [0] * len(columns)
        foot_widths = [max(len(s) for s in a) for a in zip(*foot_rows)] or \
                      [0] * len(columns)

        if any(c.width == '*' for c in columns):
            cells_rows = list(cells_rows)
            for i, (c, head, foot) in enumerate(zip(columns, head_widths, foot_widths)):
                if c.width == '*':
                    c.width = max(head_widths[i], foot_widths[i], max(len(cells[i]) for cells in cells_rows))
                elif c.width == 'fit':
                    c.width = max(head_widths[i], foot_widths[i], len(cells_rows[0][i]))
        elif any(c.width == 'fit' for c in columns):
            first_cells = next(cells_rows)
            for i, (c, cell, head, foot) in enumerate(zip(columns, first_cells, head_widths, foot_widths)):
                if c.width == 'fit':
                    c.width = max(head_widths[i], foot_widths[i], len(cell))
            cells_rows = itertools.chain([first_cells], cells_rows)

        _print_marginal_rows(head_rows, columns, self.stream)
        _print_marginal_seps('headsep', columns, self.stream)

        for cells in cells_rows:
            row = ''
            first_column = True
            for c, cell in zip(columns, cells):
                if not first_column:
                    row += c.colsep
                cell = _pad(cell, c.width, c.align, c.overflow)
                row += c.pad[0] + cell + c.pad[1]
                first_column = False
            if self.rstrip_lines:
                row = row.rstrip()
            print(row, file=self.stream)

        _print_marginal_seps('footsep', columns, self.stream)
        _print_marginal_rows(foot_rows, columns, self.stream)



class Column(object):

    def __init__(self, **kw):
        self.width = kw.pop('width', None)
        self.colsep = kw.pop('colsep', None)
        self.align = kw.pop('align', None)
        self.headsep = kw.pop('headsep', None)
        self.footsep = kw.pop('footsep', None)
        self.format = kw.pop('format', None)
        self.overflow = kw.pop('overflow', None)
        self.pad = kw.pop('pad', None)
        self.header = kw.pop('header', None)
        self.footer = kw.pop('footer', None)

        self.selector = kw.pop('selector', None)  # select data from row: None (implied int, same as column index), int (seq index), str (dict key), callable

        if kw:
            raise ValueError('unexpected keyword arguments', kw.keys())


def dir_data(dirpath):
    for s in os.listdir(dirpath):
        path = os.path.join(dirpath, s)
        name = s
        size = os.path.getsize(path)
        date = os.path.getmtime(path)
        yield name, size, date


if __name__ == '__main__':
    import os, operator, time
    path = os.path.expanduser('~')
    data = list(dir_data(path))
    data = [x for x in data if len(x[0]) < 20][:10]

    columns=[
        Column(header='name', align='c', width='*'),
        Column(header=('size', '[bytes]'), align='r', format='{:,}', width='*'),
        Column(header='modified', format=lambda n: time.ctime(n)),
    ]
    print()
    Table(colsep='|', headsep='-', footsep='+', columns=columns, pad=1).output(data)
