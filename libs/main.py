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
LINE_TRACK_POWER = 30

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
hub_started = False
hub_reached = False
to_destination = False

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

'''------------ Instantiate -------------'''
try:
    speed = Speed(8, 9)
    grayscale = Grayscale(26, 27, 28)
    ws = WS_Server(name=NAME, mode=WIFI_MODE, ssid=SSID, password=PASSWORD)
    sensors = Follow(target_color="lila")  # Using color name instead of RGB tuple
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

# TODO: Not working.
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
    global move_status, line_status, line_track_active, mode
    stop()
    move_status = 'stop'
    mode = None
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
    lights.set_off()
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
    global line_out_time, move_status, line_status, line_track_active, hub_started
    _power = LINE_TRACK_POWER

    line_track_active = True
    
    # Check exit conditions at the start
    if should_exit_with_cleanup("line_track", cleanup_line_track):
        return

    if not hub_started and sensors.hub_control_start("Green"):
        hub_started = True
        move("forward", _power)
        time.sleep_ms(100)
        # TODO: Check how long it takes for a 90° Turn. or stop turning when the right sensor is not in the hub anymore (not green)
        move("turn in place right", _power) 
        time.sleep(1)
        stop()

    
    direction = sensors.hub_find_line("Green")
    right_color = sensors.get_color_str()[2]

    if hub_started:
        # move into to the direction from the method hub_find_line() only if the right sensor did not detect the target color.
        if not right_color == sensors.target_color:
            move(direction, _power)
        else: 
            stop()
            line_status = "target found"
            hub_started = False

def line_track():
    global line_out_time, move_status, line_status, line_track_active, to_destination, hub_reached
    _power = LINE_TRACK_POWER

    if should_exit_with_cleanup("line_track", cleanup_line_track):
        return

    direction = sensors.follow_line(_power)
    if line_status == "target found":
        left_sensor, middle_sensor, right_sensor = sensors.color_match_bool("terracotta")
        # True if all Sensors detect terracotta
        to_destination = left_sensor and middle_sensor and right_sensor
    elif line_status == "line end":
        left_sensor, middle_sensor, right_sensor = sensors.color_match_bool("green")
        # True if all Sensore detect Green
        hub_reached = left_sensor and middle_sensor and right_sensor

    # Move in the direction returned from the method follow_line()
    if direction is None:
        direction = "stop"
    move(direction, _power)
    line_track_active = True

    if direction == "stop":
        line_status = "out of line"
        return    
    if to_destination:
        stop()
        line_status = "line end"
    if hub_reached:
        stop()
        line_status = "finish"
        to_destination = False
        hub_reached = False


# TODO: Mit der Gruppe absprechen wie wir am ende einer Farbigen Linie das auto drehen. 
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
    global throttle_power, steer_power, move_status, is_move_last , mode, dpad_touched, line_status, line_track_active
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
    # 0 = Line Color off, 1 = Line Color on
    ws.send_dict['J'] = 1 if sensors.color_match(sensors.__get_color_rgb(current_mode=mode), sensors.target_color_rgb) else 0

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
        if data['G'] is True:
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
                mode = None
                line_track_active = False
                line_status = None
                print("Line Track Mode Disabled")

    # TODO: adapt to the new follow_line method (Follow class - line track functions)
    # start line color tracking until returned to hub
    if 'I' in data.keys() and start and start_line_track and data['I']:
        if not line_track_active:
            mode = 'line track'
            print('line track enabled')
            line_status = None
        if line_track_active and line_status is None:
            line_status = "start"

            


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



    # Debug mode - Only Print Actions
    if 'F' in data.keys() and start and isinstance(data['F'], bool):
        set_debug(data['F'])

            
    # if 'G' in data.keys() and data['G']:
    #     micropython.mem_info()
    #     machine.freq() # get current frequency
    
    if 'E' in data.keys():
        if data['E'] is True:
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
    global left_color, middle_color, right_color, start_line_track, line_track_active, line_status

    ''' if not connected, skip & stop '''
    if not ws.is_connected() or not start:
        sonar.servo.set_angle(0)
        car.move('stop', 0)
        mode = None
        return



    ''' mode: Line Track or Obstacle Avoid or Follow '''
    if not dpad_touched and start_line_track:
        if mode == 'line track':
            # INFO: debug 
            # hub()
            line_status = 'target found'
            line_track()
            # if line_status == 'target found' or line_status == "line end":
                # line_track()
            if line_status == "out of line":
                # TODO: mit der Gruppe besprechen was passieren soll wenn das auto die farbige linie verloren hat. 
                pass
            if line_status == "finish":
                print("line track finished")
                line_status = None



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
