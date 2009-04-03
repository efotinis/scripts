import optparse

class OptParser(optparse.OptionParser):
    '''optparse.OptionParser that raises OptParseError on error.'''
    def __init__(self, *args, **kw):
        optparse.OptionParser.__init__(self, *args, **kw)
    def error(self, msg):
        # override to avoid print_usage() and to use simple msg
        raise optparse.OptParseError(msg.rstrip('\n'))
