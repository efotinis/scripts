from win32com.shell import shell, shellcon


def move_items(dest, paths):
    wnd = 0
    op = shellcon.FO_MOVE
    src = '\0'.join(paths)
    flags = shellcon.FOF_ALLOWUNDO
    failed, any_aborted = shell.SHFileOperation((wnd, op, src, dest, flags))
