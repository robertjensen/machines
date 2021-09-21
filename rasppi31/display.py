import time
import socket
import datetime
import threading

import requests

from PIL import Image, ImageDraw, ImageFont, ImageTk
from tkinter import Tk, Canvas

import PyExpLabSys.drivers.weather_info as weather_info
import credentials


FONT = ('DejaVuSans.ttf', 18)
HEADLINE = ('DejaVuSans.ttf', 20)

class ForecastUpdater(threading.Thread):
    def __init__(self, display):
        threading.Thread.__init__(self)
        self.display = display
        # todo, rewrite to use requests syntax for parameters
        self.url = 'http://servlet.dmi.dk/byvejr/servlet/byvejr_dag1?by=1000&mode=long&eps=true'
        self.latest_hour = -1
        self.update_image()

    # def update_image(self, rotate=False):
    def update_image(self, rotate=True):
        self.latest_hour = datetime.datetime.now().hour

        r = requests.get(self.url, stream=True)
        forecast  = Image.open(r.raw)
        if rotate:
            forecast = forecast.rotate(270, expand=True)
            # In wide-screen mode, a slight stretch is needed
            forecast = forecast.resize((480, 800), Image.ANTIALIAS)
        else:
            wanted_size=480
            scaled_height = int(wanted_size * (forecast.size[1] / forecast.size[0]))
            forecast = forecast.resize((wanted_size, scaled_height), Image.ANTIALIAS)

        self.forecast_image = ImageTk.PhotoImage(forecast)
        self.display.canvas.itemconfigure(self.display.forecast_display, image=self.forecast_image)

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


class WeatherUpdater(threading.Thread):
    def __init__(self, display):
        threading.Thread.__init__(self)
        self.display = display
        self.update_time = datetime.datetime.now()

        self.weather = weather_info.WheatherInformation(
            y_pos=55.660105,
            x_pos=12.589183,
            open_weather_appid=credentials.appid,
            dmi_prio={
                0: '06180'
                #0: '06186',
                #1: '06180'
            },
        )

    def angle_to_compass(self):
        compass = 'Error'
        direction = self.weather.weather_data['wind_direction']
        if direction < 11.25 or direction > 348.75:
            compass = 'N'
        elif 11.25 < direction <= 33.75:
            compass = 'NNØ'
        elif 33.75 < direction <= 56.25:
            compass = 'NØ'
        elif 56.25 < direction <= 78.75:
            compass = 'ØNØ'
        elif 78.75 < direction <= 101.25:
            compass = 'Ø'
        elif 101.25 < direction <= 123.75:
            compass = 'ØSØ'
        elif 123.75 < direction <= 146.25:
            compass = 'SØ'
        elif 146.25 < direction <= 168.75:
            compass = 'SSØ'
        elif 168.75 < direction <= 191.25:
            compass = 'S'
        elif 191.25 < direction <= 213.75:
            compass = 'SSV'
        elif 213.75 < direction <= 236.25:
            compass = 'SV'
        elif 236.25 < direction <= 258.75:
            compass = 'VSV'
        elif 258.75 < direction <= 281.25:
            compass = 'V'
        elif 281.25 < direction <= 303.75:
            compass = 'VNV'
        elif 303.75 < direction <= 326.25:
            compass = 'NV'
        elif 326.25 < direction <= 348.75:
            compass = 'NNV'
        return compass

    def update_weather(self):
        self.weather.clear_data()
        self.weather.dk_dmi()
        self.weather.global_openweather()
        self.update_time = datetime.datetime.now()
        print('Update weather')

    def run(self):
        while True:
            try:
                self.update_weather()
            except KeyError:
                # Refine this, please....
                self.update_weather()
            wd = self.weather.weather_data

            if wd['temperature']:
                msg = 'Temperatur: {:.1f}C'.format(wd['temperature'])
                self.display.canvas.itemconfigure(self.display.out_temp, text=msg)
            if wd['humidity']:
                msg = 'Fugt: {:.0f}%'.format(wd['humidity'] * 100)
                self.display.canvas.itemconfigure(self.display.out_hum, text=msg)
            if wd['wind'] and wd['wind_gust']:
                msg = 'Vind: {:.1f} ({:.1f})m/s'.format(wd['wind'], wd['wind_gust'])
                self.display.canvas.itemconfigure(self.display.out_wind, text=msg)
            if wd['wind_direction']:
                msg = 'fra {}'.format(self.angle_to_compass())
                self.display.canvas.itemconfigure(self.display.out_wind_dir, text=msg)

            msg = 'DMI hentet: {}'.format(self.update_time.strftime('%Y-%m-%d %H:%M'))
            self.display.canvas.itemconfigure(self.display.dmi_time, text=msg)

            msg = 'Solopgang: {}'.format(
                datetime.datetime.fromtimestamp(wd['sunrise']).strftime('%H:%M')
            )
            self.display.canvas.itemconfigure(self.display.sunrise, text=msg)
            msg = 'Solnedgang: {}'.format(
                datetime.datetime.fromtimestamp(wd['sunset']).strftime('%H:%M')
            )
            self.display.canvas.itemconfigure(self.display.sunset, text=msg)

                
            # 'time': datetime.datetime(2021, 3, 4, 21, 40),
            # 'precepitation': 0.0,
            # 'pressure': 102080.0,
            # 'uv_index': 0,
            # 'visibility': 10000,
            # 'cloud_percentage': 0

            indoor_hum = weather_info.equaivalent_humidity(
                outside_temp=wd['temperature'],
                outside_hum=wd['humidity'],
                pressure=wd['pressure'],
                inside_temp=24
            )
            msg = 'Ude inde: {:.1f}%'.format(indoor_hum)
            self.display.canvas.itemconfigure(self.display.ude_inde, text=msg)
            
            # Todo, should we do a more fance calculaed wait?
            time.sleep(600)


