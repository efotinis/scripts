import os


def expandEnv(s):
  """Replace environment variables (using '%...%' format) in a string."""
  i = 0
  while True:
    rng = _findExpStrRange(s, i)
    if not rng:
      return s
    id = s[rng[0]+1:rng[1]-1]
    val = os.getenv(id)
    if val is None:
      i = rng[1]-1  # start next iter at the second '%'
    else:
      s = s[:rng[0]] + val + s[rng[1]:]
      i += len(val)  # start next iter after the replaced text
  return s


def _findExpStrRange(s, beg=0):
  """Return the half-open range of the next '%...%' sequence or None."""
  i = s.find('%', beg)
  if i != -1:
    j = s.find('%', i + 1)
    if j != -1:
      return (i, j + 1)
  return None


if __name__ == '__main__':
  print 'example of temp file:', expandEnv('%TEMP%\\myTempFile.$$$')
  print 'current user: ', expandEnv('%username%')
  