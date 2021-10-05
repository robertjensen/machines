""" Dust logger """
import time
import threading
import logging
from PyExpLabSys.common.database_saver import ContinuousDataSaver
#from PyExpLabSys.common.sockets import LiveSocket
from PyExpLabSys.common.sockets import DateDataPullSocket
from PyExpLabSys.common.value_logger import ValueLogger

import PyExpLabSys.drivers.sensirion_sps30 as sensirion_sps30

import credentials


class DustReader(threading.Thread):
    """ Dust reader """
    def __init__(self, sensirion, pull_socket):
        threading.Thread.__init__(self)
        self.sensirion = sensirion
        self.pull_socket = pull_socket

        self.pm_1_0_mass = None
        self.pm_2_5_mass = None
        self.pm_4_0_mass = None
        self.pm_10_0_mass = None
        self.pm_0_5_number = None
        self.pm_1_0_number = None
        self.pm_2_5_number = None
        self.pm_4_0_number = None
        self.pm_10_0_number = None
        self.average_size = None

        self.quit = False
        self.ttl = 500

    def value(self, channel):
        """ Read temperature and  pressure """
        self.ttl = self.ttl - 1
        if self.ttl < 0:
            self.quit = True
            return_val = None
        else:
            if channel == 1:
                return_val = self.pm_1_0_mass
            if channel == 2:
                return_val = self.pm_2_5_mass
            if channel == 3:
                return_val = self.pm_4_0_mass
            if channel == 4:
                return_val = self.pm_10_0_mass
            if channel == 5:
                return_val = self.pm_0_5_number
            if channel == 6:
                return_val = self.pm_1_0_number
            if channel == 7:
                return_val = self.pm_2_5_number
            if channel == 8:
                return_val = self.pm_4_0_number
            if channel == 9:
                return_val = self.pm_10_0_number
            if channel == 10:
                return_val = self.average_size
        return return_val

    def run(self):
        while not self.quit:
            self.ttl = 500
            avg_length = 30
            averaged_data = [0] * 10
            print('Reading data')
            for _ in range(0, avg_length):
                time.sleep(1.1)
                data = self.sensirion.read_measurement()
                # Use PM10.0 mass, as proxy for fast dust readout
                self.pull_socket.set_point_now('fast_dust', data[3])
                for i in range(0, 10):
                    averaged_data[i] += data[i] / avg_length
            self.pm_1_0_mass = averaged_data[0]
            self.pm_2_5_mass = averaged_data[1]
            self.pm_4_0_mass = averaged_data[2]
            self.pm_10_0_mass = averaged_data[3]
            self.pm_0_5_number = averaged_data[4]
            self.pm_1_0_number = averaged_data[5]
            self.pm_2_5_number = averaged_data[6]
            self.pm_4_0_number = averaged_data[7]
            self.pm_10_0_number = averaged_data[8]
            self.average_size = averaged_data[9]
            # data = self.sensirion.read_measurement()
            # self.pm_1_0_mass = data[0]
            # self.pm_2_5_mass = data[1]
            # self.pm_4_0_mass = data[2]
            # self.pm_10_0_mass = data[3]
            # self.pm_0_5_number = data[4]
            # self.pm_1_0_number = data[5]
            # self.pm_2_5_number = data[6]
            # self.pm_4_0_number = data[7]
            # self.pm_10_0_number = data[8]
            # self.average_size = data[9]


def main():
    """ Main function """
    logging.basicConfig(filename="logger.txt", level=logging.ERROR)
    logging.basicConfig(level=logging.ERROR)

    codenames = [
        'dust_livingroom_mass_p1_0', 'dust_livingroom_mass_p2_5',
        'dust_livingroom_mass_p4_0', 'dust_livingroom_mass_p10_0',
        'dust_livingroom_number_pm05', 'dust_livingroom_number_pm1_0',
        'dust_livingroom_number_p2_5', 'dust_livingroom_number_p4_0',
        'dust_livingroom_number_p10_0', 'dust_livingroom_mean_size'
    ]

    socket = DateDataPullSocket('Living Room Dust Loger', codenames + ['fast_dust'],
                                port=9011, timeouts=[1.0] * (len(codenames) + 1))
    socket.start()
    
    sensirion_instance = sensirion_sps30.SensirionSPS30()
    reader = DustReader(sensirion_instance, socket)
    reader.start()
    
    # time.sleep(45)
    time.sleep(20)

    print('Start loggers')
    loggers = {}
    for i in range(0, 4):
        print(i)
        loggers[codenames[i]] = ValueLogger(reader, comp_val=0.25, comp_type='lin',
                                            channel=i + 1)
        loggers[codenames[i]].start()
    for i in range(4, 10):
        loggers[codenames[i]] = ValueLogger(reader, comp_val=5.5, comp_type='lin',
                                            channel=i + 1)
        loggers[codenames[i]].start()

    #livesocket = LiveSocket('Home Air Logger', codenames)
    #livesocket.start()

    table = 'dateplots_dust'
    print('Start db')
    db_logger = ContinuousDataSaver(continuous_data_table=table,
                                    username=credentials.user,
                                    password=credentials.passwd,
                                    measurement_codenames=codenames)
    print('Start logger')
    db_logger.start()

    while reader.isAlive():
        time.sleep(5)
        print('Check logger')
        for name in codenames:
            value = loggers[name].read_value()
            # livesocket.set_point_now(name, value)
            socket.set_point_now(name, value)
            if loggers[name].read_trigged():
                msg = '{} is logging value: {}'
                print(msg.format(name, value))
                db_logger.save_point_now(name, value)
                loggers[name].clear_trigged()


if __name__ == '__main__':
    main()
