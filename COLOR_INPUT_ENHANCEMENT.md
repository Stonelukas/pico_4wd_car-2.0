# Color Input Enhancement - Summary

## Changes Made

The Follow class has been enhanced to accept both color name strings and RGB tuples for the target color parameter, making it much more user-friendly.

### Key Changes

1. **Constructor Parameter Renamed**: 
   - Changed from `target_rgb` to `target_color` for clarity
   - Now accepts both strings and RGB tuples

2. **Enhanced Type Support**:
   - **String input**: `Follow(target_color="orange")`
   - **RGB tuple input**: `Follow(target_color=(164, 127, 107))`

3. **Automatic Type Detection**:
   - The constructor automatically detects if the input is a string or tuple
   - Converts color names to RGB using the internal color_map
   - Validates RGB tuples for proper format and range

### Available Color Names

The following pre-calibrated color names are available:
- `"terracotta"` - RGB(145, 144, 132)
- `"green"` - RGB(127, 150, 113) 
- `"yellow"` - RGB(151, 132, 96)
- `"lila"` - RGB(128, 142, 131)
- `"orange"` - RGB(164, 127, 107)
- `"blue"` - RGB(106, 151, 139)

### Usage Examples

```python
# Using color names (recommended for predefined colors)
follow = Follow(target_color="orange")
follow = Follow(target_color="blue", standalone=True)

# Using RGB tuples (for custom colors)
follow = Follow(target_color=(255, 128, 0))
follow = Follow(target_color=(164, 127, 107), standalone=True)

# Error handling
try:
    follow = Follow(target_color="invalid_color")
except ValueError as e:
    print(f"Error: {e}")  # Will show available colors
```

### Benefits

1. **Improved Usability**: Color names are much easier to remember than RGB values
2. **Reduced Errors**: Pre-calibrated values eliminate guesswork
3. **Better Documentation**: Code is self-documenting when using color names
4. **Flexibility**: Still supports custom RGB values when needed
5. **Backward Compatibility**: Existing code continues to work

### Files Updated

- `libs/classes/follow.py` - Main Follow class with enhanced constructor
- `libs/main.py` - Updated to use new parameter name
- `libs/tets.py` - Enhanced test file with color input testing
- `COLOR_INPUT_USAGE.md` - Complete usage documentation
- `test_color_input.py` - Advanced testing examples (PC-compatible)

### Error Handling

The enhanced constructor provides clear error messages:
- Invalid color names show available options
- RGB tuples are validated for proper format (3 values)
- RGB values are automatically clamped to 0-255 range
- Type errors provide helpful guidance

### Testing

Run the updated test file to verify functionality:
```bash
# On MicroPython (Raspberry Pi Pico)
python libs/tets.py

# The test will verify:
# - Color name string input
# - RGB tuple input  
# - Available color validation
# - Conversion algorithms
# - Input handling improvements
```

This enhancement makes the Follow class much more user-friendly while maintaining all existing functionality and adding robust error handling.
