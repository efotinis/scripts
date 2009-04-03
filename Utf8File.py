import os
import codecs


class Utf8File:
    """File that reads Unicode strings and writes them as UTF-8."""

    def __init__(self, name, mode):
        self.f = open(name, mode)
        self.encoder = codecs.getencoder('utf8')
        self.decoder = codecs.getdecoder('utf8')

    def close(self):
        self.f.close()

    def write(self, s):
##        if not isinstance(s, unicode):
##            raise True
        self.f.write(self.encoder(s)[0])

    def writelines(self, a):
        for s in a:
            self.write(self.encoder(s)[0])

    def readline(self):
        s = self.f.readline()
        return self.decoder(s)[0]

    def readlines(self):
        a = self.readlines()
        for i in xrange(len(a)):
            a = self.decoder(a[i])[0]

    def __iter__(self):
        return self

    def next(self):
        s = self.readline()
        if not s:
            raise StopIteration
        return s
