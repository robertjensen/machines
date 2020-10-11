import time
import socket
import threading

from PIL import Image, ImageDraw, ImageFont, ImageTk
from tkinter import Tk, Canvas

FONT = ('DejaVuSans.ttf', 14)

class Updater(threading.Thread):
    def __init__(self, display):
        threading.Thread.__init__(self)
        self.display = display

    def read_network_value(self, host, data):
        attempts = 0
        while -1 < attempts < 10:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(0.5)
                sock.sendto(data, (host, 9000))
                received = sock.recv(1024).decode()
                # print('data from {}: {}'.format(data, received))
                value = float(received.split(',')[1])
                attempts = -1
            except socket.timeout:
                attempts += 1
                print('Socket timeout from {}'.format(data))
                value = 0
            except IndexError:
                attempts += 1
                print('Index Error')
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
            time.sleep(1)
            
            value = self.read_network_value('192.168.1.26', b'home_temperature_living_room#raw')
            msg = 'Temp. stue: {:.2f}C'.format(value)
            self.display.canvas.itemconfigure(self.display.stue_temp, text=msg)

            value = self.read_network_value('192.168.1.26', b'home_humidity_living_room#raw')
            msg = 'Fugt stue: {:.2f}%'.format(value)
            self.display.canvas.itemconfigure(self.display.stue_hum, text=msg)

            value = self.read_network_value('192.168.1.27', b'home_temperature_bathroom#raw')
            msg = 'Temp. bad: {:.2f}C'.format(value)
            self.display.canvas.itemconfigure(self.display.bad_temp, text=msg)

            value = self.read_network_value('192.168.1.27', b'home_humidity_bathroom#raw')
            msg = 'Fugt bad: {:.2f}%'.format(value)
            self.display.canvas.itemconfigure(self.display.bad_hum, text=msg)


class Display(object):
    def __init__(self):
        self.root = Tk()
        self.root.geometry('480x800')
        self.root.overrideredirect(1)  # Fullscreen
        self.root.config(cursor="none")
        self.root.bind('<Button 1>', self.mouse_click)
        self.canvas = Canvas(self.root, width=480, height=800, bg='white')

        self.stue_temp = self.canvas.create_text(
            10, 10, fill="darkblue", font=FONT, text='Stue .....C', anchor='nw')
        self.stue_hum = self.canvas.create_text(
            240, 10, fill="darkblue", font=FONT, text='Stue ....0%', anchor='nw')

        self.bad_temp = self.canvas.create_text(
            10, 45, fill="darkblue", font=FONT, text='Bad .....C', anchor='nw')
        self.bad_hum = self.canvas.create_text(
            240, 45, fill="darkblue", font=FONT, text='Bad .....%', anchor='nw')
        
        self.canvas.pack()
        
    def mouse_click(self, eventorigin):
        print(eventorigin.x)
        print(eventorigin.y)                                


if __name__ == '__main__':
    app = Display()

    updater = Updater(app)
    updater.start()

    app.root.mainloop()
