# Pico-4WD Car Coding Guidelines

## Project Overview

This project is a MicroPython-based controller for the SunFounder Pico-4WD Car v2.0, a Raspberry Pi Pico-powered robot car kit. The car includes several hardware components:

- Motors (4-wheel drive)
- RGB LEDs (bottom and rear)
- Ultrasonic sensor with servo
- Color sensors (TCS34725) with multiplexer (TCA9548A)
- Grayscale sensors
- Speed sensor
- ESP8266 for WiFi connectivity
- Raspberry Pi Pico as the main controller

## Architecture and Data Flow

1. **Main Control Loop**: `libs/main.py` contains the main application that:
   - Initializes hardware components
   - Handles websocket communication with the SunFounder Controller app
   - Processes commands and sensor data
   - Manages different operating modes

2. **Hardware Abstraction Layer**:
   - `libs/classes/` contains individual driver classes for each hardware component
   - `libs/motors.py`, `libs/sonar.py`, `libs/lights.py` provide higher-level APIs
   - `libs/classes/mux.py` handles I2C multiplexing for the color sensors

3. **Communication**:
   - `libs/ws.py` handles the websocket server using the ESP8266 module via UART
   - Data exchange protocol is JSON-based key-value pairs

4. **Operation Modes**:
   - Line tracking (following colored lines)
   - Obstacle avoidance
   - Follow mode (following objects)
   - Anti-fall (cliff detection)
   - Manual control

## Key Development Patterns

### I2C Multiplexer Pattern

The project uses a TCA9548A I2C multiplexer to connect multiple TCS34725 color sensors:

```python
from classes.mux import TCA9548A
from classes.i2c import MyI2C

class Follow:
    def __init__(self, Left_channel, Middle_channel, Right_channel, target_rgb):
        self.i2c_instance = MyI2C()
        # Initialize sensors with proper channel values and shared I2C instance
        self.left_sensor = TCS34725(Left_channel, i2c=self.i2c_instance)
        self.middle_sensor = TCS34725(Middle_channel, i2c=self.i2c_instance)
        self.right_sensor = TCS34725(Right_channel, i2c=self.i2c_instance)
```

### Component Initialization Pattern

Components are initialized in the main file and exceptions are logged to `log.txt`:

```python
try:
    speed = Speed(8, 9)
    sensors = Follow(Left_channel=1, Middle_channel=2, Right_channel=3, target_rgb=(255, 0, 0))
    grayscale = Grayscale(26, 27, 28)
    ws = WS_Server(name=NAME, mode=WIFI_MODE, ssid=SSID, password=PASSWORD)
except Exception as e:
    onboard_led.off()
    sys.print_exception(e)
    with open(LOG_FILE, "a") as log_f:
        log_f.write('\n> ')
        sys.print_exception(e, log_f)
    sys.exit(1)
```

### Websocket Communication Pattern

The main loop processes websocket messages using callback handlers:

```python
def on_receive(data):
    # Process data from the SunFounder Controller app
    # Update global state variables

def main():
    ws.on_receive = on_receive
    if ws.start():
        onboard_led.on()
        while True:
            ws.loop()
            remote_handler()
```

### Mode Switching Pattern

The code uses state flags to manage operation modes:

```python
# Mode selection from app control data
if m_on:
    if mode != 'anti fall':
        mode = 'anti fall'
elif n_on:
    if mode != 'line track':
        mode = 'line track'
# ...and so on
```

## Critical Files and Their Purposes

- `libs/main.py`: Main application entry point
- `libs/classes/follow.py`: Line following using color sensors
- `libs/classes/motor.py`: Motor control primitives
- `libs/classes/mux.py`: TCA9548A I2C multiplexer implementation
- `libs/motors.py`: High-level motor control functions
- `libs/ws.py`: Websocket communication handling
- `libs/sonar.py`: Ultrasonic sensor and servo control

## Development Tips

1. **Debugging**: Enable debug mode via the app (`data['I'] = True`) or manually set `debug = True` to see detailed logs.

2. **Testing Hardware**: Use the example files in `examples/learn_modules/` to test individual components.

3. **Adding New Features**: 
   - Create a new mode handler function (like `follow()` or `obstacle_avoid()`)
   - Add mode selection logic in the `on_receive()` function
   - Call your handler in the `remote_handler()` function

4. **Common Issues**:
   - Color sensor calibration is sensitive to ambient light
   - ESP8266 connection issues require a reset (handled in exception handling)
   - Motor power needs to be adjusted gradually to avoid high back-EMF
   - I2C multiplexer channel selection must be done before each sensor read

5. **Working with Color Sensors**:
   - Always select the correct multiplexer channel before reading a sensor
   - Example: `sensor.switch_channel(channel)` before reading color values
   - Color matching is done by calculating Euclidean distance between RGB values

6. **Custom Line Tracking**:
   - Use `color_line_track(rgb)` with a custom RGB tuple to follow specific colored lines
   - Auto color tracking is available via `auto_color_line_track()` which detects line color automatically
[byterover-mcp]

# important 
always use byterover-retrive-knowledge tool to get the related context before any tasks 
always use byterover-store-knowledge to store all the critical informations after sucessful tasks