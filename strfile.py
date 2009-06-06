import sys
import struct


args = sys.argv[1:]
if not 1 <= len(args) <= 2:
    raise SystemExit('1 or 2 arguments required')
if len(args) == 1:
    args += [args[0] + '.dat']

input, output = args

HEADER = '>LLLLLc3s'
HEADER_LEN = struct.calcsize(HEADER)

fout = open(output, 'wb')
fout.write('\0' * HEADER_LEN)
fout.write(struct.pack('>L', 0))

count = 0
minsize = 2**31
maxsize = 0

curpos, lastpos = 0, 0
fin = open(input)
for s in fin:
    curpos += len(s)
    if s == '%\n':
        fout.write(struct.pack('>L', curpos))
        count += 1
        size = curpos - lastpos - 2
        assert size >= 0, fin.tell()
        if size < minsize: minsize = size
        if size > maxsize: maxsize = size
        lastpos = curpos

assert fin.tell() == lastpos, 'file does not end with a delimiter'

print minsize, maxsize

version = 1
flags = 0
delim = '%'
padding = '\0' * 3
hdr = struct.pack(HEADER, version, count, maxsize, minsize, flags, delim, padding)
fout.seek(0)
fout.write(hdr)
