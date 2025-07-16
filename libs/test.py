'''*****************************************************************************************
Use the app Sunfounder Controller to control the Pico-4WD-Car

https://github.com/sunfounder/pico_4wd_car/tree/v2.0

Pico onboard LED status:
    - off: not working
    - always on: working
    - blink: error

*****************************************************************************************'''
import time
import sys
import machine as machine
import motors as car
from motors import move, stop
import sonar as sonar
import lights as lights
from helper import set_debug, get_debug, debug_print
from classes.speed import Speed
from classes.grayscale import Grayscale
from ws import WS_Server
from machine import Pin
from classes.follow_mux import Follow

VERSION = '1.3.0'
print(f"[ Pico-4WD Car App Control {VERSION}]\n")

'''
 "w" mode will clear the previous log first, if you need to keep it,
 please use the "a" mode
'''
LOG_FILE = "log.txt"

# "a" mode
with open(LOG_FILE, "a") as log_f:
    Separation_Line = "\n" + "-"*30 + "\n"
    log_f.write(Separation_Line)

# "w" mode
# with open(LOG_FILE, "w") as log_f:
#     log_f.write("")

''' -------------- Onboard led Config -------------'''
onboard_led = Pin(25, Pin.OUT)

''' ---------------- Custom Config ----------------'''
'''Whether print serial receive '''
RECEIVE_PRINT = False

'''Set name'''
NAME = 'my_4wd_car'

'''Configure wifi'''

# STA Mode
WIFI_MODE = "sta"
SSID = "SPE-WLAN"
PASSWORD = "HeiselAir#1"

'''Configure steer sensitivity'''
steer_sensitivity = 0.8 # 0 ~ 1


'''Configure sonar'''
# Normal
NORMAL_SCAN_ANGLE = 180
NORMAL_SCAN_STEP = 5

# obstacle_avoid
OBSTACLE_AVOID_SCAN_ANGLE = 60
OBSTACLE_AVOID_SCAN_STEP = 10
OBSTACLE_AVOID_REFERENCE = 25   # distance referenece (cm)
OBSTACLE_AVOID_FORWARD_POWER = 30
OBSTACLE_AVOID_TURNING_POWER = 50


'''Configure the power of the line_track mode'''
LINE_TRACK_POWER = 80

'''Configure singal light'''
singal_on_color = [255, 255, 0] # amber:[255, 191, 0]
brake_on_color = [255, 0, 0] 


'''------------ Global Variables -------------'''
led_status = False
start = False
_start_printed = False
start_line_track = False
_start_line_track_printed = False 
line_track_active = False
line_status = None

lights_brightness = 0.2
led_rear_min_brightness = 0.08
led_rear_max_brightness = 1


dpad_touched = False
move_status = 'stop'
is_move_last  = False
brake_light_status= False
brake_light_time = 0
brake_light_brightness = 255 # 0 ~ 255
brake_light_brightness_flag = -1 # -1 or 1

# Signal light blinking variables
signal_blink_state = False
signal_blink_time = 0
signal_blink_interval = 0.5  # 500ms blink interval


mode = None
throttle_power = 0
steer_power = 0

sonar_on = False
sonar_angle = 0
sonar_distance = 0
avoid_proc = "scan" # obstacle process, "scan", "getdir", "stop", "forward", "left", "right"
avoid_has_obstacle = False

