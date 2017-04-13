"""Math utilities."""

from __future__ import division
import math
import string
import operator


BASE36_DIGITS = string.digits + string.ascii_lowercase


def gcd(a, *seq):
    """Calculate the greatest common divisor of one or more numbers.

    Better than fractions.gcd() in that:
    - it accepts multiple arguments
    - input numbers are implicitly converted to integer
    - result is always non-negative
    - commutativity works

    See <http://bugs.python.org/issue22477>.
    """
    a = int(a)
    for b in seq:
        b = int(b)
        while b:
            a, b = b, a % b
    return abs(a)


def lcm(a, *seq):
    """Calculate the least common multiplier of one or more non-zero numbers.

    Input numbers are implicitly converted to integer. Result is always
    non-negative.
    
    Note that we calculate the result by using the identity
    gcd(x,y)*lcm(x,y)==|x*y|, which is only true for 2 numbers, and
    applying it successively.
    """
    return abs(reduce(lambda x, y: x * y // gcd(x, y), seq, a))


def countcombinations(n, r):
    """Count combinations of r out of n items."""
    if n < r:
        raise ValueError('set size is less than subset size')
    return math.factorial(n) // (math.factorial(r) * math.factorial(n - r))


def countpermutations(n, r):
    """Count permutations of r out of n items."""
    if n < r:
        raise ValueError('set size is less than subset size')
    return math.factorial(n) // math.factorial(n - r)


# names commonly used in calculators
nCr = countcombinations
nPr = countpermutations


def str_base(num, base, digits=BASE36_DIGITS):
    """Convert an integer to a custom base string.

    Inverse of int(s,base), except that no base prefix is added.
    Based on <http://code.activestate.com/recipes/65212/#c10>.
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


def multi_divmod(numerator, *denominators):
    """Multiple-divisor divmod(); see PEP 303 (rejected).

    This implementation is a slighty faster variation of the one in 
    <http://mail.python.org/pipermail/python-dev/2005-June/054285.html>.
    """
    ret = ()
    for denominator in reversed(denominators):
        numerator, remainder = divmod(numerator, denominator)
        ret = (remainder,) + ret
    return (numerator,) + ret


def round_to_sgnf(x, digits):
    """Round float to significant digits.

    Source: Roy Hyunjin Han's comment to:
        http://stackoverflow.com/questions/3410976/how-to-round-a-number-to-significant-figures-in-python#3411435
    """
    return round(x, -int(math.floor(math.log10(x))) + (digits - 1))
