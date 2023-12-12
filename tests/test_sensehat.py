"""Test cases for f451 Labs SenseHat module.

Some of these test cases will collect sample data from the 
sensors on and/or will display info on the 8x8 LED on the 
RPI Sense HAT.

However, many tests can be run without the attached hardware
using the mock unit.
"""

import pytest
from src.f451_sensehat.sensehat import SenseHat


# =========================================================
#              M I S C .   C O N S T A N T S
# =========================================================
KWD_TST_VAL = 'TST_VAL'

ACTION_PRESSED = False
ACTION_HELD = False
ACTION_RELEASED = False
TEMP_MIN = 0        # Unit: C
TEMP_MAX = 65
PRESS_MIN = 260     # Unit: hPa
PRESS_MAX = 1260
HUMID_MIN = 20      # Unit: %
HUMID_MAX = 80

LED_WIDTH = 8
LED_HEIGHT = 8


# =========================================================
#          F I X T U R E S   A N D   H E L P E R S
# =========================================================
@pytest.fixture
def valid_str():
    return 'Hello world'


@pytest.fixture(scope='session')
def config():
    return {'ROTATION': 90, 'DISPLAY': 0, 'PROGRESS': 0, 'SLEEP': 600}


@pytest.fixture(scope='session')
def device_default():
    device = SenseHat()
    return device


@pytest.fixture(scope='session')
def device_config(config):
    device = SenseHat(config)
    return device


# =========================================================
#                    T E S T   C A S E S
# =========================================================
def test_dummy(valid_str):
    """Dummy test case.

    This is only a placeholder test case.
    """
    assert valid_str == 'Hello world'


def test_get_CPU_temp_mock(device_default, mocker):
    mocker.patch('src.f451_sensehat.sensehat.SenseHat.get_CPU_temp', return_value=TEMP_MIN)
    cpuTemp = device_default.get_CPU_temp()
    assert cpuTemp == TEMP_MIN


@pytest.mark.hardware
def test_get_CPU_temp(device_default):
    try:
        cpuTemp = device_default.get_CPU_temp()
    except FileNotFoundError:
        pass
    else:
        assert cpuTemp >= float(TEMP_MIN)


def test_get_pressure_mock(device_default, mocker):
    mocker.patch('src.f451_sensehat.sensehat.SenseHat.get_pressure', return_value=PRESS_MIN)
    pressure = device_default.get_pressure()
    assert pressure == PRESS_MIN


@pytest.mark.hardware
def test_get_pressure(device_default):
    pressure = device_default.get_pressure()
    assert pressure >= float(PRESS_MIN)


def test_get_humidity_mock(device_default, mocker):
    mocker.patch('src.f451_sensehat.sensehat.SenseHat.get_humidity', return_value=HUMID_MIN)
    humidity = device_default.get_humidity()
    assert humidity == HUMID_MIN


@pytest.mark.hardware
def test_get_humidity(device_default):
    humidity = device_default.get_humidity()
    assert humidity >= float(HUMID_MIN)


def test_get_temperature_mock(device_default, mocker):
    mocker.patch('src.f451_sensehat.sensehat.SenseHat.get_temperature', return_value=TEMP_MIN)
    temperature = device_default.get_temperature()
    assert temperature == TEMP_MIN


@pytest.mark.hardware
def test_get_temperature(device_default):
    temperature = device_default.get_temperature()
    assert temperature >= float(TEMP_MIN)


def test_display_init_mock(device_config, mocker):
    testDev = device_config
    mocker.patch('src.f451_sensehat.sensehat.SenseHat.display_init')
    testDev.display_init()
    testDev.display_init.assert_called_once()


@pytest.mark.hardware
def test_display_init(device_config):
    testDev = device_config
    testDev.display_init()
    assert testDev.displSleepMode == False


@pytest.mark.skip(reason='Is it worth testing?')
def test_display_on_mock(device_config, mocker):
    testDev = device_config
    mocker.patch('src.f451_sensehat.sensehat.SenseHat.display_on')
    testDev.display_on()
    testDev.display_on.assert_called_once()


@pytest.mark.skip(reason='Is it worth testing?')
def test_display_off_mock(device_config, mocker):
    testDev = device_config
    mocker.patch('src.f451_sensehat.sensehat.SenseHat.display_off')
    testDev.display_off()
    testDev.display_off.assert_called_once()


@pytest.mark.skip(reason='Is it worth testing?')
def test_display_blank_mock(device_config, mocker):
    testDev = device_config
    mocker.patch('src.f451_sensehat.sensehat.SenseHat.display_blank')
    testDev.display_blank()
    testDev.display_blank.assert_called_once()


@pytest.mark.skip(reason='Is it worth testing?')
def test_display_reset_mock(device_config, mocker):
    pass


@pytest.mark.skip(reason='TO DO')
def test_display_sparkle_mock(device_config, mocker):
    pass


@pytest.mark.skip(reason='TO DO')
def test_display_as_graph_mock(device_config, mocker):
    pass


@pytest.mark.skip(reason='TO DO')
def test_display_as_text_mock(device_config, mocker):
    pass


@pytest.mark.skip(reason='TO DO')
def test_display_progress_mock(device_config, mocker):
    pass
