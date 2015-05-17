"""Add date stamp to image names matching videos."""

import os
import sys
import time
import efutil


def get_matching_path(path):
    """Find a path in the same dir that only differs in the extension."""
    dirpath, name = os.path.split(path)
    items = [os.path.normcase(s) for s in os.listdir(dirpath)]
    name = os.path.normcase(name)
    stem = os.path.splitext(name)[0]
    for s in items:
        if s == name:
            continue  # don't match the same item
        if os.path.splitext(s)[0] == stem:
            return os.path.join(dirpath, s)
    else:
        raise ValueError('no matching path')


##def get_input_images():
##    fnames = os.listdir(u'.')
##    for s in fnames:
##        if os.path.splitext(s)[1].lower() in ('.jpg', '.jpeg')]:
##            yield s


def get_input_images(a):
    for s in a:
        if os.path.isdir(s):
            for name in os.listdir(s):
                if os.path.splitext(name)[1].lower() == '.jpg':
                    yield os.path.join(s, name)
        else:
            yield os.path.splitext(s)[0] + '.jpg'


if __name__ == '__main__':

    for image in get_input_images(sys.argv[1:]):
        try:
            print '*** img:', image
            video = get_matching_path(image)
            print '*** vid:', video
        except ValueError:
            efutil.conerr('could not find match for "%s"' % image)
            continue
        date = time.strftime('[%Y-%m-%d]',
                             time.gmtime(os.path.getmtime(video)))
        stem, ext = os.path.splitext(image)
        newname = stem + ' ' + date + ext
        os.rename(image, newname)
