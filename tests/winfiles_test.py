import os
import uuid
import unittest

import winfiles


# FIXME: there may be some race conditions, since the tests are run on
#   the user's HOME dir; we should use a temporary dir instead

# TODO: test get_info()
# TODO: test date conversions (use known values)
# TODO: test walk()


class TestFind(unittest.TestCase):
    DIRPATH = os.path.expanduser('~')
    DIRPATH_NON_EXISTING = os.path.join(DIRPATH, str(uuid.uuid4()))
    MASK = os.path.join(DIRPATH, '*')
    ITEMS_NO_DOTS = list(winfiles.find(MASK, times='unix'))
    ITEMS_WITH_DOTS = list(winfiles.find(MASK, dots=True, times='unix'))
    LD_ITEMS = os.listdir(DIRPATH)

    def test_names(self):
        self.assertEqual(
            sorted(item.name for item in self.ITEMS_NO_DOTS),
            sorted(self.LD_ITEMS))

    def test_times(self):
        for item in self.ITEMS_NO_DOTS:
            path = os.path.join(self.DIRPATH, item.name)
            self.assertAlmostEqual(item.create, os.path.getctime(path), delta=0.001)
            self.assertAlmostEqual(item.modify, os.path.getmtime(path), delta=0.001)

    def test_dots(self):
        names_no_dots = [item.name for item in self.ITEMS_NO_DOTS]
        names_with_dots = [item.name for item in self.ITEMS_WITH_DOTS]
        self.assertNotIn('.', names_no_dots)
        self.assertNotIn('..', names_no_dots)
        self.assertIn('.', names_with_dots)
        self.assertIn('..', names_with_dots)

    def test_missing_path(self):
        with self.assertRaises(WindowsError):
            a = list(winfiles.find(self.DIRPATH_NON_EXISTING))


if __name__ == '__main__':
    unittest.main()
