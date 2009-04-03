import random

responses = """
    All your code are belong to us!
"""
print random.choice(responses[1:-1].split('\n')).strip()
