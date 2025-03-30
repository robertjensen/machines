import time
import socket
import datetime
import threading

import requests

from PIL import Image, ImageDraw, ImageFont, ImageTk
from tkinter import Tk, Canvas, Button, Label# , Toplevel, PhotoImage, Label

from display_updater import DisplayUpdater
from weather_updater import WeatherUpdater
from forecast_updater import ForecastUpdater

from PyExpLabSys.common.value_logger import ValueLogger
from PyExpLabSys.common.database_saver import ContinuousDataSaver
# import PyExpLabSys.drivers.weather_info as weather_info
import PyExpLabSys.drivers.luxaflex as luxaflex
import credentials


FONT = ('DejaVuSans.ttf', 18)
HEADLINE = ('DejaVuSans.ttf', 20)


class Display(object):
    def __init__(self):
        self.root = Tk()
        # self.root.geometry('480x800')
        self.root.geometry('800x480')
        self.root.overrideredirect(1)  # Fullscreen
        self.root.config(cursor="none")
        self.root.bind('<Button 1>', self.mouse_click)

        self.hiding_forecast = False
        self.canvas = Canvas(self.root, width=800, height=480, bg='white')

        self.canvas.create_text(780, 470, fill="red", font=HEADLINE, text='Temperatur', anchor='nw', angle=180)
        self.canvas.create_text(580, 470, fill="red", font=HEADLINE, text='Fugt', anchor='nw', angle=180)

        self.stue_temp = self.canvas.create_text(
            780, 430, fill="darkblue", font=FONT, text='Stue .....C', anchor='nw', angle=180)
        self.stue_hum = self.canvas.create_text(
            580, 430, fill="darkblue", font=FONT, text='Stue ....0%', anchor='nw', angle=180)

        self.bad_temp = self.canvas.create_text(
            780, 390, fill="darkblue", font=FONT, text='Bad', anchor='nw', angle=180)
        self.bad_hum = self.canvas.create_text(
            580, 390, fill="darkblue", font=FONT, text='Bad', anchor='nw', angle=180)

        self.sia_temp = self.canvas.create_text(
            780, 350, fill="darkblue", font=FONT, text='Sia .....C', anchor='nw', angle=180)
        self.sia_hum = self.canvas.create_text(
            580, 350, fill="darkblue", font=FONT, text='Sia .....%', anchor='nw', angle=180)

        self.sove_temp = self.canvas.create_text(
            780, 310, fill="darkblue", font=FONT, text='Sove .....C', anchor='nw', angle=180)
        self.sove_hum = self.canvas.create_text(
            580, 310, fill="darkblue", font=FONT, text='Sove .....%', anchor='nw', angle=180)

        self.stue_dust = self.canvas.create_text(
            780, 50, fill="darkblue", font=FONT, text='Støv ....μg/cm³', anchor='nw', angle=180)

        self.canvas.create_text(360, 470, fill="red", font=HEADLINE,
                                text='Vejret udenfor', anchor='nw', angle=180)
        self.out_temp = self.canvas.create_text(
            360, 430, fill="darkblue", font=FONT, text='Temperatur: ', anchor='nw', angle=180)
        self.out_hum = self.canvas.create_text(
            360, 390, fill="darkblue", font=FONT, text='Luftfugtighed: ', anchor='nw', angle=180)

        self.out_wind = self.canvas.create_text(
            360, 350, fill="darkblue", font=FONT, text='Vind: ', anchor='nw', angle=180)
        # self.out_wind_gust = self.canvas.create_text(
        #    150, 250, fill="darkblue", font=FONT, text='Stød: ', anchor='nw')
        self.out_wind_dir = self.canvas.create_text(
            110, 350, fill="darkblue", font=FONT, text='Retning: ', anchor='nw', angle=180)

        self.sunrise = self.canvas.create_text(
            360, 310, fill="darkblue", font=FONT, text='Solopgang: ', anchor='nw', angle=180)
        self.sunset = self.canvas.create_text(
            360, 270, fill="darkblue", font=FONT, text='Solnedgang: ', anchor='nw', angle=180)

        # self.ude_inde= self.canvas.create_text(
        #     260, 400, fill="darkblue", font=FONT, text='Ude-inde ', anchor='nw', angle=270)
        self.dmi_time = self.canvas.create_text(
            360, 200, fill="darkblue", font=FONT, text='DMI data: ', anchor='nw', angle=180)
        # tid, pressure':  'sunrise':  'sunset':, 'uv_index'

        # self.canvas.create_rectangle(90, 600, 10, 800, fill="yellow")
        filename = '/run/user/1000/forecast.png'
        img = Image.open(filename)
        # img = img.resize((800, 480))#, Image.ANTIALIAS)
        img = ImageTk.PhotoImage(img.rotate(180))
        self.forecast_display = Label(self.root, image=img)
        self.forecast_display.image = img
        self.forecast_display.pack()

        # forecast_placeholder = ImageTk.PhotoImage(Image.new('RGBA', (15, 15), '#00000000'))
        # forecast_placeholder = ImageTk.PhotoImage(file='/run/user/1000/forecast.png')
        # forecast_placeholder = ImageTk.PhotoImage(file='/run/user/1000/forecast.png')
        #self.forecast_display = self.canvas.create_image(
        #    0, 0, image=forecast_placeholder, anchor='nw', state='normal')
        # self.forecast_display = Label(self.root, forecast_placeholder)
        # self.forecast_display.pack()
        # Start thread to get newest forefocast from DMI
        # self.fu = ForecastUpdater(self)
        # self.fu.start()
        self.canvas.pack()

        self.fu = ForecastUpdater(self)
        self.fu.start()

        self.wu = WeatherUpdater(self)
        self.wu.start()
        # self.pv = luxaflex.PowerView('192.168.1.76')
        # self.pv.find_all_shades()

        
    def mouse_click(self, eventorigin):
        print(eventorigin.x)
        print(eventorigin.y)

        # if self.hiding_forecast:
        #     self.pv.move_shade(8496, percent_pos=90)
        
        if self.hiding_forecast:
        #     if (10 < eventorigin.x < 90) and (600 < eventorigin.y < 800): 
        #         self.pv.update_shade(8496)
        #         openness = self.pv.print_current_shade_status(8496)
        #         if openness > 95:
        #             print('Close to 40%')
        #             self.pv.move_shade(8496, percent_pos=40)
        #         else:
        #             print('Open')
        #             self.pv.move_shade(8496, percent_pos=100)
        #             time.sleep(3)
        #             self.pv.update_shade(8496)
        #             openness = self.pv.print_current_shade_status(8496)
        #             if openness < 42:
        #                 print('Did not open, try again')
        #                 self.pv.move_shade(8496, percent_pos=100)
            print('Show forecast')
            # filename = '/run/user/1000/forecast.png'
            # img = Image.open(filename)
            # # img = img.resize((800, 480))#, Image.ANTIALIAS)
            # img = ImageTk.PhotoImage(img.rotate(180))
            # self.forecast_display = Label(self.root, image=img)
            # self.forecast_display.image = img
            # self.forecast_display.pack()

            self.forecast_display.place(relx = 0.5, 
                                        rely = 0.5,
                                        anchor = 'center')
            # self.canvas.itemconfigure(self.forecast_display, state='normal')
            self.hiding_forecast = False
        else:
            print('Show measurements')
            self.forecast_display.place(relx = 1.5, 
                                        rely = 1.5,
                                        anchor = 'nw')
            # self.canvas.itemconfigure(self.forecast_display, state='hidden')
            self.hiding_forecast = True


