'''Upload text to Pastebin.com.'''

import sys
import argparse
import httplib
import urllib
import contextlib
import collections


PASTEBIN_HOST = 'pastebin.com'
PASTEBIN_API = '/api_public.php'
EXPIRE_TIMES = collections.OrderedDict([
    ('n', 'never'), ('10m', '10 min'), ('1h', '1 hour'), ('1d', '1 day'), ('1m', '1 month')])


def parse_args():
    """Parse cmdline."""
    ap = argparse.ArgumentParser(
        description='upload text to pastebin.com and get paste link',
        add_help=False)

    ap.add_argument(dest='text', metavar='TEXT', nargs='?',
                    help='text data; if omitted, reads from STDIN')
    ap.add_argument('-n', dest='name',
                    help='paster\'s name (may also be used as a title)')
    ap.add_argument('-m', dest='email',
                    help='email to send link')
    ap.add_argument('-s', dest='subdomain', 
                    help='use specific subdomain (i.e. post to subdomain.pastebin.com)')
    ap.add_argument('-p', dest='private', action='store_true',
                    help='make private')
    ap.add_argument('-e', dest='expire', metavar='EXPIRE', choices=EXPIRE_TIMES,
                    help='expiration time: ' +
                    ', '.join('"%s" (%s)' % (k,v) for k,v in EXPIRE_TIMES.iteritems()) +
                    '; default is never')
    ap.add_argument('-f', dest='format', 
                    help='format for highlighting (e.g. vb, python, cpp); '
                    'default is "text" (i.e. none); check site for available options')
    ap.add_argument('-?', action='help',
                    help='this help')

    args = ap.parse_args()

    if args.text is None:
        args.text = sys.stdin.read()
    
    return args


if __name__ == '__main__':

    args = parse_args()

    # POST params
    params = {'paste_code': args.text}  # required
    if args.name:      params['paste_name']        = args.name
    if args.email:     params['paste_email']       = args.email
    if args.subdomain: params['paste_subdomain']   = args.subdomain
    if args.private:   params['paste_private']     = 1
    if args.expire:    params['paste_expire_date'] = args.expire.upper()
    if args.format:    params['paste_format']      = args.format
    
    params = urllib.urlencode(params)
    headers = {'Content-type': 'application/x-www-form-urlencoded',
               'Accept': 'text/plain'}

    with contextlib.closing(httplib.HTTPConnection(PASTEBIN_HOST)) as conn:
        conn.request('POST', PASTEBIN_API, params, headers)
        response = conn.getresponse()  # always '200 OK'
        data = response.read()

    if data.startswith('ERROR:'):
        # error message
        print >>sys.stderr, data
    else:
        # paste link
        print data
