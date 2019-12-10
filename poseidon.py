#!python3
# coding: utf8
"""Create combined weather report images from Poseidon System."""

import argparse
import contextlib
import datetime
import io
import os

from bs4 import BeautifulSoup
import dateutil.tz
from PIL import Image, ImageDraw, ImageFont
import requests


def parse_args():
    ap = argparse.ArgumentParser(
        description='create combined image weather reports')
    add = ap.add_argument
    add('-d', dest='outdir',
        help='output directory parent; default is current user desktop')
    args = ap.parse_args()
    if args.outdir is None:
        # FIXME: use proper API for Desktop path to support non-English locales
        args.outdir = os.path.expanduser('~\\Desktop')
    return args


def utc_to_local(dt):
    """http://stackoverflow.com/questions/4770297/python-convert-utc-datetime-string-to-local-datetime#4771733"""
    return dt.replace(tzinfo=dateutil.tz.tzutc()).astimezone(dateutil.tz.tzlocal())


class LocalizedTitle:
    WEEK_DAYS = {i:s for i,s in enumerate('Δευτέρα Τρίτη Τετάρτη Πέμπτη Παρασκευή Σάββατο Κυριακή'.split())}
    DAY_MONTH_FMT = {i:'{} '+s for i,s in enumerate('Ιανουαρίου Φεβρουαρίου Μαρτίου Απριλίου Μαΐου Ιουνίου Ιουλίου Αυγούστου Σεπτεμβρίου Οκτωβρίου Νοεμβρίου Δεκεμβρίου'.split(), 1)}
    def get(self, dt):
        return '{}, {}, {:02}:{:02}'.format(
            self.WEEK_DAYS[dt.weekday()],
            self.DAY_MONTH_FMT[dt.month].format(dt.day),
            dt.hour,
            dt.minute)


class WebApp:

    def __init__(self):
        URL = 'http://poseidonsystem.gr:8004/webapp/weather_forecast/en/?product_id=weather&area_id=gr'
        self.soup = BeautifulSoup(requests.get(URL).text, 'html.parser')
        self.model_date = self.soup.find('div', id='model-date').string

    def parameters(self):
        """List of weather type ID strings."""
        # the "Select Parameter" combo in the page contains the various
        # types in the option values as "meteo^...", where "..." is the type
        options = self.soup.find('select', id='type-picker').find_all('option')
        for o in options:
            yield o['value'].partition('^')[2]

    def dates(self):
        """Prediction dates in pairs of (string id, local datetime).
        
        The string ID is a UTC date in '%y%m%d%H' format.
        """
        options = self.soup.find('select', id='date-picker').find_all('option')
        for o in options:
            id = o['value']
            dt = datetime.datetime.strptime(id, '%y%m%d%H')
            yield id, utc_to_local(dt)

    def image_uri(self, param, date):
        model = self.model_date
        return f'http://poseidon.hcmr.gr/images/meteo{model}gr/gr{param}{date}.png'

    def multiple_image_data(self, date_id, params):
        for p in params:
            url = self.image_uri(p, date_id)
            with requests.get(url) as r:
                yield r.content


class ImageGenerator:

    def __init__(self):
        self.BANNERH = 80
        self.IMGW, self.IMGH = 557, 690
        self.FONT = ImageFont.truetype('arial.ttf', int(self.BANNERH * 0.85))
        self.clr1, self.clr2 = (240,105,66), (152,185,102)
        self.TRIM = (40, 60, 50, 0)  # l,t,r,b border to trim off source images
        
    def create(self, outpath, title, images, altclr):
        images = list(images)
        trimmed_w = self.IMGW - self.TRIM[0] - self.TRIM[2]
        trimmed_h = self.IMGH - self.TRIM[1] - self.TRIM[3]
        im = Image.new('RGB', (
            trimmed_w * len(images), 
            trimmed_h + self.BANNERH
        ))
        for i, data in enumerate(images):
            im2 = Image.open(io.BytesIO(data)).crop((
                self.TRIM[0],
                self.TRIM[1],
                self.IMGW - self.TRIM[2],
                self.IMGH - self.TRIM[3]
            ))
            im.paste(im2, (trimmed_w * i, self.BANNERH))
        dr = ImageDraw.Draw(im)
        clr = self.clr2 if altclr else self.clr1
        dr.text((0, 0), title, font=self.FONT, fill=clr)
        im.save(outpath, 'PNG')


class DateSequenceLargeDelta:
    def __init__(self, threshold: datetime.timedelta):
        self.previous = None
        self.threshold = threshold
    def check(self, current: datetime.datetime) -> bool:
        ret = self.previous is not None and current - self.previous > self.threshold
        self.previous = current
        return ret


def main(args):
    desired_params = ['cloud', 'rain', 'windb', 'tem']
    app = WebApp()
    assert all(p in app.parameters() for p in desired_params)

    outdir = 'poseidon ' + datetime.datetime.now().strftime('%Y-%m-%d %H%M')
    outdir = os.path.join(args.outdir, outdir)
    os.makedirs(outdir, exist_ok=True)

    imgen = ImageGenerator()
    loctitle = LocalizedTitle()
    bigdelta = DateSequenceLargeDelta(datetime.timedelta(hours=3))
    dates = list(app.dates())

    for index, (date_id, local_date) in enumerate(dates, 1):
        print(f'image {index} of {len(dates)} ...', end='\r', flush=True)

        is_long_interval = bigdelta.check(local_date)
        outname = local_date.strftime('%Y-%m%d-%H%M') + '.png'
        imgen.create(
            outpath=os.path.join(outdir, outname), 
            title=loctitle.get(local_date), 
            images=app.multiple_image_data(date_id, desired_params), 
            altclr=is_long_interval)

    print(f'generated {len(dates)} images')


if __name__ == '__main__':
   main(parse_args())
