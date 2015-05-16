# 2007.01.09  EF  created
# 2007.10.21  EF  added cmdline options, utf-8 support

import codecs
import os
import sys

import DosCmdLine
import six


def readPlaylist(f, forceUtf8=False):
    """Read an M3U(8) file and return a list of paths."""
    # check for (and skip) BOM
    if f.read(3) == codecs.BOM_UTF8:
        isUtf8 = True
    else:
        isUtf8 = False
        f.seek(0)
    if forceUtf8:
        isUtf8 = True
    decoder = codecs.getdecoder('utf-8' if isUtf8 else 'mbcs')
    return [decoder(s.rstrip('\n'))[0] for s in f]


def writePlaylist(f, a, utf8=False):
    """Write a list of paths to an M3U/M3U8 file (or None for STDOUT)."""
    encoder = codecs.getencoder('utf-8' if utf8 else 'mbcs')
    if utf8:
        f.write(codecs.BOM_UTF8)
    for s in a:
        print >>f, encoder(s)[0]


def process(playlist, lookupDirs, notFoundHandler, multipleFoundHandler):
    """Process a playlist; return new playlist and number of files not found."""
    baseNames = {}
    for s in playlist:
        baseNames[os.path.basename(s).lower()] = []
    for d in lookupDirs:
        for dpath, dirs, files in os.walk(d):
            for s in files:
                base = os.path.basename(s).lower()
                if base in baseNames:
                    baseNames[base] += [os.path.join(dpath, s)]
    notFoundCnt = 0
    for i in range(len(playlist)):
        base = os.path.basename(playlist[i]).lower()
        a = baseNames[base]
        if not a:
            playlist[i] = notFoundHandler(playlist[i])
            notFoundCnt += 1
        elif len(a) == 1:
            playlist[i] = a[0]
        else:
            playlist[i] = multipleFoundHandler(playlist[i], a)
    return playlist, notFoundCnt


def showHelp(switches):
    name = os.path.splitext(os.path.basename(sys.argv[0]))[0].upper()
    table = '\n'.join(DosCmdLine.helptable(switches))
    print """\
Fix M3U(8) playlists when files are moved around.
Elias Fotinis 2007

%s [/D:dir] [/S] [/NS] source [dest]

%s

Files are matched using just the base name, since M3U playlists contain no
other info. Files that are not found remain unchanged (a warning is printed).

Exit code: 0=ok, 1=files not found, 2=error, 3=bad param.""" % (name, table)


def errln(s):
    sys.stderr.write('ERROR: ' + s + '\n')
    

EXIT_OK = 0
EXIT_NOTFOUND = 1
EXIT_ERROR = 2
EXIT_BADPARAM = 3