class Follow:
    def __init__(self, Left_channel, Middle_channel, Right_channel, target_rgb=(255, 0, 0)):
        """
        Initialize the Follow class for line tracking with color sensors.
        
        Args:
            Left_channel: I2C multiplexer channel for left color sensor
            Middle_channel: I2C multiplexer channel for middle color sensor  
            Right_channel: I2C multiplexer channel for right color sensor
            target_rgb: Target RGB color to follow (default red)
        """
        
        # Initialize I2C and multiplexer
        self.i2c_instance = MyI2C()
        self.mux = TCA9548A(self.i2c_instance)
        
        # Store channel numbers
        self.left_channel = Left_channel
        self.middle_channel = Middle_channel
        self.right_channel = Right_channel
        
        # Initialize color sensors
        self.left_sensor = TCS34725(i2c=self.i2c_instance)
        self.middle_sensor = TCS34725(i2c=self.i2c_instance)
        self.right_sensor = TCS34725(i2c=self.i2c_instance)
        
        # Color tracking settings
        self.target_color = "rot"  # Default target color name
        self.target_color_rgb = target_rgb
        
        # Color mapping for string conversion
        self.color_map = {
            "rot": (255, 0, 0),
            "grün": (0, 255, 0),
            "blau": (0, 0, 255),
            "gelb": (255, 255, 0),
            "lila": (128, 0, 128),
            "orange": (255, 165, 0),
            "terracotta": (204, 78, 92),
            "schwarz": (0, 0, 0),
            "weiß": (255, 255, 255)
        }
        
        # Reverse mapping for RGB to color name
        self.rgb_to_color = {v: k for k, v in self.color_map.items()}
    
    def __get_color_rgb(self, channel=None, current_mode=None):
        """
        Get RGB values from a specific sensor channel.
        
        Args:
            channel: Multiplexer channel number (1=left, 2=middle, 3=right)
            current_mode: Current operation mode for debug filtering
            
        Returns:
            tuple: (R, G, B) values
        """
        if channel is None:
            channel = self.middle_channel
            
        try:
            # Switch to the correct multiplexer channel
            self.mux.switch_channel(channel)
            time.sleep(0.01)  # Small delay for channel switching
            
            # Read color from sensor
            if channel == self.left_channel:
                rgb = self.left_sensor.get_rgb()
            elif channel == self.middle_channel:
                rgb = self.middle_sensor.get_rgb()
            elif channel == self.right_channel:
                rgb = self.right_sensor.get_rgb()
            else:
                return (0, 0, 0)
                
            if get_debug() and current_mode == "line track":
                debug_print(f"Channel {channel} RGB: {rgb}", action="color_sensor", msg="RGB Reading")
                
            return rgb
            
        except Exception as e:
            if get_debug() and current_mode == "line track":
                debug_print(f"Color sensor error on channel {channel}: {e}", action="color_sensor", msg="Sensor Error")
            return (0, 0, 0)
    
    def get_color_rgb_convert(self):
        """
        Get RGB values from all three sensors.
        
        Returns:
            list: [left_rgb, middle_rgb, right_rgb]
        """
        return [
            self.__get_color_rgb(self.left_channel),
            self.__get_color_rgb(self.middle_channel), 
            self.__get_color_rgb(self.right_channel)
        ]
    
    def _rgb_distance(self, rgb1, rgb2):
        """
        Calculate Euclidean distance between two RGB colors.
        
        Args:
            rgb1: First RGB tuple
            rgb2: Second RGB tuple
            
        Returns:
            float: Distance between colors
        """
        return ((rgb1[0] - rgb2[0])**2 + (rgb1[1] - rgb2[1])**2 + (rgb1[2] - rgb2[2])**2)**0.5
    
    def _closest_color_name(self, rgb):
        """
        Find the closest color name for given RGB values.
        
        Args:
            rgb: RGB tuple to match
            
        Returns:
            str: Closest color name
        """
        min_distance = float('inf')
        closest_color = "schwarz"
        
        for color_name, color_rgb in self.color_map.items():
            distance = self._rgb_distance(rgb, color_rgb)
            if distance < min_distance:
                min_distance = distance
                closest_color = color_name
                
        return closest_color
    
    def get_color_str(self):
        """
        Get color names for all three sensors.
        
        Returns:
            list: [left_color_name, middle_color_name, right_color_name]
        """
        rgb_values = self.get_color_rgb_convert()
        return [
            self._closest_color_name(rgb_values[0]),
            self._closest_color_name(rgb_values[1]),
            self._closest_color_name(rgb_values[2])
        ]
    
    def color_match(self, target_rgb, current_mode=None, threshold=50):
        """
        Check if middle sensor detects the target color.
        
        Args:
            target_rgb: Target RGB color to match
            current_mode: Current operation mode for debug filtering
            threshold: Color matching threshold
            
        Returns:
            bool: True if color matches, False otherwise
        """
        current_rgb = self.__get_color_rgb(self.middle_channel, current_mode)
        distance = self._rgb_distance(current_rgb, target_rgb)
        
        match = distance < threshold
        
        if get_debug() and current_mode == "line track":
            debug_print(f"Color match: {match}, distance: {distance:.1f}", action="color_match", msg="Color Detection")
            
        return match
    
    def follow_line(self, power=80, current_mode=None):
        """
        Follow a line using the three color sensors.
        
        Args:
            power: Motor power for line following
            current_mode: Current operation mode for debug filtering
            
        Returns:
            str: Movement direction ('forward', 'left', 'right', 'stop')
        """
        # Get current color readings
        colors = self.get_color_str()
        left_color, middle_color, right_color = colors
        
        # Determine movement based on which sensor sees the target color
        if middle_color == self.target_color:
            if not get_debug():
                move('forward', power)
            else:
                if current_mode == "line track":
                    debug_print(f"Moving forward (middle sensor on target)", action="line_follow", msg="Forward")
            return 'forward'
            
        elif left_color == self.target_color:
            if not get_debug():
                move('left', power)
            else:
                if current_mode == "line track":
                    debug_print(f"Moving left (left sensor on target)", action="line_follow", msg="Left")
            return 'left'
            
        elif right_color == self.target_color:
            if not get_debug():
                move('right', power)
            else:
                if current_mode == "line track":
                    debug_print(f"Moving right (right sensor on target)", action="line_follow", msg="Right")
            return 'right'
            
        else:
            if not get_debug():
                stop()
            else:
                if current_mode == "line track":
                    debug_print(f"No target color detected, stopping", action="line_follow", msg="Stop")
            return 'stop'
    
    def set_target_color(self, color_name):
        """
        Set the target color to follow by name.
        
        Args:
            color_name: Name of color to follow
        """
        if color_name.lower() in self.color_map:
            self.target_color = color_name.lower()
            self.target_color_rgb = self.color_map[color_name.lower()]
            if get_debug():
                debug_print(f"Target color set to {color_name}: {self.target_color_rgb}", action="color_setup", msg="Target Color")
        else:
            if get_debug():
                debug_print(f"Unknown color: {color_name}", action="color_setup", msg="Color Error")
    
    def set_target_rgb(self, rgb):
        """
        Set the target color to follow by RGB values.
        
        Args:
            rgb: RGB tuple to follow
        """
        self.target_color_rgb = rgb
        self.target_color = self._closest_color_name(rgb)
        if get_debug():
            debug_print(f"Target RGB set to {rgb} ({self.target_color})", action="color_setup", msg="Target RGB")

