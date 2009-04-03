"""Create several subdirs in the current dir with various test files.
EF 2007.09.18"""

import os, codecs


def measuring_str(size=256, segment=10):
    """Return a string with measuring segments.

    The default params produce a 256-char string looking like this:
        '-------10#-------20#---...'
    """
    ret = ''
    while len(ret) < size:
        s = str(len(ret) + segment) + '#'  # the next segment's size and mark
        s = s.rjust(segment, '-')[-segment:]  # pad & truncate to segment size
        ret += s
    return ret[:size]  # truncate to requested size


def generate_long_name():
    """Create a dir with an long-named file (as long as it gets)."""
    DNAME = 'longname'
    if not os.path.exists(DNAME):
        os.mkdir(DNAME)
    s = measuring_str()
    while s:
        try:
            file(os.path.join(DNAME, s), 'w').close()
            break
        except IOError:
            s = s[:-1]
            

def generate_unicode_names():
    """Create a dir with file of Unicode names."""
    DNAME = 'ucnames'
    if not os.path.exists(DNAME):
        os.mkdir(DNAME)
    a = (
        u'Fran\xe7ais (French)',
        u'Ti\u1ebfng Vi\u1ec7t (Vietnamese)',
        u'\u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac (Greek)',
        u'\u0411\u044a\u043b\u0433\u0430\u0440\u0441\u043a\u0438 (Bulgarian)',
        u'\u0420\u0443\u0441\u0441\u043a\u0438\u0439 (Russian)',
        u'\u05e2\u05d1\u05e8\u05d9\u05ea (Hebrew)',
        u'\u0627\u0644\u0639\u0631\u0628\u064a\u0629 (Arabic)',
        u'\u0641\u0627\u0631\u0633\u06cc (Persian)',
        u'\u0e20\u0e32\u0e29\u0e32\u0e44\u0e17\u0e22 (Thai)',
        u'\u4e2d\u6587 (Chinese)',
        u'\ud55c\uad6d\uc5b4 (Korean)',
        u'\u65e5\u672c\u8a9e (Japanese)',
    )
    for s in a:
        file(os.path.join(DNAME, s), 'w').close()
        

def generate_text_encodings():
    """Create a dir of text files with various encodings."""
    DNAME = 'txtenc'
    if not os.path.exists(DNAME):
        os.mkdir(DNAME)
    data = ( # fname, codec, BOM
        ('a',         'mbcs',      ''),  # ansi cp
        ('u8',        'utf_8',     ''),  # UTF 8
        ('u8_bom',    'utf_8_sig', ''),  # UTF 8 + BOM
        ('u16BE',     'utf_16_be', ''),  # UTF 16 BE
        ('u16LE',     'utf_16_le', ''),  # UTF 16 LE
        ('u16BE_bom', 'utf_16_be', codecs.BOM_UTF16_BE),  # UTF 16 BE + BOM
        ('u16LE_bom', 'utf_16_le', codecs.BOM_UTF16_LE),  # UTF 16 LE + BOM
    )
    s = (
        # a char from latin-1
        u'Fran\xe7ais (French)\r\n'
        # CP_ACP chars
        u'\u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac (Greek)\r\n'
        # totally different cp
        u'\u0420\u0443\u0441\u0441\u043a\u0438\u0439 (Russian)\r\n'
        # totally different cp (double-byte charset)
        u'\u65e5\u672c\u8a9e (Japanese)\r\n'
    )
    for fname, codec, bom in data:
        f = file(os.path.join(DNAME, fname) + '.txt', 'wb')
        f.write(bom + s.encode(codec))
        f.close()


generate_long_name()
generate_unicode_names()
generate_text_encodings()
