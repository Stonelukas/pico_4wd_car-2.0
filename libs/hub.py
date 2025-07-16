import time
from motors import move, stop
from machine import I2C, Pin
from line_track import line_track

'''Configure the power of the line_track mode'''
LINE_TRACK_POWER = 80

'''Configure color sensor module'''


'''------------ Instantiate -------------'''
onboard_led = Pin(25, Pin.OUT) 

def hub(target_color, left, middle, right):
    global line_out_time
    _power = LINE_TRACK_POWER


    if left != "grün" and middle != "grün" and right != "grün":
        print(f"Auto ist nicht im Hub.")
    else:
        if middle == "grün" and left != "grün":
            move('forward', _power)
            move('turn_in_place_right', _power)
            while not (left == "grün" and middle == "grün" and right == target_color): 
                if left == "grün" and middle == "grün":
                    move('forward', _power)
                elif left == "grün":
                    move('left', _power)
            stop()
            status = line_track(target_color, left, middle, right) 
            return status
        
