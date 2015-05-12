"""Dump current Windows system colors."""

from __future__ import print_function
import win32api

defines = {
     0: ('COLOR_SCROLLBAR',),
     1: ('COLOR_BACKGROUND', 'COLOR_DESKTOP',),
     2: ('COLOR_ACTIVECAPTION',),
     3: ('COLOR_INACTIVECAPTION',),
     4: ('COLOR_MENU',),
     5: ('COLOR_WINDOW',),
     6: ('COLOR_WINDOWFRAME',),
     7: ('COLOR_MENUTEXT',),
     8: ('COLOR_WINDOWTEXT',),
     9: ('COLOR_CAPTIONTEXT',),
    10: ('COLOR_ACTIVEBORDER',),
    11: ('COLOR_INACTIVEBORDER',),
    12: ('COLOR_APPWORKSPACE',),
    13: ('COLOR_HIGHLIGHT',),
    14: ('COLOR_HIGHLIGHTTEXT',),
    15: ('COLOR_BTNFACE', 'COLOR_3DFACE'),
    16: ('COLOR_BTNSHADOW', 'COLOR_3DSHADOW'),
    17: ('COLOR_GRAYTEXT',),
    18: ('COLOR_BTNTEXT',),
    19: ('COLOR_INACTIVECAPTIONTEXT',),
    20: ('COLOR_BTNHIGHLIGHT', 'COLOR_3DHIGHLIGHT', 'COLOR_3DHILIGHT', 'COLOR_BTNHILIGHT'),
    21: ('COLOR_3DDKSHADOW',),
    22: ('COLOR_3DLIGHT',),
    23: ('COLOR_INFOTEXT',),
    24: ('COLOR_INFOBK',),
   #25: N/A
    26: ('COLOR_HOTLIGHT',),
    27: ('COLOR_GRADIENTACTIVECAPTION',),
    28: ('COLOR_GRADIENTINACTIVECAPTION',),
    29: ('COLOR_MENUHILIGHT',),
    30: ('COLOR_MENUBAR',),
}

# 21+: Win95/NT4+, 26+: Win2000+, 29+: WinXP+


for i in range(max(defines.keys()) + 1):
    clr = win32api.GetSysColor(i)
    names = defines[i][:2] if i in defines else ('(not defined)',)
    r, g, b = clr&0xff, (clr>>8)&0xff, (clr>>16)&0xff
    print('%2d: 0x%06x (%3d,%3d,%3d) %s' % (i, clr, r, g, b, ', '.join(names)))
    