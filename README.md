# f451 Labs SenseHat module v0.0.1

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

Using the module is straightforward. Simply `import` it into your code and instantiate an `SenseHat` object which you can then use throughout your code.

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