'''------------ Instantiate -------------'''
try:
    speed = Speed(8, 9)
    grayscale = Grayscale(26, 27, 28)
    ws = WS_Server(name=NAME, mode=WIFI_MODE, ssid=SSID, password=PASSWORD)
    sensors = Follow(Left_channel=1, Middle_channel=2, Right_channel=3, target_rgb=(255, 0, 0))
    left_color = sensors.get_color_str()[0]
    middle_color = sensors.get_color_str()[1]
    right_color = sensors.get_color_str()[2]
except Exception as e:
    onboard_led.off()
    sys.print_exception(e)
    with open(LOG_FILE, "a") as log_f:
        log_f.write('\n> ')
        sys.print_exception(e, log_f)
    sys.exit(1) # if ws init failed, exit
    

'''----------------- Helper Functions ---------------------'''

def should_exit_operation(operation_type="general"):
    """
    Universal exit condition checker for various operations.
    
    Args:
        operation_type: Type of operation to check exit conditions for
                       Options: "general", "line_track", "obstacle_avoid", "follow"
    
    Returns:
        bool: True if operation should exit, False otherwise
    """
    global start, start_line_track, mode, move_status
    
    # Base exit conditions - always check these first
    if not ws.is_connected():
        stop()
        move_status = 'stop'
        if get_debug():
            debug_print("Exit: WebSocket disconnected", action="exit_check", msg="Connection Lost")
        return True
    
    if not start:
        stop()
        move_status = 'stop'
        if get_debug():
            debug_print("Exit: Car stopped", action="exit_check", msg="Car Stop")
        return True
    
    # Operation-specific exit conditions
    if operation_type == "line_track":
        if not start_line_track:
            stop()
            move_status = 'stop'
            if get_debug():
                debug_print("Exit: Line track disabled", action="exit_check", msg="Line Track Stop")
            return True
        
        if mode != 'line track' and mode != 'line track enabled':
            stop()
            move_status = 'stop'
            if get_debug():
                debug_print("Exit: Mode changed from line track", action="exit_check", msg="Mode Change")
            return True
    
    elif operation_type == "obstacle_avoid":
        if mode != 'obstacle avoid':
            stop()
            move_status = 'stop'
            if get_debug():
                debug_print("Exit: Mode changed from obstacle avoid", action="exit_check", msg="Mode Change")
            return True
        
    
    return False

