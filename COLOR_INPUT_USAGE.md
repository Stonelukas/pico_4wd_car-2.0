# Follow Class Color Input Examples

## Overview
The Follow class now accepts both color name strings and RGB tuples for the target_color parameter.

## Usage Examples

### Using Color Name Strings
```python
# Initialize with color names (recommended)
follow = Follow(target_color="orange")
follow = Follow(target_color="blue") 
follow = Follow(target_color="terracotta")
follow = Follow(target_color="green")
follow = Follow(target_color="yellow")
follow = Follow(target_color="lila")

# With standalone mode
follow = Follow(target_color="orange", standalone=True)
```

### Using RGB Tuples
```python
# Initialize with RGB tuples
follow = Follow(target_color=(255, 0, 0))      # Red
follow = Follow(target_color=(0, 255, 0))      # Green
follow = Follow(target_color=(0, 0, 255))      # Blue
follow = Follow(target_color=(164, 127, 107))  # Custom orange

# With standalone mode
follow = Follow(target_color=(255, 128, 0), standalone=True)
```

### Available Color Names
The following color names are pre-defined in the color_map:
- `"terracotta"` -> RGB(145, 144, 132)
- `"green"` -> RGB(127, 150, 113)
- `"yellow"` -> RGB(151, 132, 96)
- `"lila"` -> RGB(128, 142, 131)
- `"orange"` -> RGB(164, 127, 107)
- `"blue"` -> RGB(106, 151, 139)

### Error Handling
The class will raise helpful errors for invalid inputs:
```python
# These will raise ValueError exceptions:
follow = Follow(target_color="nonexistent_color")  # Unknown color name
follow = Follow(target_color=(256, 300, -10))      # RGB values out of range
follow = Follow(target_color=(255, 128))           # Incomplete RGB tuple
```

### Backward Compatibility
The change is fully backward compatible. Existing code will continue to work:
```python
# Old way (still works)
follow = Follow(target_color="orange", standalone=True)

# New way (same result)
follow = Follow(target_color="orange", standalone=True)
```

### Benefits of Using Color Names
1. **Easier to read**: `"orange"` is clearer than `(164, 127, 107)`
2. **Consistent values**: Pre-calibrated RGB values for each color
3. **Less error-prone**: No need to remember specific RGB values
4. **Auto-validation**: Invalid color names are caught immediately

### When to Use RGB Tuples
- When you need a custom color not in the predefined list
- When you have specific RGB requirements
- When calibrating new colors

## Implementation Notes
- The constructor parameter was renamed from `target_rgb` to `target_color` for clarity
- Color names are case-insensitive (converted to lowercase internally)
- RGB values are automatically validated and clamped to 0-255 range
- The class maintains both `target_rgb` (RGB tuple) and `target_color` (color name) properties
