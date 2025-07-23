from machine import Pin, SoftI2C
from classes.lock import Lockable
from micropython import const

DEFAULT_FREQ = const(400000)        # I2C default baudrate

class MyI2C(Lockable):
    """ I2C class
        Create an I2C instance.
        <addr> is I2C address.
        <scl> and <sda> are required parameters, to be specified as Pin objects
        <freq> is I2C clock frequency, optional, default 400 KHz
        Default values for gain, integration time and autogain are set,
        but these may be changed any time by the user program.
    """
    def __init__(self, freq=DEFAULT_FREQ): 
        self.__buf1 = bytearray(1)                    # one-byte buffer
        self.__buf8 = bytearray(8)                    # eight-byte buffer
        self.__connected = False
        self.__Bus = SoftI2C(sda=Pin(2), scl=Pin(3), freq=freq)

    def connect(self, addr):
        self.__Bus.writeto(addr, b'\x80')
        self.__connected = True
        return True

    def __read_register_mem(self, addr, reg):
        """ read register <reg>, return integer value """
        try:
            self.__Bus.readfrom_mem_into(addr, reg, self.__buf1)
            return self.__buf1[0]
        except Exception as err:
            print("I2C read_register error:", err)
            return -1

    def __read_alldata(self, addr, reg):
        """ read all counts (8 contigguous data registers) into local buffer """
        try:
            # self.__Bus.readfrom_mem_into(self.__addr, TCSCMD_ADDRESS | TCSREG_ALLDATA, self.__buf8)
            self.__Bus.readfrom_mem_into(addr, reg, self.__buf8)
            return self.__buf8
        except Exception as err:
            print(f"I2C read_alldata error: {err}")
            return None

    
    def __write_register(self, addr, reg, data):
        """ write register """
        self.__buf1[0] = data
        try:
            self.__Bus.writeto_mem(addr, reg, self.__buf1)
        except Exception as err:
            print("I2C write_byte error:", err)
            return False
        return True

    """ Public methods and properties """

    def close(self, addr, reg_enable, cmd_power_off):
        """ Power-down device and close I2C bus (if supported) """
        self.__write_register(addr, reg_enable, cmd_power_off)
        self.__connected = False

    
    def readfrom_into(self, addr, buffer):
        return self.__Bus.readfrom_into(addr=None, buffer=None, stop=True)
    
    def readfrom_mem_into(self, addr, memaddr, buffer):
        """Read from memory into buffer."""
        try:
            # Use positional arguments only
            return self.__Bus.readfrom_mem_into(addr, memaddr, buffer)
        except Exception as err:
            print(f"I2C readfrom_mem_into error: {err}")
            return False
    
    def readfrom_mem(self, addr, memaddr, length):
        """Read from memory and return bytes."""
        try:
            # Use positional arguments only
            return self.__Bus.readfrom_mem(addr, memaddr, length)
        except Exception as err:
            print(f"I2C readfrom_mem error: {err}")
            return None
    
    def writeto_mem(self, addr, memaddr, buffer):
        """Write to memory."""
        try:
            # Use positional arguments only
            return self.__Bus.writeto_mem(addr, memaddr, buffer)
        except Exception as err:
            print(f"I2C writeto_mem error: {err}")
            return False
    


    @property
    def isconnected(self):
        """ return status of connection """
        return self.__connected

    def scan(self) -> list:
        return self.__Bus.scan()
        
    def read_all(self, addr, length, stop=False):
        """
        Read 'length' bytes from device at 'addr' starting from register 0x00.
        Returns the bytes read.
        """
        try:
            return self.__Bus.readfrom_mem(addr, 0x00, length)
        except Exception as err:
            print(f"I2C read_all error: {err}")
            return None
    
    def write(self, data):
        self.__Bus.write(data)
    
    def writeto(self, addr, buffer):
        if isinstance(buffer, str):
            buffer = bytes([ord(x) for x in buffer])
        # Some implementations don't accept keyword arguments
        # Use positional arguments only
        self.__Bus.writeto(addr, buffer)
    
    def start(self):
        self.writeto(0x00, 0x01)

