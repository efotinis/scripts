"""Torrent file parser.

Specs from <http://wiki.theory.org/BitTorrentSpecification>
"""
# 2009.07.03  renamed to torrentfile.py
# 2008.05.18  created

import os, string


"""
ascii_num:  r'-?[1-9][0-9]*'

item:       string | int | list | dict

string:     ascii_num ':' ('ascii_num' bytes)
int:        'i' ascii_num 'e'
list:       'l' item+ 'e'
dict:       'd' pair+ 'e'

pair:       string item
"""


class Error:
    def __init__(self, msg, pos):
        self.msg, self.pos = msg, pos
    def __str__(self):
        return '%s (%d)' % (self.msg, self.pos)


def getstring(f):
    s = ''
    while True:
        c = f.read(1)
        if not c:
            raise Error('EOF while reading string size', f.tell())
        if c == ':':
            break
        if c not in string.digits:
            raise Error('invalid string size char', f.tell())
        s += c
    try:
        size = int(s, 10)
        if size < 0:
            raise ValueError
    except ValueError:
        raise Error('invalid string size', f.tell())
    s = f.read(size)
    if len(s) != size:
        raise Error('EOF while reading string', f.tell())
    return s


def getinteger(f):
    s = ''
    while True:
        c = f.read(1)
        if not c:
            raise Error('EOF while reading integer', f.tell())
        if c == 'e':
            break
        if c not in string.digits + '-':
            raise Error('invalid integer char', f.tell())
        s += c
    try:
        return int(s, 10)
    except ValueError:
        raise Error('invalid integer', f.tell())


def getlist(f):
    a = []
    while True:
        c = f.read(1)
        if not c:
            raise Error('EOF while reading list', f.tell())
        if c == 'e':
            break
        a += [getany(f, c)]
    return a


def getdict(f):
    d = {}
    while True:
        c = f.read(1)
        if not c:
            raise Error('EOF while reading dict key', f.tell())
        if c == 'e':
            break
        f.seek(-1, os.SEEK_CUR)
        key = getstring(f)
        c = f.read(1)
        if not c:
            raise Error('EOF while reading dict value', f.tell())
        value = getany(f, c)
        d[key] = value
    return d


def getany(f, c):
    if c == 'i':
        return getinteger(f)
    if c == 'l':
        return getlist(f)
    if c == 'd':
        return getdict(f)
    f.seek(-1, os.SEEK_CUR)
    return getstring(f)


##path = r'C:\Documents and Settings\Elias\Application Data\uTorrent\Norton Ghost 14.0 + Recovery Disk.torrent'
##f = open(path, 'rb')
##assert f.read(1) == 'd'
##d = getdict(f)


DIR = r'C:\Documents and Settings\Elias\Application Data\uTorrent'
a = [s for s in os.listdir(DIR) if os.path.splitext(s)[1].lower() == '.torrent']


