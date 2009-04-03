"""Bit operations."""

# 2008.01.27  Created.
# 2008.11.09  Added Bitfield.


# -------- signed / unsigned --------


def unsigned16(n):
    """Convert 16-bit signed int to unsigned."""
    n &= 0xffff
    return n if n >= 0 else 0xfffe + n


def signed16(n):
    """Convert 16-bit unsigned int to signed."""
    n &= 0xffff
    return n if n < 0x8000 else n - 0x10000


def unsigned32(n):
    """Convert 32-bit signed int to unsigned."""
    n &= 0xffffffff
    return n if n >= 0 else 0xfffffffe + n


def signed32(n):
    """Convert 32-bit unsigned int to signed."""
    n &= 0xffffffff
    return n if n < 0x80000000 else n - 0x100000000


def unsigned64(n):
    """Convert 64-bit signed int to unsigned."""
    n &= 0xffffffffffffffff
    return n if n >= 0 else 0xfffffffffffffffe + n


def signed64(n):
    """Convert 64-bit unsigned int to signed."""
    n &= 0xffffffffffffffff
    return n if n < 0x8000000000000000 else n - 0x10000000000000000


_unsigned_funcs = { 16:unsigned16, 32:unsigned32, 64:unsigned64 }
_signed_funcs = { 16:signed16, 32:signed32, 64:signed64 }


def unsigned(n, bits):
    """Convert 16/32/64-bit signed int to unsigned."""
    return _signed_unsigned(n, bits, False)


def signed(n, bits):
    """Convert 16/32/64-bit unsigned int to signed."""
    return _signed_unsigned(n, bits, True)


def _signed_unsigned(n, bits, signed):
    try:
        return (_signed_funcs if signed else _unsigned_funcs)[bits](n)
    except KeyError:
        raise ValueError('bits must be 16, 32 or 64')


# -------- bit flags --------


def flagstr(flags, bits, names, empty=''):
    """Convert bit flags to string.

    'flags' is the bitmap number and 'bits' its bit width (16/32/64).
    'names' maps single-bit masks (i.e. 0x8000, not 0xC000) to string names.
    'empty' is the string to return if no flags are set.

    Leftover bits (not covered by 'names') will be appended in hex.
    """
    flags = unsigned(flags, bits)
    unknown = 0
    a = []
    for flag in map(lambda n: 1 << n, range(bits)):
        try:
            if flags & flag:
                a += [names[flag]]
        except KeyError:
            unknown |= flag
    if unknown:
        a += [('0x%0'+str(bits/4)+'X') % unknown]
    return ', '.join(a) or empty


def flagstr16(flags, names, empty=''):
    return flagstr(flags, 16, names, empty)
def flagstr32(flags, names, empty=''):
    return flagstr(flags, 32, names, empty)
def flagstr64(flags, names, empty=''):
    return flagstr(flags, 64, names, empty)


# -------- Bitfield --------


# bit field manipulation << ActiveState Code
# Recipe 113799: bit field manipulation
# http://code.activestate.com/recipes/113799/

class Bitfield(object):
    def __init__(self, value=0):
        self._d = value

    def __getitem__(self, index):
        return (self._d >> index) & 1 

    def __setitem__(self, index, value):
        value    = (value & 1L) << index
        mask     = (1L) << index
        self._d  = (self._d & ~mask) | value

    def __getslice__(self, start, end):
        mask = 2L ** (end - start) - 1
        return (self._d >> start) & mask

    def __setslice__(self, start, end, value):
        mask = 2L ** (end - start) - 1
        value = (value & mask) << start
        mask = mask << start
        self._d = (self._d & ~mask) | value
        return (self._d >> start) & mask

    def __int__(self):
        return self._d


# -------- test code --------


if __name__ == '__main__':
    try:

        # signed/unsigned
        for i in range(-4, 4):
            # test boundary cases
            assert unsigned16(i) == (i if i >= 0 else 0x10000+i)
            assert unsigned32(i) == (i if i >= 0 else 0x100000000+i)
            assert unsigned64(i) == (i if i >= 0 else 0x10000000000000000+i)
            # test round-tripping
            assert i == signed16(unsigned16(i))
            assert i == signed32(unsigned32(i))
            assert i == signed64(unsigned64(i))

        # flagstr
        names = { 0x1:'A', 0x2:'B' }
        assert flagstr16(0x01, names) == 'A'
        assert flagstr16(0x03, names) == 'A, B'
        assert flagstr16(0x07, names) == 'A, B, 0x0004'
        assert flagstr16(0x10, names) == '0x0010'
        assert flagstr16(0x00, names, '--') == '--'

        # bitfield
        x = Bitfield()
        assert int(x) == 0
        x[8] = 1
        assert int(x) == 256
        x[8] = 0
        assert int(x) == 0
        x[3:6] = 5
        assert x[3:6] == 5
        assert x[3] == 1
        assert x[4] == 0
        assert x[5] == 1

    except AssertionError:
        print 'test failed'

    else:
        print 'all tests passed'
