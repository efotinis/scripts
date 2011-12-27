"""Calculate the difference between two times."""

from __future__ import print_function
import re
import sys
import math
import getopt
import CommonTools
import mathutil


# time format: [[hr:]min:]sec[.fract]
rx = re.compile(r'''
    ^\s*
    (?:
        (?:
            (\d+):      # hours
        )?
        (\d+):          # minutes
    )?
    (\d+)               # seconds
    (\.\d+)?            # fractional
    \s*$''', re.VERBOSE)


def timestr_to_sec(timestr):
    """Convert a time string to seconds."""
    try:
        hours, minutes, seconds, fraction = map(
            float, (s or 0 for s in rx.match(timestr).groups()))
        return ((hours * 60 + minutes) * 60) + seconds + fraction
    except (AttributeError, ValueError):
        raise ValueError('invalid time: ' + timestr)


def sec_to_timestr(sec, fracts=True):
    """Convert seconds to a time string. Use fracts=False to round seconds."""
    h_m_s = mathutil.multi_divmod(sec, 60, 60)
    fmt = '%02d:%02d:%06.3f' if fracts else '%02d:%02d:%02.0f'
    return fmt % h_m_s


def help():
    scriptname = CommonTools.scriptname()
    print('''
Calculate the difference between two times.
    
%(scriptname)s options START END

  START,END  The two time strings: [[hr:]min:]sec[.fract]
  -v         Verbose output. Include the (normalized) input times.
  -s         Include sign if START > END.
  -f, -F     By default, milliseconds are displayed if input times are
             fractional. Use -f to always show or -F to hide (and round) them.
  -?         This help.
'''[1:-1] % locals())


class Options(object):

    help = False
    verbose = False
    signed = False
    starttime = 0
    endtime = 0
    fracts = None

    def __init__(self, args):
        opts, args = getopt.gnu_getopt(args, '?vsfF')
        for sw, val in opts:
            if sw == '-?':
                self.help = True
                return  # bail out early for help
            elif sw == '-v':  self.verbose = True
            elif sw == '-s':  self.signed = True
            elif sw == '-f':  self.fracts = True
            elif sw == '-F':  self.fracts = False
        if len(args) != 2:
            raise getopt.GetoptError('exactly two arguments required')
        try:
            self.starttime = timestr_to_sec(args[0])
            self.endtime = timestr_to_sec(args[1])
            isfract = lambda n: n != int(n)
            if self.fracts is None:
                self.fracts = isfract(self.starttime) or \
                              isfract(self.endtime)
        except ValueError as err:
            raise getopt.GetoptError(str(err))


if __name__ == '__main__':

    try:
        opt = Options(sys.argv[1:])
    except getopt.GetoptError as err:
        raise SystemExit(str(err))

    if opt.help:
        help()
    else:
        diff = opt.endtime - opt.starttime
        sign = ''
        if diff < 0:
            diff = -diff
            if opt.signed:
                sign = '-'
        if opt.verbose:
            print('%s ... %s -> ' % (
                sec_to_timestr(opt.starttime, opt.fracts),
                sec_to_timestr(opt.endtime, opt.fracts)),
                  end='')
        print('%s%s' % (sign, sec_to_timestr(diff, opt.fracts)))
