"""f451 Labs Sense HAT Device Class.

The Sense HAT Device class includes support for sensosr and 
LED display included on the Raspberry Pi Sense HAT.

The class wraps -- and extends as needed -- the methods 
and functions supported by underlying libraries, and also
keeps track of core counters, flags, etc.

TODO:
 - more/better tests

Dependencies:
 - fonts: https://pypi.org/project/fonts/
 - font-roboto: https://pypi.org/project/font-roboto/
 - Pillow: https://pypi.org/project/Pillow/
 - Raspberry Pi Sense HAT library: https://github.com/pimoroni/enviroplus-python/  
"""

import colorsys

from random import randint
from subprocess import PIPE, Popen

from . import sensehat_data as f451SenseData

try:
    from sense_hat import SenseHat as RPISenseHat, ACTION_PRESSED, ACTION_HELD, ACTION_RELEASED
except ImportError:
    from .fake_HAT import FakeSenseHat as RPISenseHat, ACTION_PRESSED, ACTION_HELD, ACTION_RELEASED  # noqa: F401

__all__ = [
    'SenseHat',
    'SenseHatError',
    'prep_data',
    'BTN_RELEASE',
    'DISPL_SPARKLE',
    'KWD_ROTATION',
    'KWD_DISPLAY',
    'KWD_PROGRESS',
    'KWD_SLEEP',
    'KWD_BTN_UP',
    'KWD_BTN_DWN',
    'KWD_BTN_LFT',
    'KWD_BTN_RHT',
    'KWD_BTN_MDL',
]


# fmt: off
# =========================================================
#              M I S C .   C O N S T A N T S
# =========================================================
DEF_ROTATION = 0                # Default display rotation
DEF_DISPL_MODE = 0              # Default display mode
DEF_SLEEP = 600                 # Default time to sleep (in seconds)
DEF_LED_OFFSET_X = 0            # Default horizontal offset for LED
DEF_LED_OFFSET_Y = 0            # Default vertical offseet for LED

STATUS_ON = True
STATUS_OFF = False

DISPL_TOP_X = 0                 # X/Y ccordinate of top-left corner for LED content
DISPL_TOP_Y = 0
DISPL_MAX_COL = 8               # sense has an 8x8 LED display
DISPL_MAX_ROW = 8

DISPL_SPARKLE = 'sparkles'      # Name of 'sparkles' view :-)
MAX_SPARKLE_PCNT = 0.2          # 20% sparkles

PROX_DEBOUNCE = 0.5             # Delay to debounce proximity sensor on 'tap'
PROX_LIMIT = 1500               # Threshold for proximity sensor to detect 'tap'

RGB_BLACK = (0, 0, 0)
RGB_WHITE = (255, 255, 255)

RGB_BLUE = (0, 0, 255)
RGB_CYAN = (0, 255, 255)
RGB_GREEN = (0, 255, 0)
RGB_YELLOW = (255, 255, 0)
RGB_RED = (255, 0, 0)

RGB_CHROME = (219, 226, 233)    # Chrome (lt grey)
RGB_GREY = (67, 70, 75)         # Dark Steel Grey
RGB_GREY2 = (57, 61, 71)        # Anthracite
RGB_PURPLE = (127, 0, 255)
RGB_GREY_BLUE = (33, 46, 82)

# RGB colors and palette for values on combo/text screen
COLOR_PALETTE = [
    RGB_BLUE,                   # Dangerously Low
    RGB_CYAN,                   # Low
    RGB_GREEN,                  # Normal
    RGB_YELLOW,                 # High
    RGB_RED,                    # Dangerously High
]

COLOR_BG = RGB_BLACK            # Default background
COLOR_TXT = RGB_CHROME          # Default text on background
COLOR_PBAR_FG = RGB_CYAN        # Default prog bar color
COLOR_PBAR_BG = RGB_GREY_BLUE   # Default prog bar background

ROTATE_90 = 90                  # Rotate 90 degrees
STEP_1 = 1                      # Display mode step

