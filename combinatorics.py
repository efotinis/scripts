"""Functions for combinations and permutations."""
# EF  2008.01.01


def fact(n):
    """Return factorial of integer."""
    n = int(n)
    if n <= 1:
        return 1
    ret = 1
    while n > 1:
        ret *= n
        n -= 1
    return ret


def _gen(pool, coll, size, partition):
    """Inernal generator for combinations and permutations."""
    if len(coll) == size:
        yield coll
    else:
        for i, n in enumerate(pool):
            for a in _gen(partition(pool, i), coll + (n,), size, partition):
                yield a

def _combos(pool, coll, size):
    return _gen(pool, coll, size, lambda a, i: a[i+1:])

def _permus(pool, coll, size):
    return _gen(pool, coll, size, lambda a, i: a[:i] + a[i+1:])


def combos(a, n):
    """Generate combinations of n items from a sequence."""
    return _combos(a, (), n)

def combocount(n, m):
    """Count combinations of m out of n items."""
    return fact(n) / (fact(m) * fact(n - m)) if n >= m else 0

def permus(a, n):
    """Generate permutaitons of n items from a sequence."""
    return _permus(a, (), n)

def permucount(n, m):
    """Count permutaitons of m out of n items."""
    return fact(n) / fact(n - m) if n >= m else 0


if __name__ == '__main__':
    a = range(8)
    m = 5
    assert len(list(combos(a, m))) == combocount(len(a), m)
    assert len(list(permus(a, m))) == permucount(len(a), m)

    a = range(3)
    m = 2
    assert list(combos(a, m)) == [ (0,1), (0,2), (1,2) ]
    assert list(permus(a, m)) == [ (0,1), (0,2), (1,0), (1,2), (2,0), (2,1) ]

    print 'combinatorics: all tests passed'
    