class Reader(object):
    def __init__(self, weather_updater):
        self.wu = weather_updater
        # Info for ude-inde here as well, if this is available in updater, value()
        # could be moved, and this class could go away.
        
    def value(self, channel):
        wd = self.wu.weather.weather_data
        return_val = None
        try:
            if channel == 1:
                return_val = wd.get('temperature')
            if channel == 2:
                if 'humidity' in wd:
                    return_val = wd['humidity'] * 100
            if channel == 3:
                if 'pressure' in wd:
                    return_val = wd['pressure'] / 100
            if channel == 4:
                return_val = wd.get('wind')
            if channel == 5:
                return_val = wd.get('wind_direction')
            if channel == 6:
                return_val = float(self.wu.indoor_hum)
        except TypeError:
            pass
        return return_val

class DataSaver(threading.Thread):
    def __init__(self,  reader):
        threading.Thread.__init__(self)
        self.reader = reader
      
    def run(self):
        codenames = [
            'wheater_temperature', 'wheater_humidity',
            'wheater_air_pressure', 'wheater_wind_speed', 'wheater_wind_direction',
            'home_humidity_outdoor_indoor'
        ]

        print('wait start 10s')
        time.sleep(10)
        print('Wait end')

        loggers = {}
        for i in range(0, 6):
            loggers[codenames[i]] = ValueLogger(reader, comp_val=0.25, comp_type='lin',
                                                channel=i + 1)
            loggers[codenames[i]].start()

        table = 'dateplots_rued_langgaards_vej'
        db_logger = ContinuousDataSaver(continuous_data_table=table,
                                        username=credentials.user,
                                        password=credentials.passwd,
                                        measurement_codenames=codenames)
        db_logger.start()

        # while reader.isAlive():
        while True:
            time.sleep(1)
            for name in codenames:
                value = loggers[name].read_value()
                if loggers[name].read_trigged():
                    print(name, value, type(value))
                    db_logger.save_point_now(name, value)
                    loggers[name].clear_trigged()

            
if __name__ == '__main__':
    app = Display()
    
    display_updater = DisplayUpdater(app)
    display_updater.start()

    # reader = Reader(wu)
    # data_saver = DataSaver(reader)
    # data_saver.start()

    app.root.mainloop()

