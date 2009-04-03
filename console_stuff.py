# 2007.06.23  created
# 2008.03.20  added SamePosOutputTry

# BUG: SamePosOutput loses track of current pos when scrolling occurs...

import win32console
import win32con
import win32file


##GetConsoleScreenBufferInfo:
##    MaximumWindowSize = PyCOORDType
##    CursorPosition = PyCOORDType
##    Window = PySMALL_RECTType
##    Attributes = n
##    Size = PyCOORDType


def iscon(h=None):
    """Check if a handle (def=STDOUT) is a console (and not a pipe,file,etc).
    Most of this module's functions only work when iscon() returns True."""
    if h is None:
        h = win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)
    return win32file.GetFileType(h) == win32con.FILE_TYPE_CHAR


class SamePosOutput:
    def __init__(self):
        self.h = win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)
        self.pos = self.h.GetConsoleScreenBufferInfo()['CursorPosition']
    def restore(self, clearToEol=False):
        self.h.SetConsoleCursorPosition(self.pos)
        if clearToEol:
            info = self.h.GetConsoleScreenBufferInfo()
            lenToEol = info['MaximumWindowSize'].X - self.pos.X
            self.h.FillConsoleOutputAttribute(info['Attributes'],
                                              lenToEol, self.pos)
            self.h.FillConsoleOutputCharacter(u' ',
                                              lenToEol, self.pos)


class SamePosOutputTry:
    """Similar to SamePosOutput, but ignores exceptions."""
    def __init__(self):
        try:
            self.h = win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)
            self.pos = self.h.GetConsoleScreenBufferInfo()['CursorPosition']
        except win32console.error:
            self.h = win32file.INVALID_HANDLE_VALUE
    def restore(self, clearToEol=False):
        if self.h == win32file.INVALID_HANDLE_VALUE:
            return
        self.h.SetConsoleCursorPosition(self.pos)
        if clearToEol:
            info = self.h.GetConsoleScreenBufferInfo()
            lenToEol = info['MaximumWindowSize'].X - self.pos.X
            self.h.FillConsoleOutputAttribute(info['Attributes'],
                                              lenToEol, self.pos)
            self.h.FillConsoleOutputCharacter(u' ',
                                              lenToEol, self.pos)


def cls():
    h = win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)
    bufInfo = h.GetConsoleScreenBufferInfo()
##    for s in bufInfo.keys():
##        print s, bufInfo[s]

    SmRect = win32console.PySMALL_RECTType
    Coord = win32console.PyCOORDType
    
    size = bufInfo['Size']
    src  = SmRect(0, 0, size.X-1, size.Y-1)
    dst  = Coord(0, -size.Y)
    attr = bufInfo['Attributes']
    h.ScrollConsoleScreenBuffer(src, None, dst, u' ', attr)

    wnd  = bufInfo['Window']
    view = SmRect(0, 0, wnd.Right-wnd.Left, wnd.Bottom-wnd.Top)
    h.SetConsoleWindowInfo(True, view)

    h.SetConsoleCursorPosition(Coord(0, 0))


if __name__ == '__main__':
    if not iscon():
        print 'STDOUT is not a console'
    else:
##        import win32api
##        print 'time for a test:',
##        spo = SamePosOutput()
##        for i in range(1,11):
##            spo.restore()
##            print 1.0/i,
##            win32api.Sleep(200)
##        spo.restore(True)
##        print 'ok!'
        cls()
