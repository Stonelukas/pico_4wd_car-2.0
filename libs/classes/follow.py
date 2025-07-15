# filepath: libs/classes/follow.py
import time
from time import sleep
from helper import debug_print, get_debug

from classes.tcs34725 import *
from classes.i2c import MyI2C

class Follow:
    def __init__(self, Left_channel, Middle_channel, Right_channel, target_rgb):
        print("Starting tcs34735")
        self.i2c_instance = MyI2C()

        self.left_channel = Left_channel
        self.middle_channel = Middle_channel
        self.right_channel = Right_channel
        # Initialize sensors with proper channel values and shared I2C instance
        self.left_sensor = TCS34725(Left_channel, i2c=self.i2c_instance)
        self.middle_sensor = TCS34725(Middle_channel, i2c=self.i2c_instance)
        self.right_sensor = TCS34725(Right_channel, i2c=self.i2c_instance)

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

    def _read_sensor(self, sensor, channel):
        sensor.switch_channel(channel)
        return sensor.color_raw[:3] # (R, G, B)
    
    @property
    def target_color_rgb(self):
        """Get the target color for the line."""
        return self.target_rgb
    

    @target_color_rgb.setter
    def target_color_rgb(self, value):
        self.target_rgb = value

    @property
    def target_color(self):
        """Get the target color for the line as a string from predefined colors"""
        return self.__translate_color(self.target_color_rgb, mode='string')
    
    @target_color.setter
    def target_color(self, color):
        self.target_rgb = self.__translate_color(color, mode='rgb')

    def _color_distance(self, color1, color2):
        """Calculate the Euclidean distance between two RGB colors."""
        return sum((a -b) ** 2 for a, b in zip(color1, color2)) ** 0.5
    
    def get_colors(self, color_code: str = 'all'):
        """Get average color values from all three sensors.
        
        Args:
            color_code: Color component to return ('red', 'green', 'blue', 'all', or 'rgb')
                       Default is 'all' which returns all components as a tuple
        
        Returns:
            float: Average value for single color component
            tuple: (red, green, blue) tuple when color_code is 'all' or 'rgb'
            None: If invalid color_code provided
        """
        try:
            # Read all sensors once and store the results
            left_rgb = self._read_sensor(self.left_sensor, 1)
            middle_rgb = self._read_sensor(self.middle_sensor, 2)
            right_rgb = self._read_sensor(self.right_sensor, 3)
            
            # Calculate averages for each color component
            red_avg = sum(rgb[0] for rgb in (left_rgb, middle_rgb, right_rgb)) / 3
            green_avg = sum(rgb[1] for rgb in (left_rgb, middle_rgb, right_rgb)) / 3
            blue_avg = sum(rgb[2] for rgb in (left_rgb, middle_rgb, right_rgb)) / 3
            
            # Debug output if enabled
            if get_debug():
                debug_print(f"Sensor readings - Left: {left_rgb}, Middle: {middle_rgb}, Right: {right_rgb}", 
                           action="color_sensing", msg="Raw Values")
                debug_print(f"Averages - Red: {red_avg:.1f}, Green: {green_avg:.1f}, Blue: {blue_avg:.1f}", 
                           action="color_sensing", msg="Calculated Averages")
            
            # Return based on requested color code
            color_code = color_code.lower()
            if color_code == 'red':
                return red_avg
            elif color_code == 'green':
                return green_avg
            elif color_code == 'blue':
                return blue_avg
            elif color_code in ('all', 'rgb'):
                return (red_avg, green_avg, blue_avg)
            else:
                raise ValueError(f"Unknown color code: '{color_code}'. Use 'red', 'green', 'blue', 'all', or 'rgb'")
                
        except IOError as e:
            print(f"IOError reading color sensors: {e}")
            if get_debug():
                debug_print(f"Color sensor IOError: {e}", action="color_sensing", msg="Error")
            return None


    def __get_color_rgb(self, current_mode=None):
        """Get the detected color from the middle sensor as RGB."""
            
        middle_color = self._read_sensor(self.middle_sensor, 2)
        return middle_color

    def get_color(self, current_mode=None):
        """ detects the color of the middle sensor and returns it as a string."""
        self.current_mode = current_mode
        
        # Only proceed if we're in line track mode
        if current_mode != 'line track':
            return (0, 0, 0)  # Return black if not in line track mode

        rgb = self.__get_color_rgb
        if get_debug() and current_mode == 'line track':
            debug_print(f"Detected color: {rgb}", action="line_track", msg="Color Detection")
        return self.__translate_color(rgb, mode='string')

    def __translate_color(self, rgb, mode):
        """ 
        Translates RGB values into strings or strings into RGB values for easy evaluation


        purple:     R:111   G:95    B:132
        blue:       R:61    G:146   B:175
        green:      R:153   G:182   B:57
        yellow:     R:229   G:174   B:47
        orange:     R:232   G:120   B:45
        terracotta: R:192   G:99    B:81

        Parameters:
        rgb (tuple): RGB values to evaluate
        mode (str): Mode of operation, either 'string' to return color name or 'rgb' to return RGB values

        Returns:
        str or tuple: Color name if mode is 'string', RGB tuple if mode is 'rgb' or empty string if no match found
        """

        if mode == 'string':
            if self.__color_compare(rgb, (111, 95, 132)):
                return "lila"
            if self.__color_compare(rgb, (61, 146, 175)):
                return "blau"
            if self.__color_compare(rgb, (153, 182, 57)):
                return "grün"
            if self.__color_compare(rgb, (229, 174, 47)):
                return "gelb"
            if self.__color_compare(rgb, (232, 120, 45)):
                return "orange"
            if self.__color_compare(rgb, (192, 99, 81)):
                return "terracotta"
            else:
                return ""

        elif mode == 'rgb':
            if rgb == "lila":
                return (111, 95, 132)
            if rgb == "blau":
                return (61, 146, 175)
            if rgb == "grün":
                return (153, 182, 57)
            if rgb == "gelb":
                return (229, 174, 47)
            if rgb == "orange":
                return (232, 120, 45)
            if rgb == "terracotta":
                return (192, 99, 81)
            else:
                return (0, 0, 0)

    def get_color_str(self):
        """
        Returns:
        tuple of str: Color that corresponds to the RGB values.
        (left, middle, right)
        """
        left = self.__translate_color(self._read_sensor(self.left_sensor, 1), mode='string')
        middle = self.__translate_color(self._read_sensor(self.middle_sensor, 2), mode='string')
        right = self.__translate_color(self._read_sensor(self.right_sensor, 3), mode='string')

        return (left, middle, right)

    def __color_compare(self, color1, color2):
        """ Compare two colors and return True if they match within the threshold. """
        threshold = 30  # Define a threshold for color matching
        return all(abs(c1 - c2) < threshold for c1, c2 in zip(color1, color2))

    def color_match(self, color, current_mode=None):
        """Check if the detected color matches the target color."""
        self.current_mode = current_mode
        
        # Only perform color matching if we're in line track mode
        # or checking for color match in the dashboard
        if current_mode != 'line track':
            return int(0)  # Return no match if not in line track mode
            
        distance = self._color_distance(color, self.target_rgb)
        
        # Only debug print if we're in debug mode AND in line track mode
        if get_debug() and current_mode == 'line track':
            if distance < self.color_threshold:
                debug_print(f"Color match found: {color} is close to target {self.target_rgb}, Distance: {distance}",
                          action="line_track", msg="Color Matching")
            else:
                debug_print(f"Color match not found: {color} is not close to target {self.target_rgb}, Distance: {distance}",
                          action="line_track", msg="Color Matching")
        
        if distance < self.color_threshold:
            match = int(1)
        else:
            match = int(0)
        return match

    def follow_line(self, power, current_mode=None):
        """Follow the line based on sensor readings.
        
        This function should be called from main.py to follow a colored line.
        It will use the debug flag to determine whether to actually move the motors
        or just print debug information.
        
        Args:
            power: Motor power level (0-100)
            current_mode: Current operating mode of the car
            
        Returns:
            The current move_status value ('left', 'right', 'forward', 'stop')
        """
        self.current_mode = current_mode
        
        # Only execute if we're actually in line track mode
        if current_mode != 'line track':
            return None
            
        from motors import move, stop
        
        position = self.get_line_position(current_mode)
        is_debug = get_debug() and current_mode == 'line track'
        move_status = 'unknown'
        
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
                position = 'stop'
                # Print debug information
                if is_debug:
                    position = "stopped"
                    power = 0
                    debug_print(("Direction:", position, "Power:", power), action="line_track", msg="Stopping line following")
                # Wait for user intervention - the car will stay stopped
                # until the line is found again or the user takes action
                while self.get_line_position() is None:
                    sleep(0.5)
                    print("Waiting for line to be detected...")
                print("Line detected again! Resuming...")
                self.line_out_time = 0
            return position
        else:
            # Reset the timer if line is detected
            self.line_out_time = 0
        # Execute movement based on line position
        if position == "left":
            if is_debug:
                debug_print(("Direction:", position, "Power:", power), action="line_track", msg="Following line")
            else:
                move("left", power)
        elif position == "right":
            if is_debug:
                debug_print(("Direction:", position, "Power:", power), action="line_track", msg="Following line")
            else:
                move("right", power)
        else:
            if is_debug:
                debug_print(("Direction:", position, "Power:", power), action="line_track", msg="Following line")
            else:
                move("forward", power)
        # Small delay to avoid overwhelming the motors
        sleep(0.1)

    def get_line_position(self, current_mode=None):
        """Determine the position of the line based on sensor readings."""
        self.current_mode = current_mode
        
        # Only execute if we're in line track mode
        if current_mode != 'line track':
            return None

        left_color = self._read_sensor(self.left_sensor, 1)
        middle_color = self._read_sensor(self.middle_sensor, 2)
        right_color = self._read_sensor(self.right_sensor, 3)

        left_distance = self._color_distance(left_color, self.target_rgb)
        middle_distance = self._color_distance(middle_color, self.target_rgb)
        right_distance = self._color_distance(right_color, self.target_rgb)

        # Check if debug mode is enabled to decide whether to print
        is_debug = get_debug() and self.current_mode == 'line track'
        if is_debug:
            debug_print((f"Left: {left_color}, Middle: {middle_color}, Right: {right_color}"), 
                        action="line_track", msg='Color Readings')
            debug_print((f"Distances - Left: {left_distance}, Middle: {middle_distance}, Right: {right_distance}"), 
                        action="line_track", msg='Distance Values')
        # Determine which sensor is closest to the target color

        # If all sensors are too far from the target color, return None
        if (left_distance > self.color_threshold and
            middle_distance > self.color_threshold and
            right_distance > self.color_threshold):
            if is_debug:
                debug_print("No target color detected by any sensor!", 
                          action="line_track", msg="Warning")
            else:
                print("No target color detected by any sensor!")
            return None

        min_dist = min(left_distance, middle_distance, right_distance)
        if min_dist == left_distance:
            return "left"
        elif min_dist == right_distance:
            return "right"
        else:
            return "forward"
