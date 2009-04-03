import os

rootsrc = r'G:\6\rilas zz2\pics'
rootdst = r'D:\temp\xxx'
cmd = 'cmd "C:\Program Files\IrfanView\i_view32.exe" "%s\*.jpg" "%s\*.png" /resample=(128,160) /aspectratio /convert="%s\*.jpg"'



print
for dir, _, _ in os.walk(rootsrc):
    print dir
    sub = dir[len(rootsrc):].lstrip('\\')
    dst = os.path.join(rootdst, sub)
    s = cmd % (dir, dir, dst)
    os.system(s)
    
    