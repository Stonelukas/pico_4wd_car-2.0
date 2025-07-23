
from machine import Pin, SoftI2C
from time import sleep_ms
from micropython import const
import ustruct
from typing import Optional, Tuple

TCS3472_I2C_ADDR = const(0x29)      # I2C default address
TCS3472_FREQ = const(400000)        # I2C default baudrate

TCS34725_ID = const(0x44)            # Device ID TCS3472
TCS34727_ID = const(0x4D)

TCS3472x_dict = {TCS34725_ID : "TCS34725",
                 TCS34727_ID : "TCS34727"}

TCSCOMMAND_BIT = const(0x80)
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
TCSCMD_PON = const(0x01)                 # PON enable
TCSCMD_AEN = const(0x02)                 # RGBC enable

TCSSTAT_AVALID = const(0x01)             # AVALID bit in status register

# ADC gain
TCSGAIN_MIN = const(0)               
TCSGAIN_LOW = const(1)
TCSGAIN_HIGH = const(2)
TCSGAIN_MAX = const(3)
TCSGAIN_FACTOR = (const(1), const(4), const(16), const(60))

# Codes for Intergration time
TCSINTEG_MIN = const(255)            # 2.4 ms 
TCSINTEG_LOW = const(252)            # 9.4
TCSINTEG_MEDIUM = const(240)            # 38.4
TCSINTEG_HIGH = const(192)            # 153.6
TCSINTEG_MAX = const(0)              # 614.4

