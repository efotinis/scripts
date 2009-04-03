# 2008.02.12  created
# 2008.07.12  modified
# 2008.09.12  better extensibility via Program base class; refactoring;
#             modified PyWin layout for widescreen displays :D

import ctypes
import win32api, win32gui, win32con, win32process
import WinUtil


class Program:
    """Base program handling class."""
    def test(self, wnd):
        """Test whether wnd belongs to program."""
        return False
    def arrange(self, wnd):
        """Arrange program using wnd passed to previous test()."""
        pass


class Gimp(Program):

    MAINWND_TITLE = 'GNU Image Manipulation Program'
    TOPLEVEL_WNDCLS = 'gdkWindowToplevel'

    def __init__(self):
        # get Gimp's PID, if running
        try:
            mainwnd = win32gui.FindWindow(self.TOPLEVEL_WNDCLS, self.MAINWND_TITLE)
        except win32api.error:
            mainwnd = 0
        self.pid = WinUtil.getWndProcId(mainwnd) if mainwnd else 0

    def test(self, wnd):
        return self.pid and WinUtil.getWndProcId(wnd) == self.pid

    def arrange(self, wnd):
        # TODO: this comment block needs updating
        #############################
        # Since all GTK child windows have the same class and title
        # ('gdkWindowChild', 'The GIMP' &%^@!!...), we get the process ID
        # of the main Gimp window and use it to figure out which top level
        # GTK windows belong to Gimp.
        #
        # I guess I could've used a regexp on the titles, but that's a bit risky.
        # And besides that, the titles are user configurable anyway...
        #############################

        # get visible, top-level windows belonging to the Gimp process
        gimpWnds = [w for w in WinUtil.genDesktopWnds(self.TOPLEVEL_WNDCLS)
                    if win32gui.IsWindowVisible(w) # ignore hidden ones
                    and WinUtil.getWndProcId(w) == self.pid]
        #print [hex(w) for w in gimpWnds]
        
        # find the two main dock windows
        leftWnd, rightWnd = 0, 0
        for w in gimpWnds[:]:  # we'll modify the original
            s = win32gui.GetWindowText(w)
            if s == 'Toolbox':
                leftWnd = w
                gimpWnds.remove(w)
            elif s.startswith('Layers, Channels, '):  # ugh...
                rightWnd = w
                gimpWnds.remove(w)

        # resize the windows to their respective client widths
        # and make them as tall as the workarea
        
        leftClientW = 200
        rightClientW = 204
        wa = WinUtil.getWorkarea()
        INFINITE_HEIGHT = 0x7fff  # user32 coords are 16-bit signed

        rc = WinUtil.RECT((0, 0, leftClientW, INFINITE_HEIGHT))
        rc = WinUtil.adjustWndRect(rc, leftWnd)
        rc.offset(-rc.left, -rc.top)
        rc.bottom = wa.bottom
        WinUtil.moveWnd(leftWnd, rc)

        rc = WinUtil.RECT((0, 0, rightClientW, INFINITE_HEIGHT))
        rc = WinUtil.adjustWndRect(rc, rightWnd)
        rc.offset(wa.width() - rc.right, -rc.top)
        rc.bottom = wa.bottom
        WinUtil.moveWnd(rightWnd, rc)

        # leave the rest of Gimp's windows
        # (image views, dialog, etc) intact


def getScreenRatio():
    """Return default monitor's video mode aspect ratio."""
    try:
        x = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        y = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        return float(x) / y
    except win32api.error:
        return 4.0 / 3


def getCascadeDelta():
    """Cascaded windows offset (system frame + caption)."""
    return (win32api.GetSystemMetrics(win32con.SM_CYFRAME) +
             win32api.GetSystemMetrics(win32con.SM_CYCAPTION))


def cascadeWnds(wnds, rc):
    """Cascade windows into specified rect."""
    if not wnds:
        return
    rc = WinUtil.RECT(rc)  # make local copy
    delta = getCascadeDelta()
    offset = delta * (len(wnds) - 1)
    rc.right -= offset
    rc.bottom -= offset
    for w in wnds:
        WinUtil.moveWnd(w, rc)
        rc.offset(delta, delta)



class PyWin(Program):

    def test(self, wnd):
        wnd = WinUtil.getTopOwnerWnd(wnd)
        title = win32gui.GetWindowText(wnd)
        wndcls = win32gui.GetClassName(wnd)
        return title.startswith('PythonWin') and wndcls.startswith('Afx:')

    def arrange(self, wnd):
        # find MDI client and its children
        mainWnd = WinUtil.getTopOwnerWnd(wnd)
        mdiWnd = win32gui.FindWindowEx(mainWnd, 0, 'MDIClient', None)
        if not mdiWnd:
            return
        childMdis = list(WinUtil.genChildWnds(mdiWnd))

        # find interactive wnd and remove it from children list
        interactiveWin = 0
        for w in childMdis[:]:
            if win32gui.GetWindowText(w) == 'Interactive Window':
                interactiveWin = w
                childMdis.remove(interactiveWin)
                break

        if getScreenRatio() < 1.6:
            # narrow display: use a fixed predefined width,
            # make interactive window 4:3 (at top-left)
            # and cascade code windows using the full mdi client height

            # enough for ~80 chars (using 9pt Lucida Console)
            CHILD_WIDTH = 640

            # move interactive wnd
            if interactiveWin:
                win32gui.MoveWindow(interactiveWin, 0, 0,
                                    CHILD_WIDTH, int(CHILD_WIDTH*0.75), True)

            # cascade the rest
            if childMdis:
                rc = WinUtil.RECT(win32gui.GetClientRect(mdiWnd))
                delta = getCascadeDelta()
                offset = delta * (len(childMdis) - 1)
                rc.left = rc.right - (offset + CHILD_WIDTH)
                cascadeWnds(childMdis, rc)

        else:
            # wide display:
            # interactive window on the left;
            # cascaded code windows on the right

            mdiClientRect = WinUtil.RECT(win32gui.GetClientRect(mdiWnd))
            INVERSE_GOLDEN_RATIO = 0.618
            interactiveWinWidth = int(mdiClientRect.width() * (1 - INVERSE_GOLDEN_RATIO))

            if interactiveWin:
                rc = WinUtil.RECT(mdiClientRect)
                rc.right = rc.left + interactiveWinWidth
                WinUtil.moveWnd(interactiveWin, rc)
        
            if childMdis:
                rc = WinUtil.RECT(mdiClientRect)
                rc.left = rc.left + interactiveWinWidth
                cascadeWnds(childMdis, rc)



curWnd = win32gui.GetForegroundWindow()
programHandlers = (Gimp(), PyWin())

for prog in programHandlers:
    if prog.test(curWnd):
        prog.arrange(curWnd)
        break
else:
    win32api.MessageBeep(-1)
