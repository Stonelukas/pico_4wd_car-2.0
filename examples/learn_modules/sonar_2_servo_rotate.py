import machine
import time

servo = machine.PWM(machine.Pin(18))
servo.freq(50)

def mapping(x, in_min, in_max, out_min, out_max):
    """Map a value from one range to another."""
    if in_min == in_max:
        raise ValueError("in_min and in_max cannot be the same value.")
    if out_min == out_max:
        raise ValueError("out_min and out_max cannot be the same value.")
    if x < in_min or x > in_max:
        raise ValueError(f"x={x} is out of bounds ({in_min}, {in_max}).")
    if out_min > out_max:
        raise ValueError("out_min should be less than out_max.")
    if in_min > in_max:
        raise ValueError("in_min should be less than in_max.")
    if out_min > out_max:
        raise ValueError("out_min should be less than out_max.")
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
# def mapping(x, in_min, in_max, out_min, out_max):
#     return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def set_angle(pin,angle):
    pulse_width=mapping(angle, -90, 90, 2.5,0.5)
    duty=int(mapping(pulse_width, 0, 20, 0,65535))
    pin.duty_u16(duty)

for angle in range(-90,90,5):
    set_angle(servo,angle)
    time.sleep(0.1)
