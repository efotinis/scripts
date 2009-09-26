"""Interactive stopwatch."""

import os
from stopwatch import StopWatch

if os.name == 'nt':
    import msvcrt
    def getch():
        ch = msvcrt.getch()
        if ch in '\0\xe0':
            ch += getch()
        return ch
else:
    raise RuntimeError('no getch() specified for this platform ("%s")' % os.name)


ESC = chr(27)


def showhelp():
    print '''Interactive stopwatch.
Keys:
  s   start/stop
  S   show status (running/stopped)
  t   show current time
  r   reset
  R   reset & restart
  l   record lap time (if running) and list all lap times
  L   clear lap times
  ?   this help
  Esc quit'''


sw = StopWatch()
laptimes = []

print 'stopped'
while True:
    cmd = getch()
    if cmd == 's':
        if sw.isrunning():
            sw.stop()
            print 'stopped'
        else:
            sw.start()
            print 'running...'
    elif cmd == 'S':
        if sw.isrunning():
            print 'running...'
        else:
            print 'stopped'
    elif cmd == 't':
        print sw.get()
    elif cmd == 'r':
        sw.reset()
        print 'reset'
    elif cmd == 'R':
        sw.reset(autostart=True)
        print 'reset'
        print 'running...'
    elif cmd == 'l':
        if sw.isrunning():
            laptimes += [sw.get()]
            print 'added lap time'
        print 'laps:'
        for i, t in enumerate(laptimes):
            print '  #%d: %f' % (i + 1, t)
    elif cmd == 'L':
        del laptimes[:]
        print 'laptimes cleared'
    elif cmd == '?':
        showhelp()
    elif cmd == ESC:
        break
    else:
        pass
