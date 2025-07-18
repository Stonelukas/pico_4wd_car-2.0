from servo_mp import Servo
from ultrasonic import Ultrasonic
#import time

class Sonar ():

    def __init__ (self, servo: Servo, ultrasonic: Ultrasonic):
        self.servo = servo
        self.ultrasonic = ultrasonic
        self.data = None
        self.progress: int = 0
        self.reference = []
        self.angle: int = 0
        self.state = "idle" # "idle", "scanning"
        
    def scan_advanced(self, angles: list, reference: list, debug=False):
        if (not (len(angles) == (len(reference)))):
            return None
        
        if (self.state == "idle"):
            self.state = "scanning"
            self.data = angles
            self.reference = reference
            self.progress = 0
            self.angle = self.data[0]
            return "scanning"
        elif (self.state == "scanning"):
            if (self.progress < len(self.data)):
                if (self.servo.move_to_angle(self.angle) == "done"):
                    self.data[self.progress] = self.ultrasonic.get_distance()
                    self.progress += 1
                    if (self.progress < len(self.data)):
                        self.angle = self.data[self.progress]
                    return False
                else:
                    return False
            else:
                self.state = "idle"
                if (debug):
                    print(self.data)
                for i in range(len(self.data)):
                    self.data[i] = bool(self.data[i] < self.reference[i])
                return self.data
        else:
            return None
    

    def scan(self, sector: int, offset: int, steps: int, reference: int=25, debug=False):
        
        if (self.state == "idle"):
            self.state = "scanning"
            self.data = [None for _ in range((sector // steps) + 1)]
            self.progress = 0
            self.angle = -abs(sector // 2) + offset
            return "scanning"
        else:
            None

        if (self.state == "scanning"):
            if (self.progress < len(self.data)):
                if (self.servo.move_to_angle(self.angle) == "done"):
                    self.data[self.progress] = self.ultrasonic.get_distance()
                    self.progress += 1
                    self.angle += steps
                    return False
                else:
                    return False
            else:
                self.state = "idle"
                if (debug):
                    print(self.data)
                for i in range(len(self.data)):
                    self.data[i] = bool(self.data[i] < reference)
                return self.data
        else:
            return None

if __name__ == '__main__':
    servo = Servo(18)
    ultrasonic = Ultrasonic(6,7)
    sonar = Sonar(servo, ultrasonic)
    while True:
        #state = sonar.scan(180, 0, 45, 20)
        #state = sonar.scan(60, 0, 15, 20)
        state = sonar.scan_advanced([-30, -15, 0, 15, 30],[40, 50, 60, 50, 40])
        #state = sonar.scan_advanced([-90, -30, 0, 30, 90],[10, 20, 40, 20, 10])
        if (state == "scanning"):
            None
            #print(state)
        elif (isinstance(state, list)):
            print(state)
        else:
            None
            #print(state)
