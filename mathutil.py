"""Various mathematical utilities."""

from __future__ import division
import math
import string


BASE36_DIGITS = string.digits + string.ascii_lowercase


def gcd(a, b):
    """Calculate greatest common divisor.

    reduce(gcd, <seq>) can be used for more than 2 numbers.
    """
    if int(a) != a or int(b) != b:
        raise ValueError('gcd() only accepts integral values')
    while b != 0:
        a, b = b, a % b
    return abs(a)


def lcm(a, b):
    """Calculate least common multiplier.

    Uses the fact that gcd(x,y)*lcm(x,y)==x*y.
    """
    return (a * b) // gcd(a, b)


def countcombinations(n, m):
    """Count combinations of m out of n items."""
    if n < m:
        raise ValueError
    return math.factorial(n) // (math.factorial(m) * math.factorial(n - m))


def countpermutations(n, m):
    """Count permutations of m out of n items."""
    if n < m:
        raise ValueError
    return math.factorial(n) // math.factorial(n - m)


def str_base(num, base, digits=BASE36_DIGITS):
    """Convert an integer to a custom base string.

    Inverse of int(s,base), except that no base prefix is added.
    Based on http://code.activestate.com/recipes/65212/#c10 .
    """
    if not 2 <= base <= len(digits):
        raise ValueError('base must be >= 2 and <= %d' % len(digits))
    if num == 0:
        return '0'
    if num < 0:
        sign = '-'
        num = -num
    else:
        sign = ''
    result = ''
    while num:
        num, remainder = divmod(num, base)
        result = digits[remainder] + result
    return sign + result
