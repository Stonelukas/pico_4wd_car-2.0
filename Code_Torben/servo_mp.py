from machine import Pin, PWM
import time

def mapping(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

class Servo():
    MAX_PW = 2500
    MIN_PW = 500
    PERIOD = 20000

    def __init__(self, pin):
        self.servo = PWM(Pin(pin, Pin.OUT))
        self.servo.freq(50)
        self.angle: int = 0
        self.angle_target: int = 0
        self.end_time = 0
        self.state = "idle" # "idle" , "moving"

    def set_angle(self, angle):
        try:
            angle = int(angle)
        except:
            raise ValueError("Angle value should be int value, not %s"%angle)
        if angle < -90: # most left
            angle = -90
        if angle > 90: #most right
            angle = 90

        pulse_width=mapping(angle, -90, 90, self.MAX_PW, self.MIN_PW)
        duty=int(mapping(pulse_width, 0, self.PERIOD, 0 ,0xffff))
        self.servo.duty_u16(duty)
    
    def move_to_angle (self, angle: int):
        """
        Uses set_angle, but waits before giving feedback.
        
        Identifies the State of itself.
        Calculates time it takes to reach desired angle based on difference to current angle.
        Returns "done" only once when timer hit zero.
        
        "idle": 	Desired angle and current angle match.
        "moving": 	Desired angle and current angle mismatch, time when move is finished not reached
        "done": 	Time when move is finished reached, will return to "idle"
        
        Parameters:
        angle (int): desired angle for the servo
        
        Returns:
        str: "idle", "moving", "done"
        
        """
        
        try:
            angle: int = int(angle)
        except:
            raise ValueError("Angle value should be int value, not %s"%angle)
        
        if (self.state == "idle"): #check for state
            if (self.angle == angle): #check if angle changed
                self.set_angle(angle)
                return "done"
            else:
                self.state = "moving"
                self.end_time = time.time_ns() + (abs(angle - self.angle) * 1710000) #set Time when turning should end
                self.angle_target = angle
                self.set_angle(self.angle_target)
                return "moving"
        elif (self.state == "moving"): #check for state
            if (time.time_ns() < self.end_time): #timer not elapsed
                self.set_angle(self.angle_target)
                return "moving"
            else: # timer elapsed
                self.end_time = 0
                self.set_angle(self.angle_target)
                self.angle = angle
                self.state = "idle"
                return "done"
        else:
            self.state = "idle"


if __name__ == '__main__':
    servo = Servo(18)
    tests = [-90, 90, 60, 30, 20, 10, 5, 0, -90]
    for num in tests:
        servo.set_angle(num)
        time.sleep(1)
    for num in tests:
        while True:
            state = servo.move_to_angle(num)
            if (state == "done"):
                print(state)
                break
            else:
                print(state)
            time.sleep(0.1)
    servo.set_angle(0)