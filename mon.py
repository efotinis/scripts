"""Monitor funcs script."""

import optparse
import time
import monitorutil


def getopt():
    op = optparse.OptionParser(description='Various monitor functions.', add_help_option=False)
    op.add_option('-x', '--off', action='store_true', dest='turnoff', help='Turn monitor off.')
    op.add_option('-z', '--sleep', action='store_true', dest='sleep', help='Suspend monitor.')
    op.add_option('-s', '--save', action='store_true', dest='screensave', help='Launch screensaver.')
    op.add_option('-w', '--wait', action='store', dest='wait', metavar='N', help='Number of seconds (float) to wait before sending command.')
    op.add_option('-?', action='help', help=optparse.SUPPRESS_HELP)
    opt, args = op.parse_args()
    if args:
        op.error('no arguments needed')
    if sum(map(bool, [opt.turnoff, opt.sleep, opt.screensave])) != 1:
        op.error('exactly one action (-x,-z,-s) is needed')
    if opt.wait:
        try:
            opt.wait = float(opt.wait)
            if opt.wait < 0:
                raise ValueError
        except ValueError:
            op.error('invalid wait value: "%s"' % opt.wait)
    return opt


if __name__ == '__main__':
    opt = getopt()
    if opt.wait:
        time.sleep(opt.wait)
    if opt.turnoff:
        monitorutil.turnoffmonitor()
    elif opt.sleep:
        monitorutil.suspendmonitor()
    elif opt.screensave:
        monitorutil.launchscreensaver()
