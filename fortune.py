# TODO: make a real fortune script using linux fortunes
# see <http://en.wikipedia.org/wiki/Fortune_(Unix)>

import random

responses = """
    All your code are belong to us!
"""
print random.choice(responses[1:-1].split('\n')).strip()
