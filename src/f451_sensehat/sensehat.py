"""f451 Labs Sense HAT Device Class.

The Sense HAT Device class includes support for sensosr and 
LED display included on the Raspberry Pi Sense HAT.

The class wraps -- and extends as needed -- the methods 
and functions supported by underlying libraries, and also
keeps track of core counters, flags, etc.

Dependencies:
 - fonts: https://pypi.org/project/fonts/
 - font-roboto: https://pypi.org/project/font-roboto/
 - Pillow: https://pypi.org/project/Pillow/
 - Raspberry Pi Sense HAT library: https://github.com/pimoroni/enviroplus-python/  
"""

import colorsys

from random import randint

from subprocess import PIPE, Popen

try:
    from sense_hat import SenseHat as RPISenseHat, ACTION_PRESSED, ACTION_HELD, ACTION_RELEASED
except ImportError:
    from .fake_HAT import FakeSenseHat as RPISenseHat, ACTION_PRESSED, ACTION_HELD, ACTION_RELEASED  # noqa: F401

__all__ = [
    'SenseHat',
    'SenseHatError',
    'BTN_RELEASE',
    'KWD_ROTATION',
    'KWD_DISPLAY',
    'KWD_PROGRESS',
    'KWD_SLEEP',
    'KWD_DISPLAY_MIN',
    'KWD_DISPLAY_MAX',
    'KWD_BTN_UP',
    'KWD_BTN_DWN',
    'KWD_BTN_LFT',
    'KWD_BTN_RHT',
    'KWD_BTN_MDL',
]


# =========================================================
#              M I S C .   C O N S T A N T S
# =========================================================
DEF_ROTATION = 0        # Default display rotation
DEF_DISPL_MODE = 0      # Default display mode
DEF_SLEEP = 600         # Default time to sleep (in seconds)
DEF_LED_OFFSET_X = 0    # Default horizontal offset for LED
DEF_LED_OFFSET_Y = 0    # Default vertical offseet for LED

STATUS_ON = True
STATUS_OFF = False

DISPL_TOP_X = 0         # X/Y ccordinate of top-left corner for LED content
DISPL_TOP_Y = 0
DISPL_MAX_COL = 8       # sense has an 8x8 LED display
DISPL_MAX_ROW = 8

PROX_DEBOUNCE = 0.5     # Delay to debounce proximity sensor on 'tap'
PROX_LIMIT = 1500       # Threshold for proximity sensor to detect 'tap'

MAX_SPARKLE_PCNT = 0.1  # 10% sparkles

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

# RGB colors and palette for values on combo/text screen
COLOR_PALETTE = [
    RGB_BLUE,       # Dangerously Low
    RGB_CYAN,       # Low
    RGB_GREEN,      # Normal
    RGB_YELLOW,     # High
    RGB_RED,        # Dangerously High
]

COLOR_BG = RGB_BLACK    # Default background
COLOR_TXT = RGB_CHROME  # Default text on background
COLOR_PBAR = RGB_CYAN   # Default progress bar

ROTATE_90 = 90      # Rotate 90 degrees
STEP_1 = 1          # Display mode step

BTN_RELEASE = ACTION_RELEASED

# =========================================================
#    K E Y W O R D S   F O R   C O N F I G   F I L E S
# =========================================================
KWD_ROTATION = 'ROTATION'
KWD_DISPLAY = 'DISPLAY'
KWD_PROGRESS = 'PROGRESS'
KWD_SLEEP = 'SLEEP'
KWD_DISPLAY_MIN = 'DISPLAYMIN'
KWD_DISPLAY_MAX = 'DISPLAYMAX'

KWD_BTN_UP = 'BTNUP'
KWD_BTN_DWN = 'BTNDWN'
KWD_BTN_LFT = 'BTNLFT'
KWD_BTN_RHT = 'BTNRHT'
KWD_BTN_MDL = 'BTNMDL'


