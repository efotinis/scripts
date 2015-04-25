"""Bit operations."""

from __future__ import print_function


# -------- signed / unsigned --------


# signedness constants
SIGNED, UNSIGNED = True, False

# cache of common-width bit and sign masks
_COMMON_MASKS = {
    8: (0xff, 0x80),
    16: (0xffff, 0x8000),
    32: (0xffffffff, 0x80000000),
    64: (0xffffffffffffffff, 0x8000000000000000)}


def castint(n, bits, signedness):
    """C-style cast of an int to a specified bit-width and signness."""
    try:
        bitmask, signmask = _COMMON_MASKS[bits]
    except KeyError:
        bitmask = (1 << bits) - 1  # all bits set
        signmask = 1 << (bits - 1)  # only sign bit set
    n &= bitmask
    if signedness == SIGNED and n & signmask:
        #n = -(~n & bitmask) - 1
        n -= bitmask + 1  # slightly faster
    return n


# convenience functions
def int8(n): return castint(n, 8, SIGNED)
def uint8(n): return castint(n, 8, UNSIGNED)
def int16(n): return castint(n, 16, SIGNED)
def uint16(n): return castint(n, 16, UNSIGNED)
def int32(n): return castint(n, 32, SIGNED)
def uint32(n): return castint(n, 32, UNSIGNED)
def int64(n): return castint(n, 64, SIGNED)
def uint64(n): return castint(n, 64, UNSIGNED)


# -------- bit flags --------


def flagchars(flags, width, chars, ignore=' '):
    """Convert bit flags to string of chars.

    flags:  flags number
    width:  flags bit width
    chars:  the chars corresponding to the bits;
            padded with ignore chars if shorter than width
    ignore: the char to ignore

    The flags are returned starting at the LSB.
    """
    flags = castint(flags, width, UNSIGNED)
    ret = ''
    for i in range(width):
        c = chars[i] if i < len(chars) else ignore
        ret += c if c != ignore and flags & 1 else ignore
        flags >>= 1
    return ret

    
def flagstring(flags, width, names, empty=''):
    """Convert bit flags to string of names.

    'flags' is the bitmap number and 'width' its bit width (16/32/64).
    'names' maps single-bit masks (e.g. 0x8000, not 0xC000) to string names.
    'empty' is the string to return if no flags are set.

    Leftover bits (not covered by 'names') will be appended in hex.
    """
    flags = castint(flags, width, True)
    unknown = 0
    a = []
    for flag in map(lambda n: 1 << n, range(width)):
        try:
            if flags & flag:
                a += [names[flag]]
        except KeyError:
            unknown |= flag
    if unknown:
        a += [('0x%0'+str(width//4)+'X') % unknown]
    return ', '.join(a) or empty


# -------- Bitfield --------


class BitField(object):
    """List like protocol for bit field manipulation.

    From ActiveState Recipe 113799: bit field manipulation
    <http://code.activestate.com/recipes/113799/>

    Original comments:
        This class allow you to access the individuals bits of a number
        with a protocol similar to list indexing and slicing.
        Since the class doesn't provide a __len__ method, calls like:
        k[-1] of k[2:] wont work.
    """
    
    def __init__(self, value=0):
        self.data = value

    def __getitem__(self, index):
        return (self.data >> index) & 1 

    def __setitem__(self, index, value):
        value = (value & 1) << index
        mask = 1 << index
        self.data  = (self.data & ~mask) | value

# TODO: implement slicing via __get/setitem__
##    def __getslice__(self, start, end):
##        mask = (1 << (end - start)) - 1
##        return (self.data >> start) & mask
##
##    def __setslice__(self, start, end, value):
##        mask = (1 << (end - start)) - 1
##        value = (value & mask) << start
##        mask = mask << start
##        self.data = (self.data & ~mask) | value
##        return (self.data >> start) & mask

    def __int__(self):
        return self.data


# -------- test code --------


if __name__ == '__main__':
    try:

        # signed/unsigned
        for i in range(-4, 4):
            # test boundary cases
            assert uint16(i) == (i if i >= 0 else 0x10000+i)
            assert uint32(i) == (i if i >= 0 else 0x100000000+i)
            assert uint64(i) == (i if i >= 0 else 0x10000000000000000+i)
            # test round-tripping
            assert i == int16(uint16(i))
            assert i == int32(uint32(i))
            assert i == int64(uint64(i))

        # flagstr
        names = { 0x1:'A', 0x2:'B' }
        assert flagstring(0x01, 16, names) == 'A'
        assert flagstring(0x03, 16, names) == 'A, B'
        assert flagstring(0x07, 16, names) == 'A, B, 0x0004'
        assert flagstring(0x10, 16, names) == '0x0010'
        assert flagstring(0x00, 16, names, '--') == '--'

        # bitfield
        x = BitField()
        assert int(x) == 0
        x[8] = 1
        assert int(x) == 256
        x[8] = 0
        assert int(x) == 0
##        x[3:6] = 5
##        assert x[3:6] == 5
##        assert x[3] == 1
##        assert x[4] == 0
##        assert x[5] == 1

    except AssertionError:
        print('test failed')

    else:
        print('all tests passed')
