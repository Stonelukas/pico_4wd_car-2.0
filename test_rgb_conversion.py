#!/usr/bin/env python3
"""
Test script to demonstrate different RGB conversion algorithms for TCS34725 color sensor.

This script shows the difference between the original algorithm (which always produces white/bright values)
and the improved algorithms that provide more realistic color detection.

Raw sensor values from your test: (614, 572, 481, 1644)
"""

import sys
sys.path.append('libs')

from libs.classes.follow import Follow


def test_rgb_algorithms_with_sample_data():
    """Test RGB conversion algorithms with the problematic sample data"""
    print("RGB Conversion Algorithm Test")
    print("=" * 60)
    
    # Use your actual sensor readings that were causing issues
    test_data = [
        ("Your Sample Reading", 614, 572, 481, 1644),
        ("High Clear Light", 800, 750, 600, 2000),
        ("Red Surface", 500, 200, 150, 800),
        ("Blue Surface", 200, 300, 600, 900),
        ("Green Surface", 300, 600, 200, 900),
    ]
    
    # Create Follow instance in standalone mode
    follow = Follow(target_rgb=(255, 0, 0), standalone=True)
    
    for test_name, r_raw, g_raw, b_raw, clear_raw in test_data:
        print(f"\nTest Case: {test_name}")
        print(f"Raw Values: R={r_raw}, G={g_raw}, B={b_raw}, Clear={clear_raw}")
        print("-" * 40)
        
        # Test each algorithm
        algorithms = [
            ("Default (Fixed)", follow._raw_to_rgb),
            ("Alternative (Illumination)", follow._raw_to_rgb_alternative),
            ("Simple (Direct)", follow._raw_to_rgb_simple)
        ]
        
        for name, method in algorithms:
            try:
                rgb = method(r_raw, g_raw, b_raw, clear_raw)
                closest_color = follow._get_closest_color_name(rgb)
                distance = follow._color_distance(rgb, follow.color_map[closest_color])
                
                print(f"{name:25} | RGB: {rgb} | Color: {closest_color:10} | Dist: {distance:5.1f}")
                
            except Exception as e:
                print(f"{name:25} | ERROR: {e}")
        
        print()


def analyze_problematic_reading():
    """Analyze the specific reading that was causing white/bright results"""
    print("\nDetailed Analysis of Problematic Reading")
    print("=" * 60)
    
    r_raw, g_raw, b_raw, clear_raw = 614, 572, 481, 1644
    
    print(f"Raw ADC Values: R={r_raw}, G={g_raw}, B={b_raw}, Clear={clear_raw}")
    print()
    
    # Show the math step by step for each algorithm
    print("Original Algorithm (the problematic one):")
    if clear_raw > 0:
        r_ratio = r_raw / clear_raw
        g_ratio = g_raw / clear_raw
        b_ratio = b_raw / clear_raw
        max_ratio = max(r_ratio, g_ratio, b_ratio)
        
        print(f"  Ratios: R={r_ratio:.3f}, G={g_ratio:.3f}, B={b_ratio:.3f}")
        print(f"  Max ratio: {max_ratio:.3f}")
        
        if max_ratio > 0:
            r = int((r_ratio / max_ratio) * 255)
            g = int((g_ratio / max_ratio) * 255)
            b = int((b_ratio / max_ratio) * 255)
            print(f"  Normalized RGB: ({r}, {g}, {b}) <- Always pushes to white!")
    
    print("\nFixed Algorithm (using scale factor):")
    if clear_raw > 0:
        r_ratio = r_raw / clear_raw
        g_ratio = g_raw / clear_raw
        b_ratio = b_raw / clear_raw
        scale_factor = 400  # Tunable parameter
        
        print(f"  Ratios: R={r_ratio:.3f}, G={g_ratio:.3f}, B={b_ratio:.3f}")
        print(f"  Scale factor: {scale_factor}")
        
        r = min(255, int(r_ratio * scale_factor))
        g = min(255, int(g_ratio * scale_factor))
        b = min(255, int(b_ratio * scale_factor))
        print(f"  Scaled RGB: ({r}, {g}, {b}) <- More realistic colors!")
    
    print("\nWhy the original algorithm failed:")
    print("- It normalized all colors to the maximum intensity")
    print("- This pushed every reading toward (255, 255, 255) - white")
    print("- The fixed algorithm uses a configurable scale factor instead")
    print("- This preserves the actual color characteristics")


if __name__ == "__main__":
    try:
        test_rgb_algorithms_with_sample_data()
        analyze_problematic_reading()
        
        print("\nNext Steps:")
        print("1. Upload this file to your Pico and run it")
        print("2. Use follow.test_conversion_algorithms() on real sensor readings")
        print("3. Adjust the scale_factor (currently 400) if needed")
        print("4. Test with different colored surfaces")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