def should_exit_with_cleanup(operation_type="general", cleanup_function=None):
    """
    Exit checker with optional cleanup function.
    
    Args:
        operation_type: Type of operation to check
        cleanup_function: Optional function to call during cleanup
    
    Returns:
        bool: True if operation should exit, False otherwise
    """
    if should_exit_operation(operation_type):
        if cleanup_function:
            try:
                cleanup_function()
            except Exception as e:
                if get_debug():
                    debug_print(f"Cleanup error: {e}", action="exit_check", msg="Cleanup Error")
        return True
    return False

def cleanup_line_track():
    """Cleanup actions for exiting line track mode."""
    global move_status, line_status, line_track_active
    stop()
    move_status = 'stop'
    line_status = None
    line_track_active = False
    if get_debug():
        debug_print("Line track cleanup executed", action="cleanup", msg="Line Track")

def cleanup_lights():
    """Cleanup actions for lights (e.g., turn off or reset brightness)."""
    global lights_brightness, brake_light_status, signal_blink_state
    lights_brightness = led_rear_min_brightness
    brake_light_status = False
    signal_blink_state = False
    # Add hardware-specific light-off code here if needed
    if get_debug():
        debug_print("Lights cleanup executed", action="cleanup", msg="Lights")



'''----------------- motors fuctions ---------------------'''
def my_car_move(throttle_power, steer_power, gradually=False):
    power_l = 0
    power_r = 0

    if steer_power < 0:
        power_l = int((100 + 2*steer_sensitivity*steer_power)/100*throttle_power)
        power_r = int(throttle_power)
    else:
        power_l = int(throttle_power)
        power_r = int((100 - 2*steer_sensitivity*steer_power)/100*throttle_power)

    if not get_debug() and gradually:
        car.set_motors_power_gradually([power_l, power_r, power_l, power_r])
    else:
        if get_debug():
            debug_print((f"Would move motors: [{power_l}, {power_r}, {power_l}, {power_r}]"),
                        action="motors", msg="Motor Power")
        else:
            car.set_motors_power([power_l, power_r, power_l, power_r])


'''----------------- color_line_track ---------------------'''

def hub():
    global line_out_time, move_status, line_status, line_track_active
    global left_color, middle_color, right_color
    _power = LINE_TRACK_POWER

    line_track_active = True
    
    # Check exit conditions at the start
    if should_exit_with_cleanup("line_track", cleanup_line_track):
        return

    if left_color != "grün" and middle_color != "grün" and right_color != "grün":
        print(f"Auto ist nicht im Hub.")
    else:
        if middle_color == "grün" and left_color != "grün":
            move('forward', _power)
            move_status = 'forward'
            move('turn_in_place_right', _power)
            move_status = 'turn_in_place_right'
            
            while not (left_color == "grün" and middle_color == "grün" and right_color == sensors.target_color):
                # Check exit conditions in the loop
                if should_exit_with_cleanup("line_track", cleanup_line_track):
                    return
                    
                if left_color == "grün" and middle_color == "grün":
                    move('forward', _power)
                    move_status = 'forward'
                elif left_color == "grün":
                    move('left', _power)
                    move_status = 'left'
                
                # Update sensor readings
                left_color = sensors.get_color_str()[0]
                middle_color = sensors.get_color_str()[1]
                right_color = sensors.get_color_str()[2]
                
                # Small delay to make loop responsive
                time.sleep(0.01)
                
            stop()
            line_status = 'target found'