class Updater(threading.Thread):
    def __init__(self, display):
        threading.Thread.__init__(self)
        self.display = display

    @staticmethod
    def read_network_value(host, data, port=9000):
        attempts = 0
        while -1 < attempts < 3:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(0.5)
                sock.sendto(data, (host, port))
                received = sock.recv(1024).decode()
                # print('data from {}: {}'.format(data, received))
                value = float(received.split(',')[1])
                attempts = -1
            except socket.timeout:
                attempts += 1
                #print('Socket timeout from {}'.format(data))
                value = 0
            except IndexError:
                attempts += 1
                # print('Index Error')
                # OLD_DATA
                value = 0  # TODO!
            except:
                attempts += 1
                print('Unforeseen error')
                value = 0  # TODO!
        sock.close()
        return value                                      
        
    def run(self):
        while True:
            time.sleep(2)
            # print('Read')
            value = self.read_network_value('192.168.1.26', b'home_temperature_living_room#raw')
            msg = 'Stue:  {:.1f}C  '.format(value)
            self.display.canvas.itemconfigure(self.display.stue_temp, text=msg)

            value = self.read_network_value('192.168.1.26', b'home_humidity_living_room#raw')
            msg = 'Stue: {:.1f}%  '.format(value)
            self.display.canvas.itemconfigure(self.display.stue_hum, text=msg)

            # value = self.read_network_value('192.168.1.27', b'home_temperature_bathroom#raw')
            # msg = 'Temp. bad: {:.3f}C'.format(value)
            # self.display.canvas.itemconfigure(self.display.bad_temp, text=msg)

            # value = self.read_network_value('192.168.1.27', b'home_humidity_bathroom#raw')
            # msg = 'Fugt bad: {:.3f}%'.format(value)
            # self.display.canvas.itemconfigure(self.display.bad_hum, text=msg)

            value = self.read_network_value('192.168.1.28', b'home_temperature_sias_room#raw')
            msg = 'Sia:   {:.1f}C  '.format(value)
            self.display.canvas.itemconfigure(self.display.sia_temp, text=msg)

            value = self.read_network_value('192.168.1.28', b'home_humidity_sias_room#raw')
            msg = 'Sia: {:.1f}%  '.format(value)
            self.display.canvas.itemconfigure(self.display.sia_hum, text=msg)

            value = self.read_network_value('192.168.1.26', b'fast_dust#raw', port=9011)
            if value > 0:
                msg = 'Støv {:.2f}μg/cm³    '.format(value)
                self.display.canvas.itemconfigure(self.display.stue_dust, text=msg)


