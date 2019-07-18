# Print info of RSS feed entries.

import argparse
import datetime
import feedparser


def parse_args():
    ap = argparse.ArgumentParser(description='dump RSS entry info')
    ap.add_argument('url', help='RSS location')
    ap.add_argument('-t', dest='trimlen', type=int, help='trim all string fields to specified length')
    return ap.parse_args()


def trim_long_string_properties_recursively(obj, maxlen):
    """Walk nested object properties and limit string length."""
    if maxlen < 1:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and len(v) > maxlen:
                obj[k] = v[:maxlen-1] + '_'
            trim_long_string_properties_recursively(v, maxlen)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, str) and len(v) > maxlen:
                obj[i] = v[:maxlen-1] + '_'
            trim_long_string_properties_recursively(v, maxlen)


if __name__ == '__main__':
    args = parse_args()
    f = feedparser.parse(args.url)
    if args.trimlen:
        trim_long_string_properties_recursively(f, args.trimlen)
    for i, e in enumerate(f.entries, 1):
        print('{0:2} {1:10} {2:>8} {3}'.format(
            i,
            str(datetime.date(*e.published_parsed[:3])),
            e.itunes_duration.rjust(7),
            e.title
        ))
