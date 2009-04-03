##import os
##
##
##def process(spec):
##    for s in file(spec):
##        if s[:5] == 'From ':
##            print s.rstrip('\n')
##    print
##    
##
##dir = u'F:\\docs\\internet\\----\\_MAILBOX'
##for s in os.listdir(dir):
##    spec = os.path.join(dir, s)
##    if os.path.isfile(spec):
##        process(spec)

import mailbox
import email


fname = u'F:\\docs\\internet\\----\\_MAILBOX\\MAILBOX.1'
fp = file(fname, 'rb')
mbox = mailbox.UnixMailbox(fp, email.message_from_file)

for m in mbox:
    print '*' * 80
    print str(m)
    print '*' * 80
    print m.as_string()
    print '*' * 80
    break;
    
    