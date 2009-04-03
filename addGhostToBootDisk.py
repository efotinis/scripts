import os
import sys
import hashlib
import shutil


floppyDrive = 'A:'

neededFiles = [
    'AUTOEXEC.BAT',
    'COMMAND.COM',
    'CONFIG.SYS',
    'DISPLAY.SYS',
    'EGA2.CPI',
    'IO.SYS',
    'KEYB.COM',
    'KEYBRD4.SYS',
    'MODE.COM',
    'MSDOS.SYS'
]

delFiles = [
    'EGA.CPI',
    'EGA3.CPI',
    'KEYBOARD.SYS',
    'KEYBRD2.SYS',
    'KEYBRD3.SYS'
]

ghostPath = 'F:\\docs\\GHOST2K3.EXE'
ghostSig  = '6624b2460ee6851b5b6ae16389cb1cd9'

# check that needed files exist
for s in neededFiles:
    s = os.path.join(floppyDrive, s)
    if not os.path.isfile(s):
        print 'A necessary file is missing:', s
        sys.exit(1)

# remove unneeded files if they exist
for s in delFiles:
    s = os.path.join(floppyDrive, s)
    if os.path.exists(s):
        os.remove(s)

# fix KEYB line in AUTOEXEC.BAT
s = os.path.join(floppyDrive, 'AUTOEXEC.BAT')
lines = file(s).readlines()
for i in range(len(lines)):
    if lines[i][:5].lower() == 'keyb ':
        lines[i] = 'keyb gk,,keybrd4.sys\n'
file(s, 'w').writelines(lines)

# copy GHOST
if not os.path.isfile(ghostPath):
    print 'Could not find GHOST:', ghostPath
    sys.exit(1)
s = file(ghostPath, 'rb').read()
curSig = hashlib.md5(s).hexdigest()
if curSig != ghostSig:
    print 'GHOST sig mismatch:', ghostPath
    print '  current: ', curSig
    print '  expected:', ghostSig
    sys.exit(1)
shutil.copy(ghostPath, os.path.join(floppyDrive, os.path.split(ghostPath)[1]))
