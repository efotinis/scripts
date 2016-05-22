#!python
"""Interactive stopwatch."""

from __future__ import print_function
import os
import stopwatch
import mathutil


if os.name == 'nt':
    import msvcrt
    def getch():
        ch = msvcrt.getch()
        if ch in b'\0\xe0':
            ch += getch()
        return ch
else:
    raise RuntimeError('no getch() specified for this platform ("%s")' % os.name)


def time_str(sec):
    """Convert seconds to 'DD:HH:MM:SS.mmm'."""
    millisec = int(round(sec * 1000, 0))
    d, h, m, s, ms = mathutil.multi_divmod(millisec, 24, 60, 60, 1000)
    return '%02d:%02d:%02d:%02d.%03d' % (d, h, m, s, ms)


def showhelp():
    print('''Interactive stopwatch.
Keys:
    Space   start/stop
    Tab     status
    Enter   record lap time, if running
    l       list lap times
    L       clear lap times
    Del     reset & stop
    ^Del    reset & start
    F1      this help
    Esc     quit''')


KEY_STARTSTOP   = b' '           # Space
KEY_STATUS      = b'\t'          # Tab
KEY_RESET       = b'\xe0S'       # Del
KEY_RESETSTART  = b'\xe0\x93'    # ^Del
KEY_ADDLAP      = b'\r'          # Enter
KEY_SHOWLAPS    = b'l'
KEY_CLEARLAPS   = b'L'
KEY_HELP        = b'\0;'         # F1
KEY_EXIT        = b'\x1b'        # Esc


def print_status(sw):
    print('%s  %s  laps:%d' % (
        time_str(sw.get()),
        'running' if sw.isrunning() else 'stopped',
        len(laps)))


if __name__ == '__main__':
    sw = stopwatch.StopWatch()
    laps = []
    print_status(sw)

    while True:
        cmd = getch()

        if cmd == KEY_STARTSTOP:
            if sw.isrunning():
                sw.stop()
            else:
                sw.start()
            print_status(sw)

        elif cmd == KEY_STATUS:
            print_status(sw)

        elif cmd == KEY_RESET:
            laps = []
            sw.reset()
            print('reset')
            print_status(sw)

        elif cmd == KEY_RESETSTART:
            laps = []
            sw.reset(autostart=True)
            print('reset')
            print_status(sw)

        elif cmd == KEY_ADDLAP:
            if not sw.isrunning():
                print('not running')
            else:
                last_lap = laps[-1] if laps else 0
                i = len(laps)
                t = sw.get()
                laps += [t]
                print('  %3d: +%s  %s' % (i + 1, time_str(t - last_lap), time_str(t)))

        elif cmd == KEY_SHOWLAPS:
            if not laps:
                print('no laps recorded')
            else:
                print('laps:')
                last_lap = 0
                for i, t in enumerate(laps):
                    print('  %3d: +%s  %s' % (i + 1, time_str(t - last_lap), time_str(t)))
                    last_lap = t

        elif cmd == KEY_CLEARLAPS:
            laps = []
            print('laps cleared')

        elif cmd == KEY_HELP:
            showhelp()

        elif cmd == KEY_EXIT:
            break

        else:
            #print(repr(cmd))
            pass
