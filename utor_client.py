import sys, socket as soc

DEFAULT_PORT = 40585

def usage():
    print 'usage: SCRIPT server-host [port]'

args = sys.argv[1:]
if '/?' in args:
    usage()
    sys.exit(0)
if not 1 <= len(args) <= 2:
    print '1 or 2 params required'
    sys.exit(2)

host = soc.gethostbyname(args[0])
port = int(args[1]) if len(args) > 1 else DEFAULT_PORT
addr = host, port

sc = soc.socket(soc.AF_INET, soc.SOCK_DGRAM)
sc.setsockopt(soc.SOL_SOCKET, soc.SO_REUSEADDR, 1)
sc.bind(('', 0))
sc.sendto('REQ', addr)

data, addr = sc.recvfrom(256)
print data
