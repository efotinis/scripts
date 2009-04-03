import sys


def showhelp():
    print """\
Display a graphical ruler.
Freeware, (C) 2005-2007 Elias Fotinis

RULER x y z a b c

  x  Total rulersize. Default is 79.
  y  Numbered interval rulersize; must be > 0. Default is 10.
  z  Non-numbered interval rulersize; if 0, it is not displayed. Default is 5.
  a  Ruler character. Default is '-'
  b  Numbered interval marker. Default is '|'
  c  Non-numbered interval marker. Default is '+'
    
All parameters are optional. Use "" to skip a parameter and specify
subsequent ones.
The return code is always 0."""


def parseint(s, default=None, rangecheck=None):
    try:
        n = int(s)
    except ValueError:
        n = default
    if callable(rangecheck) and not rangecheck(n):
        n = default
    return n


class Options:
    def __init__(self, args):
        self.help = '/?' in args
        if self.help:
            return
        # make sure there are enough args
        if len(args) < 6:
            args += [''] * (6-len(args))
        self.rulersize   = parseint(args[0], 79, lambda n: n >= 0)
        self.ticksize    = parseint(args[1], 10, lambda n: n >  0)
        self.subticksize = parseint(args[2],  5, lambda n: n >= 0)
        self.rulerchar   = args[3][:1] or '-'
        self.tickchar    = args[4][:1] or '|'
        self.subtickchar = args[5][:1] or '+'


def main(args):

    opt = Options(args)
    if opt.help:
        showhelp()
        return 0
    
    # create a number print format with proper width (ie. ticksize)
    numfmt = "%%%dd" % opt.ticksize
    
    # output number line (only full-width numbers)
    rng = range(opt.ticksize, opt.rulersize+1, opt.ticksize)
    print ''.join(numfmt % n for n in rng)
    
    setchr = lambda s, i, c: s[:i] + c + s[i+1:]

    # build ruler segment
    segment = opt.rulerchar * opt.ticksize
    if opt.subticksize:
        rng = range(opt.subticksize-1, opt.ticksize, opt.subticksize)
        for n in rng:
            segment = setchr(segment, n, opt.subtickchar)
    # set interval
    segment = setchr(segment, opt.ticksize - 1, opt.tickchar)
    
    # output graphical line
    full, part = divmod(opt.rulersize, opt.ticksize)
    print segment*full + segment[:part]
    
    return 0


sys.exit(main(sys.argv[1:]))


##---------------------------------
##old C++ version
##---------------------------------
###include "stdafx.h"
##
##
##void q(const char* s) {
##  puts(s ? s : "");
##}
##
##
##void showHelp() {
##  //         10        20        30        40        50        60        70        80
##  // ----:----|----:----|----:----|----:----|----:----|----:----|----:----|----:----|
##  q("Display a graphical ruler.");
##  q("Freeware, (C) 2005 Elias Fotinis <efotinis@freemail.gr>");
##  q("");
##  q("RULER x y z a b c");
##  q("");
##  q("  x  Total size. Default is 80.");
##  q("  y  Numbered interval size; must be > 0. Default is 10.");
##  q("  z  Non-numbered interval size; if 0, it is not displayed. Default is 5.");
##  q("  a  Ruler character. Default is '-'");
##  q("  b  Numbered interval marker. Default is '|'");
##  q("  c  Non-numbered interval marker. Default is ':'");
##  q("");
##  q("All parameters are optional. Use \"\" to skip a parameter and specify");
##  q("subsequent ones.");
##  q("The return code is always 0.");
##}
##
##
##class Options {
##public:
##  int maxLen, segmLen, subSegmLen;
##  char c1, c2, c3;
##  bool help;
##
##  Options(int argc, char* argv[]) {
##    help = false;
##    // quick check for help switch
##    for (int n = 1; n < argc; ++n)
##      if (strcmp(argv[n], "/?") == 0) {
##        help = true;
##        return;
##      }
##
##    maxLen = argc >= 2 ? atoi(argv[1]) : 80;
##    if (maxLen < 0)
##      maxLen = 0;
##
##    segmLen = argc >= 3 ? atoi(argv[2]) : 10;
##    if (segmLen <= 0)
##      segmLen = 10;
##
##    subSegmLen = argc >= 4 ? atoi(argv[3]) : 5;
##    if (subSegmLen <= 0)
##      subSegmLen = 0;
##
##    c1 = argc >= 5 && argv[4][0] ? argv[4][0] : '-';
##    c2 = argc >= 6 && argv[5][0] ? argv[5][0] : '|';
##    c3 = argc >= 7 && argv[6][0] ? argv[6][0] : ':';
##  }
##};
##
##
##int main(int argc, char* argv[]) {
##  Options opt(argc, argv);
##  if (opt.help) {
##    showHelp();
##    return 0;
##  }
##
##  // create a number print fmt of proper width (segmLen)
##  char numFmt[20];
##  sprintf(numFmt, "%%%dd", opt.segmLen);
##
##  // output number line (only full-width numbers)
##  for (int n = opt.segmLen; n <= opt.maxLen; n += opt.segmLen)
##    printf(numFmt, n);
##  printf("\n");
##
##  // build ruler segment
##  char* segment = new char[opt.segmLen + 1];
##  memset(segment, opt.c1, opt.segmLen);  // fill with ruller char
##  if (opt.subSegmLen)  // add sub intervals, if any
##    for (int n = opt.subSegmLen; n <= opt.segmLen; n += opt.subSegmLen)
##      segment[n - 1] = opt.c3;
##  segment[opt.segmLen - 1] = opt.c2;  // set interval
##  segment[opt.segmLen] = 0;       // zero-terminate
##
##  // output graphical line
##  int n;
##  for (n = opt.segmLen; n <= opt.maxLen; n += opt.segmLen)  // print full segments
##    printf(segment);
##  if (n - opt.segmLen < opt.maxLen) {  // if there's some space left, print partial segment
##    segment[opt.segmLen - n + opt.maxLen] = 0;
##    printf(segment);
##  }
##  printf("\n");
##
##  delete[] segment;
##  segment = 0;
##
##  return 0;
##}
