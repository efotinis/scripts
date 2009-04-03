# Rename the extracted Hexen 2 tracks 
# with matching names from the game's MIDIs.
# EF 2007-04-12 19:25

import os

# 16 audio tracks in order
names = ('casa1','casa2','casa3','casa4',
         'egyp1','egyp2','egyp3',
         'meso1','meso2','meso3',
         'roma1','roma2','roma3',
         'casb1','casb2','casb3')

for i, dst in enumerate(names):
    # this is how Nero extracts the tracks (first is 'Track No02.mp3')
    src = 'Track No%02d.mp3' % (i + 2)
    os.rename(src, dst + '.mp3')