BTN_RELEASE = ACTION_RELEASED


# =========================================================
#    K E Y W O R D S   F O R   C O N F I G   F I L E S
# =========================================================
KWD_ROTATION = 'ROTATION'
KWD_DISPLAY = 'DISPLAY'
KWD_PROGRESS = 'PROGRESS'
KWD_SLEEP = 'SLEEP'
# KWD_DISPLAY_MIN = 'DISPLAYMIN'
# KWD_DISPLAY_MAX = 'DISPLAYMAX'

KWD_BTN_UP = 'BTNUP'
KWD_BTN_DWN = 'BTNDWN'
KWD_BTN_LFT = 'BTNLFT'
KWD_BTN_RHT = 'BTNRHT'
KWD_BTN_MDL = 'BTNMDL'
# fmt: on


# =========================================================
#                        H E L P E R S
# =========================================================
class SenseHatError(Exception):
    """Custom exception class"""

    def __init__(self, errMsg='Unknown Sense HAT error'):
        super().__init__(errMsg)


def prep_data(inData, lenSlice=0):
    """Prep data for Sense HAT

    This function will filter data to ensure we don't have incorrect
    outliers (e.g. from faulty sensors, etc.). The final data set will
    have only valid values. Any invalid values will be replaced with
    0's so that we can display the set on the Sense HAT LED.

    This will technically affect the min/max values for the set. However,
    we're displaying this data on an 8x8 LED. So visual 'accuracy' is
    already less than ideal ;-)

    NOTE: the data structure is more complex than we need for Sense HAT
    devices. But we want to maintain a basic level of compatibility with
    other f451 Labs modules.

    Args:
        inData: 'DataUnit' named tuple with 'raw' data from sensors
        lenSlice: (optional) length of data slice

    Returns:
        'DataUnit' named tuple with the following fields:
            data   = [list of values],
            valid  = <tuple with min/max>,
            unit   = <unit string>,
            label  = <label string>,
            limits = [list of limits]
    """

    def _is_valid(val, valid, allowNone=True):
        """Verify value 'valid'

        This method allows us to verify that a given
        value falls within the 'valid' ranges are for
        a given data set. Any value outside the range
        is considered an error and is replaced by a
        default value.

        NOTE: This local function is similar to the 'is_valid()'
              function in f451 Labs Common library. We have a copy
              here so that the f451 Labs SenseHat library does not
              have another dependency

        Args:
            val: value to check
            valid: 'tuple' with min/max values for valid range
            allowNone: if 'True', then skip compare if 'valid' is 'None

        Returns:
            'True' if value is valid, else 'False'
        """
        if valid is None or not all(valid):
            return allowNone

        if val is not None and any(valid):
            isValid = True
            if valid[0] is not None:
                isValid &= float(val) >= float(valid[0])
            if valid[1] is not None:
                isValid &= float(val) <= float(valid[1])

            return isValid

        return False

    # Size of data slice we want to send to Sense HAT. The 'f451 Labs SenseHat'
    # library will ulimately only display the last 8 values anyway.
    dataSlice = list(inData.data)[-lenSlice:]

    # Return filtered data
    dataClean = [i if _is_valid(i, inData.valid) else 0 for i in dataSlice]

    return f451SenseData.DataUnit(
        data=dataClean,
        valid=inData.valid,
        unit=inData.unit,
        label=inData.label,
        limits=inData.limits,
    )


