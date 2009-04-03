import sys


def showHelp():
  pass

##  n
##  from;to
##  from;to;step
##
##  10            10
##  2;5           2,3,4,5
##  1;20;5        1,6,11,16
##  1;20;5;1,2   1,2,6,7,11,12,16,17
##
##  Filters file lines.
##
##  LNFILT file first;last;step;group [...]
##  
##    first   The start line. Default is 1.
##    last    The last line. Can be greater, less, or equal to 'first'.
##            Default is equal to 'first'.
##    step    The stepping value. Can be negative. Default is 1.
##    group   A comma-separated list of relative lines for each step.
##            Default is 1, meaning the first line at each step.
##  
##  You can use * for the total number of lines in the file.
##  
##  Example line specs and returned lines:
##  4;6 1       ->  4 5 6 1
##  7,1;-2      ->  7 5 3 1
##  1;*;10;3,1  ->  3 1 13 11 23 21 ...
##  
##  for (i = first; i <=(>=) last; i += step)
##    for each n in group:
##      use line i+n-1
##  


def readFileLines(fileInfo):
  if not fileInfo[1] is None:
    return
  try:
    fileInfo[1] = file(fileInfo[0]).readlines()
  except IOError, x:
    raise MyError(str(x))


def getInt(s, default, fileInfo):
  if not s:
    return default
  elif s == '*':
    if fileInfo[1] is None:
      readFileLines(fileInfo)
    return len(fileInfo[1])
  else:
    return int(s)


class MyError(Exception):
  def __init__(self, x):
    Exception.__init__(self, x)
  

def parseLineSpec(s, fileInfo):
  tokens = [x.strip() for x in s.split(';')]
  if len(tokens) > 4:
    raise MyError('Too many tokens in ' + s)
  while len(tokens) < 4:
    tokens.append('')
  first = getInt(tokens[0], 1, fileInfo)
  last  = getInt(tokens[1], first, fileInfo)
  step  = getInt(tokens[2], 1, fileInfo)
##  group = tokens[3]
  if step == 0:
    raise MyError('Zero step in ' + s)
  if step > 0:
    return range(first, last+1, step)
  else:
    return range(first, last-1, step)


def main(args):
  if '/?' in args:
    showHelp()
    return
  if not args:
    raise MyError('Missing file')
  fileInfo = [args[0], None]
  lines = []
  for s in args[1:]:
    lines += parseLineSpec(s, fileInfo)
  if fileInfo[1] is None:
    readFileLines(fileInfo)
  for i in lines:
    if 0 <= i-1 < len(fileInfo[1]):
      sys.stdout.write(fileInfo[1][i-1])
    else:
      sys.stdout.write('\n')


try:
  #print '-'*40
  #main(['c:\\temp\\lines.txt', '*'])
  main(sys.argv[1:])
  sys.exit(0)
except MyError, x:
  sys.stderr.write('ERROR: LNFILT.PY: ' + str(x) + '\n')
##except Exception, x:
##  sys.stderr.write(str(x) + '\n')
##  sys.stderr.write('EXCEPTION: LNFILT.PY: ' + str(x.code) + '\n')
sys.exit(1)
