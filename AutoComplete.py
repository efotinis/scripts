# 2008.07.17  created
# 2008.07.24  simplified getTokenForCompletion by using CmdLineUtils.tokenize

import win32console as wc
import win32con as co
import win32api as api
import msvcrt as ms
import re
from CmdLineUtils import tokenize as tokenizeCmdLine


##cin = wc.GetStdHandle(wc.STD_INPUT_HANDLE)
##cout = wc.GetStdHandle(wc.STD_OUTPUT_HANDLE)
gaks = api.GetAsyncKeyState


UP    = '\xe0H'
DOWN  = '\xe0P'
LEFT  = '\xe0K'
RIGHT = '\xe0M'

CTRLUP    = '\xe0\x8d'
CTRLDOWN  = '\xe0\x91'
CTRLLEFT  = '\xe0s'
CTRLRIGHT = '\xe0t'

ESC = '\x1b'
TAB = '\t'
ENTER = '\r'
CTRLENTER = '\n'
BASKSPACE = '\x08'
DEL = '\xe0S'
INS = '\xe0R'
HOME = '\xe0G'
END = '\xe0O'
PGUP = '\xe0I'
PGDN = '\xe0Q'


def isPressed(vk):
    return bool(gaks(vk) & 0x8000)


def wasPressed(vk):
    return bool(gaks(vk) & 0x1)


def inkey():
    s = ms.getch()
    if s in '\x00\xe0':
            s += ms.getch()
    return s


def keyloop():
    while True:
        s = inkey()
        if s == ESC:
            break
        print repr(s)


class ConsoleBuffer:
    '''Console buffer utilities.'''

    def __init__(self):
        self.obj = wc.GetStdHandle(wc.STD_OUTPUT_HANDLE)

    def getCursor(self):
        coords = self.obj.GetConsoleScreenBufferInfo()['CursorPosition']
        return coords.X, coords.Y

    def setCursor(self, x, y):        
        self.obj.SetConsoleCursorPosition(wc.PyCOORDType(x, y))

    def write(self, s):
        self.obj.WriteConsole(s)

    def getSize(self):
        coords = self.obj.GetConsoleScreenBufferInfo()['Size']
        return coords.X, coords.Y

    def setCursorInfo(self, size, visible):
        self.obj.SetConsoleCursorInfo(size, visible)


class Manager:

    def __init__(self):
        self.history = []               # command history
        self.completer = None           # autocomplete candidate func
        self.cout = ConsoleBuffer()     # STDOUT

    def input(self, prompt=''):
        if prompt:
            self.cout.write(prompt)
        return _Input(self.cout).readline(self.completer)


class _Input:
    '''Used by Manager. One readline() call per object.'''

    def __init__(self, cout):
        self.cout = cout            # STDOUT
        self.line = ''              # edited line
        self.pos = 0                # cursor pos
        self.insert = True          # insert mode
        self.candidates = None      # autocomplete candidates
        self.candIndex = 0          # autocomplete index
        self.completionPos = 0      # autocomplete begin pos
        self.cursPos = self.cout.getCursor()  # input start coords

    def updateText(self, charsDel=0):
        '''Redisplay whole text, deleting any trailing old chars if > 0.'''
        self.cout.setCursor(*self.cursPos)
        self.cout.write(self.line)
        if charsDel > 0:
            self.cout.write(' ' * charsDel)
        self.updateCursor()

    def updateCursor(self):
        '''Reposition cursor to current position.'''
        x, y = self.cursPos
        width = self.cout.getSize()[0]
        x += self.pos
        while x >= width:
            x -= width
            y += 1
        self.cout.setCursor(x, y)

    def readline(self, completerFunc=None):
        while True:
            s = inkey()
            if len(s) == 1 and ord(s) >= 32:
                if self.insert:
                    self.line = self.line[:self.pos] + s + self.line[self.pos:]
                else:
                    self.line = self.line[:self.pos] + s + self.line[self.pos+1:]
                self.pos += 1
                self.updateText()
                self.candidates = None
            elif s == LEFT:
                if self.pos > 0:
                    self.pos -= 1
                    self.updateCursor()
            elif s == RIGHT:
                if self.pos < len(self.line):
                    self.pos += 1
                    self.updateCursor()
            elif s == TAB:
                self.handleTab(completerFunc)
            elif s == ENTER:
                self.pos = len(self.line)
                self.updateCursor()
                print
                return self.line
            elif s == BASKSPACE:
                if self.pos > 0:
                    self.pos -= 1
                    self.line = self.line[:self.pos] + self.line[self.pos+1:]
                    self.updateText(1)
                    self.candidates = None
            elif s == DEL:
                if self.pos < len(self.line):
                    self.line = self.line[:self.pos] + self.line[self.pos+1:]
                    self.updateText(1)
                    self.candidates = None
            elif s == INS:
                self.insert = not self.insert
                cout.setCursorInfo(20 if insert else 50, 1)
            elif s == HOME:
                self.pos = 0
                self.updateCursor()
            elif s == END:
                self.pos = len(self.line)
                self.updateCursor()
            elif s == ESC:
                oldLen = len(self.line)
                self.line = ''
                self.pos = 0
                self.updateText(oldLen)

    def handleTab(self, completerFunc):
        shift = isPressed(co.VK_SHIFT)
        if self.pos == len(self.line) and self.candidates is not None:
            pass  # keep current candidates
        else:
            self.completionPos, seed = self.getTokenForCompletion()
            self.candidates = completerFunc(seed)
            self.candIndex = 0
        if not self.candidates:
            #cout.WriteConsole('\a')
            api.MessageBeep(-1)
        else:
            if shift:
                self.candIndex -= 1
                if self.candIndex < 0:
                    self.candIndex = len(self.candidates) - 1
                s = self.candidates[self.candIndex]
            else:
                s = self.candidates[self.candIndex]
                self.candIndex += 1
                if self.candIndex >= len(self.candidates):
                    self.candIndex = 0
            if ' ' in s:
                s = '"' + s + '"'
            oldLineLen = len(self.line)
            self.line = self.line[:self.completionPos] + s
            self.pos = len(self.line)
            self.updateText(oldLineLen - len(self.line))

    def getTokenForCompletion(self):
        s = self.line[:self.pos]  # ignore anything past the cursor
        for beg, end, token in tokenizeCmdLine(s):
            if beg <= self.pos <= end:
                return beg, token
        else:
            return self.pos, ''
