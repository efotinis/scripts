# 2007.08.15  Created.
# 2008.01.29  Added genre names and prune option.

# NOTE: file objects must be opened in binary mode

import os, re


# genres by index (0..79 defined by id3v1; 80..125 by Winamp)
genres = [
    'Blues', 'Classic Rock', 'Country', 'Dance', 'Disco',
    'Funk', 'Grunge', 'Hip-Hop', 'Jazz', 'Metal',
    'New Age', 'Oldies', 'Other', 'Pop', 'R&B',
    'Rap', 'Reggae', 'Rock', 'Techno', 'Industrial',
    'Alternative', 'Ska', 'Death Metal', 'Pranks', 'Soundtrack',
    'Euro-Techno', 'Ambient', 'Trip-Hop', 'Vocal', 'Jazz+Funk',
    'Fusion', 'Trance', 'Classical', 'Instrumental', 'Acid',
    'House', 'Game', 'Sound Clip', 'Gospel', 'Noise',
    'AlternRock', 'Bass', 'Soul', 'Punk', 'Space',
    'Meditative', 'Instrumental Pop', 'Instrumental Rock', 'Ethnic', 'Gothic',
    'Darkwave', 'Techno-Industrial', 'Electronic', 'Pop-Folk', 'Eurodance',
    'Dream', 'Southern Rock', 'Comedy', 'Cult', 'Gangsta',
    'Top 40', 'Christian Rap', 'Pop/Funk', 'Jungle', 'Native American',
    'Cabaret', 'New Wave', 'Psychadelic', 'Rave', 'Showtunes',
    'Trailer', 'Lo-Fi', 'Tribal', 'Acid Punk', 'Acid Jazz',
    'Polka', 'Retro', 'Musical', 'Rock & Roll', 'Hard Rock',
    'Folk', 'Folk-Rock', 'National Folk', 'Swing', 'Fast Fusion',
    'Bebob', 'Latin', 'Revival', 'Celtic', 'Bluegrass',
    'Avantgarde', 'Gothic Rock', 'Progressive Rock', 'Psychedelic Rock', 'Symphonic Rock',
    'Slow Rock', 'Big Band', 'Chorus', 'Easy Listening', 'Acoustic',
    'Humour', 'Speech', 'Chanson', 'Opera', 'Chamber Music',
    'Sonata', 'Symphony', 'Booty Bass', 'Primus', 'Porn Groove',
    'Satire', 'Slow Jam', 'Club', 'Tango', 'Samba',
    'Folklore', 'Ballad', 'Power Ballad', 'Rhythmic Soul', 'Freestyle',
    'Duet', 'Punk Rock', 'Drum Solo', 'A capella', 'Euro-House',
    'Dance Hall',
]
# value typically used for 'no genre'
NO_GENRE = 255

TAG_SIZE = 128


# tag fields; v1.1 uses part of 'comment' for 'track'
# (name, byte-size, NUL-padded)
_fields = (
    ('title',   30, True),
    ('artist',  30, True),
    ('album',   30, True),
    ('year',     4, False),
    ('comment', 30, True),
    ('genre',    1, False))

_stripchars = '\0 \t'

_BADCHAR_RX = re.compile(r'[\\/:*?"<>|]')


def _open(f, mode):
    """Open file if 'f' is a string, else return 'f'."""
    return open(f, mode) if isinstance(f, basestring) else f


def hastag(f):
    """Test if a file contains a tag."""
    f = _open(f, 'rb')
    f.seek(-TAG_SIZE, os.SEEK_END)
    return f.read(3) == 'TAG'


def readtag(f, prune=False):
    """Read tag (or None) from a file.

    The tag is a mapping of: title,artist,album,year,comment,track,genre.
    All tag values are strings (incl. year), except track and genre (ints).
    'prune' omits empty/invalid fields.
    """
    f = _open(f, 'rb')
    f.seek(-TAG_SIZE, os.SEEK_END)
    data = f.read(TAG_SIZE)
    i, j = 0, 3  # cur field beg/end
    if len(data) != TAG_SIZE or data[i:j] != 'TAG':
        return None
    tag = {}
    for name, size, strip in _fields:
        i, j = j, j + size
        s = data[i:j]
        if strip:
            s = s.rstrip(_stripchars)
        tag[name] = s
    # last byte of comment may be the track number
    s = tag['comment']
    if len(s) == 30 and s[-2] == '\0' and s[-1] != '\0':
        tag['track'] = ord(s[-1])
        tag['comment'] = s[:28].rstrip(_stripchars)
    tag['genre'] = ord(tag['genre'])
    if prune:
        try:
            int(tag['year'])
        except ValueError:
            del tag['year']
        for s in ('title', 'artist', 'album', 'comment'):
            if not tag[s].strip():
                del tag[s]
        if tag['genre'] == NO_GENRE:
            del tag['genre']
    return tag


def writetag(f, info):
    """Add new or update existing tag."""
    f = _open(f, 'r+b')
    f.seek(-TAG_SIZE if hastag(f) else 0, os.SEEK_END)
    f.write(buildtag(info))


def removetag(f):
    """Remove tag if it exists."""
    f = _open(f, 'r+b')
    if hastag(f):
        f.seek(-TAG_SIZE, os.SEEK_END)
        f.truncate()


def _pad(s, n):
    """Pad with NULs (or truncate) a string to a specfied size.

    Also convert string to local encoding.
    """
    return s.encode('mbcs')[:n].ljust(n, '\0')


def buildtag(info):
    """Convert tag data (s. return of readtag()) to binary string.

    Unknown keys in info are ignored; missing fields are set to defaults.
    """
    return ''.join((
        'TAG',
        _pad(info.get('title',   ''), 30),
        _pad(info.get('artist',  ''), 30),
        _pad(info.get('album',   ''), 30),
        _pad(info.get('year',    ''), 4),
        _pad(info.get('comment', ''), 28) + '\0',
        chr(info.get('track', 0)),
        chr(info.get('genre', NO_GENRE))))


def getsafename(s, c='_'):
    """Replace invalid filesystem name chars.

    Useful when creating filenames from tags.
    """
    return _BADCHAR_RX.sub(c, s)
