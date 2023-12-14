"""Custom class for Sense HAT sensor data.

This class defines a data structure thaty can be used 
to manage all sensor data from the Sendse HAT device. There
are also methods to support conversion between units, etc.

Dependencies:
    - deque - double-ended queue from 'collections' library
"""

from collections import deque

__all__ = [
    'SenseData',
    'SenseObject',
    'TemperatureObject',
    'COLOR_MAP',
    'TEMP_UNIT_C',
    'TEMP_UNIT_F',
    'TEMP_UNIT_K',
    'COLOR_LOW',
    'COLOR_NORM',
    'COLOR_HIGH',
]


# =========================================================
#              M I S C .   C O N S T A N T S
# =========================================================
TEMP_UNIT_C = 'C'  # Celsius
TEMP_UNIT_F = 'F'  # Fahrenheit
TEMP_UNIT_K = 'K'  # Kelvin

# Limit set [A, B, C, D] means:
#
#             val <= A -> Dangerously Low   = "red"
#     B >= val >  A -> Low                  = "yellow"
#     C >= val >  B -> Normal               = "green"
#     D >= val >  C -> High                 = "cyan"
#             val >  D -> Dangerously High  = "blue"
#
COLOR_MAP = [
    'red',              # 0
    'yellow',           # 1
    'green',            # 2
    'cyan',             # 3
    'blue',             # 4
]
# Shortcuts for indicating main colors
COLOR_LOW = 0
COLOR_NORM = 2
COLOR_HIGH = 4


# =========================================================
#                     M A I N   C L A S S
# =========================================================
class SenseObject:
    """Data structure for environment data object.

    Attributes:
        data:   'dequeue' for data points
        valid:  'tuple' with valid range (min and max) values for data points
        unit:   'str' for data unit of measure (e.g. "C" for temperature)
        limits: 'list' of limit values
        label:  'str' for data object label (e .g. "Temperature")

    Methods:
        as_dict: return data attributes as 'dict'
    """

    def __init__(self, data, valid, unit, limits, label):
        self.data = data
        self.valid = valid
        self.unit = unit
        self.limits = limits
        self.label = label

    def as_dict(self):
        """Return data object as 'dict' with each attribute as key."""
        return {
            'data': self.data,
            'valid': self.valid,
            'unit': self.unit,
            'limits': self.limits,
            'label': self.label.capitalize(),
        }


class TemperatureObject(SenseObject):
    """Data structure for environment data object.

    Attributes:
        data:   'dequeue' for data points
        valid:  'tuple' with valid range (min and max) values
                for data points. If either value is 'None', then
                disregard limits
        unit:   'str' for data unit of measure (e.g. "C" for temperature)
        limits: 'list' of limit values
        label:  'str' for data object label (e .g. "Temperature")

    Methods:
        as_dict: return data attributes as 'dict'
    """

    def __init__(self, data, valid, unit, limits, label):
        super().__init__(data, valid, unit, limits, label)

    def as_dict(self, unit=TEMP_UNIT_C):
        """Return object as 'dict' with temp in C, F, or K

        Args:
            unit: if "C" then return temperature in Celsius
                  if "F"            -"-          in Fahrenheit
                  if "K"            -"-          in Kelvin
        """
        if unit == TEMP_UNIT_F:
            data = [self._convert_C2F(c) for c in self.data]
        elif unit == TEMP_UNIT_K:
            data = [self._convert_C2K(c) for c in self.data]
        else:
            data = self.data

        return {
            'data': data,
            'valid': self.valid,
            'unit': self.unit,
            'limits': self.limits,
            'label': self.label.capitalize(),
        }

    @staticmethod
    def _convert_C2F(celsius):
        """Convert Celsius to Fahrenheit"""
        return (celsius * 9 / 5) + 32.0

    @staticmethod
    def _convert_C2K(celsius):
        """Convert Celsius to Kelvin"""
        return float(celsius) + 273.15


class SenseData:
    """Data structure for holding and managing sensor data.

    Create an empty full-size data structure that we use
    in the app to collect a series of sensor data.

    NOTE: The 'limits' attribute stores a list of limits. You
            can define your own warning limits for your environment
            data as follows:

            Example limits explanation for temperature:
            [4,18,28,35] means:
            -273.15 ... 4     -> Dangerously Low
                  4 ... 18    -> Low
                 18 ... 28    -> Normal
                 28 ... 35    -> High
                 35 ... MAX   -> Dangerously High

    DISCLAIMER: The limits provided here are just examples and come
    with NO WARRANTY. The authors of this example code claim
    NO RESPONSIBILITY if reliance on the following values or this
    code in general leads to ANY DAMAGES or DEATH.

    Attributes:
        temperature:    temperature in C
        pressure:       barometric pressure in hPa
        humidity:       humidity in %
        light:          illumination in Lux

    Methods:
        as_list: returns a 'list' with data from each attribute as 'dict'
        convert_C2F: static (wrapper) method. Converts Celsius to Fahrenheit
        convert_C2K: static (wrapper) method. Converts Celsius to Kelvin
    """

    def __init__(self, defVal, maxLen):
        """Initialize data structurte.

        Args:
            defVal: default value to use when filling up the queues
            maxLen: max length of each queue

        Returns:
            'dict' - holds entire data structure
        """
        self.temperature = TemperatureObject(
            deque([defVal] * maxLen, maxlen=maxLen),
            (0, 65),        # Sense HAT temp sensor (STMicro LPS25HB) range 0-65°C (±2°C)
            'C',
            [4, 18, 25, 35],
            'Temperature',
        )
        self.pressure = SenseObject(
            deque([defVal] * maxLen, maxlen=maxLen),
            (260, 1260),    # Sense HAT pressure sensor (STMicro LPS25HB) range 260-1260 hPa
            'hPa',
            [250, 650, 1013.25, 1015],
            'Pressure',
        )
        self.humidity = SenseObject(
            deque([defVal] * maxLen, maxlen=maxLen),
            (0, 100),       # Sense HAT humidity sensor (STMicro HTS221) range 0-100%
            '%',
            [20, 30, 60, 70],
            'Humidity',
        )
        self.light = SenseObject(
            deque([defVal] * maxLen, maxlen=maxLen),
            (None, None),   # Sense HAT color/brightness sensor (TCS3400)
            'Lux',
            [-1, -1, 30000, 100000],
            'Light',
        )

    def as_list(self, tempUnit=TEMP_UNIT_C):
        return [
            self.temperature.as_dict(tempUnit),
            self.pressure.as_dict(),
            self.humidity.as_dict(),
            self.light.as_dict(),
        ]

    def as_dict(self, tempUnit=TEMP_UNIT_C):
        return {
            'temperature': self.temperature.as_dict(tempUnit),
            'pressure': self.pressure.as_dict(),
            'humidity': self.humidity.as_dict(),
            'light': self.light.as_dict(),
        }

    def convert_C2F(self, celsius):
        return self.temperature._convert_C2F(celsius)

    def convert_C2K(self, celsius):
        return self.temperature._convert_C2K(celsius)
