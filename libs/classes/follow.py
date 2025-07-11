# filepath: libs/classes/follow.py
import sys
import time
from time import sleep
from machine import Pin

from classes.tcs34725 import *
from classes.i2c import MyI2C

class Follow:
    def __init__(self, target_rgb):
        print("Starting tcs34725")
        self.i2c_instance = MyI2C()

        # Initialize sensors with proper channel values and shared I2C instance
        self.left_sensor = TCS34725(scl=Pin(2), sda=Pin(3))
        self.middle_sensor = TCS34725(scl=Pin(4), sda=Pin(5))
        self.right_sensor = TCS34725(scl=Pin(6), sda=Pin(7))

        # Set default gain and integration time for each sensor
        self.left_sensor.gain = TCSGAIN_LOW # Low gain
        self.middle_sensor.gain = TCSGAIN_LOW # Low gain
        self.right_sensor.gain = TCSGAIN_LOW # Low gain
        self.left_sensor.integ = TCSINTEG_MEDIUM # ~40 ms integration time
        self.middle_sensor.integ = TCSINTEG_MEDIUM
        self.right_sensor.integ = TCSINTEG_MEDIUM

        self.target_rgb = target_rgb # (R, G, B) tuple for the line color
        print("I2C started")
        self.color_threshold = 60  # Adjust this value as needed
        self.line_out_time = 0  # Track when line was lost

    def _read_sensor(self, sensor):
        return sensor.color_raw[:3] # (R, G, B)
    
    @property
    def target_color(self):
        """Get the target color for the line."""
        return self.target_rgb

    @target_color.setter
    def target_color(self, value):
        self.target_rgb = value
    
    def _color_distance(self, color1, color2):
        """Calculate the Euclidean distance between two RGB colors."""
        return sum((a -b) ** 2 for a, b in zip(color1, color2)) ** 0.5


    def get_line_position(self):
        """Determine the position of the line based on sensor readings."""
        left_color = self._read_sensor(self.left_sensor)
        middle_color = self._read_sensor(self.middle_sensor)
        right_color = self._read_sensor(self.right_sensor)

        left_distance = self._color_distance(left_color, self.target_rgb)
        middle_distance = self._color_distance(middle_color, self.target_rgb)
        right_distance = self._color_distance(right_color, self.target_rgb)

        print(f"Left: {left_color}, Middle: {middle_color}, Right: {right_color}")
        print(f"Distances - Left: {left_distance}, Middle: {middle_distance}, Right: {right_distance}")
        # Determine which sensor is closest to the target color

        # If all sensors are too far from the target color, return None
        if (left_distance > self.color_threshold and
            middle_distance > self.color_threshold and
            right_distance > self.color_threshold):
            print("No target color detected by any sensor!")
            return None

        min_dist = min(left_distance, middle_distance, right_distance)
        if min_dist == left_distance:
            return "left"
        elif min_dist == right_distance:
            return "right"
        else:
            return "center"

    def get_color(self):
        """Get the detected color from the middle sensor."""
        middle_color = self._read_sensor(self.middle_sensor)
        print(f"Detected color: {middle_color}")
        return middle_color 

    def color_match(self, color):
        """Check if the detected color matches the target color."""
        distance = self._color_distance(color, self.target_rgb)
        print(f"Color: {color}, Target: {self.target_rgb}, Distance: {distance}")
        if distance < self.color_threshold:
            match = int(1)
        else:
            match = int(0)
        return match

    def follow_line(self, power):
        """Follow the line based on sensor readings."""
        from motors import move, stop
        
        while True:
            position = self.get_line_position()
            
            # Check if no line is detected
            if position is None:
                # If the car is out of the line, stop it
                if self.line_out_time == 0:
                    self.line_out_time = time.time()
                    print("Warning: No target color detected by any sensor!")
                
                # If no line detected for more than 2 seconds, stop and wait
                if (time.time() - self.line_out_time > 2):
                    print("Line lost! Stopping car. Please reposition the car on the line.")
                    stop()
                    # Wait for user intervention - the car will stay stopped
                    # until the line is found again or the user takes action
                    while self.get_line_position() is None:
                        sleep(0.5)
                        print("Waiting for line to be detected...")
                    print("Line detected again! Resuming...")
                    self.line_out_time = 0
                return
            else:
                # Reset the timer if line is detected
                self.line_out_time = 0
            
            # Execute movement based on line position
            if position == "left":
                print("Turning left")
                move("left", power)
            elif position == "right":
                print("Turning right")
                move("right", power)
            else:
                print("Moving forward")
                move("forward", power)
            # Small delay to avoid overwhelming the motors
            sleep(0.1)
