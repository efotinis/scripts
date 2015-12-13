import sys
import time
import random


class Status:
    def __init__(self):
        self.text = ''
    def update(self, s):
        extra = len(self.text) - len(s)
        self.text = s + (' ' * extra if extra > 0 else '')
        print(self.text + '\r', end='')
    def hide(self):
        return self._Hide(self)
    def __enter__(self):
        return self
    def __exit__(self, x,y,z):
        self.update('')
    class _Hide:
        def __init__(self, status):
            self.st = status
        def __enter__(self):
            self.text = self.st.text
            self.st.update('')
        def __exit__(self, x,y,z):
            self.st.update(self.text)
        
    
if __name__ == '__main__':
    MAX = 50
    A = [random.randint(1, MAX) for i in range(MAX)]
    with Status() as st:
        for i, n in enumerate(A):
            st.update('{}/{}'.format(i,MAX))
            if n % 10 == 0:
                with st.hide():
                    print('***', i, n)
            time.sleep(0.1)
