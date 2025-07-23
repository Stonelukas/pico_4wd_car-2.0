from machine import Pin, SoftI2C
from classes.follow import Follow



follow = Follow(target_rgb=(255, 0, 0), standalone=True)
follow.test_conversion_algorithms()  # Compare all algorithms
