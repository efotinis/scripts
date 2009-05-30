import win32api
import win32gui
import win32con


def findWnd(cls, txt=None):
    try:
        return win32gui.FindWindow(cls, txt)
    except:
        return 0


def shellExec(doc, show):    
    try:
        win32api.ShellExecute(0, None, doc, None, None, show)
        return True
    except:
        return False


def closeWnd(wnd):    
    print win32gui.SendMessage(wnd, win32con.WM_CLOSE, 0, 0)


def msg(s):
    win32api.MessageBox(0, s, 0, 0)    


def sleep(msec):
    win32api.Sleep(200)
    

def main():
    dgVoodooWnd = findWnd('DGVOODOODLGCLASS')
    if not dgVoodooWnd:
        if not shellExec('C:\\TOMBRAID\\NOVDD.LNK', win32con.SW_SHOWMINIMIZED):
            msg('Could not start DGVOODOO')
            return
        sleep(200)
        dgVoodooWnd = findWnd('DGVOODOODLGCLASS')

    if not shellExec('C:\\TOMBRAID\\tomb.vlp', win32con.SW_SHOWNORMAL):
        msg('Could not start TOMBRAIDER')

##    if dgVoodooWnd:
##        closeWnd(dgVoodooWnd)


main()


##
##-mount
##allows mounting images from command line (or shortcut).
##Syntax is: -mount <n>,<path>
##where 'n' means DVD-ROM device number ('0' - '3' allowed) and 'path' is the full path to the image file. 
##Example: daemon.exe -mount 0,"c:\My Images\nameofimage.cue".
##Do not forget to set the path in quotes if it contains spaces! 
##
##-unmount
##allows unmounting images from command line.
##Syntax is: -unmount <n>
##where 'n' means DVD-ROM device number ('0' - '3' allowed) 
##


#shellExec('"C:\\Program Files\\DAEMON Tools\\daemon.exe" ', win32con.SW_SHOWNORMAL)