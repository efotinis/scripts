"""Various mathematical utilities."""

import math


def gcd(x, y):
    """Calculate greatest common divisor."""
    while x and y:
        if x < y:
            y %= x
        else:
            x %= y
    return x or y


def lcm(x, y):
    """Calculate least common multiplier.

    Uses the fact that gcd(x,y)*lcm(x,y)==x*y.
    """
    return (x * y) / gcd(x, y)


def countcombinations(n, m):
    """Count combinations of m out of n items."""
    if n < m:
        raise ValueError
    return math.factorial(n) / (math.factorial(m) * math.factorial(n - m))


def countpermutations(n, m):
    """Count permutaitons of m out of n items."""
    if n < m:
        raise ValueError
    return math.factorial(n) / math.factorial(n - m)
