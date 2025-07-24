# filepath: libs/classes/follow.py
import time
from time import sleep
from machine import Pin, SoftI2C
from helper import debug_print, get_debug
from typing import Optional, Union, Tuple, Any

from classes.new_tcs import TCS34725, TCSGAIN_LOW, TCSINTEG_MEDIUM


class Follow:
    def __init__(
        self,
        target_color: Union[str, Tuple[int, int, int]] = "orange",
        standalone: bool = False,
    ):
        """
        Initialize the Follow class for line tracking with color sensors.

        Args:
            target_color: Target color to follow - can be either:
                         - A color name string (e.g., "orange", "blue", "terracotta")
                         - An RGB tuple (e.g., (255, 128, 0))
            standalone: Whether to run in standalone mode with single sensor
        """
        print("Starting tcs34725")
        self.standalone = standalone

        # Initialize sensors with proper channel values and shared I2C instance
        if not self.standalone:
            self.left_sensor = TCS34725(SoftI2C(scl=Pin(3), sda=Pin(2)))
            self.middle_sensor = TCS34725(SoftI2C(scl=Pin(1), sda=Pin(0)))
            self.right_sensor = TCS34725(SoftI2C(scl=Pin(11), sda=Pin(10)))
            # Set default gain and integration time for each sensor
            for sensor in (self.left_sensor, self.middle_sensor, self.right_sensor):
                sensor.gain = TCSGAIN_LOW  # Low gain
                sensor.integ = TCSINTEG_MEDIUM  # ~40 ms integration time
        else:
            self.sensor = TCS34725(SoftI2C(scl=Pin(3), sda=Pin(2)))
            self.sensor.gain = TCSGAIN_LOW  # Low gain
            self.sensor.integ = TCSINTEG_MEDIUM  # ~40 ms integration time


        # Color mapping for string conversion - adjusted for realistic sensor readings
        self.color_map = {
            "terracotta": (149, 144, 130),
            "green": (142, 153, 110),
            "yellow": (151, 145, 124),
            # "weiss": (127, 138, 112),
            # "schwarz": (164, 133, 115),
            "lila": (139, 146, 137),
            # "orange": (164, 127, 107),
            "blue": (121, 157, 147),
        }
        self.rgb_to_color = {v: k for k, v in self.color_map.items()}
        self.min_lila_map = (150, 140, 110, 350)
        self.max_lila_map = (200, 190, 160, 600)

        # Convert target_color to RGB tuple and validate
        if isinstance(target_color, str):
            # Convert color name to RGB
            self.target_rgb = self._validate_rgb(self.color_name_to_rgb(target_color))
        else:
            # Assume it's an RGB tuple
            self.target_rgb = self._validate_rgb(target_color)


        # Set target color name based on RGB
        self.target_color = self._get_closest_color_name(self.target_rgb)
        print("I2C started")
        self.color_threshold = 40  # Adjust this value as needed
        self.line_out_time = 0  # Track when line was lost

    def _safe_input(self, prompt: str = "", timeout_ms: int = 30000) -> str:
        """Safe input function that handles MicroPython limitations

        Args:
            prompt: Text to display to user
            timeout_ms: Timeout in milliseconds (default 30 seconds)

        Returns:
            str: User input or empty string if failed
        """
        if prompt:
            print(prompt)

        try:
            # Try standard input first
            user_input = input()
            print(f"Received input: '{user_input}'")
            return user_input
        except (OSError, KeyboardInterrupt, EOFError) as e:
            print(f"Input error: {e}")
            print("Using alternative input method...")

            # Alternative method for MicroPython
            try:
                import sys
                import time

                start_time = time.ticks_ms()
                result = ""

                print("Press Enter when ready (or wait for timeout)...")

                while True:
                    if time.ticks_diff(time.ticks_ms(), start_time) > timeout_ms:
                        print("Input timeout reached, proceeding...")
                        break

                    # Simple character-by-character reading
                    try:
                        char = sys.stdin.read(1) if hasattr(sys.stdin, "read") else None
                        if char and (char == "\n" or char == "\r"):
                            break
                        elif char:
                            result += char
                    except (OSError, AttributeError):
                        # If character reading fails, just break
                        break

                    time.sleep_ms(100)  # Small delay

                if result:
                    print(f"Received: '{result}'")
                return result

            except (ImportError, AttributeError, OSError):
                # If all input methods fail, use a simple delay
                print("Input not available - waiting 3 seconds then proceeding...")
                try:
                    time.sleep(3)
                except Exception as sleep_error:
                    print(f"Sleep error: {sleep_error}")
                return ""

        except Exception as e:
            print(f"Unexpected input error: {e}")
            print("Proceeding without user input...")
            return ""

    def _validate_rgb(self, rgb: Tuple[Any, ...]) -> Tuple[int, int, int]:
        """Validate RGB tuple and ensure it contains exactly 3 integers.

        Args:
            rgb (Tuple[Any, ...]): Tuple of 3 Color Values (R, G, B)

        Raises:
            ValueError: rgb must be tuple of 3 value
            ValueError: rgb must be numbers (int or float)
            ValueError: rgb value at index was not a number

        Returns:
            Tuple[int, int, int]: Tuple of the 3 validated color values (R, G, B)
        """
        if not isinstance(rgb, tuple) or len(rgb) != 3:
            raise ValueError("RGB must be a tuple of exactly 3 values (R, G, B)")

        # Ensure all values are integers and within valid range (0-255) also make sure the color is in the color_map dictionary
        if not all(isinstance(value, (int, float)) for value in rgb):
            raise ValueError("RGB values must be numbers (int or float)")
        validated_rgb = []
        for i, value in enumerate(rgb):
            # Ensure each value is a number and within the range 0-255
            if not isinstance(value, (int, float)):
                raise ValueError(f"RGB value at index {i} must be a number")

            # Convert to int and clamp to 0-255 range
            int_value = int(value)
            clamped_value = max(0, min(255, int_value))
            validated_rgb.append(clamped_value)

        return tuple(validated_rgb)

    def _get_closest_color_name(self, rgb: Tuple[int, int, int]) -> str:
        """Get the closest color name for an RGB value using the color_map.

        Args:
            rgb (Tuple[int, int, int]): Tuple of 3 values (R, G, B)

        Returns:
            str: Color name for the rgb value (e.g.: (255, 0, 0) => "Red")
        """
        if rgb in self.rgb_to_color:
            return self.rgb_to_color[rgb]

        # If exact match not found, find the closest color
        min_distance = float("inf")
        closest_color = ""

        for color_name, color_rgb in self.color_map.items():
            distance = self._color_distance(rgb, color_rgb)
            if distance < min_distance:
                min_distance = distance
                closest_color = color_name

        return closest_color

    def read_raw(self, sensor: str = None) -> Tuple[int, int, int, int]:
        """Read raw ADC values from sensor without conversion

        Args:
            sensor: The sensor to read from (None for standalone mode)

        Returns:
            Tuple[int, int, int, int]: Raw ADC values (r, g, b, clear)
        """
        if self.standalone:
            raw_values = self.sensor.read()
        else:
            if sensor == "left":
                raw_values = self.left_sensor.read() 
            if sensor == "middle":
                raw_values = self.middle_sensor.read() 
            if sensor == "right":
                raw_values = self.right_sensor.read() 
        return raw_values

    def _read_sensor(self, sensor: Any = None) -> Tuple[int, int, int]:
        """Read color values from the specified sensor

        Args:
            sensor (Any): The sensor to read from

        Returns:
            Tuple[int, int, int]: Tuple of the 3 color values read from the sensor (R, G, B)
        """
        if self.standalone:
            # If standalone, read from the single sensor instance
            raw_values = self.sensor.read()  # Returns (r, g, b, clear)
        else:
            raw_values = sensor.read()  # Returns (r, g, b, clear)

        # Convert raw ADC values to standard RGB (0-255)
        return self._raw_to_rgb(
            raw_values[0], raw_values[1], raw_values[2], raw_values[3]
        )

    def _raw_to_rgb(
        self, r_raw: int, g_raw: int, b_raw: int, clear_raw: int
    ) -> Tuple[int, int, int]:
        """Convert raw ADC values from TCS34725 to standard RGB (0-255)

        This uses a better algorithm that doesn't always push values to white.

        Args:
            r_raw: Raw red ADC value (may be int or tuple)
            g_raw: Raw green ADC value (may be int or tuple)
            b_raw: Raw blue ADC value (may be int or tuple)
            clear_raw: Raw clear/total light ADC value (may be int or tuple)

        Returns:
            Tuple[int, int, int]: Standard RGB values (0-255)
        """

        # Ensure we have integers, not tuples
        def extract_int(value):
            if isinstance(value, tuple):
                return int(value[0]) if len(value) > 0 else 0
            return int(value)

        r_raw = extract_int(r_raw)
        g_raw = extract_int(g_raw)
        b_raw = extract_int(b_raw)
        clear_raw = extract_int(clear_raw)

        if clear_raw == 0:
            return (0, 0, 0)

        # Method 1: Simple ratio normalization (better for color detection)
        # Normalize each channel against the clear channel to get relative intensities
        r_ratio = r_raw / clear_raw
        g_ratio = g_raw / clear_raw
        b_ratio = b_raw / clear_raw

        # Apply a scaling factor to get meaningful RGB values
        # This factor can be adjusted based on your lighting conditions
        scale_factor = 355  # Adjust this value based on your sensor readings

        r = int(r_ratio * scale_factor)
        g = int(g_ratio * scale_factor)
        b = int(b_ratio * scale_factor)

        # Clamp values to 0-255 range
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))

        return (r, g, b)

    def _raw_to_rgb_alternative(
        self, r_raw: int, g_raw: int, b_raw: int, clear_raw: int
    ) -> Tuple[int, int, int]:
        """Alternative RGB conversion method - removes illumination effects

        This method removes the illumination component to get purer color representation.

        Args:
            r_raw: Raw red ADC value
            g_raw: Raw green ADC value
            b_raw: Raw blue ADC value
            clear_raw: Raw clear ADC value

        Returns:
            Tuple[int, int, int]: RGB values (0-255)
        """

        # Ensure we have integers
        def extract_int(value):
            if isinstance(value, tuple):
                return int(value[0]) if len(value) > 0 else 0
            return int(value)

        r_raw = extract_int(r_raw)
        g_raw = extract_int(g_raw)
        b_raw = extract_int(b_raw)
        clear_raw = extract_int(clear_raw)

        if clear_raw == 0:
            return (0, 0, 0)

        # Calculate illumination-corrected values
        # This removes the white light component
        illumination = clear_raw - max(r_raw, g_raw, b_raw)

        # Subtract illumination from each channel
        r_corrected = max(0, r_raw - illumination * 0.3)  # Adjust factors as needed
        g_corrected = max(0, g_raw - illumination * 0.3)
        b_corrected = max(0, b_raw - illumination * 0.3)

        # Find the sum for normalization
        total = r_corrected + g_corrected + b_corrected

        if total == 0:
            return (85, 85, 85)  # Return neutral gray if no color

        # Normalize to 0-255 range while preserving color ratios
        scale = 255 / total
        r = int(r_corrected * scale)
        g = int(g_corrected * scale)
        b = int(b_corrected * scale)

        return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

    def _raw_to_rgb_simple(
        self, r_raw: int, g_raw: int, b_raw: int, clear_raw: int
    ) -> Tuple[int, int, int]:
        """Simple RGB conversion - direct scaling

        Args:
            r_raw: Raw red ADC value
            g_raw: Raw green ADC value
            b_raw: Raw blue ADC value
            clear_raw: Raw clear ADC value (unused in this method)

        Returns:
            Tuple[int, int, int]: RGB values (0-255)
        """

        # Ensure we have integers
        def extract_int(value):
            if isinstance(value, tuple):
                return int(value[0]) if len(value) > 0 else 0
            return int(value)

        r_raw = extract_int(r_raw)
        g_raw = extract_int(g_raw)
        b_raw = extract_int(b_raw)

        # Find the maximum value for scaling
        max_val = max(r_raw, g_raw, b_raw)

        if max_val == 0:
            return (0, 0, 0)

        # Scale to 0-255 range
        scale = 255 / max_val
        r = int(r_raw * scale)
        g = int(g_raw * scale)
        b = int(b_raw * scale)

        return (r, g, b)

    def calibrate_white_balance(self, sensor: Any = None) -> Tuple[int, int, int, int]:
        """Calibrate white balance by reading a white surface

        Args:
            sensor: The sensor to calibrate (None for standalone mode)

        Returns:
            Tuple[int, int, int, int]: White balance calibration values (r, g, b, clear)
        """
        print("Point sensor at a white surface and press Enter...")
        self._safe_input()

        if self.standalone:
            white_values = self.sensor.read()
        else:
            white_values = sensor.read()

        print(
            f"White calibration values: R={white_values[0]}, G={white_values[1]}, B={white_values[2]}, Clear={white_values[3]}"
        )
        return white_values

    def test_and_calibrate_colors(self, sensor: Any = None) -> dict:
        """Test all colors in the color_map and allow adjustment of RGB values

        This method will guide you through testing each color in your color_map
        and allow you to update the RGB values based on actual sensor readings.

        Args:
            sensor: The sensor to use for testing (None for standalone mode)

        Returns:
            dict: Updated color_map with new RGB values
        """
        print("=== Color Calibration Tool ===")
        print("This tool will help you calibrate each color in your color_map.")
        print("For each color, point the sensor at that color and press Enter.")
        print(
            "You can then choose to update the RGB values or keep the current ones.\n"
        )

        updated_color_map = self.color_map.copy()

        for color_name, current_rgb in self.color_map.items():
            print(f"\n--- Testing Color: {color_name.upper()} ---")
            print(f"Current RGB values: {current_rgb}")
            print(f"Point the sensor at a {color_name} surface and press Enter...")

            try:
                self._safe_input()

                # Read current sensor values
                if self.standalone:
                    raw_values = self.sensor.read()
                else:
                    raw_values = sensor.read() if sensor else self.middle_sensor.read()

                converted_rgb = self._raw_to_rgb(
                    raw_values[0], raw_values[1], raw_values[2], raw_values[3]
                )
                distance_to_current = self._color_distance(converted_rgb, current_rgb)

                print(
                    f"Raw sensor reading: R={raw_values[0]}, G={raw_values[1]}, B={raw_values[2]}, Clear={raw_values[3]}"
                )
                print(f"Converted RGB: {converted_rgb}")
                print(f"Distance to current {color_name}: {distance_to_current:.2f}")

                # Ask if user wants to update
                while True:
                    choice = (
                        self._safe_input(
                            f"Update {color_name} RGB values? (y/n/m for manual): "
                        )
                        .lower()
                        .strip()
                    )

                    if choice == "y":
                        updated_color_map[color_name] = converted_rgb
                        print(
                            f"✓ Updated {color_name}: {current_rgb} → {converted_rgb}"
                        )
                        break
                    elif choice == "n":
                        print(f"✓ Kept original {color_name}: {current_rgb}")
                        break
                    elif choice == "m":
                        # Manual RGB input
                        try:
                            print("Enter RGB values manually (format: r,g,b):")
                            manual_input = self._safe_input("RGB: ").strip()
                            if manual_input:
                                r, g, b = map(int, manual_input.split(","))
                                manual_rgb = (
                                    max(0, min(255, r)),
                                    max(0, min(255, g)),
                                    max(0, min(255, b)),
                                )
                                updated_color_map[color_name] = manual_rgb
                                print(
                                    f"✓ Manually set {color_name}: {current_rgb} → {manual_rgb}"
                                )
                                break
                            else:
                                print("No input received, keeping original value")
                                break
                        except ValueError:
                            print("Invalid format. Use: r,g,b (e.g., 255,128,64)")
                    elif choice == "":
                        # No input received, keep original
                        print(f"✓ No input - kept original {color_name}: {current_rgb}")
                        break
                    else:
                        print("Please enter 'y', 'n', or 'm'")

            except KeyboardInterrupt:
                print(f"\nSkipping {color_name}...")
                continue
            except Exception as e:
                print(f"Error reading {color_name}: {e}")
                continue

        print("\n=== Calibration Complete ===")
        print("Updated color map:")
        for color_name, rgb_values in updated_color_map.items():
            old_values = self.color_map[color_name]
            if rgb_values != old_values:
                print(f"  {color_name}: {old_values} → {rgb_values} ✓")
            else:
                print(f"  {color_name}: {rgb_values} (unchanged)")

        # Ask if user wants to apply changes
        while True:
            apply = (
                self._safe_input("\nApply these changes to the color_map? (y/n): ")
                .lower()
                .strip()
            )
            if apply == "y":
                self.color_map = updated_color_map
                self.rgb_to_color = {v: k for k, v in self.color_map.items()}
                print("✓ Color map updated!")
                break
            elif apply == "n" or apply == "":
                print("✓ Changes discarded, original color map kept.")
                break
            else:
                print("Please enter 'y' or 'n'")

        return updated_color_map

    def save_color_map(self, filename: str = "color_calibration.py") -> None:
        """Save the current color_map to a Python file

        Args:
            filename: Name of the file to save to
        """
        try:
            with open(filename, "w") as f:
                f.write("# Auto-generated color calibration file\n")
                f.write("# Generated by Follow.save_color_map()\n\n")
                f.write("color_map = {\n")
                for color_name, rgb_values in self.color_map.items():
                    f.write(f'    "{color_name}": {rgb_values},\n')
                f.write("}\n\n")
                f.write("# To use: sensor.load_color_map('color_calibration.py')\n")
            print(f"✓ Color map saved to {filename}")
        except Exception as e:
            print(f"Error saving color map: {e}")

    def load_color_map(self, filename: str = "color_calibration.py") -> bool:
        """Load color_map from a Python file

        Args:
            filename: Name of the file to load from

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Read the file and extract the color_map
            with open(filename, "r") as f:
                content = f.read()

            # Execute the file content to get the color_map
            namespace = {}
            exec(content, namespace)

            if "color_map" in namespace:
                self.color_map = namespace["color_map"]
                self.rgb_to_color = {v: k for k, v in self.color_map.items()}
                print(f"✓ Color map loaded from {filename}")
                print("Loaded colors:")
                for color_name, rgb_values in self.color_map.items():
                    print(f"  {color_name}: {rgb_values}")
                return True
            else:
                print(f"Error: No 'color_map' found in {filename}")
                return False
        except FileNotFoundError:
            print(f"Error: File {filename} not found")
            return False
        except Exception as e:
            print(f"Error loading color map: {e}")
            return False

    def test_single_color(
        self, color_name: str, sensor: str = None
    ) -> Tuple[Tuple[int, int, int, int], Tuple[int, int, int], float]:
        """Test a single color and compare with current color_map value

        Args:
            color_name: Name of the color to test
            sensor: The sensor to use (None for standalone mode)

        Returns:
            Tuple containing (raw_values, converted_rgb, distance_to_current)
        """
        if color_name.lower() not in self.color_map:
            raise ValueError(
                f"Color '{color_name}' not found in color_map. Available colors: {list(self.color_map.keys())}"
            )

        color_name = color_name.lower()
        current_rgb = self.color_map[color_name]

        print(f"\n--- Testing {color_name.upper()} ---")
        print(f"Current RGB: {current_rgb}")
        print(f"Point sensor at {color_name} surface and press Enter...")
        self._safe_input()

        # Read sensor
        if self.standalone:
            raw_values = self.sensor.read()
        else:
            if sensor == "left":
                raw_values = self.left_sensor.read() 
            if sensor == "middle":
                raw_values = self.middle_sensor.read() 
            if sensor == "right":
                raw_values = self.right_sensor.read() 

        converted_rgb = self._raw_to_rgb(
            raw_values[0], raw_values[1], raw_values[2], raw_values[3]
        )
        distance = self._color_distance(converted_rgb, current_rgb)

        print(
            f"Raw reading: R={raw_values[0]}, G={raw_values[1]}, B={raw_values[2]}, Clear={raw_values[3]}"
        )
        print(f"Converted RGB: {converted_rgb}")
        print(f"Distance to current: {distance:.2f}")
        print(f"Match threshold: {self.color_threshold}")
        print(f"Would match: {'✓ YES' if distance < self.color_threshold else '✗ NO'}")

        return raw_values, converted_rgb, distance

    def print_color_distances(self, test_rgb: Tuple[int, int, int]) -> None:
        """Print distances from test_rgb to all colors in color_map

        Args:
            test_rgb: RGB tuple to compare against all colors
        """
        print(f"\nDistances from RGB {test_rgb} to all colors:")
        print("-" * 50)

        distances = []
        for color_name, color_rgb in self.color_map.items():
            distance = self._color_distance(test_rgb, color_rgb)
            distances.append((distance, color_name, color_rgb))

        # Sort by distance (closest first)
        distances.sort()

        for distance, color_name, color_rgb in distances:
            match_status = (
                "✓ MATCH" if distance < self.color_threshold else "✗ no match"
            )
            print(f"  {color_name:12} {color_rgb}: {distance:6.2f} {match_status}")

        closest_color = distances[0][1]
        print(f"\nClosest color: {closest_color} (distance: {distances[0][0]:.2f})")

    def debug_color_reading(
        self, sensor: str = None
    ) -> Tuple[Tuple[int, int, int, int], Tuple[int, int, int], str]:
        """Debug method to show both raw and converted values

        Args:
            sensor: The sensor to read from (None for standalone mode)

        Returns:
            Tuple containing (raw_values, converted_rgb, color_name)
        """
        if self.standalone:
            raw_values = self.sensor.read()
        else:
            if sensor == "left":
                raw_values = self.left_sensor.read() 
            if sensor == "middle":
                raw_values = self.middle_sensor.read() 
            if sensor == "right":
                raw_values = self.right_sensor.read() 

        converted_rgb = self._raw_to_rgb(
            raw_values[0], raw_values[1], raw_values[2], raw_values[3]
        )
        color_name = self.rgb_to_color_name(converted_rgb)

        print(
            f"Raw ADC values: R={raw_values[0]}, G={raw_values[1]}, B={raw_values[2]}, Clear={raw_values[3]}"
        )
        print(f"Converted RGB: {converted_rgb}")
        print(f"Detected color: {color_name}")
        print(
            f"Distance to target ({self.target_color}): {self._color_distance(converted_rgb, self.target_rgb):.2f}"
        )

        # Show distances to all colors
        self.print_color_distances(converted_rgb)

        return raw_values, converted_rgb, color_name

    def get_raw_values(self, sensor: Any = None) -> Tuple[int, int, int, int]:
        """Get raw ADC values from sensor without conversion

        Args:
            sensor: The sensor to read from (None for standalone mode)

        Returns:
            Tuple[int, int, int, int]: Raw ADC values (r, g, b, clear)
        """
        if self.standalone:
            return self.sensor.read()
        else:
            return sensor.read()

    def test_conversion_algorithms(self) -> None:
        """Test all three RGB conversion algorithms on current reading"""
        print("Testing RGB Conversion Algorithms")
        print("=" * 50)

        try:
            # Read raw values
            if self.standalone:
                raw_values = self.sensor.read()
            else:
                raw_values = self.read_raw()

            print(f"Raw ADC values: {raw_values}")
            r_raw, g_raw, b_raw, clear_raw = raw_values

            # Test each algorithm
            algorithms = [
                ("Default (Ratio + Scale)", "_raw_to_rgb"),
                ("Alternative (Illumination Corrected)", "_raw_to_rgb_alternative"),
                ("Simple (Direct Scaling)", "_raw_to_rgb_simple"),
            ]

            for name, method_name in algorithms:
                print(f"\n{name}:")
                try:
                    if method_name == "_raw_to_rgb":
                        rgb = self._raw_to_rgb(r_raw, g_raw, b_raw, clear_raw)
                    elif method_name == "_raw_to_rgb_alternative":
                        rgb = self._raw_to_rgb_alternative(
                            r_raw, g_raw, b_raw, clear_raw
                        )
                    else:  # simple
                        rgb = self._raw_to_rgb_simple(r_raw, g_raw, b_raw, clear_raw)

                    print(f"  RGB: {rgb}")

                    # Find closest color and distance
                    closest_color = self._get_closest_color_name(rgb)
                    distance = self._color_distance(rgb, self.color_map[closest_color])
                    print(f"  Closest: {closest_color} (distance: {distance:.2f})")

                    if distance <= self.color_threshold:
                        print(f"  ✓ Match within threshold ({self.color_threshold})")
                    else:
                        print("  ✗ No match (exceeds threshold)")

                except Exception as e:
                    print(f"  Error: {e}")

            print("\n" + "=" * 50)

        except Exception as e:
            print(f"Error reading sensor: {e}")

    @property
    def target_color_rgb(self) -> Tuple[int, int, int]:
        """Get the target color for the line.

        Returns:
            Tuple[int, int, int]:
        """
        return self.target_rgb

    @target_color_rgb.setter
    def target_color_rgb(self, target_rgb: Tuple[int, int, int]) -> None:
        """
        Set the target color to follow by RGB values.

        Args:
            target_rgb (Tuple[int, int, int]): RGB values of the color to follow

        Returns:
            None
        """
        self.target_rgb = self._validate_rgb(target_rgb)
        self.target_color = self._get_closest_color_name(self.target_rgb)
        if get_debug():
            debug_print(
                f"Target color set to {self.target_color}: {self.target_rgb}",
                action="color_setup",
                msg="Target Color",
            )
        else:
            if get_debug():
                debug_print(
                    f"Unknown color: {self.target_color}",
                    action="color_setup",
                    msg="Color Error",
                )

    @property
    def target_color(self) -> str:
        """Get the target color for the line as a string from predefined colors

        Returns:
            str: Target color as color name (e.g "Red").
        """
        return self._get_closest_color_name(self.target_rgb)

    color = target_color

    @target_color.setter
    def target_color(self, color: str) -> None:
        """Set the target color using a predefined color name.

        Args:
            color (str): Target color as color name (e.g "Red").

        Raises:
            ValueError: Color name not valid for the Sensor ("lila", "blau", "grün", "gelb", "orange", "terracotta")
        """
        if color.lower() in self.color_map:
            self.target_rgb = self.color_map[color.lower()]
        else:
            raise ValueError(
                f"Invalid color name: '{color}'. Must be one of: {list(self.color_map.keys())}"
            )

    def _color_distance(
        self, color1: Tuple[int, int, int], color2: Tuple[int, int, int]
    ) -> float:
        """Calculate the Euclidean distance between two RGB colors.

        Args:
            color1 (Tuple[int, int, int]): RGB values of the first color
            color2 (Tuple[int, int, int]): RGB values of the second color

        Returns:
            float: Distance between the three colors (High -> colors do not match, lower -> colors are somewhat equal)
        """
        return sum((a - b) ** 2 for a, b in zip(color1, color2)) ** 0.5

    def get_colors(
        self, color_code: str = "all"
    ) -> Optional[Union[float, Tuple[float, float, float]]]:
        """Get average color values from all three sensors.

        Args:
            color_code (str): Color component to return ('red', 'green', 'blue', 'all', or 'rgb')
                              Default is 'all' which returns all components as a tuple

        Returns:
            float: Average value for single color component
            tuple[float, float, float]: (red, green, blue) tuple when color_code is 'all' or 'rgb'
            None: If invalid color_code provided
        """
        try:
            # Read all sensors once and store the results
            left_rgb = self._read_sensor(self.left_sensor)
            middle_rgb = self._read_sensor(self.middle_sensor)
            right_rgb = self._read_sensor(self.right_sensor)

            # Calculate averages for each color component
            red_avg = sum(rgb[0] for rgb in (left_rgb, middle_rgb, right_rgb)) / 3
            green_avg = sum(rgb[1] for rgb in (left_rgb, middle_rgb, right_rgb)) / 3
            blue_avg = sum(rgb[2] for rgb in (left_rgb, middle_rgb, right_rgb)) / 3

            # Debug output if enabled
            if get_debug():
                debug_print(
                    f"Sensor readings - Left: {left_rgb}, Middle: {middle_rgb}, Right: {right_rgb}",
                    action="color_sensing",
                    msg="Raw Values",
                )
                debug_print(
                    f"Averages - Red: {red_avg:.1f}, Green: {green_avg:.1f}, Blue: {blue_avg:.1f}",
                    action="color_sensing",
                    msg="Calculated Averages",
                )

            # Return based on requested color code
            color_code = color_code.lower()
            if color_code == "red":
                return red_avg
            elif color_code == "green":
                return green_avg
            elif color_code == "blue":
                return blue_avg
            elif color_code in ("all", "rgb"):
                return (red_avg, green_avg, blue_avg)
            else:
                raise ValueError(
                    f"Unknown color code: '{color_code}'. Use 'red', 'green', 'blue', 'all', or 'rgb'"
                )

        except IOError as e:
            print(f"IOError reading color sensors: {e}")
            if get_debug():
                debug_print(
                    f"Color sensor IOError: {e}", action="color_sensing", msg="Error"
                )
            return None

    def __get_color_rgb(
        self, current_mode: Optional[str] = None
    ) -> Tuple[int, int, int]:
        """Get the detected color from the middle sensor as RGB.

        Args:
            current_mode (Optional[str], optional): the mode the car is currently in, returns early if mode is not "line track". Defaults to None.

        Returns:
            Tuple[int, int, int]: RGB value of the middle Sensor. If mode is not "line track" return tuple of (0, 0, 0)
        """
        self.current_mode = current_mode
        if current_mode != "line track":
            return (0, 0, 0)
        middle_color = self._read_sensor(self.middle_sensor)
        return middle_color

    def get_color_rgb_convert(self) -> Tuple[str, str, str]:
        """convert RGB value to a number with 2 numbers before the comma. The third number is after the comma.

        Returns:
            Tuple[str, str, str]: RGB color values (R, G, B)
        """
        """
        
        """
        rgb = self.__get_color_rgb()
        # Convert each RGB component to a string with 2 digits before the decimal and 1 after
        r = f"{rgb[0]:02d}"
        g = f"{rgb[1]:02d}"
        b = f"{rgb[2]:02d}"
        return (r, g, b)

    def get_color(self, current_mode: Optional[str] = None) -> Tuple[int, int, int]:
        """Detects the color of the middle sensor and returns it as RGB tuple.

        Args:
            current_mode (Optional[str], optional): the mode the car is currently in, returns early if mode is not "line track". Defaults to None.
                                                    Defaults to None.

        Returns:
        - Tuple[int, int, int]: RGB color values of the middle sensor.
        """
        self.current_mode = current_mode

        # Only proceed if we're in line track mode
        if current_mode != "line track":
            return (0, 0, 0)  # Return black if not in line track mode

        rgb = self._read_sensor(self.middle_sensor)
        if get_debug() and current_mode == "line track":
            debug_print(
                f"Detected color: {rgb}", action="line_track", msg="Color Detection"
            )
        return rgb

    def rgb_to_color_name(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to color name using color_map dictionary."""
        return self._get_closest_color_name(rgb)

    def color_name_to_rgb(self, color_name: str) -> Tuple[int, int, int]:
        """Convert color name to RGB tuple using color_map dictionary."""
        color_name = color_name.lower()
        if color_name in self.color_map:
            return self.color_map[color_name]
        else:
            raise ValueError(
                f"Unknown color: {color_name}. Available colors: {list(self.color_map.keys())}"
            )

    def color_match(
        self,
        color: Tuple[int, int, int],
        target_rgb: Optional[Tuple[int, int, int]] = None,
    ) -> bool:
        """Check if the detected color matches the target color."""
        # Return early if the line track mode is not on.

        if target_rgb is None:
            target_rgb = self.target_rgb

        distance = self._color_distance(color, target_rgb)
        # print(f"Color: {color}, Target: {target_rgb}, Distance: {distance}")
        if distance < self.color_threshold:
            return True
        else:
            return False

    def get_color_str(self) -> Tuple[str, str, str]:
        """
        Returns:
        tuple of str: Color that corresponds to the RGB values.
        (left, middle, right)
        """
        left_result = self.rgb_to_color_name(rgb=self._read_sensor(self.left_sensor))
        middle_result = self.rgb_to_color_name(
            rgb=self._read_sensor(self.middle_sensor)
        )
        right_result = self.rgb_to_color_name(rgb=self._read_sensor(self.right_sensor))

        # Ensure we return strings (cast to str if needed)
        left = str(left_result) if isinstance(left_result, str) else ""
        middle = str(middle_result) if isinstance(middle_result, str) else ""
        right = str(right_result) if isinstance(right_result, str) else ""

        return (left, middle, right)

    def simple_get_line(self):
        l = self.read_raw("left")
        m = self.read_raw("middle")
        r = self.read_raw("right")

        print(l, m, r)

        left = all(lower <= value <= upper for value, lower, upper in zip(l, self.min_lila_map, self.max_lila_map))
        middle = all(lower <= value <= upper for value, lower, upper in zip(m, self.min_lila_map, self.max_lila_map))
        right = all(lower <= value <= upper for value, lower, upper in zip(r, self.min_lila_map, self.max_lila_map))

        return (left, middle, right)

    def get_line_position(self, current_mode: Optional[str] = None) -> Optional[str]:
        """Determine the position of the line based on sensor readings."""
        self.current_mode = current_mode

        # Only proceed if we're in line track mode
        if self.current_mode != "line track":
            print("Not in line track mode, skipping get_line_position.")
            return None

        left = self.simple_get_line()[0]
        middle = self.simple_get_line()[1]
        right = self.simple_get_line()[2]
        print(left, middle, right)

        if left is None and middle is None and right is None:
            return None

        if left:
            return "left"
        elif right:
            return "right"
        elif middle:
            return "forward"
        else: 
            return None

    def color_match_bool(self, match_color: str) -> Tuple[bool, bool, bool]:
        left_color = self.color_match(
            self._read_sensor(self.left_sensor), self.color_name_to_rgb(match_color)
        )
        middle_color = self.color_match(
            self._read_sensor(self.middle_sensor), self.color_name_to_rgb(match_color)
        )
        right_color = self.color_match(
            self._read_sensor(self.right_sensor), self.color_name_to_rgb(match_color)
        )

        return left_color, middle_color, right_color


    def follow_line(self, power: int) -> Optional[str]:
        """Follow the line based on sensor readings.

        This function should be called from main.py to follow a colored line.
        It will use the debug flag to determine whether to actually move the motors
        or just print debug information.

        Args:
            power: Motor power level (0-100)

        Returns:
            The current move_status value ('left', 'right', 'forward', 'stop')
        """

        position = self.get_line_position(self.current_mode)
        # Check if debug mode is enabled and we're in line track mode
        is_debug = get_debug() and self.current_mode == "line track"

        # Check if no line is detected
        if position is None:
            # If the car is out of the line, stop it
            if self.line_out_time == 0:
                self.line_out_time = time.time()
                print("Warning: No target color detected by any sensor!")

            # If no line detected for more than 2 seconds, stop and wait
            if time.time() - self.line_out_time > 2:
                # print_once("Line lost! Stopping car. Please reposition the car on the line.")
                position = "stop"
                # Print debug information
                # if is_debug:
                #     debug_position = "stopped"
                #     power = 0
                #     debug_print(
                #         ("Direction: {debug_position}, Power: {power}"),
                #         action="line_track",
                #         msg="Stopping line following",
                #     )
                print(f"Direction: {position}")
                # Wait for user intervention - the car will stay stopped
                # until the line is found again or the user takes action
            return position
        else:
            # Reset the timer if line is detected
            self.line_out_time = 0
        # Execute movement based on line position
        # if position == "left":
        #     # if is_debug:
        #         # debug_print(
        #         #     ("Direction: {position}, Power: {power}"),
        #         #     action="line_track",
        #         #     msg="Following line",
        #         # )
        #     print(f"Direction: {position}")
        # elif position == "right":
        #     # if is_debug:
        #     #     debug_print(
        #     #         (f"Direction: {position}, Power: {power}"),
        #     #         action="line_track",
        #     #         msg="Following line",
        #     #     )
        #     print(f"Direction: {position}")
        # else:
        #     # if is_debug:
        #     #     debug_print(
        #     #         (f"Direction: {position}, Power: {power}"),
        #     #         action="line_track",
        #     #         msg="Following line",
        #     #     )
        #     print(f"Direction: {position}")
        # Small delay to avoid overwhelming the motors
        sleep(0.1)
        return position