# =========================================================
#                        H E L P E R S
# =========================================================
class SenseHatError(Exception):
    """Custom exception class"""

    pass


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

    Methods:
        get_CPU_temp:       Get CPU temp which we then can use to compensate temp reads
        get_lux:            Get illumination value from sensor
        get_pressure:       Get barometric pressure from sensor
        get_humidity:       Get humidity from sensor
        get_temperature:    Get temperature from sensor
        display_init:       Initialize display so we can draw on it
        display_on:         Turn 'on' LED
        display_off:        Turn 'off' LED
        display_blank:      Erase LED
        display_reset:      Erase LED
        display_sparkle:    Show random sparkles on LED
        display_as_graph:   Display data as graph
        display_as_text:    Dummy - for compatibility
        display_message:    Display text message
        display_progress:   Display progress bar
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
        self.displMode = settings.get(KWD_DISPLAY, DEF_DISPL_MODE)
        self.displProgress = bool(settings.get(KWD_PROGRESS, STATUS_ON))

        self.displModeMin = settings.get(KWD_DISPLAY_MIN, 0)
        self.displModeMax = settings.get(KWD_DISPLAY_MAX, 0)

        self.displSleepTime = settings.get(KWD_SLEEP, DEF_SLEEP)
        self.displSleepMode = False

        self.displTopX = DISPL_TOP_X
        self.displTopY = DISPL_TOP_Y

    @property
    def widthLED(self):
        return DISPL_MAX_COL

    @property
    def heightLED(self):
        return DISPL_MAX_ROW

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

        sense.stick.direction_up = kwargs.get(KWD_BTN_UP, self._btn_dummy)
        sense.stick.direction_down = kwargs.get(KWD_BTN_UP, self._btn_dummy)
        sense.stick.direction_left = kwargs.get(KWD_BTN_UP, self._btn_dummy)
        sense.stick.direction_right = kwargs.get(KWD_BTN_UP, self._btn_dummy)
        sense.stick.direction_middle = kwargs.get(KWD_BTN_UP, self._btn_dummy)

        return sense

    @staticmethod
    def _btn_dummy(*args):
        """SenseHat Joystick dummy event

        This is a placeholder event which is assigned when no other
        action can be tied to a given Sene HAT Joystick event.
        """
        pass

    def is_fake(self):
        return getattr(self._SENSE, 'fake', False)

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

    def get_pressure(self):
        """Get air pressure data from Sense HAT sensor"""
        return self._SENSE.get_pressure()

    def get_humidity(self):
        """Get humidity data from Sense HAT sensor"""
        return self._SENSE.get_humidity()

    def get_temperature(self):
        """Get temperature data from Sense HAT sensor"""
        return self._SENSE.get_temperature()

    def update_display_mode(self, direction):
        """Change LED display mode

        We're changing the LED display mode and we're also
        waking up the display if needed.

        Args:
            direction: pos/neg integer
        """
        if int(direction) < 0:
            self.displMode = (
                self.displModeMax
                if self.displMode <= self.displModeMin
                else self.displMode - STEP_1
            )
        else:
            self.displMode = (
                self.displModeMin
                if self.displMode >= self.displModeMax
                else self.displMode + STEP_1
            )

        # Wake up display?
        if not self.displSleepMode:
            self.display_on()

    def update_sleep_mode(self, *args):
        """Enable or disable LED sleep mode

        We're turning on/off the LED sleep mode flag based
        on whether one or more args are 'True'

        Args:
            args: list of one or more flags
        """
        sleep = any(args)

        # Do we need to turn off LED?
        if sleep and not self.displSleepMode:
            self.display_off()

        # Do we need to turn on LED?
        elif not sleep and self.displSleepMode:
            self.display_on()

    def joystick_init(self, **kwargs):
        """Initialize Sense HAT joystick

        We can set/update the actions that are tied to
        Sense HAT joystick events.

        Args:
            kwargs: optional values for joystick actions
        """
        self._SENSE.stick.direction_up = kwargs.get(
            KWD_BTN_UP, self._SENSE.stick.direction_up
        )
        self._SENSE.stick.direction_down = kwargs.get(
            KWD_BTN_UP, self._SENSE.stick.direction_down
        )
        self._SENSE.stick.direction_left = kwargs.get(
            KWD_BTN_UP, self._SENSE.stick.direction_left
        )
        self._SENSE.stick.direction_right = kwargs.get(
            KWD_BTN_UP, self._SENSE.stick.direction_right
        )
        self._SENSE.stick.direction_middle = kwargs.get(
            KWD_BTN_UP, self._SENSE.stick.direction_middle
        )

    def display_init(self, **kwargs):
        """Initialize LED display

        We can set/update the number of possible displays by
        using the 'kwargs' to displayMode min/max values.

        Args:
            kwargs: optional values for displayMode min/max values
        """
        self.displModeMin = kwargs.get(KWD_DISPLAY_MIN, self.displModeMin)
        self.displModeMax = kwargs.get(KWD_DISPLAY_MAX, self.displModeMax)

        self.display_on()

    def display_rotate(self, direction):
        """Rotate LED display

        Since LED is square (8x8), rotate it 90 degrees at a time
        without affecting aspect ratio, etc.

        Args:
            direction: pos/neg integer
        """
        if int(direction) < 0:
            self.displRotation = 270 if self.displRotation <= 0 else self.displRotation - ROTATE_90
        else:
            self.displRotation = 0 if self.displRotation >= 270 else self.displRotation + ROTATE_90

        # Rotate as needed
        self._SENSE.set_rotation(self.displRotation)

        # Wake up display?
        if not self.displSleepMode:
            self.display_on()

    def display_on(self):
        """Turn 'on' LED display"""
        self._SENSE.low_light = True
        self.displSleepMode = False  # Reset 'sleep mode' flag
        self.display_blank()

    def display_off(self):
        """Turn 'off' LED display"""
        self.display_blank()
        self.displSleepMode = True  # Set 'sleep mode' flag

    def display_blank(self):
        """Show clear/blank LED"""
        # Skip this if we're in 'sleep' mode
        if self.displSleepMode:
            return

        self._SENSE.clear()  # Clear 8x8 LED

    def display_reset(self):
        """Reset and clear LED"""
        self._SENSE.low_light = False
        self._SENSE.clear()  # Clear 8x8 LED

    def display_as_graph(self, data):
        """Display graph and data point as text label

        This method will redraw the entire 8x8 LED all at once. That means
        we need to create a list of 64 RGB tuples, and then send the list
        to the Sense HAT 'set_pixels()' method.

        NOTE: the data structure is more complex than we need for Sense HAT
        devices. But we want to maintain a basic level of compatibility with
        other f451 Labs modules.

        Args:
            data:
                'dict' as follows:
                    {
                        "data": [list of values],
                        "unit" <unit string>,
                        "label": <label string>,
                        "limit": [list of limits]
                    }
        """

        def _get_rgb(val, curRow, maxRow):
            # Should the pixel on this row be black?
            if curRow < (maxRow - int(val * maxRow)):
                return RGB_BLACK

            # Convert the values to colors from red to blue
            color = (1.0 - val) * 0.6
            return tuple([int(x * 255.0) for x in colorsys.hsv_to_rgb(color, 1.0, 1.0)])

        # Skip this if we're in 'sleep' mode
        if self.displSleepMode:
            return

        # Create a list with 'DISPL_MAX_COL' num values. We add 0 (zero) to the
        # beginning of the list if whole set has less than 'DISPL_MAX_COL' num
        # values. This allows us to simulate 'scrolling' right to left.
        subSet = data['data'][-DISPL_MAX_COL:]  # Grab last 'n' values that can fit LED
        lenSet = min(DISPL_MAX_COL, len(subSet))  # Do we have enough data?

        # Extend 'value' list as needed
        values = (
            subSet
            if lenSet == DISPL_MAX_COL
            else [0 for _ in range(DISPL_MAX_COL - lenSet)] + subSet
        )

        # Scale incoming values in the data set to be between 0 and 1
        vmin = min(values)
        vmax = max(values)
        colors = [(v - vmin + 1) / (vmax - vmin + 1) for v in values]

        # Reserve space for progress bar?
        yMax = DISPL_MAX_ROW - 1 if (self.displProgress) else DISPL_MAX_ROW

        pixels = [
            _get_rgb(colors[col], row, yMax) for row in range(yMax) for col in range(DISPL_MAX_COL)
        ]

        self._SENSE.set_pixels(pixels)

    def display_as_text(self, *args):
        """Display data points as text in columns

        NOTE: for compatibility only

        Args:
            args: placeholder for compatibility
        """
        pass

    def display_message(self, msg):
        """Display text message

        This method will redraw the entire LED

        Args:
            msg: 'str' with text to display
        """
        # Skip this if we're in 'sleep' mode
        if self.displSleepMode:
            return

        # # Reserve space for progress bar?
        # yMin = 2 if (self.displProgress) else 0
        # self._draw.rectangle((0, yMin, self._LED.width, self._LED.height), RGB_BLACK)

        # # Draw message
        # x = DEF_LED_OFFSET_X
        # y = DEF_LED_OFFSET_Y + int((self._LED.height - FONT_SIZE_LG) / 2)
        # self._draw.text((x, y), str(msg), font=self._fontLG, fill=COLOR_TXT)

        # # Display results
        # self._LED.display(self._img)
        pass

    def display_progress(self, inFrctn=0.0):
        """Update progressbar on LED

        This method marks 'fraction complete' (0.0 - 1.0)
        on 1px tall progress bar on top row of LED

        Args:
            inFrctn: 'float' representing fraction complete
        """
        # Skip this if we're in 'sleep' mode
        if self.displSleepMode or not self.displProgress:
            return

        # Calculate X value. We ensure that we do not go over max width
        # of LED by limiting any input value to a range of 0.0 - 1.0
        col = int(max(min(float(inFrctn), 1.0), 0.0) * DISPL_MAX_COL)

        for x in range(col):
            self._SENSE.set_pixel(x, DISPL_MAX_ROW - 1, COLOR_PBAR)

    def display_sparkle(self):
        """Show random sparkles on LED"""
        # Skip this if we're in 'sleep' mode
        if self.displSleepMode:
            return

        # Reserve space for progress bar?
        yMax = DISPL_MAX_ROW - 1 if (self.displProgress) else DISPL_MAX_ROW

        # Create sparkles
        x = randint(0, DISPL_MAX_COL - 1)
        y = randint(0, yMax - 1)
        r = randint(0, 255)
        g = randint(0, 255)
        b = randint(0, 255)

        # Do we want to clear the screen? Or add more sparkles?
        maxSparkle = int(DISPL_MAX_COL * yMax * MAX_SPARKLE_PCNT)
        if randint(0, maxSparkle):
            self._SENSE.set_pixel(x, y, r, g, b)
        else:
            self._SENSE.clear()
