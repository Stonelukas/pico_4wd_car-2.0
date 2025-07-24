from classes.follow import Follow
from helper import set_debug
from time import sleep

follow = Follow("green", True)
set_debug(True)

while True:
    print(follow.simple_get_line())
    sleep(2)
    


# print("\t Testing left sensor")
# print("---------------------")
# left = follow.debug_color_reading("left")
# print("left finished")
# print("other sensor readings")
# print("middle")
# middle = follow.debug_color_reading("middle")
# print("right")
# right = follow.debug_color_reading("right")
# follow._safe_input()
# print("\t Testing middle sensor")
# print("---------------------")
# middle = follow.debug_color_reading("middle")
# print("middle finished")
# print("other sensor readings")
# print("middle")
# middle = follow.debug_color_reading("middle")
# print("right")
# right = follow.debug_color_reading("right")
# follow._safe_input()
# print("\t Testing right sensor")
# print("---------------------")
# right = follow.debug_color_reading("right")
# print("right finished")
# print("other sensor readings")
# print("middle")
# middle = follow.debug_color_reading("middle")
# print("right")
# right = follow.debug_color_reading("right")
