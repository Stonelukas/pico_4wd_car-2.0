from classes.follow import Follow

print("=== Testing Color Input Functionality ===")
print("Testing both string color names and RGB tuple inputs")
print()

# Test 1: Color name string input
print("1. Testing color name string input...")
try:
    follow_string = Follow(target_color="orange", standalone=True)
    print("✓ Successfully created Follow with color name 'orange'")
    print(f"  Target RGB: {follow_string.target_rgb}")
    print(f"  Target color: {follow_string.target_color}")
except Exception as e:
    print(f"✗ Error with color name: {e}")

print()

# Test 2: RGB tuple input  
print("2. Testing RGB tuple input...")
try:
    follow_rgb = Follow(target_color=(164, 127, 107), standalone=True)
    print("✓ Successfully created Follow with RGB tuple (164, 127, 107)")
    print(f"  Target RGB: {follow_rgb.target_rgb}")
    print(f"  Target color: {follow_rgb.target_color}")
except Exception as e:
    print(f"✗ Error with RGB tuple: {e}")

print()

# Test 3: Test different color names
print("3. Testing different available color names...")
available_colors = ["terracotta", "green", "yellow", "lila", "blue"]

for color_name in available_colors:
    try:
        follow_test = Follow(target_color=color_name, standalone=True)
        print(f"✓ Color '{color_name}' -> RGB{follow_test.target_rgb}")
    except Exception as e:
        print(f"✗ Error with color '{color_name}': {e}")

print()

# Test 4: Test the conversion algorithms (this doesn't require user input)
print("4. Testing conversion algorithms...")
follow = Follow(target_color="orange", standalone=True)
follow.test_conversion_algorithms()

print("\n" + "="*50)
print("5. Testing single color detection...")
print("   This will prompt for user input but won't hang if input fails.")

# Test terracotta color specifically (this was the problematic one)
try:
    raw_vals, rgb_vals, distance = follow.test_single_color("terracotta")
    print("✓ Terracotta test completed successfully!")
    print(f"   Raw values: {raw_vals}")
    print(f"   RGB values: {rgb_vals}")
    print(f"   Distance: {distance:.2f}")
except Exception as e:
    print(f"Error in terracotta test: {e}")

print("\n" + "="*50)
print("✓ All tests completed!")
print("\nNow you can use either:")
print("  Follow(target_color='orange')        # Color name")
print("  Follow(target_color=(164, 127, 107)) # RGB tuple")
