# Pico-4WD Car V2 Coding Guide

This guide provides essential knowledge for working with the SunFounder Pico-4WD Car V2 codebase, a MicroPython-based robot car platform.

## Architecture Overview

The project follows a modular architecture with these key components:

- **Main Controller** (`libs/main.py`): Central control loop handling user input, sensor data, and operating modes
- **Hardware Drivers**: Individual modules for interacting with physical components
  - Motors (`classes/motor.py`, `libs/motors.py`)
  - Sensors (`classes/grayscale.py`, `classes/tcs34725.py`, `classes/ultrasonic.py`)
  - I2C Communication (`classes/i2c.py`, `classes/mux.py`)
  - Lights (`libs/lights.py`, `libs/ws2812.py`)
- **Operating Modes**:
  - Line following (via color or grayscale)
  - Obstacle avoidance
  - Edge detection
  - Remote control via websocket

## Key Design Patterns

### I2C Multiplexer Architecture
The project uses a TCA9548A multiplexer for handling multiple I2C devices on the same bus:

```python
# Creating sensors with multiplexer channels
self.left_sensor = TCS34725(Left_channel, i2c=self.i2c_instance)
self.middle_sensor = TCS34725(Middle_channel, i2c=self.i2c_instance)
self.right_sensor = TCS34725(Right_channel, i2c=self.i2c_instance)
```

### Error Handling
Hardware interactions use try/except blocks with specific error messages:

```python
try:
    # Hardware operation here
except Exception as err:
    print(f"I2C read_register error at channel {self.__channel}, reg {reg:#x}: {err}")
    return -1
```

### Configuration Constants
Key parameters are defined at the top of files as constants:

```python
OBSTACLE_AVOID_SCAN_ANGLE = 60
OBSTACLE_AVOID_SCAN_STEP = 10
OBSTACLE_AVOID_REFERENCE = 25   # distance referenece (cm)
```

## Development Workflow

### Running Code
Code is executed directly on the Raspberry Pi Pico microcontroller. The main entry point is `libs/main.py`, which is automatically executed when the Pico starts.

### Debugging
- The onboard LED indicates system status:
  - Off: not working
  - Always on: working
  - Blinking: error
- Debug output is sent to serial console and logged to `log.txt`

### Common Issues
- **I2C Communication Errors**: Usually indicate disconnected hardware or incorrect pin configuration
- **'sda' argument required** error: Indicates missing I2C pin configuration
- **Timeout errors**: Normal when hardware is not connected

## Important Cross-Component Dependencies

- The `Follow` class depends on `TCS34725` color sensors 
- Motors depend on proper PWM pin configuration
- Remote control features depend on WiFi settings in `main.py`

## Testing

Example projects in `examples/` demonstrate individual features:
- `examples/funny_projects/project_1_cliff.py`: Edge detection
- `examples/funny_projects/project_2_line.py`: Line following
- `examples/funny_projects/project_3_follow.py`: Following objects
- `examples/funny_projects/project_4_avoid.py`: Obstacle avoidance

## Additional Resources

- [Pico-4WD Car Documentation](https://docs.sunfounder.com/projects/pico-4wd-car/en/latest/index.html)
- [SunFounder Controller App](https://docs.sunfounder.com/projects/sf-controller/en/latest/index.html)
