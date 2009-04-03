# Note that gcd(a,b) * lcm(a,b) = a * b.

def gcd(x, y):
    """Calculate greatest common divisor."""
    while x and y:
        if x < y:
            y %= x
        else:
            x %= y
    return x or y


def lcm(x, y):
    """Calculate least common multiplier."""
    return (x * y) / gcd(x, y)
