'''
This example adds the N widget for line track.
"A" widget for display greyscale work.
'''

import time
from motors import move, stop
from machine import I2C, Pin

# line track
line_out_time = 0

'''Configure the power of the line_track mode'''
LINE_TRACK_POWER = 80

'''Configure color sensor module'''


'''------------ Instantiate -------------'''
onboard_led = Pin(25, Pin.OUT) 
    
'''----------------- line_track ---------------------'''
def line_track(target_color, left, middle, right):
    global line_out_time
    _power = LINE_TRACK_POWER
    
    #print(f"gs_data: {gs_data}, {grayscale.line_ref}")

    if not (middle == 'terracotta' and left == 'terracotta' and right == 'terracotta'):
        while not (middle == target_color and left == target_color and right == target_color):
            if middle == target_color:
                move('forward', _power)
            elif right == target_color:
                move('right', _power)
            elif left == target_color:
                move('left', _power)
        stop()
    return 'line end'
        

