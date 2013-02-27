"""PythonWin utilities."""

import subprocess
import win32api


def launch_new_instance():
    """Launch another PythonWin instance.

    Can be added to the Tools menu (View > Options > Tools Menu).
    """
    path = win32api.GetModuleFileNameW(None)
    subprocess.Popen([path, '/new'])
