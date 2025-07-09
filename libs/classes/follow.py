import sys
from time import sleep
from machine import Pin

from classes.tcs34725 import *
from classes.mux import TCA9548A_Channel

class follow:
    def __init__(self, channel):
        print("Starting tcs34735")
        self.i2c_instance = I2C()
        self.tca_instance = TCA9548A(self.i2c_instance)
        self.tca = TCA9548A_Channel(self.tca_instance, channel=1)
        print("I2C started")
        devices = self.tca.scan()            # Print devices found

    def get_value(self, sensor : str):
        if sensor == "left":

            
    

