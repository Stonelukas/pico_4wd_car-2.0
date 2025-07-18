from machine import Pin
from rp2 import PIO, StateMachine, asm_pio
import array
import time

# add type hints for the rp2.PIO Instructions
try: 
    from typing_extensions import TYPE_CHECKING # type: ignore
except ImportError:
    TYPE_CHECKING = False
if TYPE_CHECKING:
    from rp2.asm_pio import *

@asm_pio(sideset_init=PIO.OUT_LOW, out_shiftdir=PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    label("bitloop")
    out(x, 1).side(0)[T3 - 1]
    jmp(not_x, "do_zero").side(1)[T1 - 1]
    jmp("bitloop").side(1)[T2 - 1]
    label("do_zero")
    nop().side(0)[T2 - 1]

class WS2812():
    
    def __init__(self, pin, num):
        # Configure the number of WS2812 LEDs.
        self.led_nums = num
        self.pin = pin
        self.sm = StateMachine(0, ws2812, freq=8000000, sideset_base=Pin(self.pin))
        # Start the StateMachine, it will wait for data on its FIFO.
        self.sm.active(1)
        
        self.buf = array.array("I", [0 for _ in range(self.led_nums)])

    def write(self):
        self.sm.put(self.buf, 8)

    def write_all(self, value):
        for i in range(self.led_nums):
            self.__setitem__(i, value)
        self.write()

    def list_to_hex(self, color):
        if isinstance(color, list) and len(color) == 3:
            c = (color[0] << 8) + (color[1] << 16) + (color[2])
            return c
        elif isinstance(color, int):
            value = (color & 0xFF0000)>>8 | (color & 0x00FF00)<<8 | (color & 0x0000FF)
            return value
        else:
            raise ValueError("Color must be 24-bit RGB hex or list of 3 8-bit RGB, not %s"%color)

    def hex_to_list(self, color):
        if isinstance(color, list) and len(color) == 3:
            return color
        elif isinstance(color, int):
            r = color >> 8 & 0xFF
            g = color >> 16 & 0xFF
            b = color >> 0 & 0xFF
            return [r, g, b]
        else:
            raise ValueError("Color must be 24-bit RGB hex or list of 3 8-bit RGB, not %s"%color)

    def __getitem__(self, i):
        return self.hex_to_list(self.buf[i])

    def __setitem__(self, i, value):
        value = self.list_to_hex(value)
        self.buf[i] = value

    
if __name__ == "__main__":
    
    LIGHT_PIN = 19
    LIGHT_NUM = 24
    np = WS2812(LIGHT_PIN, LIGHT_NUM)
    
    # blue
    for i in range(LIGHT_NUM):
        np[i] = 0x0000ff
    np.write()
    time.sleep(1)
    # off 
    for i in range(LIGHT_NUM):
        np[i] = 0x000000
    np.write()    
    
    ## random
    # import random
    # for i in range(LIGHT_NUM):
    #    np[i] = random.randint(0,0xFFFFFF)
    # np.write()