def line_track(way_back=None):
    global line_out_time, move_status, line_status, line_track_active, left_color, middle_color, right_color
    _power = LINE_TRACK_POWER
    
    destination_cond = (middle_color == 'terracotta' and left_color == 'terracotta' and right_color == 'terracotta') 
    way_back_cond = (middle_color == 'grün' and left_color == 'grün' and right_color == 'grün')

    if way_back:
        cond = way_back_cond
    else:
        cond = destination_cond

    if not cond:
        while not (middle_color == sensors.target_color and left_color == sensors.target_color and right_color == sensors.target_color):
            # Check exit conditions in the loop
            if should_exit_with_cleanup("line_track", cleanup_line_track):
                return
                
            if middle_color == sensors.target_color:
                move('forward', _power)
                move_status = 'forward'
            elif right_color == sensors.target_color:
                move('right', _power)
                move_status = 'right'
            elif left_color == sensors.target_color:
                move('left', _power)
                move_status = 'left'
            
            # Update sensor readings
            left_color = sensors.get_color_str()[0]
            middle_color = sensors.get_color_str()[1]
            right_color = sensors.get_color_str()[2]
            
            # Small delay to make loop responsive
            time.sleep(0.01)
            
        stop()
        move_status = 'stop'
        if way_back:
            line_status = 'finish'
        else:
            line_status = 'line end'
            line_track_active = False

def line_track_end():
    global move_status, line_status, left_color, middle_color, right_color
    _power = LINE_TRACK_POWER
    
    while not (left_color == sensors.target_color or middle_color == sensors.target_color or right_color == sensors.target_color):
        # Check exit conditions in the loop
        if should_exit_with_cleanup("line_track", cleanup_line_track):
            return

        if middle_color == 'terracotta':
            move('forward', _power)
            move_status = 'forward'
        elif right_color == 'terracotta':
            move('right', _power)
            move_status = 'right'
        elif left_color == 'terracotta':
            move('left', _power)
            move_status = 'left'
        
        # Update sensor readings
        left_color = sensors.get_color_str()[0]
        middle_color = sensors.get_color_str()[1]
        right_color = sensors.get_color_str()[2]
        
        # Small delay to make loop responsive
        time.sleep(0.01)
        
    line_status = "way back"

# def color_line_track(rgb=None):
#     """Track a colored line using the color sensors.
    
#     Args:
#         rgb: Optional tuple of (R, G, B) values for the line color.
#              If not provided, the default target color will be used.
    
#     Returns:
#         None
#     """
#     global move_status
    
#     # Only execute if we're actually in line track mode
#     if mode != 'line track':
#         return
        
#     # Example: channels 1, 2, 3 and a red line (adjust as needed)
#     target_rgb = rgb or (255, 0, 0)  # Default to red if no color is provided
    
#     # Update the target color to track
#     sensors.target_color = target_rgb
    
#     # Get the car's movement direction from the follow_line function
#     # Pass the current mode to ensure debug prints only happen in line_track mode
#     new_move_status = sensors.follow_line(power=LINE_TRACK_POWER, current_mode=mode)
    
#     # Only update move_status if we got a valid status
#     if new_move_status is not None:
#         move_status = new_move_status

# def auto_color_line_track():
#     """ Scan for a Color on the middle Sensor and use that as the Target RGB to follow. """
#     global move_status
    
#     # Only execute if we're actually in line track mode
#     if mode != 'line track':
#         return

#     target_rgb = sensors.get_color(current_mode=mode)
#     if get_debug():
#         debug_print(f"Auto-tracking color: {target_rgb}", action="line_track", msg="Auto Color Track")
#     color_line_track(target_rgb)


'''----------------- singal_lights_handler ---------------------'''
def singal_lights_handler():
    """ Blink left or Right depending on the direction the car is moving """
    global signal_blink_state, signal_blink_time, signal_blink_interval

    # Early exit check - but still update timing for consistency
    should_exit = should_exit_operation("general")
    
    current_time = time.time()
    
    # Always update timing to prevent drift
    if current_time - signal_blink_time >= signal_blink_interval:
        signal_blink_state = not signal_blink_state
        signal_blink_time = current_time
    
    # Exit after timing update but before hardware operations
    if should_exit:
        cleanup_lights()
        return
    
    # Set the signal lights based on move_status and blink state
    if move_status == 'left':
        if signal_blink_state:
            lights.set_rear_left_color(singal_on_color)
        else:
            lights.set_rear_left_color(0x000000)
        lights.set_rear_right_color(0x000000)
    elif move_status == 'right':
        lights.set_rear_left_color(0x000000)
        if signal_blink_state:
            lights.set_rear_right_color(singal_on_color)
        else:
            lights.set_rear_right_color(0x000000)
    else:
        lights.set_rear_left_color(0x000000)
        lights.set_rear_right_color(0x000000)

