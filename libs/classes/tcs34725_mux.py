from machine import Pin, SoftI2C
from time import sleep_ms
from micropython import const
from struct import unpack
from classes.mux import TCA9548A_Channel, TCA9548A
from classes.i2c import MyI2C

from typing_extensions import Literal

TCS3472_I2C_ADDR = const(0x29)      # I2C default address
TCS3472_FREQ = const(400000)        # I2C default baudrate

TCS34725_ID = const(0x44)            # Device ID TCS3472
TCS34727_ID = const(0x4D)

TCS3472x_dict = {TCS34725_ID : "TCS34725",
                 TCS34727_ID : "TCS34727"}

TCSREG_ENABLE = const(0x00)          # Enable states and interrupts 
TCSREG_ATIME = const(0x01)           # RGBC time
TCSREG_CONFIG = const(0x0D)          # Configuration
TCSREG_CONTROL = const(0x0F)         # Control
TCSREG_ID = const(0x12)              # Device ID
TCSREG_STATUS = const(0x13)          # Device Status
TCSREG_ALLDATA = const(0x14)         # All data low byte
TCSREG_CDATA = const(0x14)           # Clear data low byte
TCSREG_RDATA = const(0x16)           # Red data low byte
TCSREG_GDATA = const(0x18)           # Green data low byte
TCSREG_BDATA = const(0x1A)           # Blue data low byte

TCSCMD_ADDRESS = const(0xA0)
TCSCMD_POWER_OFF = const(0x00)           # Power Off
TCSCMD_POWER_ON =  const(0x01)           # Power ON
TCSCMD_AEN = const(0x02)                 # RGBC enable

TCSSTAT_AVALID = const(0x01)             # AVALID bit in status register

# ADC gain
TCSGAIN_MIN = const(0)               
TCSGAIN_LOW = const(1)
TCSGAIN_HIGH = const(2)
TCSGAIN_MAX = const(3)
TCSGAIN_FACTOR = (const(1), const(4), const(16), const(60))

# Codes for Integration time
TCSINTEG_MIN = const(255)            # 2.4 ms 
TCSINTEG_LOW = const(252)            # 9.4
TCSINTEG_MEDIUM = const(240)            # 38.4
TCSINTEG_HIGH = const(192)            # 153.6
TCSINTEG_MAX = const(0)              # 614.4

# TCS34725 specific clear interrupt thresholds 
TCSREG_WTIME = const(0x03)
TCSREG_AILTL = const(0x04)
TCSREG_AILTH = const(0x05)
TCSREG_AIHTL = const(0x06)
TCSREG_AIHTH = const(0x07)
TCSREG_PERS = const(0x0C)

