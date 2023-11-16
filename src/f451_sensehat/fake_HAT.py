"""Mock version of SenseHat library.

This mock version of the SenseHat library can be used during 
testing, etc. It mimicks the SenseHat sensors by generating
random values within the limits of the actual hardware.
"""

import random


# =========================================================
#              M I S C .   C O N S T A N T S
# =========================================================
ACTION_PRESSED = False
ACTION_HELD = False
ACTION_RELEASED = False

TEMP_MIN = 0.0          # Min/max sense degrees in C
TEMP_MAX = 65.0
PRESS_MIN = 260.0       # Min/max sense pressure in hPa
PRESS_MAX = 1260.0
HUMID_MIN = 0.0         # Min/max sense humidity in %
HUMID_MAX = 100.0

LED_WIDTH = 8
LED_HEIGHT = 8


# =========================================================
#                H E L P E R   C L A S S E S
# =========================================================
class Stick:
    def __init__(self):
        self.direction_up = None
        self.direction_down = None
        self.direction_left = None
        self.direction_right = None
        self.direction_middle = None


class FakeSenseHat:
    def __init__(self):
        self.low_light = True
        self.rotation = 0
        self.stick = Stick()
        self.fake = True

    def clear(self):
        pass

    def set_pixel(self, *args):
        pass

    def set_pixels(self, *args):
        pass

    def set_rotation(self, *args):
        pass

    def set_imu_config(self, *args):
        pass

    def get_temperature(self):
        return random.randint(TEMP_MIN * 10, TEMP_MAX * 10) / 10
    
    def get_pressure(self):
        return random.randint(PRESS_MIN * 10, PRESS_MAX * 10) / 10
    
    def get_humidity(self):
        return random.randint(HUMID_MIN * 10, HUMID_MAX * 10) / 10