if __name__ == "__main__":

    def safe_input(prompt=""):
        """Simple safe input for main section"""
        try:
            if prompt:
                print(prompt, end="")
            return input()
        except (OSError, KeyboardInterrupt, EOFError) as e:
            print(f"Input error: {e}")
            print("Using default values...")
            return ""
        except Exception as e:
            print(f"Unexpected input error: {e}")
            return ""

    print("=== TCS34725 Color Sensor Testing ===")
    print("Choose a testing mode:")
    print("1. Test raw-to-RGB conversion (no hardware needed)")
    print("2. Debug single color reading (requires hardware)")
    print("3. Test single color calibration (requires hardware)")
    print("4. Full color calibration (requires hardware)")
    print("5. Load saved color calibration")

    try:
        choice = safe_input("Enter choice (1-5): ").strip()
        if not choice:
            choice = "1"  # Default to option 1 if no input

        if choice == "1":
            # Test the conversion without requiring hardware
            print("\n=== Testing Raw-to-RGB Conversion ===")

            class TestFollow:
                def _raw_to_rgb(self, r_raw, g_raw, b_raw, clear_raw):
                    def extract_int(value):
                        if isinstance(value, tuple):
                            return int(value[0]) if len(value) > 0 else 0
                        return int(value)

                    r_raw = extract_int(r_raw)
                    g_raw = extract_int(g_raw)
                    b_raw = extract_int(b_raw)
                    clear_raw = extract_int(clear_raw)

                    if clear_raw == 0:
                        return (0, 0, 0)

                    r_ratio = r_raw / clear_raw
                    g_ratio = g_raw / clear_raw
                    b_ratio = b_raw / clear_raw

                    max_ratio = max(r_ratio, g_ratio, b_ratio)

                    if max_ratio == 0:
                        return (0, 0, 0)

                    r = int((r_ratio / max_ratio) * 255)
                    g = int((g_ratio / max_ratio) * 255)
                    b = int((b_ratio / max_ratio) * 255)

                    return (
                        max(0, min(255, r)),
                        max(0, min(255, g)),
                        max(0, min(255, b)),
                    )

            test_sensor = TestFollow()
            test_cases = [
                (614, 572, 481, 1644, "Purple test 1"),
                (319, 313, 277, 851, "Purple test 2"),
                (800, 400, 200, 1500, "Reddish test"),
                (200, 800, 300, 1400, "Greenish test"),
                (300, 400, 900, 1600, "Blueish test"),
            ]

            for r, g, b, c, description in test_cases:
                result = test_sensor._raw_to_rgb(r, g, b, c)
                print(f"{description} ({r}, {g}, {b}, {c}) -> RGB: {result}")

        elif choice in ["2", "3", "4", "5"]:
            # Create sensor instance for hardware testing
            try:
                print("\nInitializing sensor...")
                sensor = Follow(target_color="orange", standalone=True)

                if choice == "2":
                    print("\n=== Debug Color Reading ===")
                    raw_vals, rgb_vals, color_name = sensor.debug_color_reading()

                elif choice == "3":
                    print("\n=== Single Color Test ===")
                    available_colors = list(sensor.color_map.keys())
                    print(f"Available colors: {', '.join(available_colors)}")
                    color_to_test = (
                        safe_input("Enter color name to test: ").strip().lower()
                    )
                    if color_to_test and color_to_test in available_colors:
                        sensor.test_single_color(color_to_test)
                    elif color_to_test:
                        print(f"Color '{color_to_test}' not found!")
                    else:
                        print("No color specified, testing 'terracotta'")
                        sensor.test_single_color("terracotta")

                elif choice == "4":
                    print("\n=== Full Color Calibration ===")
                    updated_map = sensor.test_and_calibrate_colors()

                    # Ask if user wants to save
                    save_choice = (
                        safe_input("Save calibration to file? (y/n): ").lower().strip()
                    )
                    if save_choice == "y" or save_choice == "":
                        filename = safe_input(
                            "Filename (default: color_calibration.py): "
                        ).strip()
                        if not filename:
                            filename = "color_calibration.py"
                        sensor.save_color_map(filename)

                elif choice == "5":
                    print("\n=== Load Color Calibration ===")
                    filename = safe_input(
                        "Filename (default: color_calibration.py): "
                    ).strip()
                    if not filename:
                        filename = "color_calibration.py"
                    sensor.load_color_map(filename)

            except Exception as e:
                print(f"Hardware error: {e}")
                print("Make sure the sensor is properly connected.")

        else:
            print("Invalid choice!")

    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
