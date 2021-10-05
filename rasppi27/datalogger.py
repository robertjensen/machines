""" Pressure and temperature logger """
import threading
import time
import logging
from PyExpLabSys.common.database_saver import ContinuousDataSaver
#from PyExpLabSys.common.sockets import LiveSocket
from PyExpLabSys.common.sockets import DateDataPullSocket
from PyExpLabSys.common.value_logger import ValueLogger
import PyExpLabSys.drivers.bosch_bme280 as bme280
import credentials

class Reader(threading.Thread):
    """ Pressure reader """
    def __init__(self, bme280, pull_socket):
        threading.Thread.__init__(self)
        self.bme280 = bme280
        self.pull_socket = pull_socket
        self.temperature = None
        self.humidity = None
        self.air_pressure = None
        self.quit = False
        self.ttl = 20

    def value(self, channel):
        """ Read temperature and  pressure """
        self.ttl = self.ttl - 1
        if self.ttl < 0:
            self.quit = True
            return_val = None
        else:
            if channel == 1:
                return_val = self.temperature
            if channel == 2:
                return_val = self.humidity
            if channel == 3:
                return_val = self.air_pressure
        return return_val

    def run(self):
        while not self.quit:
            time.sleep(1)
            self.ttl = 400
            avg_length = 25
            temperature = 0
            humidity = 0
            air_pressure = 0
            for _ in range(0, avg_length):
                # time.sleep(0.1)
                values = self.bme280.read_all_values()
                temperature +=values ['temperature']
                humidity += values['humidity']
                air_pressure += values['air_pressure']

            self.temperature = temperature / avg_length
            self.humidity = humidity / avg_length
            self.air_pressure = air_pressure / avg_length

            #livesocket.set_point_now(name, value)
            self.pull_socket.set_point_now('home_temperature_bathroom', self.temperature)
            self.pull_socket.set_point_now('home_humidity_bathroom', self.humidity)
            self.pull_socket.set_point_now('home_airpressure_bathroom', self.air_pressure)


def main():
    """ Main function """
    logging.basicConfig(filename="logger.txt", level=logging.ERROR)
    logging.basicConfig(level=logging.ERROR)

    codenames = ['home_temperature_bathroom', 'home_humidity_bathroom', 'home_airpressure_bathroom']
    #livesocket = LiveSocket('Home Air Logger', codenames)
    #livesocket.start()

    socket = DateDataPullSocket('Home Air Logger', codenames,
                                timeouts=[1.0] * len(codenames))
    socket.start()
    
    bme280_instance = bme280.BoschBME280()
    reader = Reader(bme280_instance, socket)
    reader.start()

    print('wait start 10s')
    time.sleep(10)
    print('Wait end')

    loggers = {}
    loggers[codenames[0]] = ValueLogger(reader, comp_val=0.25, comp_type='lin',
                                        channel=1)
    loggers[codenames[0]].start()
    loggers[codenames[1]] = ValueLogger(reader, comp_val=1.1, comp_type='lin',
                                        channel=2)
    loggers[codenames[1]].start()
    loggers[codenames[2]] = ValueLogger(reader, comp_val=1.5, comp_type='lin',
                                        channel=3)
    loggers[codenames[2]].start()


    table = 'dateplots_rued_langgaards_vej'
    db_logger = ContinuousDataSaver(continuous_data_table=table,
                                    username=credentials.user,
                                    password=credentials.passwd,
                                    measurement_codenames=codenames)
    db_logger.start()

    while reader.isAlive():
        time.sleep(1)
        for name in codenames:
            value = loggers[name].read_value()
            if loggers[name].read_trigged():
                print(value)
                db_logger.save_point_now(name, value)
                loggers[name].clear_trigged()

if __name__ == '__main__':
    main()
