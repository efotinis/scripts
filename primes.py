import collections


# cached list of primes and the max tested number
cache = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
cacheTop = 100


def primeFactors(n):
    """Decompose n to its prime factors; return dict of primes and powers."""
    factors = collections.defaultdict(int)
    while True:
        for i in xrange(2, n/2 + 1):
            if n % i == 0:
                factors[i] += 1
                n /= i
                break
        else:
            factors[n] += 1
            break
    return dict(factors)


def primes(n):
    """Return a list of primes up to n (non-inclusive).

    Could be optimized a bit and cache results incrementally.
    """
    a = []
    for i in xrange(2, n):
        v = primeFactors(i).values()
        if len(v) == 1 and v[0] == 1:
            a.append(i)
    return a


##def xprimes(n):
##    """Like primes() but uses cache."""
##
##
##
##def check(n):
##    """Test whether a number is prime."""
##    if n <= cacheTop:
##        return n in cache
##    for i in xrange(