def brake_lights_handler():
    global is_move_last , brake_light_status, brake_light_time, led_status, brake_light_brightness
    global brake_light_brightness, brake_light_brightness_flag

    if should_exit_with_cleanup("general", cleanup_lights):
        return

    if move_status == 'stop':
        if brake_light_brightness_flag == 1:
            brake_light_brightness += 5
            if brake_light_brightness > 255:
                brake_light_brightness = 255
                brake_light_brightness_flag = -1
        elif brake_light_brightness_flag == -1:
            brake_light_brightness -= 5
            if brake_light_brightness < 0:
                brake_light_brightness = 0
                brake_light_brightness_flag = 1          
        brake_on_color = [brake_light_brightness, 0, 0]
        lights.set_rear_color(brake_on_color)
    else:
        if is_move_last:
            lights.set_rear_middle_color(0x000000)
        else:
            lights.set_rear_color(0x000000)
        is_move_last = True
        brake_light_brightness = 255


'''----------------- on_receive (ws.loop()) ---------------------'''
def on_receive(data):
    global throttle_power, steer_power, move_status, is_move_last , mode, dpad_touched, line_status
    global sonar_on
    global start, prev_modes, start_line_track

    if RECEIVE_PRINT:
        print("recv_data: %s"%data)
    
    # print(f"Received data: {data['A']}")

    ''' if not connected, skip & stop '''
    if not ws.is_connected():
        sonar.servo.set_angle(0)
        car.move('stop', 0)
        return

    ''' data to display'''
    # Color track
    # ws.send_dict['A'] = sensors.color_match(sensors.target_color, current_mode=mode) # uint: 0 or 1
    # Speed measurement
    ws.send_dict['B'] = round(speed.get_speed(), 2) # uint: cm/s
    # Speed mileage
    ws.send_dict['C'] = speed.get_mileage() # unit: meter
    # # sonar and distance
    ws.send_dict['D'] = [sonar_angle, sonar_distance]
    ws.send_dict['J'] = sonar_distance
    # ws.send_dict['M'] = sensors.get_color_rgb_convert()[0] # Red component
    # ws.send_dict['Q'] = sensors.get_color_rgb_convert()[1] # Green component
    # ws.send_dict['R'] = sensors.get_color_rgb_convert()[2] # Blue component
    # TODO: Add data to send to the app
    # 0 = Line Color off, 1 = Line Color on
    ws.send_dict['J'] = 1 if sensors.color_match(sensors.__get_color_rgb(current_mode=mode), current_mode=mode) else 0

    ''' remote control'''
    # Move - power
    if 'Q' in data.keys() and isinstance(data['Q'], int):
        throttle_power = data['Q']
    else:
        throttle_power = 0

    # Move - direction
    if 'K' in data.keys() and start:
        if data['K'] == "left":
            dpad_touched = True
            move_status = 'left'
            if steer_power > 0:
                steer_power = 0
            steer_power -= int(throttle_power/2)
            if steer_power < -100:
                steer_power = -100
        elif data['K'] == "right":
            dpad_touched = True
            move_status = 'right'
            if steer_power < 0:
                steer_power = 0
            steer_power += int(throttle_power/2)
            if steer_power > 100:
                steer_power = 100
        elif data['K'] == "forward":
            dpad_touched = True
            move_status = 'forward'
            steer_power = 0
        elif data['K'] == "backward":
            dpad_touched = True
            move_status = 'backward'
            steer_power = 0
            throttle_power = -throttle_power
        else:
            dpad_touched = False
            move_status = 'stop'
            steer_power = 0

    if throttle_power == 0:
        move_status = 'stop'

    # rear LEDs brightness
    if throttle_power < 0:
        lights_brightness = (-throttle_power)/100
    else:
        lights_brightness = throttle_power/100
    if lights_brightness < led_rear_min_brightness:
        lights_brightness = led_rear_min_brightness
    elif lights_brightness > led_rear_max_brightness:
        lights_brightness = led_rear_max_brightness

    if 'G' in data.keys() and start:
        if data['G'] == True:
            if not start_line_track:
                start_line_track = True
                # Print once to indicate start
                global _start_line_track_printed
                if not _start_line_track_printed:
                    print("Line Track Mode Enabled")
                    _start_line_track_printed = True
        else:
            if start_line_track:
                start_line_track = False
                _start_line_track_printed = False
                print("Line Track Mode Disabled")

    # start line color tracking until returned to hub
    if 'I' in data.keys() and start and start_line_track and data['I']:
        if not line_track_active:
            mode = 'line track'
            line_status = None
        else:
            if line_status == 'line end':
                line_track_end()
            


    # color select: Purple, Blue, Yellow, Orange, Terracotta
    # Set target color based on received buttons
    if start:
        if 'N' in data.keys() and data['N']:
            # sensors.target_color = "Purple"
            print("purple")
            # print(f"Set target color to {sensors.target_color.upper()} with RGB values of {sensors.target_color_rgb}")
        if 'O' in data.keys() and data['O']:
            # sensors.target_color = "Blue"
            print("blue")
            # print(f"Set target color to {sensors.target_color.upper()} with RGB values of {sensors.target_color_rgb}")
        if 'P' in data.keys() and data['P']:
            # sensors.target_color = "Yellow"
            print("yellow")
            # print(f"Set target color to {sensors.target_color.upper()} with RGB values of {sensors.target_color_rgb}")
        if 'S' in data.keys() and data['S']:
            # sensors.target_color = "Orange"
            print("orange")
            # print(f"Set target color to {sensors.target_color.upper()} with RGB values of {sensors.target_color_rgb}")
        if 'T' in data.keys() and data['T']:
            # sensors.target_color = "Terracotta"
            print("terracotta")
            # print(f"Set target color to {sensors.target_color.upper()} with RGB values of {sensors.target_color_rgb}")

        

    # Debug mode - Only Print Actions
    if 'F' in data.keys() and start and isinstance(data['F'], bool):
        set_debug(data['F'])

            
    # if 'G' in data.keys() and data['G']:
    #     micropython.mem_info()
    #     machine.freq() # get current frequency
    
    if 'E' in data.keys():
        if data['E'] == True:
            if not start:
                start = True
                # Print once to indicate start
                global _start_printed
                if not _start_printed:
                    print("Car started")
                    _start_printed = True
        else:
            if start:
                start = False
                _start_printed = False
                print("Car stopped")


