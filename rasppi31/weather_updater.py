import time
import datetime
import threading

import PyExpLabSys.drivers.weather_info as weather_info
import credentials


class WeatherUpdater(threading.Thread):
    def __init__(self, display):
        threading.Thread.__init__(self)
        self.display = display
        self.update_time = datetime.datetime.now()
        self.indoor_hum = None

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
                print('updated')
            except KeyError:
                print('Klaf')
                # Refine this, please....
                self.update_weather()
                print('Klaf')
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

            # self.indoor_hum = weather_info.equaivalent_humidity(
            #     outside_temp=wd['temperature'],
            #     outside_hum=wd['humidity'],
            #     pressure=wd['pressure'],
            #     inside_temp=24
            # )
            # msg = 'Ude inde: {:.1f}%'.format(self.indoor_hum)
            # self.display.canvas.itemconfigure(self.display.ude_inde, text=msg)
            
            # Todo, should we do a more fance calculaed wait?
            time.sleep(600)