def main(args):
    Flag = DosCmdLine.Flag
    Swtc = DosCmdLine.Switch
    switches = (
        Swtc('D', 'lookupDirs',
             'Directory to search files into (recursively). Multiple switches '
             'are allowed, in order to look into many directories. '
             'If omitted, the current directory is used.',
             [], accumulator=lambda s,a:a+[s]),
        Flag('S', 'silent',
             'Do not prompt when multiple files are found with the same name; '
             'a random file is picked instead.'),
        Flag('NS', 'noSummary',
             'Do not print summary details.'),
        Flag('source', None,
             'Input playlist.'),
        Flag('dest', None,
             'Output playlist. If omitted, output is written to STDOUT. '
             'If the extension is M3U8, UTF-8 encoding is used.'),
    )
    if '/?' in args:
        showHelp(switches)
        return EXIT_OK
    try:
        opt, srcDst = DosCmdLine.parse(args, switches)
        if not 1 <= len(srcDst) <= 2:
            raise DosCmdLine.Error('exactly one or two parameters are needed')
        if not opt.lookupDirs:
            opt.lookupDirs = ['.']
        opt.lookupDirs = map(six.text_type, opt.lookupDirs)
        for s in opt.lookupDirs:
            if not os.path.isdir(s):
                errln('not a directory: "%s"' % s)
                return EXIT_BADPARAM
    except DosCmdLine.Error, x:
        errln(str(x))
        return EXIT_BADPARAM

    try:
        forceUtf8 = os.path.splitext(srcDst[0])[1].lower() == '.m3u8'
        playlist = readPlaylist(file(srcDst[0]), forceUtf8)
    except IOError, x:
        errln('could not read from "%s": %s' % (srcDst[0], str(x)))
        return EXIT_ERROR

    def notFound(s):
        print 'no match for "%s"' % s
        return s
    def multipleFoundChoose(s, a):
        print 'multiple matches for "%s"' % s
        for i, fpath in enumerate(a):
            print '  %d: %s' % (i+1, fpath)
        print '  0: leave unchanged'
        while True:
            s = raw_input('Choose:')
            try:
                answer = int(s)
                if answer == 0:
                    return s
                elif 1 <= answer <= len(a):
                    return a[answer - 1]
            except ValueError:
                pass
    def multipleFoundPickRandom(s, a):
        return a[0]

    multFnd = multipleFoundPickRandom if opt.silent else multipleFoundChoose 
    playlist, notFoundCnt = process(playlist, opt.lookupDirs, notFound, multFnd)

    try:
        if len(srcDst) > 1:
            outName = srcDst[1]
            f = file(outName, 'w')
            utf8 = os.path.splitext(outName)[1].lower() == '.m3u8'
        else:
            outName = 'STDOUT'
            f = None
            utf8 = False
        writePlaylist(f, playlist, utf8)
    except IOError, x:
        errln('could not write to "%s": %s' % (outName, str(x)))
        return EXIT_ERROR
    
    if not opt.noSummary:
        print 'Entries: %d' % len(playlist)
        print 'Not found: %d' % notFoundCnt

    return EXIT_NOTFOUND if notFoundCnt else EXIT_OK
    

sys.exit(main(sys.argv[1:]))


# here's the old version; it sure looks more elegant than the current :o)
### 2007.01.09  EF  created
##
##import os, sys
##
##
##def main():
##    if '/?' in sys.argv:
##        print 'FIX_M3U m3u_file song_dirs ...'
##        print ''
##        print '  m3u_file   Playlist file to process.'
##        print '  song_dirs  List of dir paths containing songs.'
##        sys.exit(0)
##
##    if len(sys.argv) < 3:
##        sys.stderr.write('ERROR: Parameters missing.\n')
##        sys.exit(1)
##
##    fileDict = {}
##    for s in sys.argv[2:]:
##        scanDir(s, fileDict)
##    print len(fileDict.keys())
##
##    a = [s.rstrip('\n') for s in open(sys.argv[1]).readlines()]
##    aNew = []
##    for s in a:
##        aNew.append(findSong(s, fileDict))
##
##    newPlayList = os.path.splitext(sys.argv[1])
##    newPlayList = os.path.join(newPlayList[0] + ' (F)' + newPlayList[1])
##    aNew = [s + '\n' for s in aNew]
##    open(newPlayList, 'w').writelines(aNew)
##
##
##def scanDir(rootPath, fileDict):
##    rootPath = rootPath
##    for path, dirs, files in os.walk(rootPath):
##        for s in files:
##            addDictList(fileDict, s.lower(), os.path.join(path, s))
##
##        
##def addDictList(d, k, v):
##    if k in d:
##        d[k].append(v)
##    else:
##        d[k] = [v]
##
##        
##def findSong(songPath, fileDict):
##    s = os.path.split(songPath)[1].lower()
##    if not s in fileDict:
##        sys.stderr.write('ERROR: Song not found: "' + s + '"')
##        return songPath
##    a = fileDict[s]
##    if len(a) == 1:
##        return a[0]
##    print 'Multiple songs found for "' + s + '"'
##    for n in xrange(len(a)):
##        print '  ' + str(n + 1) + ':', a[n]
##    print '  0: Don\'t change.'
##    while True:
##        try:
##            n = int(raw_input('Select: '))
##            if n >= len(a):
##                raise 0
##            elif n == 0:
##                return songPath
##            else:
##                return a[n - 1]
##        except:
##            print 'Invalid value.'
##
##
##if __name__ == '__main__':
##    main()
    