# =========================================================
#                     M A I N   C L A S S
# =========================================================
class SenseHat:
    """Main SenseHat for managing the Raspberry Pi Sense HAT.

    This class encapsulates all methods required to interact with the
    sensors and the LED on the Raspberry Pi Sense HAT.

    NOTE: some methods are not needed, but are kept to maintain a basic
    level of compatibility with f451 Labs modules for other HATs and/or
    displays (e.g. f451-enviro, etc.).

    NOTE: attributes follow same naming convention as used in the
    'settings.toml' file. This makes it possible to pass in the 'config'
    object (or any other dict) as is.

    NOTE: we let users provide an entire 'dict' object with settings as
    key-value pairs, or as individual settings. User can combine both and,
    for example, provide a standard 'config' object as well as individual
    settings which could override the values in the 'config' object.

    Example:
        mySenseHat = SenseHat(config)           # Use values from 'config'
        mySenseHat = SenseHat(key=val)          # Use val
        mySenseHat = SenseHat(config, key=val)  # Use values from 'config' and also use 'val'

    Attributes:
        ROTATION:   Default rotation for LED display - [0, 90, 180, 270]
        DISPLAY:    Default display mode [0...]
        PROGRESS:   Show progress bar - [0 = no, 1 = yes]
        SLEEP:      Number of seconds until LED goes to screen saver mode

    Methods & Properties:
        displayWidth:       Width (cols) of LED display
        displayHeight:      Height (rows) of LED display
        isFake:             'False' if physical Sense HAT
        get_CPU_temp:       Get CPU temp which we then can use to compensate temp reads
        get_proximity:      Dummy - for compatibility
        get_lux:            Dummy - for compatibility
        get_pressure:       Get barometric pressure from sensor
        get_humidity:       Get humidity from sensor
        get_temperature:    Get temperature from sensor
        set_display_mode:   Switch display mode
        update_sleep_mode:  Switch to/from sleep mode
        joystick_init:      Initialize joystick actions
        display_init:       Initialize display so we can draw on it
        display_rotate:     Rotate display +/- 90 degrees
        display_on:         Turn 'on' LED
        display_off:        Turn 'off' LED
        display_blank:      Erase LED
        display_reset:      Erase LED and reset 'low_light' flag
        display_sparkle:    Show random sparkles on LED
        display_as_graph:   Display data as graph
        display_as_text:    Dummy - for compatibility
        display_message:    Display text message - wrapper for 'display_8x8_message
        display_progress:   Display progress bar
        display_8x8_image:  Display 8x8 image on LED
        display_8x8_message: Display scrolling text on LED
        debug_joystick:     Fake joystick actions for debugging
    """

    def __init__(self, *args, **kwargs):
        """Initialize Sense HAT hardware

        Args:
            args:
                User can provide single 'dict' with settings
            kwargs:
                User can provide individual settings as key-value pairs
        """
        # We combine 'args' and 'kwargs' to allow users to provide the entire
        # 'config' object and/or individual settings (which could override
        # values in 'config').
        settings = {**args[0], **kwargs} if args and isinstance(args[0], dict) else kwargs

        self._SENSE = self._init_SENSE(**settings)

        self.displRotation = settings.get(KWD_ROTATION, DEF_ROTATION)
        self.displProgress = bool(settings.get(KWD_PROGRESS, STATUS_ON))

        self.displayModes = [DISPL_SPARKLE]
        self.displMode = DISPL_SPARKLE
        # self.displModeMin = settings.get(KWD_DISPLAY_MIN, 0)
        # self.displModeMax = settings.get(KWD_DISPLAY_MAX, 0)

        self.displSleepTime = settings.get(KWD_SLEEP, DEF_SLEEP)
        self.displSleepMode = False

        self.displTopX = DISPL_TOP_X
        self.displTopY = DISPL_TOP_Y

    @property
    def displayWidth(self):
        return DISPL_MAX_COL

    @property
    def displayHeight(self):
        return DISPL_MAX_ROW

    @property
    def isFake(self):
        """Is this 'real' or 'fake' SeneSHAT?

        Returns 'True' if we use 'FakeSenseHat' library
        """
        return getattr(self._SENSE, 'fake', False)

    def _init_SENSE(self, **kwargs):
        """Initialize SenseHat

        Initialize the SenseHat device, set some
        default parameters, and clear LED.
        """
        sense = RPISenseHat()

        sense.set_imu_config(False, False, False)  # Disable IMU functions
        sense.low_light = True
        sense.clear()  # Clear 8x8 LED
        sense.set_rotation(kwargs.get(KWD_ROTATION, DEF_ROTATION))  # Set initial rotation

        sense.stick.direction_up = SenseHat._btn_dummy
        sense.stick.direction_down = SenseHat._btn_dummy
        sense.stick.direction_left = SenseHat._btn_dummy
        sense.stick.direction_right = SenseHat._btn_dummy
        sense.stick.direction_middle = SenseHat._btn_dummy

        return sense

    @staticmethod
    def _btn_dummy(*args):
        """SenseHat Joystick dummy event

        This is a placeholder event which is assigned when no other
        action can be tied to a given Sense HAT Joystick event.
        """
        pass

    @staticmethod
    def _scrub(data, default=0):
        """Scrub 'None' values from data"""
        return [default if i is None else i for i in data]

    @staticmethod
    def _clamp(val, minVal=0, maxVal=1):
        """Clamp values to min/max range"""
        return min(max(float(minVal), float(val)), float(maxVal))

    @staticmethod
    def _scale(val, minMax, height):
        """Scale value to fit on SenseHAT LED

        This is similar to 'num_to_range()' in f451 Labs Common module,
        but simplified for fitting values to SenseHAT LED display dimensions.
        """
        if minMax is None or minMax[1] == minMax[0]:
            return 0

        return float(val - minMax[0]) / float(minMax[1] - minMax[0]) * height

    @staticmethod
    def _get_rgb(val, curRow, height):
        """Get a color value using 'colorsys' library

        We use this method if there is no color map and/or
        no limits are defined for a give data set.
        """
        # Should the pixel on this row be black?
        if curRow < (height - int(val * height)):
            return RGB_BLACK

        # Convert the values to colors from red to blue
        color = (1.0 - val) * 0.6
        return tuple(int(x * 255.0) for x in colorsys.hsv_to_rgb(color, 1.0, 1.0))

    def _get_rgb_from_map(self, val, minMax, curRow, height, limits, colorMap):
        """Get a color from color map based on limits

        This function maps a value against a color map. Note that
        we need to map an original value (as opposed to scaled value)
        against the color map, as the color map limits use actual
        (full-scale) values.

        Args:
            val: value to map
            minMax: 'tuple' with min/max values
            curRow: 'int' with current row
            height: 'int' height display
            limits: 'list' with limits
            colorMap: named 'tuple' with color map

        Returns:
            'tuple' with RGB as '(R, G, B)'
        """
        # Should the pixel on this row be black?
        scaledVal = int(self._clamp(self._scale(val, minMax, height), 0, height))
        if curRow < (height - scaledVal):
            return RGB_BLACK

        if val > round(limits[2], 1):
            return colorMap.high
        elif val <= round(limits[1], 1):
            return colorMap.low
        else:
            return colorMap.normal

    def get_CPU_temp(self, strict=True):
        """Get CPU temp

        We use this for compensating temperature reads from BME280 sensor.

        Based on code from Sense HAT example 'luftdaten_combined.py'

        Args:
            strict:
                If 'True', then we raise an exception, else we simply
                return 'regular' temperature (from BME280) if the
                exceptions is 'FileNotFoundError'
        Raises:
            Same exceptions as 'Popen'
        """
        try:
            process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE, universal_newlines=True)
            output, _error = process.communicate()
            return float(output[output.index('=') + 1 : output.rindex("'")])

        except FileNotFoundError:
            if not strict:
                return self._SENSE.get_temperature()
            else:
                raise

    def get_proximity(self, *args):
        """Get proximity data

        NOTE: For compatibility only! We cannot get
              this data from Sense HAT (yet).
        """
        return None

    def get_lux(self, *args):
        """Get illumination data

        NOTE: For compatibility only! We cannot get
              this data from Sense HAT (yet).
        """
        return None

    def get_pressure(self):
        """Get air pressure data from Sense HAT sensor"""
        return self._SENSE.get_pressure()

    def get_humidity(self):
        """Get humidity data from Sense HAT sensor"""
        return self._SENSE.get_humidity()

    def get_temperature(self):
        """Get temperature data from Sense HAT sensor"""
        return self._SENSE.get_temperature()

    def add_displ_modes(self, modes):
        """Add list of display modes to existing list
        
        We combine the lists, convert them to a set to ensure that
        there are no duplicates, and then convert back to a list.

        Args:
            modes: list of one or more view names
        """
        # If it's a single string, then we'll assume it's the name
        # of a new view and we'll convert it to alist with 1 item.
        if isinstance(modes, str):
            modes = [modes]
        
        self.displayModes = list(set(self.displayModes + modes))

    def set_display_mode(self, mode):
        """Change LED display mode

        Change the LED display mode and also wake
        up the display if needed.

        Args:
            mode: if pos/neg int, then move to next/prev view/mode
                  if string, then move to specific view/mode

        """
        newMode = DISPL_SPARKLE

        # Did we get a string? Check if it's a valid view.
        if isinstance(mode, str) and mode in self.displayModes:
            newMode = mode

        # Or did we get 'direction' ? Then loop to prev/next view.
        elif isinstance(mode, int):
            displMax = max(0, len(self.displayModes) - 1)
            
            newModeIndx = self.displayModes.index(self.displMode)
            newModeIndx += (-1 if int(mode) < 0 else 1)

            if newModeIndx > displMax:
                newModeIndx = 0
            elif newModeIndx < 0:
                newModeIndx = displMax

            newMode = self.displayModes[newModeIndx]

        self.displMode = newMode

        # Wake up display?
        if self.displSleepMode:
            self.display_on()

        # Clear the display
        self._SENSE.clear()

    def update_sleep_mode(self, *args):
        """Enable or disable LED sleep mode

        We're turning on/off the LED sleep mode flag based
        on whether one or more args are 'True'

        Args:
            args: list of one or more flags. If any flag
                  is 'True' then we 'go to sleep' and turn
                  off display
        """
        if any(args) and not self.displSleepMode:
            self.display_off()
        elif not any(args) and self.displSleepMode:
            self.display_on()

    def joystick_init(self, **kwargs):
        """Initialize Sense HAT joystick

        We can set/update the actions that are tied to
        Sense HAT joystick events.

        Args:
            kwargs: optional values for joystick actions
        """
        self._SENSE.stick.direction_up = kwargs.get(KWD_BTN_UP, SenseHat._btn_dummy)
        self._SENSE.stick.direction_down = kwargs.get(KWD_BTN_DWN, SenseHat._btn_dummy)
        self._SENSE.stick.direction_left = kwargs.get(KWD_BTN_LFT, SenseHat._btn_dummy)
        self._SENSE.stick.direction_right = kwargs.get(KWD_BTN_RHT, SenseHat._btn_dummy)
        self._SENSE.stick.direction_middle = kwargs.get(KWD_BTN_MDL, SenseHat._btn_dummy)

    def display_rotate(self, direction):
        """Rotate LED display

        Since LED is square (8x8), rotate it 90 degrees at a time
        without affecting aspect ratio, etc.

        Args:
            direction: pos/neg integer
        """
        if self.isFake:
            return

        if int(direction) < 0:
            self.displRotation = 270 if self.displRotation <= 0 else self.displRotation - ROTATE_90
        else:
            self.displRotation = 0 if self.displRotation >= 270 else self.displRotation + ROTATE_90

        # Rotate as needed
        self._SENSE.set_rotation(self.displRotation)

        # Wake up display?
        if self.displSleepMode:
            self.display_on()

    # fmt: off
    def display_on(self):
        """Turn 'on' LED display"""
        if not self.isFake:
            self._SENSE.low_light = True
        self.displSleepMode = False     # Reset 'sleep mode' flag

    def display_off(self):
        """Turn 'off' LED display"""
        if not self.isFake:
            self._SENSE.clear()         # Clear 8x8 LED
        self.displSleepMode = True      # Set 'sleep mode' flag

    def display_blank(self):
        """Show clear/blank LED"""
        # Skip this if we're in 'sleep' mode
        if not (self.isFake or self.displSleepMode):
            self._SENSE.clear()         # Clear 8x8 LED

    def display_reset(self):
        """Reset and clear LED"""
        if not self.isFake:
            self._SENSE.low_light = False
            self._SENSE.clear()         # Clear 8x8 LED
    # fmt: on

    def display_as_graph(self, data, minMax=None, colorMap=None, default=0):
        """Display graph

        This method will redraw the entire 8x8 LED all at once. That means
        we need to create a list of 64 RGB tuples, and then send the list
        to the Sense HAT 'set_pixels()' method.

        NOTE: the data structure is more complex than we need for Sense HAT
        devices. But we want to maintain a basic level of compatibility with
        other f451 Labs modules.

        Args:
            data:
                'DataUnit' named tuple with the following fields:
                    data   = [list of values],
                    valid  = <tuple with min/max>,
                    unit   = <unit string>,
                    label  = <label string>,
                    limits = [list of limits]
            minMax:
                'tuple' with min/max values. If 'None' then calculate locally.
            colorMap:
                'tuple' (optional) custom color map to use if data has defined 'limits'
            default:
                'float' (optional) default value to use when replacing 'None' values
        """
        # Skip this if we're in 'sleep' mode
        if self.isFake or self.displSleepMode:
            return

        # Create a list with 'displayWidth' num values. We add 0 (zero) to
        # the beginning of the list if whole set has less than 'displayWidth'
        # num values. This allows us to simulate 'scrolling' right to left. We
        # grab last 'n' values that can fit LED and scrub any 'None' values. If
        # there are not enough values to to fill display, we add 0's
        displWidth = self.displayWidth
        displHeight = self.displayHeight
        subSet = self._scrub(data.data[-displWidth:], default)
        lenSet = min(displWidth, len(subSet))

        # Extend 'value' list as needed
        values = (
            subSet
            if lenSet == displWidth
            else [default for _ in range(displWidth - lenSet)] + subSet
        )

        # Reserve space for progress bar?
        yMax = displHeight - 1 if self.displProgress else displHeight
        if minMax is None or minMax[1] == minMax[0]:
            vMin = min(values) if minMax is None else minMax[0]
            vMax = max(values) if minMax is None else minMax[1]
        else:
            vMin, vMax = minMax

        # Get colors based on limits and color map? Or generate based on
        # value itself compared to defined limits?
        if all(data.limits):
            pixels = [
                self._get_rgb_from_map(v, (vMin, vMax), row, yMax, data.limits, colorMap)
                for row in range(yMax)
                for v in values
            ]
        else:
            # Scale incoming values to be between 0 and 1. We may need to clamp
            # values when values are outside min/max for current sub-set. This
            # can happen when original data set has more values than the chunk
            # (8 values) that we display on the Sense HAT 8x8 LED.
            scaled = [self._clamp((v - vMin + 1) / (vMax - vMin + 1)) for v in values]
            pixels = [self._get_rgb(v, row, yMax) for row in range(yMax) for v in scaled]

        # If there's a progress bar on bottom (8th) row, lets copy the existing
        # pixels, and then append them to the new (7 row) pixel list
        if self.displProgress:
            currPixels = self._SENSE.get_pixels()
            pixels += currPixels[-displWidth:]

        # Display all pixels for entire Sense HAT LED all at once
        self._SENSE.set_pixels(pixels)

    def display_as_text(self, *args):
        """Display data points as text in columns

        NOTE: For compatibility only! We cannot display
              this text info in a meaningful manner on
              the Sense HAT 8x8 LED display.
        """
        pass

    def display_message(self, msg, fgCol=None, bgCol=None):
        """Display text message

        This method wraps the 'display_8x8_message' method.

        Args:
            msg: 'str' with text to display
            fgCol: 'tuple' with (R, G, B) for text color
            bgCol: 'tuple' with (R, G, B) for background color
        """
        self.display_8x8_message(msg, fgCol, bgCol)

    def display_progress(self, inFrctn=0.0):
        """Update progressbar on LED

        This method marks 'fraction complete' (0.0 - 1.0)
        on 1px tall progress bar on top row of LED

        Args:
            inFrctn: 'float' representing fraction complete
        """
        # Skip this if we're in 'sleep' mode
        if self.isFake or self.displSleepMode or not self.displProgress:
            return

        # Calculate X value. We ensure that we do not go over max width
        # of LED by limiting any input value to a range of 0.0 - 1.0
        col = int(max(min(float(inFrctn), 1.0), 0.0) * DISPL_MAX_COL)

        # First, paint forteground color to indicate progress. Then
        # paint remainder of row with background color so user can
        # see that entire bottom row is reserved for prog bar.
        for x in range(col):
            self._SENSE.set_pixel(x, DISPL_MAX_ROW - 1, COLOR_PBAR_FG)
        for x in range(col, DISPL_MAX_COL):
            self._SENSE.set_pixel(x, DISPL_MAX_ROW - 1, COLOR_PBAR_BG)

    def display_sparkle(self):
        """Show random sparkles on LED

        This is essenmtially a screen saver to show the app
        is still running on the device.
        """

        def _sparkle():
            x = randint(0, DISPL_MAX_COL - 1)
            y = randint(0, yMax - 1)
            r = randint(0, 255)
            g = randint(0, 255)
            b = randint(0, 255)

            return x, y, (r, g, b)

        # Skip this if we're in 'sleep' mode
        if self.isFake or self.displSleepMode:
            return

        # Reserve space for progress bar?
        yMax = DISPL_MAX_ROW - 1 if (self.displProgress) else DISPL_MAX_ROW

        # Do we want to clear the screen? Or add more sparkles?
        maxSparkle = int(DISPL_MAX_COL * yMax * MAX_SPARKLE_PCNT)
        if randint(0, maxSparkle):
            x, y, rgb = _sparkle()
            self._SENSE.set_pixel(x, y, rgb)
        else:
            # If we have a progress bar, we'll create a blank top
            # and add back in the last row with the progress bar
            # fmt: off
            if self.displProgress:
                currPixels = self._SENSE.get_pixels()
                pixels = [RGB_BLACK for _ in range(DISPL_MAX_COL * yMax)] + currPixels[-DISPL_MAX_COL:]
                self._SENSE.set_pixels(pixels)
            else:
                self._SENSE.clear()
            # fmt: on

    def display_8x8_image(self, image):
        """Display 8x8 image on LED

        Args:
            image:
                'list' with 64 tuples, each representing
                complete RGB value as follows:

                    [(r,g,b), (r,g,b), ... (r,g,b)]

                See demo for example.
        """
        # Skip this if we're in 'sleep' mode
        if not (self.isFake or self.displSleepMode):
            self._SENSE.set_pixels(image)

    def display_8x8_message(self, msg, fgCol=None, bgCol=None):
        """Display scrolling message

        Args:
            msg: text string to display
            fgCol: 'tuple' with (R, G, B) for text color
            bgCol: 'tuple' with (R, G, B) for background color
        """
        # Skip this if we're in 'sleep' mode
        if not (self.isFake or self.displSleepMode):
            fg = RGB_RED if fgCol is None else fgCol
            bg = RGB_GREY if bgCol is None else bgCol
            self._SENSE.show_message(msg, text_colour=fg, back_colour=bg)
            self._SENSE.clear()  # Clear 8x8 LED

    def debug_joystick(self, direction=''):
        """Assign to joystick events to confirm actions"""
        if direction == 'up':
            self._SENSE.show_letter('U')
        elif direction == 'down':
            self._SENSE.show_letter('D')
        elif direction == 'left':
            self._SENSE.show_letter('L')
        elif direction == 'right':
            self._SENSE.show_letter('R')
        elif direction == 'press':
            self._SENSE.show_letter('+')
        else:
            self._SENSE.show_letter('?')
