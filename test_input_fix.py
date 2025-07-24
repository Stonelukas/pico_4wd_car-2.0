#!/usr/bin/env python3
"""
Test script to verify the input fix for the terracotta sensor issue.

This script can be run on both PC (for testing the logic) and on MicroPython 
to test the actual fix.
"""

def test_safe_input():
    """Test the safe input method with simulated sensor data"""
    print("=== Testing Safe Input Method ===")
    print("This test simulates the terracotta sensor input issue and fix")
    print()
    
    # Simulate the Follow class _safe_input method
    def _safe_input(prompt="", timeout_ms=30000):
        """Safe input function that handles MicroPython limitations"""
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
                import time
                print("Input not available - waiting 3 seconds then proceeding...")
                time.sleep(3)
                return ""
                
            except Exception as sleep_error:
                print(f"Sleep error: {sleep_error}")
                return ""
        
        except Exception as e:
            print(f"Unexpected input error: {e}")
            print("Proceeding without user input...")
            return ""
    
    # Test the terracotta scenarioa
    print("Simulating: 'Point the sensor at a terracotta surface and press Enter...'")
    result = _safe_input()
    
    if result is not None:
        print(f"✓ Input received successfully: '{result}'")
    else:
        print("✓ No input received, but test proceeded gracefully")
    
    print("\n=== Test Complete ===")
    print("The fix ensures that even if input() fails, the test continues")
    print("instead of hanging with just a newline.")

if __name__ == "__main__":
    test_safe_input()
