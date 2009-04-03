from __future__ import with_statement
import os
from contextlib import contextmanager
import win32api as api, win32gui as gui, win32con as con

import ctypes
import SharedLib

BOOL    = ctypes.c_ulong
HANDLE  = ctypes.c_void_p
LPCTSTR = ctypes.c_wchar_p
WORD    = ctypes.c_ushort
LPVOID  = ctypes.c_void_p
DWORD   = ctypes.c_ulong
UpdateResource = SharedLib.winfunc('kernel32', 'UpdateResourceW', BOOL,
                                   #[HANDLE, LPCTSTR, LPCTSTR, WORD, LPVOID, DWORD])
                                   [HANDLE, LPCTSTR, DWORD, WORD, LPVOID, DWORD])  # hack to use numeric ID


@contextmanager
def Module(path):
    mod = api.LoadLibrary(path)
    yield mod
    api.FreeLibrary(mod)


def dump_resources(mod, restype, outdir):
    print 'dumping %s resources to "%s"...' % (restype, outdir)
    for id in api.EnumResourceNames(mod, restype):
        langs = api.EnumResourceLanguages(mod, restype, id)
        print id, langs
        for lang in langs:
            outname = 'foxit_%s_%s_%s.jpg' % (restype, id, lang)
            with open(os.path.join(outdir, outname), 'wb') as f:
                data = api.LoadResource(mod, restype, id, lang)
                f.write(data)

def remove_resources(fname, restype, ids):
    print 'removing %s resources...' % (restype,)
    h = api.BeginUpdateResource(fname, False)
    for id in ids:
        print id
        #api.UpdateResource(h, restype, id, '', con.LANG_NEUTRAL)
        UpdateResource(h, restype, id, 1033, None, 0)
    api.EndUpdateResource(h, False)
    

def replace_resources(fname, restype, ids, data):
    print 'replacing %s resources...' % (restype,)
    h = api.BeginUpdateResource(fname, False)
    for id in ids:
        print id
        api.UpdateResource(h, restype, id, data, 1033)
    api.EndUpdateResource(h, False)
    

def build_dummy_image():
    """Create a JPEG to use instead of the ads."""
    import Image, ImageDraw, ImageFont
    from StringIO import StringIO

    imgsize = (232,19)
    text = '[ blocked ad ]'
    dpiY = 96  # assume default; proper value is win32ui.GetDeviceCaps(dc, win32con.LOGPIXELSY)
    pt = imgsize[1] * 72 / dpiY  # calc font point size for required pixel height
    fgclr = gui.GetSysColor(con.COLOR_3DSHADOW)
    bgclr = gui.GetSysColor(con.COLOR_3DFACE)
    outname = r'C:\Documents and Settings\Elias\Desktop\blocked.jpg'

    img = Image.new('RGB', imgsize, bgclr)
    fnt = ImageFont.truetype('Tahoma.ttf', pt)
    drw = ImageDraw.Draw(img)
    w = drw.textsize(text, font=fnt)[0]
    x = (imgsize[0] - w) / 2  # calc draw offset, so that string is centered
    drw.text((x, 0), text, font=fnt, fill=fgclr)

    data = StringIO()
    img.save(data, 'jpeg')
    return data.getvalue()


EXEPATH = r'C:\Program Files\Foxit Reader\Foxit Reader.exe'
RESTYPE = 'JPEG'

##outdir = r'C:\Documents and Settings\Elias\Desktop\foxit'
##with Module(EXEPATH) as mod:
##    dump_jpeg_resources(mod, RESTYPE, outdir)

ADVERT_IDS = (907,908,909,910,911,912,913,914,915)  # for v3.0 build 1120

# simply removing them crashes Foxit
#remove_resources(EXEPATH, RESTYPE, ADVERT_IDS)

# so we replace them with dummies instead
data = build_dummy_image()
replace_resources(EXEPATH, RESTYPE, ADVERT_IDS, data)

'''
NOTE: EndUpdateResource sometimes fails because it's partly broken:
    Its the End[UpdateResource] of the world we know it
    Thursday, August 21, 2008 7:01 AM Michael S. Kaplan 
    http://blogs.msdn.com/michkap/archive/2008/08/21/8883552.aspx
'''
