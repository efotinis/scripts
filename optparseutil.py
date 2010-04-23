"""optparse utilities.

Contains additional types for option parsing.

Example:

    class CustomOption(optparse.Option):
        '''Extended optparse Option class which includes a 'size' type.'''
        TYPES = optparse.Option.TYPES + ('size',)
        TYPE_CHECKER = copy.copy(optparse.Option.TYPE_CHECKER)
        TYPE_CHECKER['size'] = check_size
"""

import optparse


def check_size(option, opt, value):
    """Custom 'size' type checker for optparse.

    Parses a string of a float with an optional size prefix and returns an truncated int.
    """
    UNITS = 'kmgtpezy'
    if not value:
        raise optparse.OptionValueError('option %s: empty size value' % opt)
    # separate number and factor (if any)
    number, factor = value, 1
    i = UNITS.find(value[-1].lower())
    if i != -1:
        factor = 1024 ** (i + 1)
        number = value[:-1]
    # calc result
    try:
        return int(float(number) * factor)
    except ValueError:
        raise optparse.OptionValueError('option %s: bad size value "%s"' % (opt, value))

