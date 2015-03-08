import os
import subprocess
import time
import tempfile
import unittest

import win32api
import win32con

import shellutil


# TODO: SpecialFolders, delete_items, recycle_items, move_items


def normalize_path(s):
    return os.path.normcase(os.path.normpath(s))


class TestOpenDirWindows(unittest.TestCase):

    def test_existing(self):
        shellutil.get_open_explorer_directories()

    def test_new(self):
        TESTDIR = normalize_path(os.path.expanduser('~'))
        a = list(shellutil.get_open_explorer_directories())
        self.assertNotIn(TESTDIR, [normalize_path(path) for hwnd,path in a],
            'Explorer directory "%s" must be closed before this test' % TESTDIR)

        # open the user's home directory
        explorer_path = os.path.expandvars('%SystemRoot%\\system32\\explorer.exe')
        subprocess.call([explorer_path, TESTDIR])
        time.sleep(2)  # wait for the window to open

        a = list(shellutil.get_open_explorer_directories())
        self.assertIn(TESTDIR, [normalize_path(path) for hwnd,path in a])

        # close the previously opened window
        for hwnd, path in a:
            if normalize_path(path) == TESTDIR:
                win32api.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                break


def normalize_link_info_for_compare(d):
    return {
        'target':normalize_path(d['target']),
        'args':d['args'],
        'cwd':normalize_path(d['cwd']),
        'hotkey':sorted(d['hotkey'].split('+')),
        'wstyle':d['wstyle'],
        'comment':d['comment'],
        'icon':normalize_path(d['icon'])}


class TestShurtcuts(unittest.TestCase):

    LINKPATH = tempfile.mktemp(suffix='.lnk')

    def tearDown(self):
        try:
            os.unlink(self.LINKPATH)
        except OSError:
            pass

    def test_save_and_load(self):

        params = dict(
            target=tempfile.mktemp(),
            args='-a -b -c',
            cwd=os.path.expanduser('~'),
            hotkey='Ctrl+Alt+E',
            wstyle='max',
            comment='foo',
            icon=tempfile.mktemp() + ',1')

        # create
        shellutil.create_shortcut(self.LINKPATH, **params)

        # load
        d = shellutil.load_shortcut(self.LINKPATH)
        self.assertDictEqual(
            normalize_link_info_for_compare(params),
            normalize_link_info_for_compare(d))

        # update
        params['args'] = 'new args'
        shellutil.create_shortcut(self.LINKPATH, args=params['args'], update=True)
        d = shellutil.load_shortcut(self.LINKPATH)
        self.assertDictEqual(
            normalize_link_info_for_compare(params),
            normalize_link_info_for_compare(d))


if __name__ == '__main__':
    unittest.main()

