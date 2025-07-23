# RGB Conversion Algorithm Fix - Instructions

## Problem Fixed

Your TCS34725 color sensor was returning raw ADC values like `(614, 572, 481, 1644)` but the RGB conversion algorithm was always producing white/bright values like `(255, 255, 255)` or close to it.

## Root Cause

The original `_raw_to_rgb()` method was normalizing colors by dividing by the maximum ratio, which pushed all results toward white:

```python
# PROBLEMATIC CODE:
max_ratio = max(r_ratio, g_ratio, b_ratio)
r = int((r_ratio / max_ratio) * 255)  # Always pushes toward 255
```

## Solution

I've added **three different RGB conversion algorithms** to your `follow.py`:

### 1. `_raw_to_rgb()` - Fixed Default Algorithm
- Uses a configurable scale factor instead of max normalization
- Scale factor = 400 (adjustable for your lighting conditions)
- Preserves actual color characteristics

### 2. `_raw_to_rgb_alternative()` - Illumination Corrected
- Removes white light component for purer colors
- Better for colored surfaces under bright lighting
- More complex but handles varied lighting better

### 3. `_raw_to_rgb_simple()` - Direct Scaling  
- Simple max-value scaling
- Good for high-contrast scenarios
- Fastest computation

## How to Test

1. **Upload the updated files** to your Pico
2. **Use the new test method**:
   ```python
   follow = Follow(target_rgb=(255, 0, 0), standalone=True)
   follow.test_conversion_algorithms()
   ```

3. **Test each algorithm individually**:
   ```python
   # Read raw values
   raw = follow.read_raw()
   r_raw, g_raw, b_raw, clear_raw = raw
   
   # Test different algorithms
   rgb_default = follow._raw_to_rgb(r_raw, g_raw, b_raw, clear_raw)
   rgb_alt = follow._raw_to_rgb_alternative(r_raw, g_raw, b_raw, clear_raw)  
   rgb_simple = follow._raw_to_rgb_simple(r_raw, g_raw, b_raw, clear_raw)
   
   print(f"Default: {rgb_default}")
   print(f"Alternative: {rgb_alt}")
   print(f"Simple: {rgb_simple}")
   ```

## Tuning

If colors still seem too bright/dim, adjust the scale factor in `_raw_to_rgb()`:

```python
scale_factor = 400  # Try values between 200-800
```

- **Lower values (200-300)**: Dimmer, more conservative colors
- **Higher values (600-800)**: Brighter, more saturated colors

## Expected Results

With your raw reading `(614, 572, 481, 1644)`:

- **Before**: RGB ≈ `(255, 255, 255)` (always white)
- **After**: RGB ≈ `(149, 138, 116)` (brownish/beige - realistic!)

## Integration

The calibration system now supports all three algorithms:

```python
# Test with specific algorithm
follow.test_and_calibrate_colors(algorithm="default")
follow.test_and_calibrate_colors(algorithm="alternative") 
follow.test_and_calibrate_colors(algorithm="simple")
```

Choose the algorithm that gives the best color detection for your specific setup and lighting conditions.
