import win32console
import win32con
import win32file

# BUG: SamePosOutput loses track of current pos when scrolling occurs...


##GetConsoleScreenBufferInfo:
##    MaximumWindowSize = PyCOORDType
##    CursorPosition = PyCOORDType
##    Window = PySMALL_RECTType
##    Attributes = n
##    Size = PyCOORDType


def iscon(h=None):
    """Check if a handle (def=STDOUT) is a console (and not a pipe,file,etc).
    Most of this module's functions only work when iscon() returns True.
    """
    if h is None:
        h = win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)
    return win32file.GetFileType(h) == win32con.FILE_TYPE_CHAR


class SamePosOutput:
    """Fixed position output, e.g. for running status messages.
    If fallback is true, console errors are ignored
    (useful when stdout is not a console buffer.)
    """

    def __init__(self, fallback=False):
        self.fallback = fallback
        self.reset()

    def restore(self, eolclear=False):
        """Restore saved position. Optionally clear to end-of-line."""
        if self.h == win32file.INVALID_HANDLE_VALUE:
            return
        self.h.SetConsoleCursorPosition(self.pos)
        if eolclear:
            info = self.h.GetConsoleScreenBufferInfo()
            lenToEol = info['MaximumWindowSize'].X - self.pos.X
            self.h.FillConsoleOutputAttribute(info['Attributes'],
                                              lenToEol, self.pos)
            self.h.FillConsoleOutputCharacter(u' ',
                                              lenToEol, self.pos)

    def reset(self):
        """Save current position."""
        try:
            self.h = win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)
            self.pos = self.h.GetConsoleScreenBufferInfo()['CursorPosition']
        except win32console.error:
            if not self.fallback:
                raise
            self.h = win32file.INVALID_HANDLE_VALUE


class SamePosOutputTry(SamePosOutput):
    """Deprecated; use SamePosOutput(fallback=True)."""
    def __init__(self):
        SamePosOutput.__init__(self, fallback=True)


def cls():
    """Clear output console buffer and move to top-left."""
    h = win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)
    bufInfo = h.GetConsoleScreenBufferInfo()

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


def consolesize():
    """Rows and columns of output console."""
    h = win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)
    size = h.GetConsoleScreenBufferInfo()['Size']
    return size.Y, size.X


def set_full_width(buffer, columns):
    """Set console buffer width and fit window width to it if possible."""

    info = buffer.GetConsoleScreenBufferInfo()
    buffer_size = info['Size']
    original_window_rect = info['Window']

    w = min(columns, buffer.GetLargestConsoleWindowSize().X)
    h = original_window_rect.Bottom - original_window_rect.Top + 1
    new_window_rect = win32console.PySMALL_RECTType(0, 0, w - 1, h - 1)

    # NOTE: the minimum depends on system metrics and if exceeded will cause
    # the API to fail; the maximum is automatically capped without error at
    # a value that depends on the total buffer size (width * height)
    new_buffer_size = win32console.PyCOORDType(columns, buffer_size.Y)

    try:
        if columns < buffer_size.X:
            buffer.SetConsoleWindowInfo(True, new_window_rect)
            buffer.SetConsoleScreenBufferSize(new_buffer_size)
        else:
            buffer.SetConsoleScreenBufferSize(new_buffer_size)
            buffer.SetConsoleWindowInfo(True, new_window_rect)
    except win32console.error:
        buffer.SetConsoleWindowInfo(True, original_window_rect)
        raise


if __name__ == '__main__':
    import sys
    if not iscon():
        sys.exit('STDOUT is not a console')
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