'''----------------- remote_handler ---------------------'''
def remote_handler():
    global mode, throttle_power, steer_power, move_status, dpad_touched
    global sonar_angle, sonar_distance
    global lights_brightness
    global left_color, middle_color, right_color, start_line_track, line_track_active

    ''' Debug print '''
    # if debug and mode is None:
        # debug_print(("Motor Power:", throttle_power, "Steer Power:", steer_power, "Move Status:", move_status, "Sonar Angle:", sonar_angle, "Sonar Distance:", sonar_distance, "Grayscale Value:", grayscale.get_value(), "Lights Brightness:", lights_brightness), mode, msg='Remote Handler Data')
        # sonar.servo.set_angle(0)  # Allow sonar to move
        # mode = None  # Stop mode if debug mode is on
        

    ''' if not connected, skip & stop '''
    if not ws.is_connected() or not start:
        sonar.servo.set_angle(0)
        car.move('stop', 0)
        mode = None
        return



    ''' mode: Line Track or Obstacle Avoid or Follow '''
    if not dpad_touched and start_line_track:
        if mode == 'line track':
            hub()
            if line_status == 'target found':
                line_track()
            elif line_status == 'way back':
                line_track(way_back=True)
            elif line_status == 'line end':
                mode = 'line track enabled'



    ''' no operation '''
    if not dpad_touched and mode == None: 
        move_status = "stop"
        car.move('stop')

    # ''' Singal lights '''
    singal_lights_handler()
    # ''' Brake lights '''
    brake_lights_handler()

'''----------------- main ---------------------'''
def main():
    sonar.servo.set_angle(0)
    car.move('stop')
    ws.on_receive = on_receive
    if ws.start():
        onboard_led.on()
        while True:
            ws.loop()
            remote_handler()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.print_exception(e)
        with open(LOG_FILE, "a") as log_f:
            log_f.write('\n> ')
            sys.print_exception(e, log_f)
    finally:
        car.move("stop")
        lights.set_off()
        ws.set("RESET", timeout=25000)
        while True: # pico onboard led blinking indicates error
            time.sleep(0.25)
            onboard_led.off()
            time.sleep(0.25)
            onboard_led.on()

