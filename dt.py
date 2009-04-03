import re, sys, math

# [[HH:]MM:]SS[.XX]
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

def combine(a):
    h, m, s, x = a
    return ((h*60 + m)*60) + s + x

def split(sec):
    hours = sec // 3600; sec %= 3600
    minutes = sec // 60; sec %= 60
    fraction, seconds = math.modf(sec)
    return hours, minutes, seconds, fraction

def parse(s):
    try:
        a = rx.match(s).groups()
        a = [s if s else 0 for s in a]
        a = map(int, a[:3]) + [float(a[3])]
    except (AttributeError, ValueError):
        raise SystemExit('invalid time: ' + s)
    return a

def format(a):
    a = tuple(a[:3]) + (round(a[3] * 1000), )
    return '%02d:%02d:%02d.%03d' % a

args = sys.argv[1:]
if '/?' in args:
    print 'Calc difference between two times.'
    print
    print 'DT.PY end beg'
    print ''
    print '  beg end  Time stamps. Format: [[h:]m:]s[.x]'
    raise SystemExit

if len(args) != 2:
    raise SystemExit('exactly two arguments required')

end = combine(parse(args[0]))
beg = combine(parse(args[1]))
sign = ''
if end < beg:
    beg, end = end, beg
    sign = '-'
diff = end - beg
print '%s - %s = %s' % (
    format(split(end)), format(split(beg)), sign + format(split(diff)))