# TCS34725 specific clear interupt threshholds 
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
        <scl> and <sda> are required parameters, to be specified as Pin objects
        <freq> is I2C clock frequency, optional, default 400 KHz
        Default values for gain, integration time and autogain are set,
        but these may be changed any time by the user program.
    """
    def __init__(self, i2c: SoftI2C, addr=TCS3472_I2C_ADDR, freq=TCS3472_FREQ): 
        self.address = addr
        self.i2c = i2c
        self.__buf1 = bytearray(1)                    # one-byte buffer
        self.__buf8 = bytearray(8)                    # 8-byte buffer
        self.__gain = 0
        self.__integ = 0
        self.__id = 0x00                               # Device id
        self.__autogain = False
        self.__connected = False
        self.__active = False
        # TODO: change after updating code with new library.
        try:
            self.active(True)
            self.__id = self._register8(TCSREG_ID)
            print(f"Connected {self.device_type} at address 0x{self.address:02x}")
        except OSError:
            print("Failed to connect to device with I2C address 0x{:02x}".format(self.address))
            return
        finally:
            self.active(False)
            self.__connected = True
        # Validate the device ID
        if self.__id not in TCS3472x_dict.keys():
            print("Failed to detect supported color sensor.")
            print(f"Expected ID {TCS34725_ID:#X} ({TCS3472x_dict[TCS34725_ID]}) or "
                f"{TCS34727_ID:#X} ({TCS3472x_dict[TCS34727_ID]}), "
                f"received {self.__id:#02X}")
            return
        self.gain = TCSGAIN_LOW
        self.integ = TCSINTEG_MEDIUM

    def _register8(self, register: int, value: Optional[int] = None) -> int:
        register |= TCSCOMMAND_BIT
        if value is None:
            try:
                result = self.i2c.readfrom_mem(self.address, register, 1)[0]
                return int(result)  # Ensure it's an int
            except Exception as err:
                print(f"I2C register8 read error: {err}")
                return 0  # Return 0 instead of None for bitwise operations
        try:
            data = ustruct.pack('<B', value)
            self.i2c.writeto_mem(self.address, register, data)
        except Exception as err:
            print(f"I2C register8 write error: {err}")
        return 0  # Return something for write operations too
        
    def _register16(self, register: int, value: Optional[int] = None) -> Optional[Tuple[int]]:
        register |= TCSCOMMAND_BIT
        if value is None:
            try:
                data = self.i2c.readfrom_mem(self.address, register, 2)
                return ustruct.unpack('<H', data)
            except Exception as err:
                print(f"I2C register16 read error: {err}")
                return None
        try:
            data = ustruct.pack('<H', value)
            self.i2c.writeto_mem(self.address, register, data)
        except Exception as err:
            print(f"I2C register16 write error: {err}")
        return None

    def active(self, value=None):
        if value is None:
            return self.__active
        value = bool(value)
        if self.__active == value:
            return
        self.__active = value
        enable = self._register8(TCSREG_ENABLE)
        if value:
            self._register8(TCSREG_ENABLE, enable | TCSCMD_PON)
            sleep_ms(3)
            self._register8(TCSREG_ENABLE, enable | TCSCMD_PON | TCSCMD_AEN)
        else:
            self._register8(TCSREG_ENABLE, enable & ~(TCSCMD_PON | TCSCMD_AEN))


    
    def __read_alldata(self):
        """ read all counts (8 contigguous data registers) into local buffer """
        try:
            # self.__Bus.readfrom_mem_into(self.__addr, TCSCMD_ADDRESS | TCSREG_ALLDATA, self.__buf8)
            data = self._register16(TCSREG_ALLDATA)
            return data
        except Exception as err:
            print(f"I2C read_alldata error: {err}")
            return None

    def __adjustgain_one_step(self, counts):
        """ 
            adjust gain (if possible!) when a certain count limits are reached:
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
        self._register8(TCSREG_ENABLE, TCSCMD_POWER_OFF)
        self.__connected = False

    @property
    def isconnected(self):
        """ return status of connection """
        return self.__connected
        

    @property
    def device_type(self):
        """ return name (string) of connected sensor """
        if self.__id is None:
            return "Unknown"
        return TCS3472x_dict.get(self.__id, "Unknown")

    @property
    def gain(self):
        """ return current gain code """
        return self.__gain
    
    @gain.setter 
    def gain(self, gain):
        """ 
        set gain code, forced to a value within limits 
        Args:
            gain: gain code (0..3)
        """
        self.__gain = max(TCSGAIN_MIN, min(TCSGAIN_MAX, gain))
        self._register8(TCSREG_CONTROL, self.gain)
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
        """ 
        set autogain setting.
        Args:
            autogain_new: new autogain value
        """
        self.__autogain = True if autogain_new is True else False

    @property
    def integ(self):
        """ return current integrationtime code code"""
        return self.__integ
    
    @integ.setter
    def integ(self, integ):
        """ set integrationtime code, forced to a value within limits 
        Args:
            integ: integrationtime code value between 0-255.
        """
        self.__integ = max(TCSINTEG_MAX, min(TCSINTEG_MIN, integ))
        self._register8(TCSREG_ATIME, self.__integ)
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
        data = self.__read_alldata()
        format_counts = "<HHHH"                     # 4 USHORTS ( 16-bits, Little Endian)
        counts = ustruct.unpack(format_counts, data)
        if self.__autogain:
            while self.__adjustgain_one_step(counts):
                data = self.__read_alldata()
                counts = ustruct.unpack(format_counts, data)
        return counts

    @property
    def color_raw(self):
        """ Return raw color data as a tuple (red, green, blue, clear). """
        self.__read_alldata()
        # Unpack the buffer into clear , red, green, blue
        clear = self.__buf8[1] << 8 | self.__buf8[0]
        red = self.__buf8[3] << 8 | self.__buf8[2]
        green = self.__buf8[5] << 8 | self.__buf8[4]
        blue = self.__buf8[7] << 8 | self.__buf8[6]
        return (red, green, blue, clear)

    def _valid(self):
        status = self._register8(TCSREG_STATUS)
        return bool(status & 0x01)

    def read(self, raw=False):
        was_active = self.active()
        self.active(True)
        while not self._valid():
            sleep_ms(int(self.integration_time + 0.9))
        # Read the color data registers as integers
        
        r_data = self._register16(TCSREG_RDATA)
        g_data = self._register16(TCSREG_GDATA)
        b_data = self._register16(TCSREG_BDATA)
        c_data = self._register16(TCSREG_CDATA)
        
        if r_data is None or g_data is None or b_data is None or c_data is None:
            self.active(was_active)
            return (0, 0, 0, 0)  # Return zeros if read failed
            
        r = r_data[0]
        g = g_data[0]
        b = b_data[0]
        c = c_data[0]
        
        self.active(was_active)
        return (r, g, b, c)

    def scan(self):
        results = self.i2c.scan()
        print(f"Devices found: \r \n {results}")
        
    def read_all(self, addr, length):
        """
        Read data from the device.

        Args:
            addr: Address to read from on the I2C Bus.
            length: the length to read from the Address.
        """
        try:
            # Select channel using the switch_channel method for consistency
            return self.i2c.readfrom_mem(addr, 0x00, length)
        except Exception as err:
            print(f"I2C read_all error: {err}")
            return None
    
    def write(self, data):
        """
        Write data directly to the bus (after selecting channel).
        
        Args:
            data: data to write to the bus starting at address 0x00
        """
        try:
            # Pass data through to i2c instance
            return self.i2c.write(data)
        except Exception as err:
            print(f"I2C write error: {err}")
            return False
    
    def writeto(self, addr, data):
        """
        Write data to a specific address (after selecting channel).

        Args:
            addr: Address to write to the I2C Bus.
            data: Data to send to the Address on the I2C Bus.
        """
        try:
            # Select channel using the switch_channel method for consistency
            return self.i2c.writeto(addr, data)
        except Exception as err:
            print(f"I2C writeto error: {err}")
            return False


if __name__ == "__main__":
    i2c = SoftI2C(scl=Pin(3), sda=Pin(2))
    sensor = TCS34725(i2c)
    # Get a tuple of integers (red, green, blue, clear)
    r, g, b, c = sensor.read()
    print(f"Red: {r}, Green: {g}, Blue: {b}, Clear: {c}")
