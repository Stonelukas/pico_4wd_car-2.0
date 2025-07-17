import machine as machine
from machine import Timer
import time
from motors import move, stop
from helper import debug_print, print_on_change, print_once, set_debug, get_debug, clear_print_caches 
import classes.grayscale

try:
    grayscale = classes.grayscale.Grayscale(26, 27, 28)
except Exception as e:
    debug_print(f"Grayscale sensor initialization failed: {e}")
    
'''---------------- helper functions ----------------'''
def get_grayscale_values():
    """Get the grayscale values from the sensor. And Convert to a specified color value for testing the color sensor implementation"""
    if grayscale:
        value = grayscale.get_value()
        left, middle, right = "black", "black", "black"
        # if the grayscale value for each sensor separate is above a certain threshold, we can simulate a color as string (above 10000 = "orange", below 1000 = "black")
        if value[0] > 10000:
            left = "orange"
        elif value[1] > 10000:
            middle = "orange"
        elif value[2] > 10000:
            right = "orange"
        elif value[0] < 1000:
            left = "black"
        elif value[1] < 1000:
            middle = "black"
        elif value[2] < 1000:
            right = "black"
        return left, middle, right
    return None

def compare():
    """Compare the grayscale values to a predefined set of values."""
    values = get_grayscale_values()
    # Check the values and determine the position
    # left, middle, right are the three sensors
    print_once(f"Grayscale values: {values}")
    if values:
        left, middle, right = values
        if left == "orange" and middle == "black" and right == "black":
            return "left"
        elif left == "black" and middle == "orange" and right == "black":
            return "forward"
        elif left == "black" and middle == "black" and right == "orange":
            return "right"
        else:
            return None
    return None


def follow_line(power):
    """Follow the line based on sensor readings.
    
    This function should be called from main.py to follow a colored line.
    It will use the debug flag to determine whether to actually move the motors
    or just print debug information.
    
    Args:
        power: Motor power level (0-100)
        
    Returns:
        The current move_status value ('left', 'right', 'forward', 'stop')
    """
    position = compare()
    print_once(f"Current position: {position}")
    if position is None:
        line_out_time = time.ticks_ms()

        if time.ticks_diff(time.ticks_ms(), line_out_time) > 5000:
            debug_print("No line detected for 5 seconds. Stopping car.", action="follow_line", msg="Line lost")
            print_once("No line detected! Stopping car.")
            stop()
            position = 'stop'
        
            # Wait until the line is detected again
            while compare() is None:
                time.sleep(0.1)
            line_out_time = 0  
            print_once("Line detected again! Resuming line following.")
        return position
    
    # If the line is detected, continue with the normal line following logic
    if position == "left":
        debug_print(("Direction:", position, "Power:", power), action="line_track", msg="Following line")
        move("left", power)
    elif position == "right":
        debug_print(("Direction:", position, "Power:", power), action="line_track", msg="Following line")
        move("right", power)
    else:
        debug_print(("Direction:", position, "Power:", power), action="line_track", msg="Following line")
        move("forward", power)
    
    if position == "left":
        debug_print(("Direction:", position, "Power:", power), action="line_track", msg="Following line")
        move("left", power)
    elif position == "right":
        debug_print(("Direction:", position, "Power:", power), action="line_track", msg="Following line")
        move("right", power)
    else:
        debug_print(("Direction:", position, "Power:", power), action="line_track", msg="Following line")
        move("forward", power)


if __name__ == "__main__":
    # Example usage
    set_debug(True)  # Enable debug mode for testing
    print("Starting line following test. Place the car on a colored line.")   
    try:
        follow_line(50)  # Adjust power as needed
    except Exception as e:
        print(f"Error occurred: {e}")
    time.sleep(0.1)  # Small delay to avoid busy-waiting
