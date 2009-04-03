import os
import sys
import shutil
import win32api
import win32con
import efDrives


def errLn(s):
    sys.stderr.write('ERROR: ' + s + '\n')

    
def wantHelp(args):
    return '/?' in args


def dispUsage():
    pass
##    cout << "================================\n";
##    cout << "MissJPEG 99 - Cracker (finally!)\n";
##    cout << "================================\n";
##    cout << "The needed files will be copied to C:\\MissJPEG.\n";
##    cout << "You can then run \\CONTROL\\missjpeg.exe from the CD,\n";
##    cout << "which will cleanup the C:\\MissJPEG dir on exit.\n";
##    cout << "Enjoy!\n";
##    cout << '\n';


def getVolumeLabelAndSerial(path):
    try:
        return win32api.GetVolumeInformation(path)[:2]
    except:
        return None


def getCdPath():
    """Detect CD drive and let user enter another path if needed."""

    cd = ''
    for root in efDrives.getDriveRoots(win32con.DRIVE_CDROM):
        if getVolumeLabelAndSerial(root) == ('CDShow37', -39429415):
            cd = root
            break

    prompt = 'Enter CDROM root path'
    if cd:
        prompt += ' (hit ENTER to accept detected: "%s")' % cd
    prompt += ':'

    new = raw_input(prompt).strip()
    if new:
        cd = new
        if cd[-1] == ':':
            cd += '\\'

    return cd


def tryFileOpen(path, mode):
    try:
        return file(path, mode)
    except IOError, x:
        errLn('Could not open "%s": %s' % (path, x.strerror))
        return None


def openFiles(root):
    """Open and return control files."""
    nameFile = os.path.join(root, 'control\\Fei00.001')
    dataFile = os.path.join(root, 'control\\Ivox.sta')
    f1 = tryFileOpen(nameFile, 'r')
    f2 = tryFileOpen(dataFile, 'rb')
    return f1, f2


def createOutDir():
    s = 'C:\\CDSHOW'
    if not os.path.exists(s):
        try:
            os.mkdir(s)
        except OSError:
            return False
    return True


def patchFiles(cdPath, nameFile, dataFile):

    BUFLEN = 16 * 15

    dataFile.seek(239)

    while True:
        fname = nameFile.readline().rstrip('\n')
        if not fname:
            break

        buf = dataFile.read(BUFLEN)
        if len(buf) <> BUFLEN:
            errLn('Error while reading data.')
            return

        src = os.path.join(cdPath, 'CONTROL\\Jen', fname)
        dst = os.path.join('C:\\CDSHOW', fname)

        try:
            try:
                win32api.SetFileAttributes(dst, win32con.FILE_ATTRIBUTE_NORMAL)
            except:
                pass
            shutil.copyfile(src, dst)
            win32api.SetFileAttributes(dst, win32con.FILE_ATTRIBUTE_NORMAL)
        except IOError, x:
            errLn(str(x))
            continue
        
        try:
            ofs = file(dst, 'r+b')
            ofs.seek(0)
            ofs.write(buf)
        except IOError, x:
            errLn(str(x))
            continue


def main(args):

    if wantHelp(args):
        dispUsage()
        return 0

    cdPath = getCdPath()
    if not os.path.isdir(cdPath):
        errLn('Invalid CD path: "%s"' % cdPath)
        return 1

    nameFile, dataFile = openFiles(cdPath)
    if not nameFile or not dataFile:
        return 1

    if not createOutDir():
        errLn('Could not create output dir,')
        return 1

    patchFiles(cdPath, nameFile, dataFile)


sys.exit(main(sys.argv[1:]))
