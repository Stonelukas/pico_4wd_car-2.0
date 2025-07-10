import time
from micropython import const
from machine import SoftI2C, Pin
from classes.i2c import MyI2C

from typing_extensions import Literal

_DEFAULT_ADDRESS = const(0x70)
_TCS3472_FREQ = const(400000)        # I2C default baudrate
_SDA_PIN = const(2)                 # TODO not sure which pin is right
_SCL_PIN = const(3)                 # TODO not sure which pin is right

class TCA9548A_Channel(SoftI2C):
    def __init__(self, tca: "TCA9548A", channel: int) -> None:
        self.tca = tca
        self.channel = channel
        self.channel_switch = bytearray([1 << channel])
        
    def reinit(self, channel: int):
        self.channel = channel
        self.channel_switch = bytearray([1 << channel])
        self.try_lock()
    
    def try_lock(self) -> bool:
        while not self.tca.i2c.try_lock():
            time.sleep(0)
        self.tca.i2c.writeto(self.tca.addr, self.channel_switch)
        return True
    
    def unlock(self):
        self.tca.i2c.writeto(self.tca.addr, b"\x00")
        return self.tca.i2c.unlock()
    
    # def writeto_mem(self, addr, reg, data):
    #     self.tca.i2c.writeto(self.tca.addr, self.channel_switch)
    #     return self.tca.i2c.write_mem_to(addr, reg, data)
        
    # def readfrom_mem_into(self, addr, reg, buf):
    #     self.tca.i2c.writeto(self.tca.addr, self.channel_switch)
    #     return self.tca.i2c.read_mem_into(addr, reg, buf)
    
    def scan(self):
        result = []
        for i in range(3):
            self.reinit(i)
            self.try_lock()
            new_devices : list = self.tca.i2c.scan()
            result = result + new_devices
            self.unlock()
        print(f"Devices found:")
        print("\n".join([str(device) for device in result])) 

class TCA9548A:
    def __init__(self, i2c: MyI2C, addr: int = _DEFAULT_ADDRESS, freq = _TCS3472_FREQ, ) -> None:
        self.i2c = i2c
        self.addr = addr
        self.channels: list[TCA9548A_Channel | None] = [None] * 8

    def __len__(self) -> Literal[8]:
        return 8
    
    def __getitem__(self, key: Literal[0, 1, 2, 3, 4, 5, 6, 7]) -> "TCA9548A_Channel":
        if not 0 <= key <= 7:
            raise IndexError("Channel must be an integer in the range: 0-7.")
        if self.channels[key] is None:
            self.channels[key] = TCA9548A_Channel(self, key)
        return self.channels[key]  # type: ignore
