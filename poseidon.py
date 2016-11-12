#!python3
#encoding:utf8
"""Create combined weather report images from Poseidon System."""

import argparse
import collections
import contextlib
import datetime
import io
import os
import re

from bs4 import BeautifulSoup
from dateutil import tz
from PIL import Image, ImageDraw, ImageFont
import requests


DAY_OF_WEEK = {i:s for i,s in enumerate('Δευτέρα Τρίτη Τετάρτη Πέμπτη Παρασκευή Σάββατο Κυριακή'.split())}
MONTH_WITH_DAY_FMT = {i:'{} '+s for i,s in enumerate('Ιανουαρίου Φεβρουαρίου Μαρτίου Απριλίου Μαΐου Ιουνίου Ιουλίου Αυγούστου Σεπτεμβρίου Οκτωβρίου Νοεμβρίου Δεκεμβρίου'.split(), 1)}


def parse_args():
    ap = argparse.ArgumentParser(
        description='create combined image weather reports')
    add = ap.add_argument
    add('-d', dest='outdir',
        help='output directory parent; default is current user desktop')
    args = ap.parse_args()
    if args.outdir is None:
        args.outdir = os.path.expanduser('~\\Desktop')  # FIXME: proper desktop path
    return args


def utc_to_local(dt):
    """http://stackoverflow.com/questions/4770297/python-convert-utc-datetime-string-to-local-datetime#4771733"""
    return dt.replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())


'''
16102209 21 10 16gr10 - 2016-10-22 12:00:00+03:00
http://www.poseidon.hcmr.gr/images/meteo/2016/10/21/gr/grwindb16102209.png
...
16102612 21 10 16gr33 - 2016-10-26 15:00:00+03:00
http://www.poseidon.hcmr.gr/images/meteo/2016/10/21/gr/grwindb16102612.png
'''

TimePoint = collections.namedtuple('TimePoint', 'timestamp day month year localdate')


def img_url(param, tp):
    """Build image URL."""
    return 'http://www.poseidon.hcmr.gr/images/meteo/20{}/{}/{}/gr/gr{}{}.png'.format(
        tp.year, tp.month, tp.day, param, tp.timestamp)


def get_params(soup):
    """Generate (id, name) of available weather parameters."""
    sel = soup.find('select', attrs={'name':'parameterSelect'})
    for opt in sel.find_all('option'):
        yield opt['value'], opt.string.strip()


def get_times(soup):
    """Generate TimePoints of available weather times."""
    sel = soup.find('select', id='fordaySelect')
    for opt in sel.find_all('option'):
        text = opt.string.strip()
        if text.lower() == 'animation':
            continue
        date = utc_to_local(datetime.datetime.strptime(text, '%A, %d-%m-%y Hour %H:%M UTC'))
        ts, dy, mo, yr = opt['value'].partition('gr')[0].split()
        yield TimePoint(ts, dy, mo, yr, date)


def greek_time_label(d):
    return '{}, {}, {:02}:{:02}'.format(
        DAY_OF_WEEK[d.weekday()],
        MONTH_WITH_DAY_FMT[d.month].format(d.day),
        d.hour,
        d.minute)


def main(args):
    URL = 'http://www.poseidon.hcmr.gr/weather_forecast.php?area_id=gr'
    html = requests.get(URL).text

    # remove extraneous closing tag that confuses BeautifulSoup
    html = re.sub(r'^\s+</option>\n', '', html, count=1, flags=re.MULTILINE)

    soup = BeautifulSoup(html, 'html.parser')

    outdir = 'poseidon ' + datetime.datetime.now().strftime('%Y-%m-%d %H%M')
    outdir = os.path.join(args.outdir, outdir)
    os.makedirs(outdir, exist_ok=True)

##    timepoints = list(get_times(soup))
##    for param, name in get_params(soup):
##        print(name)
##        for tp in timepoints:
##            url = img_url(param, tp)
##            #outpath = os.path.join(outdir, os.path.basename(url))
##            outstamp = '{0.year:04}-{0.month:02}{0.day:02}-{0.hour:02}{0.minute:02}'.format(tp.localdate)
##            outpath = os.path.join(outdir, '{} {}.png'.format(param, outstamp))
##            with contextlib.closing(requests.get(url)) as r, open(outpath, 'wb') as f:
##                f.write(r.content)

    timepoints = list(get_times(soup))
    params = list(get_params(soup))
    wanted = 'cloud rain windb tem'.split()
    BANNERH = 80
    IMGW, IMGH = 557, 690

    font = ImageFont.truetype('arial.ttf', int(BANNERH * 0.85))
    
    prevdate = None
    for tp in timepoints:

        long_interval = False
        if prevdate:
            hours_diff = (tp.localdate - prevdate).total_seconds() / 3600
            if hours_diff > 3:
                long_interval = True
        prevdate = tp.localdate

        outstamp = '{0.year:04}-{0.month:02}{0.day:02}-{0.hour:02}{0.minute:02}'.format(tp.localdate)
        print(outstamp)
        images = []
        for param, name in params:
            if param not in wanted:
                continue
            url = img_url(param, tp)
            with contextlib.closing(requests.get(url)) as r:
                images.append(r.content)
        outpath = os.path.join(outdir, outstamp + '.png')
        im = Image.new('RGB', (IMGW * len(images), IMGH + BANNERH))
        for i, data in enumerate(images):
            im2 = Image.open(io.BytesIO(data))
            im.paste(im2, (IMGW * i, BANNERH))
        dr = ImageDraw.Draw(im)
        clr = (152,185,102) if long_interval else (240,105,66)
        dr.text((0, 0), greek_time_label(tp.localdate), font=font, fill=clr)
        im.save(outpath, 'PNG')


if __name__ == '__main__':
    main(parse_args())
