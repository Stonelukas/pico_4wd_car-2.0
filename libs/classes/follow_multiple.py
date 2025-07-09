import sys
from time import sleep
from machine import Pin

from classes.tcs34725 import *
from classes.mux import TCA9548A_Channel

class follow:
    def __init__(self):
        print("Starting tcs34735")
        self.i2c_instance = I2C()
        self.tca_instance = TCA9548A(self.i2c_instance)
        self.tca = TCA9548A_Channel(self.tca_instance, channel=1)
        self.tcs_left = TCS34725(channel=1)
        self.tcs_middle = TCS34725(channel=2)
        self.tcs_right = TCS34725(channel=3)
        self.sensors = [self.tcs_left, self.tcs_middle, self.tcs_right]
        if not any([self.tcs_left.isconnected, self.tcs_middle.isconnected, self.tcs_right.isconnected]):
            left, middle, right = (not self.tcs_left.isconnected, not self.tcs_middle.isconnected, not self.tcs_right.isconnected)
            if left:
                print("Terminating. Sensor left not connected")
            if middle:
                print("Terminating. Sensor middle not connected")
            if right:
                print("Terminating. Sensor right not connected")
            sys.exit()
        for instance in self.sensors:
            instance.gain = TCSGAIN_LOW
            instance.integ = TCSINTEG_MAX
            instance.autogain = True
        print("I2C started")
        devices = self.tca.scan()            # Print devices found

    def get_value(self, sensor : str):
        if sensor == "left":
            self.tcs_left

            
    

