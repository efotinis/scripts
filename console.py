import win32console


def coord2rc(coord):
    """Convert PyCOORD to row/col pair."""
    return coord.Y, coord.X

def rc2coord(r, c):
    """Convert row/col pair to PyCOORD."""
    return win32console.PyCOORDType(c, r)

def smrc2tlbr(rc):
    """Convert PySMALL_RECT to top,left,bottom,right."""
    return rc.Top, rc.Left, rc.Bottom, rc.Right

def tlbr2smrc(top,left,bottom,right):
    """Convert top,left,bottom,right to PySMALL_RECT."""
    return win32console.PySMALL_RECTType(left, top, right, bottom)


def create_screen_buffer(access, sharing, security, flags):
    return ScreenBuffer(win32console.CreateConsoleScreenBuffer(access, sharing, security, flags))


class ScreenBuffer(object):

    def __init__(self, obj):
        self.buf = obj

    def getmode(self):
        return self.buf.GetConsoleMode()
    def setmode(self, mode):
        self.buf.SetConsoleMode(mode)

    def setactive(self):
        self.buf.SetConsoleActiveScreenBuffer()

    def getmaxwindow(self):
        return coord2rc(self.buf.GetLargestConsoleWindowSize())

    def getsize(self):
        return coord2rc(self.buf.GetConsoleScreenBufferInfo()['Size'])
    def setsize(self, rows, cols):
        self.buf.SetConsoleScreenBufferSize(rc2coord(rows, cols))

    def getwindow(self):
        return smrc2tlbr(self.buf.GetConsoleScreenBufferInfo()['Window'])
    def setwindow(self, top, left, bottom, right, relative=False):
        self.buf.SetConsoleWindowInfo(not relative, tlbr2smrc(top, left, bottom, right))

    def getcursorinfo(self):
        return self.buf.GetConsoleCursorInfo()
    def setcursorinfo(self, size, visible):
        self.buf.SetConsoleCursorInfo(size, visible)

    def getcursorpos(self):
        return coord2rc(self.buf.GetConsoleScreenBufferInfo()['CursorPosition'])
    def setcursorpos(self, row, col):
        self.buf.SetConsoleCursorPosition(rc2coord(row, col))
    
    def gettextattr(self):
        return self.buf.GetConsoleScreenBufferInfo()['Attributes']
    def settextattr(self, attr):
        self.buf.SetConsoleTextAttribute(attr)


    def readchar(self, row, col, count):
        return self.buf.ReadConsoleOutputCharacter(count, rc2coord(row, col))
    def readattr(self, row, col, count):
        return self.buf.ReadConsoleOutputAtribute(count, rc2coord(row, col))

    def writechar(self, row, col, char):
        self.buf.WriteConsoleOutputCharacter(char, rc2coord(row, col))
    def writeattr(self, row, col, attr):
        self.buf.WriteConsoleOutputAttribute(attr, rc2coord(row, col))

    def fillchar(self, row, col, count, char):
        self.buf.FillConsoleOutputCharacter(char, count, rc2coord(row, col))
    def fillattr(self, row, col, count, attr):
        self.buf.FillConsoleOutputAttribute(attr, count, rc2coord(row, col))


    def write(self, s):
        self.buf.WriteConsole(s)

    def scroll(self, rect, clip, dest, fillchar, fillattr):
        self.buf.ScrollConsoleScreenBuffer(
            tlbr2smrc(*rect),
            tlbr2smrc(*clip) if clip else None,
            rc2coord(*dest),
            fillchar,
            fillattr)


class InputBuffer(object):

    def __init__(self, obj):
        self.buf = obj

    def readinput(self, count):
        return self.buf.ReadConsoleInput(count)


##stdin = InputBuffer(win32console.GetStdHandle(win32console.STD_INPUT_HANDLE))
##stdout = ScreenBuffer(win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE))
##stderr = ScreenBuffer(win32console.GetStdHandle(win32console.STD_ERROR_HANDLE))


def get_stdin():
    return InputBuffer(win32console.GetStdHandle(win32console.STD_INPUT_HANDLE))

def get_stdout():
    return ScreenBuffer(win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE))

def get_stderr():
    return ScreenBuffer(win32console.GetStdHandle(win32console.STD_ERROR_HANDLE))



##def inputtest():
##    """Display input events in a loop; exit with Ctrl-C."""
##    ENABLE_WINDOW_INPUT = 0x0008
##    stdin = get_stdin()
##    stdin.SetConsoleMode(stdin.GetConsoleMode() | ENABLE_WINDOW_INPUT)
##    try:
##        while True:
##            inp = stdin.ReadConsoleInput(1)[0]
##            if inp.EventType == win32console.FOCUS_EVENT:
##                print 'FOCUS: SetFocus=%s' % inp.SetFocus
##            elif inp.EventType == win32console.KEY_EVENT:
##                print 'KEY: Down=%s, Repeat:%s, Vk:%s, Scan:%s, Char:%s, CtrlKey:%s' % (
##                    inp.KeyDown, inp.RepeatCount, inp.VirtualKeyCode,
##                    inp.VirtualScanCode, ord(inp.Char), inp.ControlKeyState)
##            elif inp.EventType == win32console.MENU_EVENT:
##                print 'MENU: CmdId=%s' % inp.CommandId
##            elif inp.EventType == win32console.MOUSE_EVENT:
##                print 'MOUSE: Pos=%s, Btns=%s, CtrlKey=%s, Flags=%s' % (
##                    inp.MousePosition, inp.ButtonState, inp.ControlKeyState, inp.EventFlags)
##            elif inp.EventType == win32console.WINDOW_BUFFER_SIZE_EVENT:
##                print 'BUFFER: Size=%s' % inp.Size
##            else:
##                print dir(inp)
##    except KeyboardInterrupt:
##        return
##    
