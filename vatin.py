"""VAT Identification Number testing utilities.

Created on 25/04/2010 as a simple checksum tester of Greek VATINs.

tags: tax, commerce
"""

import re


class Error(Exception): pass
class CountryCodeError(Error): pass
class NoChecksumError(Error): pass


# see <http://en.wikipedia.org/wiki/Vat_number> for more
# legend:
#    9   digit
#    L   letter
#    X   digit/letter
#    S   digit/letter/'+'/'*'
#    `   next character verbatim
#    <   0-4
#    >   5-9
#
DATABASE = {
    'AT': r'U\d{8}',  # Austria: '`U99999999'
    'BE': r'0\d{9}',  # Belgium: '`0999999999'
    'BG': r'\d{9}\d?',  # Bulgaria: '999999999(9)'
    'HR': r'\d{11}',  # Croatia: '99999999999'
    'CY': r'\d{8}[A-Z]',  # Cyprus: '99999999L'
    'CZ': r'\d{8,10}',  # Czech Republic: '99999999(9(9))'
    'DK': r'\d{8}',  # Denmark: '99999999'
    'EE': r'\d{9}',  # Estonia: '999999999'
    'FI': r'\d{8}',  # Finland: '99999999'
    'FR': r'[0-9A-Z]{2}\d{9}',  # France: 'XX999999999'
    'DE': r'\d{9}',  # Germany: '999999999'
    'EL': r'\d{9}',  # Greece: '999999999'
    'HU': r'\d{8}',  # Hungary: '99999999'
    'IE': r'\d[0-9A-Z+*]\d{5}[A-Z]',  # Ireland: '9S99999L'
    'IT': r'\d{11}',  # Italy: '99999999999'
    'LV': r'\d{11}',  # Latvia: '99999999999'
    'LT': r'\d{9}(\d{3})?',  # Lithuania: '999999999(999)'
    'LU': r'\d{8}',  # Luxembourg: '99999999'
    'MT': r'\d{8}',  # Malta: '99999999'
    'NL': r'\d{9}B\d{2}',  # Netherlands: '999999999`B99'
    'PL': r'\d{10}',  # Poland: '9999999999'
    'PT': r'\d{9}',  # Portugal: '999999999'
    'RO': r'\d{2,10}',  # Romania: '99(9(9(9(9(9(9(9(9))))))))'
    'SK': r'\d{10}',  # Slovakia: '9999999999'
    'SI': r'\d{8}',  # Slovenia: '99999999'
    'ES': r'[0-9A-Z]\d{7}[0-9A-Z]',  # Spain: 'X9999999X'
    'SE': r'\d{10}01',  # Sweden: '9999999999`0`1'
    'GB': r'(\d{9}(\d{3})?|GD[0-4]\d{2}|HA[5-9]\d{2})',  # UK/Isle of Man: '999999999(999)', '`G`D<99', '`H`A>99'
}

# convert regexp patterns to functions testing a string to a compiled regexp
DATABASE = {cc: lambda s, rx=re.compile('^' + pattern + '$'): rx.match(s) is not None
            for cc, pattern in DATABASE.items()}


def normalize(s):
    """Remove spacing characters and convert to uppercase."""
    return s.replace(' ', '').replace('-', '').upper()


def get_format_func(country):
    """Get the format test function for a specific country."""
    try:
        return DATABASE[country]
    except KeyError:
        raise CountryCodeError(country)


def get_checksum_func(country):
    """Get the checksum test function for a specific country."""
    try:
        return globals()['_checksum_' + country]
    except KeyError:
        raise NoChecksumError(country)


def test_format(s):
    """Check the general format of a normalized VATIN."""
    country, data = s[:2], s[2:]
    return get_format_func(country)(data)


def test_checksum(s):
    """Verify checksum (if possible) of a properly formatted VATIN."""
    country, data = s[:2], s[2:]
    return get_checksum_func(country)(data)


def validate(s):
    """Validate the existance of a VATIN."""
    # could use the form at:
    #   http://ec.europa.eu/taxation_customs/vies/vieshome.do
    raise NotImplementedError


# --- start of individual country checksum functions ---

def _checksum_EL(s):
    n = sum(int(c) * 2**(8-i) for i,c in enumerate(s[:8])) % 11
    if n == 10:
        n = 0
    return n == int(s[-1])

# --- end of individual country checksum functions ---
