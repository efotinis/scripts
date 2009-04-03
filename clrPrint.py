import sys
import re
import win32api
import win32console


cout = win32console.GetStdHandle(win32api.STD_OUTPUT_HANDLE)
oldAttr = cout.GetConsoleScreenBufferInfo()['Attributes']


def showHelp():
    print """Prints text with colors.
(C) Elias Fotinis 2007.03.03

CLRPRINT [/N] text [...]

  /N    Prevents printing of a trailing newline.
  text  The item(s) to print. Multiple items are not separated with whitespace.
        Use quotes with embedded spaces instead.
        
        Text can have embedded color specifiers, which set the console's output
        color. The color specifier format is:

          { [foreColor] [,backColor] }

        where:
          foreColor is the foreground color and
          backColor is the background color

        Both colors are optional and will default to the current values.
        Each can be in the range 0-15 (in decimal or hexadecimal).
        Special colors:
          CFG  current foreground
          CBG  current background
          OFG  original foreground
          OBG  original background
            
        Two special, shortcur specifiers are also available:
          {i}  Invert current colors (same as {CBG,CFG}).
          {r}  Restore original colors (same as {OFG,OBG})."""


def main(args):
    if '/?' in args:
        showHelp()
        return 0
    noNewline = False
    if '/n' in args or '/N' in args:
        noNewline = True
        args = [s for s in args if s.upper() <> '/N']
    rx = re.compile(r'(?:\{.*?\})|(?:[^{]*)', re.I)
    for s in args:
        l = rx.findall(s)
        for i, part in enumerate(l):
            if part.startswith('{') and part.endswith('}'):
                applyFormat(part[1:-1])
            else:
                sys.stdout.write(part)
    if not noNewline:
        sys.stdout.write('\n')
    return 0


def splitAttr(attr):
    return attr & 0xF, (attr >> 4) & 0xF
def joinAttr(fore, back):
    return fore | (back << 4)


def applyFormat(s):
    s = re.sub(r'\s+', '', s).upper()
    if s == 'R':
        # reset original
        cout.SetConsoleTextAttribute(oldAttr)
    elif s == 'I':
        # invert current
        attr = cout.GetConsoleScreenBufferInfo()['Attributes']
        f, b = splitAttr(attr)
        cout.SetConsoleTextAttribute(joinAttr(b, f))
    else:
        a = s.split(',', 1)
        while len(a) < 2:
            a.append('')
        s1, s2 = a
        attr = cout.GetConsoleScreenBufferInfo()['Attributes']
        curFG, curBG = splitAttr(attr)
        orgFG, orgBG = splitAttr(oldAttr)
        d = {'CFG':curFG, 'CBG':curBG, 'OFG':orgFG, 'OBG':orgBG}
        for n in range(16):
            d[str(n)] = n
            d[hex(n)] = n
        f = getDictDef(d, s1, curFG)
        b = getDictDef(d, s2, curBG)
        cout.SetConsoleTextAttribute(joinAttr(f, b))


def getDictDef(d, key, default):
    if key in d:
        return d[key]
    else:
        return default

    
sys.exit(main(sys.argv[1:]))
