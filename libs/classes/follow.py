# filepath: libs/classes/follow.py
import sys
from time import sleep
from machine import Pin

from classes.tcs34725 import *

<<<<<<< HEAD
class Follow:
=======
class follow:
>>>>>>> dde97ccd33c4c4dbfe88673b4d2a21fdc98ebb99
    def __init__(self, Left_channel, Middle_channel, Right_channel, target_rgb):
        print("Starting tcs34735")
        self.i2c_instance = I2C()
        self.tca_instance = TCA9548A(self.i2c_instance)
        self.left_sensor = TCS34725(Left_channel)
        self.middle_sensor = TCS34725(Middle_channel)
        self.right_sensor = TCS34725(Right_channel)
        self.target_rgb = target_rgb # (R, G, B) tuple for the line color
        print("I2C started")

    def _read_sensor(self, sensor, channel):
        sensor.switch_channel(channel)
        return sensor.color_raw[:3] # (R, G, B)
    
    def _color_distance(self, color1, color2):
        """Calculate the Euclidean distance between two RGB colors."""
        return sum((a -b) ** 2 for a, b in zip(color1, color2)) ** 0.5

    def get_line_position(self):
        """Determine the position of the line based on sensor readings."""
        left_color = self._read_sensor(self.left_sensor, 1)
        middle_color = self._read_sensor(self.middle_sensor, 2)
        right_color = self._read_sensor(self.right_sensor, 3)

        left_distance = self._color_distance(left_color, self.target_rgb)
        middle_distance = self._color_distance(middle_color, self.target_rgb)
        right_distance = self._color_distance(right_color, self.target_rgb)

        print(f"Left: {left_color}, Middle: {middle_color}, Right: {right_color}")
        print(f"Distances - Left: {left_distance}, Middle: {middle_distance}, Right: {right_distance}")
        # Determine which sensor is closest to the target color
        min_dist = min(left_distance, middle_distance, right_distance)
        if min_dist == left_distance:
            return "left"
        elif min_dist == right_distance:
            return "right"
        else:
            return "center"

    def follow_line(self, power=50):
        """Follow the line based on sensor readings and control the motors."""
        from classes.motors import move, stop
        while True:
            position = self.get_line_position()
            if position == "left":
                print("Turning left")
                move("left", power)
            elif position == "right":
                print("Turning right")
                move("right", power)
            else:
                print("Moving forward")
                move("forward", power)
            sleep(0.1)
