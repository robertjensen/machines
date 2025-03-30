import time
import socket
import threading

class DisplayUpdater(threading.Thread):
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
                # print('Socket timeout from {}'.format(data))
                value = 0
            except IndexError:
                attempts += 1
                # print('Index Error')
                # OLD_DATA
                value = 0  # TODO!
            except OSError as e:
                attempts += 0.1
                print('{:.2f}: OSError: {}'.format(attempts, e))
                time.sleep(0.25)
                value = 0  # TODO!
            # except:
            #     attempts += 1
            #     print('Unforeseen error')
            #     value = 0  # TODO!
        sock.close()
        return value                                      
        
    def run(self):
        while True:
            time.sleep(2)
            # print('Read')
            value = self.read_network_value('192.168.1.26', b'home_temperature_living_room#raw')
            msg = 'Stue:  {:.2f}C  '.format(value)
            self.display.canvas.itemconfigure(self.display.stue_temp, text=msg)

            value = self.read_network_value('192.168.1.26', b'home_humidity_living_room#raw')
            msg = 'Stue: {:.2f}%  '.format(value)
            self.display.canvas.itemconfigure(self.display.stue_hum, text=msg)

            value = self.read_network_value('192.168.1.27', b'home_temperature_bathroom#raw')
            if value > 0:
                msg = 'Bad: {:.2f}C'.format(value)
                self.display.canvas.itemconfigure(self.display.bad_temp, text=msg)

            value = self.read_network_value('192.168.1.27', b'home_humidity_bathroom#raw')
            if value > 0:
                msg = 'Bad: {:.2f}%'.format(value)
                self.display.canvas.itemconfigure(self.display.bad_hum, text=msg)

            value = self.read_network_value('192.168.1.198', b'home_temperature_sias_room#raw')
            msg = 'Sia:   {:.2f}C  '.format(value)
            self.display.canvas.itemconfigure(self.display.sia_temp, text=msg)

            value = self.read_network_value('192.168.1.198', b'home_humidity_sias_room#raw')
            msg = 'Sia: {:.2f}%  '.format(value)
            self.display.canvas.itemconfigure(self.display.sia_hum, text=msg)

            value = self.read_network_value('192.168.1.36', b'home_temperature_bedroom#raw')
            msg = 'Sove:   {:.2f}C  '.format(value)
            self.display.canvas.itemconfigure(self.display.sove_temp, text=msg)

            value = self.read_network_value('192.168.1.36', b'home_humidity_bedroom#raw')
            msg = 'Sove: {:.2f}%  '.format(value)
            self.display.canvas.itemconfigure(self.display.sove_hum, text=msg)

            value = self.read_network_value('192.168.1.26', b'fast_dust#raw', port=9011)
            if value > 0:
                msg = 'Støv {:.2f}μg/cm³    '.format(value)
                self.display.canvas.itemconfigure(self.display.stue_dust, text=msg)