class TCS34725:
    """ TCS34725 class
        Create an I2C instance for the PyBoard/ESP32/ESP8266.
        <addr> is I2C address, optional, default 0x29
        <i2c> is an optional I2C instance, if not provided a new one is created
        <channel> is the multiplexer channel to use, optional, default 0
        <freq> is I2C clock frequency, optional, default 400 KHz
        Default values for gain, integration time and autogain are set,
        but these may be changed any time by the user program.
    """
    def __init__(self, channel, i2c=None, addr=TCS3472_I2C_ADDR, freq=TCS3472_FREQ): 
        self.__addr = addr
        self.__buf1 = bytearray(1)            # one-byte buffer
        self.__buf8 = bytearray(8)            # 8-byte buffer
        self.__gain = 0
        self.__integ = 0
        self.__id = 0x00                      # Device id
        self.__channel = channel
        self.__autogain = False
        self.__connected = False
        
        # Create or store the provided I2C instance
        if i2c is None:
            # Create a default I2C instance if none provided
            self.i2c = MyI2C(freq=freq)
        else:
            self.i2c = i2c
        try:
            # Select the multiplexer channel
            self.i2c.writeto(0x70, bytearray([1 << self.__channel]))
            sleep_ms(5)
            # Try to communicate with the sensor (address | command bit)
            self.i2c.writeto(self.__addr, b'\x80')
            self.i2c.readfrom_into(self.__addr, self.__buf1)
            self.__id = self.__buf1[0]
            # Validate the device ID
            if not self.__id in TCS3472x_dict.keys():
                print(f"Failed to detect supported color sensor on channel {channel}")
                print(f"Expected ID {TCS34725_ID:#X} ({TCS3472x_dict[TCS34725_ID]}) or "
                    f"{TCS34727_ID:#X} ({TCS3472x_dict[TCS34727_ID]}), "
                    f"received {self.__id:#02X}")
                return
            self.__connected = True    
            print(f"Connected {self.device_type} at address 0x{self.__addr:02x} on channel {channel}")
            # Initialize the sensor
            self.__write_register(TCSREG_ENABLE, TCSCMD_POWER_ON | TCSCMD_AEN)
            sleep_ms(5)
            
            # Set default values
            self.gain = TCSGAIN_LOW
            self.integ = TCSINTEG_MEDIUM
        except Exception as e:
            print(f"Error initializing TCS34725 on channel {channel}: {e}")


    def switch_channel(self, chan=None):
        """Switch to a different multiplexer channel"""
        if chan is not None and 0 <= chan <= 7 and self.i2c is not None:
            self.__channel = chan
            try:
                # Reinitialize the bus with the new channel
                self.i2c.writeto(0x70, bytearray([1 << chan]))
            except Exception as e:
                print(f"Error switching to channel {chan}: {e}")
        return self.__channel

    def __read_register(self, reg):
        """ read register <reg>, return integer value """
        try:
            # Select channel using the switch_channel method for consistency
            self.switch_channel(self.__channel)
            # Use readfrom_mem_into for more efficient reading
            # Command bit (MSB=1) must be set for all register access per datasheet p.9
            # Ensure we're passing positional args only, no keyword args
            self.i2c.readfrom_mem_into(self.__addr, reg | 0x80, self.__buf1)
            return self.__buf1[0]
        except Exception as err:
            print(f"I2C read_register error at channel {self.__channel}, reg {reg:#x}: {err}")
            return -1
    
    def __write_register(self, reg, data):
        """ write register """
        self.__buf1[0] = data
        try:
            # Select channel using the switch_channel method for consistency
            self.switch_channel(self.__channel)
            # Use writeto_mem for more efficient writing
            # Command bit (MSB=1) must be set for all register access per datasheet p.9
            # Ensure we're passing positional args only, no keyword args
            self.i2c.writeto_mem(self.__addr, reg | 0x80, self.__buf1)
        except Exception as err:
            print(f"I2C write_register error at channel {self.__channel}, reg {reg:#x}: {err}")
            return False
        return True
    
    def __read_alldata(self):
        """ read all counts (8 contigguous data registers) into local buffer """
        try:
            # Select channel using the switch_channel method for consistency
            self.switch_channel(self.__channel)
            # Use readfrom_mem_into for more efficient reading of all data
            # Command bit (MSB=1) must be set for all register access per datasheet p.9
            self.i2c.readfrom_mem_into(self.__addr, TCSREG_ALLDATA | 0x80, self.__buf8)
            return self.__buf8
        except Exception as err:
            print(f"I2C read_alldata error at channel {self.__channel}: {err}")
            return None

    def __adjustgain_one_step(self, counts):
        """ adjust gain (if possible!) when a certain count limits are reached:
            <counts> is tuple of 4 integers
            switch to lower gain when highest count exceeds 85% of maximum
            switch to higher gain when highest count is below 15% of maximum
            note: quotient of high over low boundaries must be greater
                than 4 to prevent flip-flopping between gain factors
            return True when gain changed, False otherwise
        """

        UNDERFLOW_PERCENT = const(15)
        OVERFLOW_PERCENT = const(85)
        print("overflow_count=", self.overflow_count)
        count_max = max(counts)
        if count_max >= self.overflow_count * OVERFLOW_PERCENT // 100:
            if self.gain > TCSGAIN_MIN:
                print("==> Actual gain factor", self.gain_factor, end="")
                self.gain -= 1 
                print(", new", self.gain_factor)
                return True
        elif count_max < self.overflow_count * UNDERFLOW_PERCENT // 100:
            if self.gain < TCSGAIN_MAX:
                print("==> Actual gain factor", self.gain_factor, end="")
                self.gain += 1
                print(", new", self.gain_factor)
                return True
        return False

    """ Public methods and properties """
    
    def close(self):
        """ Power-down device and close I2C bus (if supported) """
        self.__write_register(TCSREG_ENABLE, TCSCMD_POWER_OFF)
        self.__connected = False

    @property
    def channel(self):
        """ return integer of current channel of the multiplexer"""
        return self.__channel

    @channel.setter
    def channel(self, channel):
        """ set channel of of the multiplexer """
        self.__channel = channel

    @property
    def isconnected(self):
        """ return status of connection """
        return self.__connected
        

    @property
    def device_type(self):
        """ return name (string) of connected sensor """
        return TCS3472x_dict.get(self.__id, "Unknown")

    @property
    def gain(self):
        """ return current gain code """
        return self.__gain
    
    @gain.setter 
    def gain(self, gain):
        """ set gain code (0..3), forced to a value within limits """
        self.__gain = max(TCSGAIN_MIN, min(TCSGAIN_MAX, gain))
        self.__write_register(TCSREG_CONTROL, self.gain)
        sleep_ms(2 * self.integration_time)
    
    @property
    def gain_factor(self):
        """ return current gain factor """
        return TCSGAIN_FACTOR[self.__gain]

    @property
    def autogain(self):
        """ return current autogain setting """
        return self.__autogain
    
    @autogain.setter
    def autogain(self, autogain_new):
        """ set autogain setting (True/False) """
        self.__autogain = True if autogain_new == True else False

    @property
    def integ(self):
        """ return current integrationtime code code"""
        return self.__integ
    
    @integ.setter
    def integ(self, integ):
        """ set integrationtime code (255..0), forced to a value within limits """
        self.__integ = max(TCSINTEG_MAX, min(TCSINTEG_MIN, integ))
        self.__write_register(TCSREG_ATIME, self.__integ)
        sleep_ms(2 * self.integration_time)
    
    @property
    def integration_time(self):
        """ return current integration time in milliseconds """
        return int(2.4 * (256 - self.__integ))

    @property
    def overflow_count(self):
        """ return maximum count for actual integration time """
        return min(65535, (256 - self.__integ) * 1024)
    
    @property
    def colors(self):
        """ read all data registers, return tuple: (clear, red, green, blue) """
        self.i2c.__read_alldata(self.__addr, TCSREG_ALLDATA | 0x80)
        format_counts = "<HHHH"                     # 4 USHORTS ( 16-bits, Little Endian)
        counts = unpack(format_counts, self.__buf8)
        if self.__autogain == True:
            while self.__adjustgain_one_step(counts):
                self.i2c.__read_alldata(self.__addr, TCSREG_ALLDATA | 0x80)
                counts = unpack(format_counts, self.__buf8)
        return counts

    @property
    def color_raw(self):
        """Return raw color data as a tuple (red, green, blue, clear)."""
        self.i2c.__read_alldata(self.__addr, TCSREG_ALLDATA | 0x80)
        # Unpack the buffer into clear, red, green, blue (order as per datasheet)
        clear = self.__buf8[1] << 8 | self.__buf8[0]
        red   = self.__buf8[3] << 8 | self.__buf8[2]
        green = self.__buf8[5] << 8 | self.__buf8[4]
        blue  = self.__buf8[7] << 8 | self.__buf8[6]
        return (red, green, blue, clear)

    def read_all(self, addr, length):
        """Read data from the device."""
        try:
            # Select channel using the switch_channel method for consistency
            self.switch_channel(self.__channel)
            return self.i2c.readfrom_mem(addr, 0x00, length)
        except Exception as err:
            print(f"I2C read_all error at channel {self.__channel}: {err}")
            return None
    
    def write(self, data):
        """Write data directly to the bus (after selecting channel)."""
        try:
            # Select channel using the switch_channel method for consistency
            self.switch_channel(self.__channel)
            # Pass data through to i2c instance
            return self.i2c.write(data)
        except Exception as err:
            print(f"I2C write error at channel {self.__channel}: {err}")
            return False
    
    def writeto(self, addr, data):
        """Write data to a specific address (after selecting channel)."""
        try:
            # Select channel using the switch_channel method for consistency
            self.switch_channel(self.__channel)
            return self.i2c.writeto(addr, data)
        except Exception as err:
            print(f"I2C writeto error at channel {self.__channel}, addr {addr:#x}: {err}")
            return False
    
    def start(self):
        """Start the device by enabling power and ADC."""
        # Use the constants instead of hardcoded values
        return self.__write_register(TCSREG_ENABLE, TCSCMD_POWER_ON | TCSCMD_AEN)

