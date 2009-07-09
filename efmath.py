"""Various mathematical utilities."""

import math


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
    return (a * b) / gcd(a, b)


def countcombinations(n, m):
    """Count combinations of m out of n items."""
    if n < m:
        raise ValueError
    return math.factorial(n) / (math.factorial(m) * math.factorial(n - m))


def countpermutations(n, m):
    """Count permutations of m out of n items."""
    if n < m:
        raise ValueError
    return math.factorial(n) / math.factorial(n - m)
