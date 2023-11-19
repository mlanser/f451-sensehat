# f451 Labs SenseHat module v1.1.1

## Overview

The *f451 Labs SenseHat* module encapsulates the drivers for the [*Raspberry Pi Sense HAT*](https://www.raspberrypi.com/documentation/accessories/sense-hat.html) within a single class. This module also provides a standard set of methods to read sensor data and display content to the onboard 8x8 LED display.

## Install

This module is not (yet) available on PyPi. however, you can still use `pip` to install the module directly from Github (see below).

### Dependencies

This module is dependent on the following libraries:

- [sense-hat](https://pypi.org/project/sense-hat/)

NOTE: Only install `sense-hat` library on a device that also has the physical Sense HAT installed.

NOTE: You can run this app in demo mode in (almost) any device even without the Sense HAT. It will then create random numbers and can send output to the `logger` when log level is `DEBUG` or when `--debug` flag is used.

### Installing from Github using `pip`

You can use `pip install` to install this module directly from Github as follows:

Using HTTPS:

```bash
$ pip install 'f451-sensehat @ git+https://github.com/mlanser/f451-sensehat.git'
```

Using SSH:

```bash
$ pip install 'f451-sensehat @ git+ssh://git@github.com:mlanser/f451-sensehat.git'
```

## How to use

### SenseHat Device

The `SenseHat` object makes it easy to interact with the *Sense HAT* device. The methods of this object help read sensor data, display data to the 8x8 LED, etc., and using the module is straightforward. Simply `import` it into your code and instantiate an `SenseHat` object which you can then use throughout your code.

```Python
# Import f451 Labs SenseHat
from f451_sensehat.sensehat import SenseHat

# Initialize device instance which includes all sensors
# and LED display on Sense HAT
mySense = SenseHat({
    "ROTATION": 0,
    "DISPLAY": 0,
    "PROGRESS": 0,
    "SLEEP": 600    
})

print(f"TEMP:     {round(mySense.get_temperature(), 1)} C")
print(f"PRESSURE: {round(mySense.get_pressure(), 1)} hPa")
print(f"HUMIDITY: {round(mySense.get_humidity(), 1)} %")
```

### SenseHat Data

The *f451 Labs SenseHat* module also includes a `SenseData` object and a few other helper objects. These objects are designed to simplify storing and managing sensor data. The `SenseData` object implements so-called [double-ended queues ('deque')](https://docs.python.org/3/library/collections.html#deque-objects) which makes it easy to add and retrieve data. To use these objects in your code, simply `import` them into your code and instantiate an `SenseData` object.

```Python
# Import f451 Labs SenseHat Data
from f451_sensehat.sensehat_data import SenseData

maxLen = 10     # Max length of queue
defVal = 1      # Default value for initialization

myData = SenseData(defVal, maxlen)

# Assuming we have instantiated the SenseHat object as 'mySense' we
# can then read and store sensor data right into the data queues
myData.temperature.data.append(mySense.get_temperature())
myData.pressure.data.append(mySense.get_pressure())
myData.humidity.data.append(mySense.get_humidity())
```

## How to test

The tests are written for [pytest](https://docs.pytest.org/en/7.1.x/contents.html) and we use markers to separate out tests that require the actual Sense HAT hardware. Some tests do not rely on the hardware to be prexent. However, those tests rely on the `pytest-mock` module to be present.

```bash

# Run all tests (except marked 'skip')
$ pytest

# Run tests with 'hardware' marker
$ pytest -m "hardware"

# Run tests without 'hardware' marker
$ pytest -m "not hardware"
```
