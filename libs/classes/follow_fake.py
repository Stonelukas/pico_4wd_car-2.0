from typing import Tuple, Any, Optional
from machine import Pin
from classes.grayscale import Grayscale


class Follow():
    def __init__(self, target_color: str):
        self._target_color = target_color
        self._left = "lila"
        self._middle = "lila"
        self._right = "lila"


    @property
    def left(self):
        return self._left
            
    
    @property
    def middle(self):
        return self._middle

    def right(self):
        return self._right

    def get_left(self, gs_data):
        if gs_data == [1, 0, 0] or gs_data == [1, 1, 0] or gs_data == [1, 1, 1] or gs_data == [1, 0, 1]:
            self._left = "orange"
            return self._left
        else: 
            self._left = "black"
            return self._left
        
    def get_middle(self, gs_data):
        if gs_data == [0, 1, 0] or gs_data == [1, 1, 0] or gs_data == [1, 1, 1] or gs_data == [0, 1, 1]:
            self._middle = "orange"
            return self._middle
        else: 
            self._middle = "black"
            return self._middle

    def get_right(self, gs_data):
        if gs_data == [0, 0, 1] or gs_data == [0, 1, 1] or gs_data == [1, 1, 1] or gs_data == [0, 1, 1]:
            self._right = "orange"
            return self._right
        else: 
            self._right = "black"
            return self._right
        
    def hub(self):
        self._left = "green"
        self._middle = "green"
        self._right = "green"

    def get_color_str(self) -> Tuple[str, str, str]:
        left = self._left
        middle = self._middle
        right = self._right

        return (left, middle, right)

    @property
    def target_color(self):
        return self._target_color

    @target_color.setter
    def target_color(self, color: str):
        self._target_color = color
