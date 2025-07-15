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
import sonar as sonar
import lights as lights
from helper import set_debug, get_debug, debug_print, print_once
from classes.speed import Speed
from classes.grayscale import Grayscale
from ws import WS_Server
from machine import Pin
from classes.follow import Follow

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
# AP Mode
# WIFI_MODE = "ap"
# SSID = "" # your wifi name, if blank, use the set name "NAME"
# PASSWORD = "12345678" # your password

# STA Mode
WIFI_MODE = "sta"
SSID = "SPE-WLAN"
PASSWORD = "HeiselAir#1"

'''Configure steer sensitivity'''
steer_sensitivity = 0.8 # 0 ~ 1

'''Configure grayscale module'''
GRAYSCALE_LINE_REFERENCE_DEFAULT = 10000
GRAYSCALE_CLIFF_REFERENCE_DEFAULT = 2000

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

# follow
FOLLOW_SCAN_ANGLE = 90
FOLLOW_SCAN_STEP = 5
FOLLOW_REFERENCE = 20 # distance referenece (m)
FOLLOW_FORWARD_POWER = 20
FOLLOW_TURNING_POWER = 15

# voice control power
VOICE_CONTROL_POWER = 50

'''Configure the power of the line_track mode'''
LINE_TRACK_POWER = 80

'''Configure singal light'''
singal_on_color = [255, 255, 0] # amber:[255, 191, 0]
brake_on_color = [255, 0, 0] 

'''------------ Configure Voice Control Commands -------------'''
voice_commands = {
    # action : [[command , similar commands], [run time(s)]
    "forward": [["forward", "forwhat", "for what"], 3],
    "backward": [["backward"], 3],
    "left": [["left", "turn left"], 1],
    "right": [["right", "turn right", "while", "white"], 1],
    "stop": [["stop"], 1],
}

current_voice_cmd = None
voice_start_time = 0
voice_max_time = 0

'''------------ Global Variables -------------'''
led_status = False
start = False
_start_printed = False
debug = set_debug(False) # global debug flag
debug_printed = False
prev_modes = {'M': False, 'N': False, 'O': False, 'P': False} # previous mode state for negative edge detection

lights_brightness = 0.2
led_rear_min_brightness = 0.08
led_rear_max_brightness = 1

led_theme_code = 0
led_theme = {
    "0": [0, 0, 255], # blue
    "1": [255, 0, 255], # purple
    "2": [200, 0, 0], # red 
    "3": [128, 20, 0], # orange 
    "4": [128, 128, 0], # yellow 
    "5": [0, 128, 0], # green
}
led_theme_sum = len(led_theme)

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

anti_fall_enabled = False
on_edge = False

mode = None
throttle_power = 0
steer_power = 0

sonar_on = False
sonar_angle = 0
sonar_distance = 0
avoid_proc = "scan" # obstacle process, "scan", "getdir", "stop", "forward", "left", "right"
avoid_has_obstacle = False

line_out_time = 0

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

@print_once
def print_obstacle_avoid():
    print(" Obstacle Avoid Mode Enabled \r \n")
    
@print_once
def print_follow():
    print(" Follow Mode Enabled \r \n")

@print_once
def print_color_line_track():
    print(" Line Track Mode Enabled \r \n")
    

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
    
    current_time = time.time()
    
    # Check if it's time to toggle the blink state
    if current_time - signal_blink_time >= signal_blink_interval:
        signal_blink_state = not signal_blink_state
        signal_blink_time = current_time
    
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

def bottom_lights_handler():
    global led_status
    if led_status:
        color = list(led_theme[str(led_theme_code)])
    else:
        color = [0, 0, 0]
    lights.set_bottom_color(color)

'''----------------- on_receive (ws.loop()) ---------------------'''
def on_receive(data):
    global throttle_power, steer_power, move_status, is_move_last , mode, dpad_touched
    global led_status, led_theme_code, led_theme_sum, lights_brightness
    global current_voice_cmd, voice_start_time, voice_max_time
    global sonar_on
    global anti_fall_enabled
    global debug_printed, start, prev_modes

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

    # LEDs switch
    if 'I' in data.keys() and start:
        led_status = data['I']

    if led_status:
        # LEDs color theme change
        if 'J' in data.keys() and data['J'] == True:
            led_theme_code = (led_theme_code + 1) % led_theme_sum
            print(f"set led theme color: {led_theme_code}, {led_theme[str(led_theme_code)][0]}")


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
    global current_voice_cmd, voice_start_time, voice_max_time
    global lights_brightness
    global on_edge

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

    ''' sonar and distance '''
    if mode == None or mode == 'anti fall':
        if sonar_on:
            sonar.set_sonar_scan_config(NORMAL_SCAN_ANGLE, NORMAL_SCAN_STEP)
            sonar_angle, sonar_distance, _ = sonar.sonar_scan()
        else:
            sonar_angle = 0
            sonar_distance = sonar.get_distance_at(sonar_angle)

    ''' move && anti-fall '''
    if mode == "anti fall":
        if grayscale.is_on_edge():
            if dpad_touched and move_status == "backward":
                my_car_move(throttle_power, steer_power, gradually=True)
            else:
                move_status = "stop"
                car.move("stop")
        else:
            if dpad_touched:
                my_car_move(throttle_power, steer_power, gradually=True)
            else:
                move_status = "stop"
                car.move("stop")                
    elif dpad_touched:
        if not debug:
            my_car_move(throttle_power, steer_power, gradually=True)
        else:
            debug_print(("Motor Power:", throttle_power, "Steer Power:", steer_power, "Move Status:", move_status), action=mode, msg='DPAD Movement')

    ''' mode: Line Track or Obstacle Avoid or Follow '''
    if not dpad_touched and mode != 'anti fall':
        if mode == 'line track':
            print_color_line_track()
            # Only call color_line_track if we're actually in line track mode
            # The function will handle checking mode internally too
            # color_line_track()


    ''' no operation '''
    if not dpad_touched and mode == None and current_voice_cmd == None:
        move_status = "stop"
        car.move('stop')

    # ''' Bottom Lights '''
    bottom_lights_handler()
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

