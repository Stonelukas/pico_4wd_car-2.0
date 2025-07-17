# filepath: libs/classes/follow.py
import time
from time import sleep
from machine import Pin
from helper import debug_print, get_debug
from typing import Optional, Union, Tuple, Any

from classes.tcs34725 import *
from classes.i2c import MyI2C

class Follow:
    def __init__(self, target_rgb):
        """
        Initialize the Follow class for line tracking with color sensors.
        
        Args:
            Left_channel: I2C multiplexer channel for left color sensor
            Middle_channel: I2C multiplexer channel for middle color sensor  
            Right_channel: I2C multiplexer channel for right color sensor
            target_rgb: Target RGB color to follow (default red)
        """
        print("Starting tcs34725")
        self.i2c_instance = MyI2C()

        # Initialize sensors with proper channel values and shared I2C instance
        self.left_sensor = TCS34725(scl=Pin(2), sda=Pin(3))
        self.middle_sensor = TCS34725(scl=Pin(4), sda=Pin(5))
        self.right_sensor = TCS34725(scl=Pin(6), sda=Pin(7))

        # Set default gain and integration time for each sensor
        for sensor in (self.left_sensor, self.middle_sensor, self.right_sensor):
            sensor.gain = TCSGAIN_LOW # Low gain
            sensor.integ = TCSINTEG_MEDIUM # ~40 ms integration time

        # Validate and set target RGB tuple (R, G, B)
        self.target_rgb = self._validate_rgb(target_rgb)
        
        # Color mapping for string conversion
        self.color_map = {
            "lila": (111, 95, 132),
            "blau": (61, 146, 175),
            "grün": (153, 182, 57),
            "gelb": (229, 174, 47),
            "orange": (232, 120, 45),
            "terracotta": (192, 99, 81)
        }
        self.rgb_to_color = {v: k for k, v in self.color_map.items()}
        
        # Set target color name based on RGB
        self.target_color = self._get_closest_color_name(self.target_rgb)
        print("I2C started")
        self.color_threshold = 60  # Adjust this value as needed
        self.line_out_time = 0  # Track when line was lost

    def _validate_rgb(self, rgb: Tuple[Any, ...]) -> Tuple[int, int, int]:
        """Validate RGB tuple and ensure it contains exactly 3 integers (R, G, B)."""
        if not isinstance(rgb, tuple) or len(rgb) != 3:
            raise ValueError("RGB must be a tuple of exactly 3 values (R, G, B)")
        
        # Ensure all values are integers and within valid range (0-255) also make sure the color is in the color_map dictionary
        if not all(isinstance(value, (int, float)) for value in rgb):
            raise ValueError("RGB values must be numbers (int or float)")
        validated_rgb = []
        for i, value in enumerate(rgb):
            # Ensure each value is a number and within the range 0-255
            if not isinstance(value, (int, float)):
                raise ValueError(f"RGB value at index {i} must be a number")
            
            # Convert to int and clamp to 0-255 range
            int_value = int(value)
            clamped_value = max(0, min(255, int_value))
            validated_rgb.append(clamped_value)
        
        return tuple(validated_rgb)
    
    def _get_closest_color_name(self, rgb: Tuple[int, int, int]) -> str:
        """Get the closest color name for an RGB value using the color_map."""
        if rgb in self.rgb_to_color:
            return self.rgb_to_color[rgb]
        
        # If exact match not found, find the closest color
        min_distance = float('inf')
        closest_color = ""
        
        for color_name, color_rgb in self.color_map.items():
            distance = self._color_distance(rgb, color_rgb)
            if distance < min_distance:
                min_distance = distance
                closest_color = color_name
        
        return closest_color
    
    def _read_sensor(self, sensor: Any) -> Tuple[int, int, int]:
        return sensor.color_raw[:3] # (R, G, B)
    
    @property
    def target_color_rgb(self) -> Tuple[int, int, int]:
        """Get the target color for the line."""
        return self.target_rgb

    @target_color_rgb.setter
    def target_color_rgb(self, target_rgb: Tuple[int, int, int]) -> None:
        """
        Set the target color to follow by RGB values.
        
        Args:
            target_rgb: RGB values of the color to follow
        """
        self.target_rgb = self._validate_rgb(target_rgb)
        self.target_color = self._get_closest_color_name(self.target_rgb)
        if get_debug():
            debug_print(f"Target color set to {self.target_color}: {self.target_rgb}", action="color_setup", msg="Target Color")
        else:
            if get_debug():
                debug_print(f"Unknown color: {self.target_color}", action="color_setup", msg="Color Error")

    @property
    def target_color(self) -> str:
        """Get the target color for the line as a string from predefined colors"""
        return self._get_closest_color_name(self.target_rgb)

    @target_color.setter
    def target_color(self, color: str) -> None:
        """Set the target color using a predefined color name."""
        if color.lower() in self.color_map:
            self.target_rgb = self.color_map[color.lower()]
        else:
            raise ValueError(f"Invalid color name: '{color}'. Must be one of: {list(self.color_map.keys())}")
    
    def _color_distance(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
        """Calculate the Euclidean distance between two RGB colors."""
        return sum((a - b) ** 2 for a, b in zip(color1, color2)) ** 0.5

    def get_colors(self, color_code: str = 'all') -> Optional[Union[float, Tuple[float, float, float]]]:
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
            left_rgb = self._read_sensor(self.left_sensor)
            middle_rgb = self._read_sensor(self.middle_sensor)
            right_rgb = self._read_sensor(self.right_sensor)
            
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

    def __get_color_rgb(self, current_mode: Optional[str] = None) -> Tuple[int, int, int]:
        """Get the detected color from the middle sensor as RGB."""
        middle_color = self._read_sensor(self.middle_sensor)
        return middle_color
    
    def get_color_rgb_convert(self) -> Tuple[str, str, str]:
        """
        convert RGB value to a number with 2 numbers before the comma. 
        The 3 number is after the comma.
        return as tuple (R, G, B)
        """
        rgb = self.__get_color_rgb()
        # Convert each RGB component to a string with 2 digits before the decimal and 1 after
        r = f"{rgb[0]:02d}"
        g = f"{rgb[1]:02d}"
        b = f"{rgb[2]:02d}"
        return (r, g, b)

    def get_color(self, current_mode: Optional[str] = None) -> Tuple[int, int, int]:
        """ detects the color of the middle sensor and returns it as RGB tuple."""
        self.current_mode = current_mode
        
        # Only proceed if we're in line track mode
        if current_mode != 'line track':
            return (0, 0, 0)  # Return black if not in line track mode

        rgb = self.__get_color_rgb()
        if get_debug() and current_mode == 'line track':
            debug_print(f"Detected color: {rgb}", action="line_track", msg="Color Detection")
        return rgb

    def rgb_to_color_name(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to color name using color_map dictionary."""
        return self._get_closest_color_name(rgb)
    
    def color_name_to_rgb(self, color_name: str) -> Tuple[int, int, int]:
        """Convert color name to RGB tuple using color_map dictionary."""
        color_name = color_name.lower()
        if color_name in self.color_map:
            return self.color_map[color_name]
        else:
            raise ValueError(f"Unknown color: {color_name}. Available colors: {list(self.color_map.keys())}")

    def __color_compare(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> bool:
        """ Compare two colors and return True if they match within the threshold. """
        threshold = 30  # Define a threshold for color matching
        return all(abs(c1 - c2) < threshold for c1, c2 in zip(color1, color2))


    def color_match(self, color: Tuple[int, int, int]) -> int:
        """Check if the detected color matches the target color."""
        distance = self._color_distance(color, self.target_rgb)
        print(f"Color: {color}, Target: {self.target_rgb}, Distance: {distance}")
        if distance < self.color_threshold:
            match = int(1)
        else:
            match = int(0)
        return match

    def follow_line(self, power: int, current_mode: Optional[str] = None) -> Optional[str]:
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
        
        # Only proceed if we're in line track mode
        if self.current_mode != 'line track':
            print("Not in line track mode, skipping follow_line.")
            return None
        
        from motors import move, stop

        position = self.get_line_position(self.current_mode)
        # Check if debug mode is enabled and we're in line track mode
        is_debug = get_debug() and self.current_mode == 'line track'

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
        return position

    def get_line_position(self, current_mode: Optional[str] = None) -> Optional[str]:
        """Determine the position of the line based on sensor readings."""
        self.current_mode = current_mode
        
        # Only proceed if we're in line track mode
        if self.current_mode != 'line track':
            print("Not in line track mode, skipping get_line_position.")
            return None

        left_color = self._read_sensor(self.left_sensor)
        middle_color = self._read_sensor(self.middle_sensor)
        right_color = self._read_sensor(self.right_sensor)

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
            return "center"

if __name__ == "__main__":

