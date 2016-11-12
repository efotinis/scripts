#!python3
"""Firefox data utilities."""

import collections
import configparser
import datetime
import os
import re
import sqlite3


BM_TYPE_PLACE = 1
BM_TYPE_FOLDER = 2


def profiles():
    """Generate (name,index,path) of installed Firefox profiles."""
    INIPATH = os.path.expandvars(r'%APPDATA%\mozilla\Firefox\profiles.ini')
    ini = configparser.ConfigParser()
    ini.read(INIPATH)
    for sect in ini.sections():
        m = re.match(r'Profile(\d+)', sect)
        if m:
            d = ini[sect]
            path = d['Path']
            if d['IsRelative'] == '1':
                path = os.path.join(os.path.dirname(INIPATH), path)
            yield d['Name'], m.group(1), path


def nameguid(s):
    """Make special GUID (e.g. root)."""
    return s.ljust(12, '_')


def date(n):
    """Convert stored date number to datetime object."""
    return datetime.datetime.fromtimestamp(n / 1000000)


BmInfo = collections.namedtuple('BmInfo', 'title url added modified tags notes guid')


##    fields = [x[1] for x in db.execute('PRAGMA table_info(moz_bookmarks)')]
##
##    moz_bookmarks:
##        0  *id              int     primary key
##        1   type            int     1: place, 2: folder, 3: ? (one entry, no title, child of Bookmarks Menu)
##        2   fk              int     link to moz_places:id
##        3   parent          int     id of parent (0 at root entry)
##        4   position        int     0-based position in parent
##        5   title           text
##        6   keyword_id      int     NULL
##        7   folder_type     text    NULL
##        8   dateAdded       int     UNIX timestamp * 10^6
##        9   lastModified    int     (as above)
##        10  guid            text    [-_A-Za-z0-9]{12}  (2**72 possible values)
##
##    moz_places:
##        0  *id              int
##        1   url             text
##        2   title           text
##        3   rev_host        text
##        4   visit_count     int
##        5   hidden          int
##        6   typed           int
##        7   favicon_id      int
##        8   frecency        int
##        9   last_visit_date int
##        10  guid            text
##        11  foreign_count   int
##
class Bookmarks:

    def __init__(self, db):
        db.row_factory = sqlite3.Row
        self.bookmarks = db.execute('SELECT * FROM moz_bookmarks').fetchall()
        self.db = db
        tags_id = [x for x in self.bookmarks if x['guid'] == nameguid('tags')][0]['id']
        self.tags = {x['id']:x['title'] for x in self.bookmarks if x['parent'] == tags_id}

    def find_guid(self, s):
        for x in self.bookmarks:
            if x['guid'] == s:
                return x
        raise KeyError('GUID not found: {}'.format(s))

    def _get_tags(self, bm):
        """Get bookmark tag names."""
        parents = [x['parent'] for x in self.bookmarks if x['fk'] == bm['fk']]
        return tuple(self.tags.get(n, 'unknown:{}'.format(n)) for n in parents[1:])

    def _get_url(self, bm):
        """Get bookmark URL."""
        return self.db.execute('SELECT * FROM moz_places WHERE id = ?', (bm['fk'],)).fetchone()['url']
        
    def _get_comment(self, bm):
        """Get bookmark comment."""
        r = self.db.execute('SELECT * FROM moz_items_annos WHERE item_id = ?', (bm['id'],)).fetchone()
        return r['content'] if r else None

    def unfiled(self):
        """Generate all Other Bookmarks recursively."""
        yield from self._all_under(self.find_guid(nameguid('unfiled')))

    def _all_under(self, parent):
        """Generate all bookmarks under parent recursively."""
        for bm in self.bookmarks:
            if bm['parent'] != parent['id']:
                continue
            if bm['type'] == BM_TYPE_PLACE:
                yield bm
            elif bm['type'] == BM_TYPE_FOLDER:
                yield from self._all_under(bm)

    def get_info(self, bm):
        """Convert bookmark record to BmInfo object.

        This is relatively slow, since it has to lookup into several tables.
        """
        return BmInfo(
            title=bm['title'],
            url=self._get_url(bm),
            added=date(bm['dateAdded']),
            modified=date(bm['lastModified']),
            tags=self._get_tags(bm),
            notes=self._get_comment(bm) or '',
            guid=bm['guid']
        )


def profile_path(name_or_id):
    """Get profile path, given its name or ID."""
    for name, index, path in profiles():
        if name_or_id in (name, index):
            return path
    raise KeyError('profile name or id not found: {}'.format(profile_path))


def open_profile(name_or_id, database):
    """Open the database of a profile specified by name or ID."""
    profpath = profile_path(name_or_id)
    return sqlite3.connect(os.path.join(profpath, database))


##import contextlib
##with contextlib.closing(open_profile('default', 'places.sqlite')) as db:
##    bm = Bookmarks(db)

##    a = [bm.get_info(x) for x in bm.unfiled()]

##    special = [x for x in bm.bookmarks if x['guid'].endswith('__')]
##    for x in special:
##        print(x['guid'], len(list(bm._all_under(x))))

##    for x in bm.bookmarks:
##        if 'hedonic' in (x['title'] or '').lower():
##            break
            
