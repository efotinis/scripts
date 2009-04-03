import os
import sys


def split(s):
    """Argv-style splitting of a string into tokens.

    """
    ret = []
    while s:
        next, s = splitFirst(s)
        if next <> None:
            ret.append(next)
    return ret            


def splitFirst(s):
    #s = re.sub(r'\\"', '"', s)
    s = s.strip()
    if not s:
        return None, None
    i = 0
    token = ''
    inQuote = False
    len_s = len(s)
    while i < len_s:
        if s[i:i+2] == '\\"':
            token += '"'
            i += 2
        elif inQuote:
            if s[i:i+3] == '"""':
                token += '"'
                i += 3
            elif s[i:i+2] == '""':
                token += '"'
                i += 2
                inQuote = False
            elif s[i] == '"':
                i += 1
                inQuote = False
            else:
                token += s[i]
                i += 1
        else:  # not inQuote
            if s[i] == '"':
                i += 1
                inQuote = True
            elif s[i].isspace():
                break
            else:
                token += s[i]
                i += 1
    return token, s[i:]                
                
        

##args = sys.argv[1:]
##if args:
##    print args
##else:
##    for n in range(10):
##        os.system('cliOpt.py ' + str(n))

def printStr(s, alphabet, moreChars):
    if not moreChars:
        print s
    else:
        moreChars -= 1
        for c in alphabet:
            printStr(s + c, alphabet, moreChars)


printStr('', ' c"', 3)



### ___"2"2" ___      =>    __22 __
### ___"2""2" ___     =>    __2"2 __
### ___"2"""2" ___    =>    __2"2__
##
##in quoted:
##    
##    """   => '"'
##    ""    => '"' + close_Q
##    "     =>       close_Q
##
##
##class Parser:
##
##    def __init__(self):
##		switchPrefix = '/'      # /X
##		switchValueSep = ':'    # /X:Y
##		tempSwitchEscape = '/'  # turn off switch matching of next token
##		switchEndToken = '//'   # turn off switch matching of all subsequent tokens
##        ...
##        
##    def 
##
