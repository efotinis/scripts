# 2006/02/21  Created.
# 2007/03/08  Modified.

import os, hashlib, shutil, collections


def getmultiples(items):
    """Return all items of length >= 2 from a sequence or iterator."""
    return (x for x in items if len(x) >= 2)


def filesig(path):
    """MD5 hash of a file's contents."""
    return hashlib.md5(file(path, 'rb').read()).digest()


def dirfiles(rootdir, recurse=False):
    """Generate the paths of all files in a dir."""
    if recurse:
        for dpath, dirs, files in os.walk(rootdir):
            for fname in files:
                yield os.path.join(dpath, fname)
    else:
        for s in os.listdir(dirspec):
            path = os.path.join(dirspec, s)
            if not os.path.isdir(path):
                yield path


def finddups(files):
    sizeMap = collections.defaultdict(list)
    for s in files:
        sizeMap[os.path.getsize(s)] += [s]
    sizeGroups = getmultiples(sizeMap.itervalues())
    for group in sizeGroups:
        sigMap = collections.defaultdict(list)
        for spec in group:
            sig = filesig(spec)
            sigMap[sig] += [spec]
        for group in getmultiples(sigMap.itervalues()):
            yield group


##dir = u'F:\\docs\\internet\\----'
##finddups(dirfiles(dir, recurse=True))

##dir1 = u'F:\\docs\\internet\\----\\_mail & usenet archive -- recovered data --\\TEI'
##dir2 = u'F:\\docs\\internet\\----\\_mail & usenet archive -- recovered data --\\(more 2)\\TEI'
##grp1 = [os.path.join(dir1, s) for s in os.listdir(dir1)]
##grp2 = [os.path.join(dir2, s) for s in os.listdir(dir2)]
##finddups(grp1 + grp2)


##compareDirs(dir1, dir2)

##s1 = 'c:\\temp\\foo.bar'
##s2 = 'c:\\temp\\' + ('foo' * 760) + '.bar'
##file(s1, 'w').close()
##
##import shutil
##shutil.move(s1, s2)


## Move files with identical contents found on *all* of the specified dirs
## to a new subdir under their current location.
def moveCommonToSub(dirs, subdirName):
    
    # test if the list contains all the indexes of 'dirs' exactly once
    def areCommon(indexList):
        n = len(dirs)
        return n == len(indexList) and sorted(indexList) == range(n)
    
    # test if the list contains all the indexes of 'dirs' one or more times
    def couldBeCommon(indexList):
        n = len(dirs)
        return len(indexList) >= n and sorted(list(set(indexList))) == range(n)
    
    # get index list from list of (index,string) tuples
    def getIndexes(lst):
        return [t[0] for t in lst]
    
    # first, group by size
    print 'Scanning directories...'
    sizeMap = collections.defaultdict(list)
    for i in range(len(dirs)):
        for f in os.listdir(dirs[i]):
            path = os.path.join(dirs[i], f)
            if not os.path.isdir(path):
                size = os.path.getsize(path)
                sizeMap[size] += [(i, f)]


##    for x in sizeMap[1215]:
##        print x
##    print couldBeCommon(getIndexes(sizeMap[1215]))
##    return

    # get possibly valid groups
    sizeGroups = [x for x in sizeMap.values() if couldBeCommon(getIndexes(x))]

##    print sizeGroups
##    test = u'BC++ 5.02 RTL κώδικας.nws'
##    testl = [t[1] for t in sizeGroups]
##    print test in testl
##    print testl

    # then, test each size group by md5
    print 'Finding duplicates...'
    commonGroups = []
    for grp in sizeGroups:
        sigMap = collections.defaultdict(list)
        for item in grp:
            sig = filesig(os.path.join(dirs[item[0]], item[1]))
            sigMap[sig] += [item]
        commonGroups += [x for x in sigMap.values() if areCommon(getIndexes(x))]

    print 'Duplicate groups found:', len(commonGroups)

    # finally, move the found files
    if len(commonGroups) != 0:
        print 'Moving files...'
        # create subdirs if they don't exist yet
        for s in dirs:
            sub = os.path.join(s, subdirName)
            if not os.path.isdir(sub):
                os.mkdir(sub)
        for grp in commonGroups:
            assert len(grp) == len(dirs)
            for item in grp:
                src = os.path.join(dirs[item[0]], item[1])
                dst = os.path.join(dirs[item[0]], subdirName, item[1])
                shutil.move(src, dst)
##                print src
##                print dst
##            print

    print 'Done'        


##pfx = u'F:\\docs\\internet\\----\\_mail & usenet archive -- recovered data --'
##dirs = [\
##    os.path.join(pfx, u'grk.comp.software'),\
##    os.path.join(pfx, u'(more 2)\\grk.comp.software.dbx')\
##]
##
###for s in dirs: findDupsInDir(s)
##moveCommonToSub(dirs, u'common')


##root = r'D:\2burn'
##for a in finddups(dirfiles(root, True)):
##    for s in a:
##        print s
##    print
