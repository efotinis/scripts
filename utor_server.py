import sys, socket as soc
import utor_scrape

DEFAULT_PORT = 40585

def usage():
    print 'usage: SCRIPT [port]'

args = sys.argv[1:]
if '/?' in args:
    usage()
    sys.exit(0)
if not 0 <= len(args) <= 1:
    print '0 or 1 params required'
    sys.exit(2)

port = int(args[0]) if len(args) > 0 else DEFAULT_PORT

sc = soc.socket(soc.AF_INET, soc.SOCK_DGRAM)
sc.setsockopt(soc.SOL_SOCKET, soc.SO_REUSEADDR, 1)
sc.bind(('', port))
print 'server running (Ctrl-C to exit)...'
while True:
    try:
        data, addr = sc.recvfrom(256)
        if data == 'REQ':
            try:
                s = ' | '.join(utor_scrape.getStatus())
            except (WindowsError, utor_scrape.error), x:
                s = '(error: %s)' % x
            sc.sendto(s, addr)
            print 'sent data to %s:%d' % addr
        else:
            print 'error: bad data from %s:%d - %s' % (addr + (data,))
    except soc.error, x:
        print 'error: %s' % x
