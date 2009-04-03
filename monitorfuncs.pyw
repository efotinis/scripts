import sys, win32api, win32gui, win32con

WAIT_MSEC = 2000
OPTIONS = {
    'screensave':(win32con.SC_SCREENSAVE, 0),
    'standby':(win32con.SC_MONITORPOWER, 1),
    'off':(win32con.SC_MONITORPOWER, 2)
    }

def main(args):
    if (len(args) <> 1 or args[0].lower() not in OPTIONS):
        msgbox('Invalid parameter. Must be one of: ' + ', '.join(sorted(OPTIONS.keys())))
        return
    wnd = win32gui.GetForegroundWindow()
    msg = win32con.WM_SYSCOMMAND
    wp, lp = OPTIONS[args[0].lower()]
    if wp == win32con.SC_SCREENSAVE and not win32gui.SystemParametersInfo(win32con.SPI_GETSCREENSAVEACTIVE):
        msgbox('No screensaver is currently set.')
        return
    win32api.Sleep(WAIT_MSEC)
    win32api.PostMessage(wnd, msg, wp, lp)

def msgbox(s):
    win32api.MessageBox(0, s)

main(sys.argv[1:])
