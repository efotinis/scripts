def rawbin(n, bits):
    """Bin str of specified width, without pfx. Used to init nibble dict."""
    return ''.join('1' if (n & (1 << i)) else '0'
                   for i in xrange(bits-1, -1, -1))


NIBBLES = dict((i,rawbin(i,4)) for i in range(16))


def bin(n):
    """Return a base-2 string repr of a number, similar to hex()."""
    neg = n < 0
    if neg:
        n = -n
    s = ''
    while n:
        s = NIBBLES[n & 0xf] + s
        n >>= 4
    s = s.lstrip('0')
    if not s:
        s = '0'
    s = '0b' + s
    if neg:
        s = '-' + s
    return s


if __name__ == '__main__':
    for i in range(-16, 16):
        print i, bin(i), bin(i & 0xff)


##hex2bin = {
##    '0':'0000', '1':'0001', '2':'0010', '3':'0011',
##    '4':'0100', '5':'0101', '6':'0110', '7':'0111',
##    '8':'1000', '9':'1001', 'a':'1010', 'b':'1011',
##    'c':'1100', 'd':'1101', 'e':'1110', 'f':'1111',
##}
##
##def bin(n):
####    neg = n < 0
####    if neg:
####        n = -n
####    s = ''
####    while n:
####        s = ('1' if n & 1 else '0') + s
####        n >>= 1
####    if not s:
####        s = '0'
####    s = '0b' + s
####    if neg:
####        s = '-' + s
####    return s
##    neg = n < 0
##    ret = ''
##    for c in hex(n)[2+neg:]:
##        ret += hex2bin[c]
##    return ('-' if neg else '') + '0b' + ret


