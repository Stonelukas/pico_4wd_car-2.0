#!/usr/bin/env python3
"""
Example usage of the Follow class with string color names and RGB tuples.

This script demonstrates how to initialize the Follow class with different
target color formats.
"""

# Mock classes for testing on PC (without MicroPython hardware)
class MockPin:
    def __init__(self, pin_num):
        self.pin_num = pin_num

class MockSoftI2C:
    def __init__(self, scl, sda):
        self.scl = scl
        self.sda = sda

class MockTCS34725:
    def __init__(self, i2c):
        self.i2c = i2c
        self.gain = None
        self.integ = None
    
    def read(self):
        # Return mock sensor data
        return (150, 120, 100, 400)

# Mock the hardware modules for PC testing
import sys
class MockMachine:
    Pin = MockPin
    SoftI2C = MockSoftI2C

sys.modules['machine'] = MockMachine()
sys.modules['classes.new_tcs'] = type(sys)('mock_tcs')
sys.modules['classes.new_tcs'].TCS34725 = MockTCS34725
sys.modules['classes.new_tcs'].TCSGAIN_LOW = 1
sys.modules['classes.new_tcs'].TCSINTEG_MEDIUM = 2
sys.modules['helper'] = type(sys)('mock_helper')
sys.modules['helper'].debug_print = lambda *args, **kwargs: None
sys.modules['helper'].get_debug = lambda: False
sys.modules['time'] = type(sys)('mock_time')
sys.modules['time'].sleep = lambda x: None
sys.modules['time'].time = lambda: 0
sys.modules['time'].ticks_ms = lambda: 0
sys.modules['time'].ticks_diff = lambda a, b: 0
sys.modules['time'].sleep_ms = lambda x: None

# Now import and test the Follow class
from libs.classes.follow import Follow

def test_color_name_initialization():
    """Test initializing Follow with color name strings"""
    print("=== Testing Color Name Initialization ===")
    
    # Test with different color names
    color_names = ["orange", "blue", "terracotta", "green", "yellow", "lila"]
    
    for color_name in color_names:
        try:
            print(f"\nTesting color: {color_name}")
            follow = Follow(target_color=color_name, standalone=True)
            print(f"✓ Successfully initialized with color '{color_name}'")
            print(f"  Target RGB: {follow.target_rgb}")
            print(f"  Target color name: {follow.target_color}")
        except Exception as e:
            print(f"✗ Error with color '{color_name}': {e}")

def test_rgb_tuple_initialization():
    """Test initializing Follow with RGB tuples"""
    print("\n=== Testing RGB Tuple Initialization ===")
    
    # Test with different RGB tuples
    rgb_tuples = [
        (255, 0, 0),      # Red
        (0, 255, 0),      # Green
        (0, 0, 255),      # Blue
        (255, 165, 0),    # Orange
        (164, 127, 107),  # Custom color
    ]
    
    for rgb_tuple in rgb_tuples:
        try:
            print(f"\nTesting RGB: {rgb_tuple}")
            follow = Follow(target_color=rgb_tuple, standalone=True)
            print(f"✓ Successfully initialized with RGB {rgb_tuple}")
            print(f"  Target RGB: {follow.target_rgb}")
            print(f"  Closest color name: {follow.target_color}")
        except Exception as e:
            print(f"✗ Error with RGB {rgb_tuple}: {e}")

def test_invalid_inputs():
    """Test error handling with invalid inputs"""
    print("\n=== Testing Invalid Input Handling ===")
    
    invalid_inputs = [
        "nonexistent_color",  # Invalid color name
        (256, 300, -10),      # RGB values out of range
        (255, 128),           # Incomplete RGB tuple
        123,                  # Invalid type
    ]
    
    for invalid_input in invalid_inputs:
        try:
            print(f"\nTesting invalid input: {invalid_input}")
            follow = Follow(target_color=invalid_input, standalone=True)
            print(f"✗ Unexpectedly succeeded with: {invalid_input}")
        except Exception as e:
            print(f"✓ Correctly rejected invalid input '{invalid_input}': {e}")

def show_available_colors():
    """Display all available color names"""
    print("\n=== Available Color Names ===")
    
    # Create a Follow instance to access the color_map
    follow = Follow(target_color="orange", standalone=True)
    
    print("You can use any of these color names:")
    for color_name, rgb_values in follow.color_map.items():
        print(f"  '{color_name}' -> RGB{rgb_values}")
    
    print(f"\nTotal available colors: {len(follow.color_map)}")

if __name__ == "__main__":
    print("Follow Class Color Input Testing")
    print("=" * 50)
    
    try:
        show_available_colors()
        test_color_name_initialization() 
        test_rgb_tuple_initialization()
        test_invalid_inputs()
        
        print("\n" + "=" * 50)
        print("✓ All tests completed!")
        print("\nUsage examples:")
        print("  follow = Follow(target_color='orange')         # Use color name")
        print("  follow = Follow(target_color=(255, 128, 0))    # Use RGB tuple")
        print("  follow = Follow('blue', standalone=True)       # Positional argument")
        
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()
