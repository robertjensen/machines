import time
import datetime
import threading
import subprocess

import requests
from PIL import Image, ImageDraw, ImageFont, ImageTk
from tkinter import Label

class ForecastUpdater(threading.Thread):
    # Copy exists in old.py, feel free to modify this version
    def __init__(self, display):
        threading.Thread.__init__(self)
        self.name='ForecastUpadterThread'
        self.display = display

        # self.url = 'http://servlet.dmi.dk/byvejr/servlet/byvejr_dag1?by=1000&mode=long&eps=true'
        self.url = 'https://www.yr.no/nb/innhold/2-9034952/meteogram.svg'
        
        self.latest_hour = -1
        self.update_image()

    def update_image(self, rotate=True):
        print('Update Forecast')
        self.latest_hour = datetime.datetime.now().hour
        try:
            r = requests.get(self.url, stream=True)
            with open('/run/user/1000/forecast.svg', "wb") as f:
                f.write(r.content)
        except requests.exceptions.ConnectionError:
            print('Failed to get updated svg from yr.no')
            return

        cmd_list = [
            '/usr/bin/inkscape',  
            '/run/user/1000/forecast.svg',
            '--export-width', '800',
            '--export-height', '480',
            '-o', '/run/user/1000/forecast.png'
        ]
        subprocess.run(cmd_list, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Now the png is ready, but it wuld be nice to crop it to use the sceen
        # a bit more efficiently
        filename = '/run/user/1000/forecast.png'
        img = Image.open(filename)
        img = ImageTk.PhotoImage(img.rotate(180))
        self.display.forecast_display.configure(image=img)
        self.display.forecast_display.image = img

    def run(self):
        while True:
            now = datetime.datetime.now()
            if now.hour == self.latest_hour:
                time.sleep(180)
                continue

            # We are an hour later that last time:
            if now.minute < 10:
                print('Not updating')
                time.sleep(60)
                continue
            print('Updating')
            self.update_image()


if __name__ == '__main__':
    FU = ForecastUpdater('')

    FU.update_image()