class Display(object):
    # def ___init__(self):
    #     self.root = Tk()
    #     self.root.geometry('480x800')
    #     self.root.overrideredirect(1)  # Fullscreen
    #     self.root.config(cursor="none")
    #     self.root.bind('<Button 1>', self.mouse_click)
    #     self.canvas = Canvas(self.root, width=480, height=800, bg='white')

    #     self.hiding_forecast = False

    #     self.canvas.create_text(10, 5, fill="red", font=HEADLINE, text='Temperatur', anchor='nw')
    #     self.canvas.create_text(240, 5, fill="red", font=HEADLINE, text='Fugt', anchor='nw')
        
    #     self.stue_temp = self.canvas.create_text(
    #         10, 40, fill="darkblue", font=FONT, text='Stue .....C', anchor='nw')
    #     self.stue_hum = self.canvas.create_text(
    #         240, 40, fill="darkblue", font=FONT, text='Stue ....0%', anchor='nw')

    #     self.bad_temp = self.canvas.create_text(
    #         10, 75, fill="darkblue", font=FONT, text='Bad', anchor='nw')
    #     self.bad_hum = self.canvas.create_text(
    #         240, 75, fill="darkblue", font=FONT, text='Bad', anchor='nw')

    #     self.sia_temp = self.canvas.create_text(
    #         10, 110, fill="darkblue", font=FONT, text='Sia .....C', anchor='nw')
    #     self.sia_hum = self.canvas.create_text(
    #         240, 110, fill="darkblue", font=FONT, text='Sia .....%', anchor='nw')

    #     self.stue_dust = self.canvas.create_text(
    #         10, 160, fill="darkblue", font=FONT, text='Støv ....μg/cm³', anchor='nw')

    #     self.canvas.create_text(10, 210, fill="red", font=HEADLINE,
    #                             text='Vejret udenfor', anchor='nw')
    #     self.out_temp = self.canvas.create_text(
    #         10, 245, fill="darkblue", font=FONT, text='Temperatur: ', anchor='nw')
    #     self.out_hum = self.canvas.create_text(
    #         240, 245, fill="darkblue", font=FONT, text='Luftfugtighed: ', anchor='nw')

    #     self.out_wind = self.canvas.create_text(
    #         10, 280, fill="darkblue", font=FONT, text='Vind: ', anchor='nw')
    #     #self.out_wind_gust = self.canvas.create_text(
    #     #    150, 250, fill="darkblue", font=FONT, text='Stød: ', anchor='nw')
    #     self.out_wind_dir = self.canvas.create_text(
    #         280, 280, fill="darkblue", font=FONT, text='Retning: ', anchor='nw')

    #     # tid, pressure':  'sunrise':  'sunset':, 'uv_index'

    #     forecast_placeholder = ImageTk.PhotoImage(Image.new('RGBA', (1, 1), '#00000000'))
    #     self.forecast_display = self.canvas.create_image(
    #         0, 800, image=forecast_placeholder, anchor='nw')
        
    #     # Start thread to get newest forefocast from DMI
    #     self.fu = ForecastUpdater(self)
    #     self.fu.start()
    #     self.canvas.pack()

    def __init__(self):
        self.root = Tk()
        self.root.geometry('480x800')
        self.root.overrideredirect(1)  # Fullscreen
        self.root.config(cursor="none")
        self.root.bind('<Button 1>', self.mouse_click)

        self.hiding_forecast = False
        
        self.canvas = Canvas(self.root, width=480, height=800, bg='white')

        self.canvas.create_text(460, 5, fill="red", font=HEADLINE, text='Temperatur', anchor='nw', angle=270)
        self.canvas.create_text(460, 200, fill="red", font=HEADLINE, text='Fugt', anchor='nw', angle=270)
        
        self.stue_temp = self.canvas.create_text(
            400, 5, fill="darkblue", font=FONT, text='Stue .....C', anchor='nw', angle=270)
        self.stue_hum = self.canvas.create_text(
            400, 200, fill="darkblue", font=FONT, text='Stue ....0%', anchor='nw', angle=270)

        self.bad_temp = self.canvas.create_text(
            360, 5, fill="darkblue", font=FONT, text='Bad', anchor='nw', angle=270)
        self.bad_hum = self.canvas.create_text(
            360, 200, fill="darkblue", font=FONT, text='Bad', anchor='nw', angle=270)

        self.sia_temp = self.canvas.create_text(
            320, 5, fill="darkblue", font=FONT, text='Sia .....C', anchor='nw', angle=270)
        self.sia_hum = self.canvas.create_text(
            320, 200, fill="darkblue", font=FONT, text='Sia .....%', anchor='nw', angle=270)

        self.stue_dust = self.canvas.create_text(
            50, 5, fill="darkblue", font=FONT, text='Støv ....μg/cm³', anchor='nw', angle=270)

        self.canvas.create_text(460, 400, fill="red", font=HEADLINE,
                                text='Vejret udenfor', anchor='nw', angle=270)
        self.out_temp = self.canvas.create_text(
            400, 400, fill="darkblue", font=FONT, text='Temperatur: ', anchor='nw', angle=270)
        self.out_hum = self.canvas.create_text(
            360, 400, fill="darkblue", font=FONT, text='Luftfugtighed: ', anchor='nw', angle=270)

        self.out_wind = self.canvas.create_text(
            320, 400, fill="darkblue", font=FONT, text='Vind: ', anchor='nw', angle=270)
        #self.out_wind_gust = self.canvas.create_text(
        #    150, 250, fill="darkblue", font=FONT, text='Stød: ', anchor='nw')
        self.out_wind_dir = self.canvas.create_text(
            320, 650, fill="darkblue", font=FONT, text='Retning: ', anchor='nw', angle=270)

        self.sunrise = self.canvas.create_text(
            260, 5, fill="darkblue", font=FONT, text='Solopgang: ', anchor='nw', angle=270)
        self.sunset = self.canvas.create_text(
            220, 5, fill="darkblue", font=FONT, text='Solnedgang: ', anchor='nw', angle=270)

        self.ude_inde= self.canvas.create_text(
            260, 400, fill="darkblue", font=FONT, text='Ude-inde ', anchor='nw', angle=270)
        self.dmi_time = self.canvas.create_text(
            220, 400, fill="darkblue", font=FONT, text='DMI data: ', anchor='nw', angle=270)
        # tid, pressure':  'sunrise':  'sunset':, 'uv_index'

        forecast_placeholder = ImageTk.PhotoImage(Image.new('RGBA', (15, 15), '#00000000'))
        self.forecast_display = self.canvas.create_image(
            0, 0, image=forecast_placeholder, anchor='nw')

        # Start thread to get newest forefocast from DMI
        self.fu = ForecastUpdater(self)
        self.fu.start()
        self.canvas.pack()

        
    def mouse_click(self, eventorigin):
        print(eventorigin.x)
        print(eventorigin.y)

        if self.hiding_forecast:
            self.canvas.itemconfigure(self.forecast_display, state='normal')
            self.hiding_forecast = False
        else:
            self.canvas.itemconfigure(self.forecast_display, state='hidden')
            self.hiding_forecast = True

if __name__ == '__main__':
    # indoor_hum = weather_info.equaivalent_humidity(
    #     outside_temp=vejr.weather_data['temperature'],
    #     outside_hum=vejr.weather_data['humidity'],
    #     pressure=vejr.weather_data['pressure'],
    #     inside_temp=24
    # )
    # print(indoor_hum)


    app = Display()

    wu = WeatherUpdater(app)
    wu.start()

    # fu = ForecastUpdater(app)
    # fu.start()
    
    updater = Updater(app)
    updater.start()

    app.root.mainloop()
