#!/usr/bin/env python3
"""Demo application showcasing the f451 Labs SenseHat module.

This application is designed to demo core features of the CLI UI library. It simulates
'sensor' data by generating random values and then displaying them in the terminal.

To launch this application from terminal:

    $ python -m sh_demo

It's also possible to install this package via 'pip' from Github and one can then launch 
this application as follows:

    $ sh_demo

NOTE: This application will NOT upload any data to the cloud.

NOTE: This application requires a physical Raspberry Pi Sense HAT add-on.

NOTE: This application depends on the 'f451-common' library

TODO:
    - add more 8x8 images
    - add more demo data feeds
"""

import time
import sys
import asyncio
import contextlib
import platform

from datetime import datetime
from pathlib import Path

from . import sh_constants as const
from . import sh_demo_data as f451DemoData

# import f451_common.cli_ui as f451CLIUI
import f451_common.common as f451Common
import f451_common.logger as f451Logger

import f451_sensehat.sensehat as f451SenseHat

from rich.console import Console

# from Adafruit_IO import RequestError, ThrottlingError

# Install Rich 'traceback' and 'pprint' to
# make (debug) life is easier. Trust me!
from rich.pretty import pprint
from rich.traceback import install as install_rich_traceback

install_rich_traceback(show_locals=True)


# fmt: off
# =========================================================
#          G L O B A L S   A N D   H E L P E R S
# =========================================================
APP_VERSION = '1.0.0'
APP_NAME = 'f451 Labs - SenseHat Demo'
APP_NAME_SHORT = 'SH Demo'
APP_LOG = 'f451-sensehat-demo.log'  # Individual logs for devices with multiple apps
APP_SETTINGS = 'sh_demo_settings.toml' # Standard for all f451 Labs projects

APP_MIN_SENSOR_READ_WAIT = 1        # Min wait in sec between sensor reads
APP_MIN_PROG_WAIT = 1               # Remaining min (loop) wait time to display prog bar
APP_WAIT_1SEC = 1
APP_MAX_DATA = 120                  # Max number of data points in the queue
APP_DELTA_FACTOR = 0.02             # Any change within X% is considered negligable

APP_DATA_TYPES = ['number1', 'number2']

APP_DISPLAY_MODES = {
    f451SenseHat.KWD_DISPLAY_MIN: const.MIN_DISPL,
    f451SenseHat.KWD_DISPLAY_MAX: 2,
}

class AppRT(f451Common.Runtime):
    def __init__(self, appName, appVersion, appNameShort=None, appLog=None, appSettings=None):
        super().__init__(
            appName, 
            appVersion, 
            appNameShort, 
            appLog, 
            appSettings,
            platform.node(),        # Get device 'hostname'
            Path(__file__).parent   # Find dir for this app
        )
        
    def init_runtime(self, cliArgs, data):
        """Initialize the 'runtime' variable
        
        We use an object to hold all core runtime values, flags, etc. 
        This makes it easier to send global values around the app as
        a single entitye rather than having to manage a series of 
        individual (global) values.

        Args:
            cliArgs: holds user-supplied values from ArgParse
            data: general data set (used to create CLI UI table rows, etc.)
        """
        # Load settings and initialize logger
        self.config = f451Common.load_settings(self.appDir.joinpath(self.appSettings))
        self.logger = f451Logger.Logger(self.config, LOGFILE=self.appLog)

        self.ioFreq = self.config.get(const.KWD_FREQ, const.DEF_FREQ)
        self.ioDelay = self.config.get(const.KWD_DELAY, const.DEF_DELAY)
        self.ioWait = max(self.config.get(const.KWD_WAIT, const.DEF_WAIT), APP_MIN_SENSOR_READ_WAIT)
        self.ioThrottle = self.config.get(const.KWD_THROTTLE, const.DEF_THROTTLE)
        self.ioRounding = self.config.get(const.KWD_ROUNDING, const.DEF_ROUNDING)
        self.ioUploadAndExit = False

        # Update log file or level?
        if cliArgs.debug:
            self.logLvl = f451Logger.LOG_DEBUG
            self.debugMode = True
        else:
            self.logLvl = self.config.get(f451Logger.KWD_LOG_LEVEL, f451Logger.LOG_NOTSET)
            self.debugMode = (self.logLvl == f451Logger.LOG_DEBUG)

        self.logger.set_log_level(self.logLvl)

        if cliArgs.log is not None:
            self.logger.set_log_file(appRT.logLvl, cliArgs.log)

        # Initialize various counters, etc.
        self.timeSinceUpdate = float(0)
        self.timeUpdate = time.time()
        self.displayUpdate = self.timeUpdate
        self.uploadDelay = self.ioDelay
        self.maxUploads = int(cliArgs.uploads)
        self.numUploads = 0
        self.loopWait = APP_WAIT_1SEC   # Wait time between main loop cycles

        # Initialize UI for terminal
        self.console = Console() # type: ignore

    def debug(self, cli=None, data=None):
        """Print/log some basic debug info.
        
        Args:
            cli: CLI args
            data: app data
        """

        self.console.rule('Config Settings', style='grey', align='center')

        self.logger.log_debug(f"DISPL ROT:   {self.sensors['SenseHat'].displRotation}")
        self.logger.log_debug(f"DISPL MODE:  {self.sensors['SenseHat'].displMode}")
        self.logger.log_debug(f"DISPL PROGR: {self.sensors['SenseHat'].displProgress}")
        self.logger.log_debug(f"SLEEP TIME:  {self.sensors['SenseHat'].displSleepTime}")
        self.logger.log_debug(f"SLEEP MODE:  {self.sensors['SenseHat'].displSleepMode}")

        self.logger.log_debug(f'IO DEL:      {self.ioDelay}')
        self.logger.log_debug(f'IO WAIT:     {self.ioWait}')
        self.logger.log_debug(f'IO THROTTLE: {self.ioThrottle}')

        # Display Raspberry Pi serial and Wi-Fi status
        self.logger.log_debug(f'Raspberry Pi serial: {f451Common.get_RPI_serial_num()}')
        self.logger.log_debug(
            f'Wi-Fi: {(f451Common.STATUS_YES if f451Common.check_wifi() else f451Common.STATUS_UNKNOWN)}'
        )

        # List CLI args
        if cli:
            for key, val in vars(cli).items():
                self.logger.log_debug(f"CLI Arg '{key}': {val}")

        # List config settings
        self.console.rule('CONFIG', style='grey', align='center')  # type: ignore
        pprint(self.config, expand_all=True)

        if data:
            self.console.rule('APP DATA', style='grey', align='center')  # type: ignore
            pprint(data.as_dict(), expand_all=True)

        # Display nice border below everything
        self.console.rule(style='grey', align='center')  # type: ignore

    def show_summary(self, cli=None, data=None):
        """Display summary info
        
        We (usually) call this method to display summary info
        at the before we exit the application.

        Args:
            cli: CLI args
            data: app data
        """
        print()
        self.console.rule(f'{self.appName} (v{self.appVersion})', style='grey', align='center')  # type: ignore
        print(f'Work start:  {self.workStart:%a %b %-d, %Y at %-I:%M:%S %p}')
        print(f'Work end:    {(datetime.now()):%a %b %-d, %Y at %-I:%M:%S %p}')
        print(f'Num uploads: {self.numUploads}')

        # Show config info, etc. if in 'debug' mode
        if self.debugMode:
            self.debug(cli, data)

    def add_sensor(self, sensorName, sensorType):
        self.sensors[sensorName] = sensorType(self.config)
        return self.sensors[sensorName]

    def update_action(self, cliUI, msg=None):
        """Wrapper to help streamline code"""
        if cliUI:
            self.console.update_action(msg) # type: ignore

    def update_progress(self, cliUI, prog=None, msg=None):
        """Wrapper to help streamline code"""
        if cliUI:
            self.console.update_progress(prog, msg) # type: ignore        

    def update_upload_status(self, cliUI, lastTime, lastStatus):
        """Wrapper to help streamline code"""
        if cliUI:
            self.console.update_upload_status(      # type: ignore
                lastTime, 
                lastStatus, 
                lastTime + self.uploadDelay, 
                self.numUploads, 
                self.maxUploads
            )

    def update_data(self, cliUI, data):
        """Wrapper to help streamline code"""
        if cliUI:
            self.console.update_data(data) # type: ignore


# Define app runtime object and basic data unit
appRT = AppRT(APP_NAME, APP_VERSION, APP_NAME_SHORT, APP_LOG, APP_SETTINGS)


# =========================================================
#              H E L P E R   F U N C T I O N S
# =========================================================
async def send_data(*args):
    """Fake 'send' function"""
    print('Fake upload start ...')
    time.sleep(5)
    print('... fake upload end')


async def upload_demo_data(*args, **kwargs):
    """Fake upload function

    This helper function simulates parsing and uploading data
    to some cloud service.

    Args:
        args:
            User can provide single 'dict' with data
        kwargs:
            User can provide individual data points as key-value pairs
    """
    # We combine 'args' and 'kwargs' to allow users to provide a 'dict' with
    # all data points and/or individual data points (which could override
    # values in the 'dict').
    upload = {**args[0], **kwargs} if args and isinstance(args[0], dict) else kwargs

    sendQ = []

    # Send download speed data ?
    if upload.get('data') is not None:
        sendQ.append(send_data(upload.get('data')))  # type: ignore

    # deviceID = appRT.sensors['SenseHat'].get_ID(DEF_ID_PREFIX)

    await asyncio.gather(*sendQ)


def btn_up(event):
    """SenseHat Joystick UP event

    Rotate display by -90 degrees and reset screen blanking
    """
    global appRT

    if event.action != f451SenseHat.BTN_RELEASE:
        appRT.sensors['SenseHat'].display_rotate(-1)
        appRT.displayUpdate = time.time()


def btn_down(event):
    """SenseHat Joystick DOWN event

    Rotate display by +90 degrees and reset screen blanking
    """
    global appRT

    if event.action != f451SenseHat.BTN_RELEASE:
        appRT.sensors['SenseHat'].display_rotate(1)
        appRT.displayUpdate = time.time()


def btn_left(event):
    """SenseHat Joystick LEFT event

    Switch display mode by 1 mode and reset screen blanking
    """
    global appRT

    if event.action != f451SenseHat.BTN_RELEASE:
        appRT.sensors['SenseHat'].update_display_mode(-1)
        appRT.displayUpdate = time.time()


def btn_right(event):
    """SenseHat Joystick RIGHT event

    Switch display mode by 1 mode and reset screen blanking
    """
    global appRT

    if event.action != f451SenseHat.BTN_RELEASE:
        appRT.sensors['SenseHat'].update_display_mode(1)
        appRT.displayUpdate = time.time()


def btn_middle(event):
    """SenseHat Joystick MIDDLE (down) event

    Turn display on/off
    """
    global appRT

    if event.action != f451SenseHat.BTN_RELEASE:
        # Wake up?
        if appRT.sensors['SenseHat'].displSleepMode:
            appRT.sensors['SenseHat'].update_sleep_mode(False)
            appRT.displayUpdate = time.time()
        else:
            appRT.sensors['SenseHat'].update_sleep_mode(True)


APP_JOYSTICK_ACTIONS = {
    f451SenseHat.KWD_BTN_UP: btn_up,
    f451SenseHat.KWD_BTN_DWN: btn_down,
    f451SenseHat.KWD_BTN_LFT: btn_left,
    f451SenseHat.KWD_BTN_RHT: btn_right,
    f451SenseHat.KWD_BTN_MDL: btn_middle,
}


def update_SenseHat_LED(sense, data, colors=None):
    """Update Sense HAT LED display depending on display mode

    We check current display mode and then prep data as needed
    for display on LED.

    Args:
        sense: hook to SenseHat object
        data: full data set where we'll grab a slice from the end
        colors: (optional) custom color map
    """

    def _minMax(data):
        """Create min/max based on all collecxted data

        This will smooth out some hard edges that may occur
        when the data slice is to short.
        """
        scrubbed = [i for i in data if i is not None]
        return (min(scrubbed), max(scrubbed)) if scrubbed else (0, 0)

    def _get_color_map(data, colors=None):
        return f451Common.get_tri_colors(colors, True) if all(data.limits) else None

    # Check display mode. Each mode corresponds to a data type
    if sense.displMode == 1:
        minMax = _minMax(data.number1.as_tuple().data)
        dataClean = f451SenseHat.prep_data(data.number1.as_tuple())
        colorMap = _get_color_map(dataClean, colors)
        sense.display_as_graph(dataClean, minMax, colorMap)

    elif sense.displMode == 2:
        minMax = _minMax(data.number2.as_tuple().data)
        dataClean = f451SenseHat.prep_data(data.number2.as_tuple())
        colorMap = _get_color_map(dataClean, colors)
        sense.display_as_graph(dataClean, minMax, colorMap)

    else:  # Display sparkles
        sense.display_sparkle()


def init_cli_parser(appName, appVersion, setDefaults=True):
    """Initialize CLI (ArgParse) parser.

    Initialize the ArgParse parser with CLI 'arguments'
    and return new parser instance.

    Args:
        appName: 'str' with app name
        appVersion: 'str' with app version
        setDefaults: 'bool' flag indicates whether to set up default CLI args

    Returns:
        ArgParse parser instance
    """
    # fmt: off
    parser = f451Common.init_cli_parser(appName, appVersion, setDefaults)

    # Add app-specific CLI args
    parser.add_argument(
        '--noLED',
        action='store_true',
        default=False,
        help='do not display output on LED',
    )
    parser.add_argument(
        '--progress',
        action='store_true',
        default=False,
        help='show upload progress bar on LED',
    )
    parser.add_argument(
        '--uploads',
        action='store',
        type=int,
        default=-1,
        help='number of uploads before exiting',
    )

    return parser
    # fmt: on


def collect_data(app, data, timeCurrent):
    """Collect data from sensors.
    
    This is core of the application where we collect data from 
    one or more sensors, and then upload the data as needed.

    Args:
        app: application runtime object with config, counters, etc.
        data: main application data queue
        timeCurrent: time stamp from when loop started

    Returns:
        'bool' if 'True' then we're done with all loops and we can exit app
    """
    exitApp = False

    # --- Get magic data ---
    #
    newData = app.sensors['FakeSensor'].get_demo_data()
    #
    # ----------------------

    # Is it time to upload data?
    if app.timeSinceUpdate >= app.uploadDelay:
        try:
            asyncio.run(
                upload_demo_data(
                    data=newData.number1,
                    deviceID=f451Common.get_RPI_ID(f451Common.DEF_ID_PREFIX),
                )
            )

        except KeyboardInterrupt:
            exitApp = True

        else:
            # Reset 'uploadDelay' back to normal 'ioFreq' on successful upload
            app.numUploads += 1
            app.uploadDelay = app.ioFreq
            exitApp = exitApp or app.ioUploadAndExit
            app.logger.log_info(
                f'Uploaded: Magic #: {round(newData.number1, app.ioRounding)}'
            )

        finally:
            app.timeUpdate = timeCurrent
            exitApp = (app.maxUploads > 0) and (app.numUploads >= app.maxUploads)

    # Update data set and display to terminal as needed
    data.number1.data.append(newData.number1)
    data.number2.data.append(newData.number2)

    update_SenseHat_LED(app.sensors['SenseHat'], data)

    return exitApp


def main_loop(app, data):
    """Main application loop.

    This is where most of the action happens. We continously collect
    data from our sensors, process it, display it, and upload it at
    certain intervals.

    Args:
        app: application runtime object with config, counters, etc.
        data: main application data queue
    """
    # Set 'wait' counter 'exit' flag and start the loop!
    exitApp = False
    waitForSensor = 0

    while not exitApp:
        try:
            # fmt: off
            timeCurrent = time.time()
            app.timeSinceUpdate = timeCurrent - app.timeUpdate
            app.sensors['SenseHat'].update_sleep_mode(
                (timeCurrent - app.displayUpdate) > app.sensors['SenseHat'].displSleepTime, # Time to sleep?
                # cliArgs.noLED,                                                            # Force no LED?
                app.sensors['SenseHat'].displSleepMode                                      # Already asleep?
            )
            # fmt: on

            # Update Sense HAT prog bar as needed
            app.sensors['SenseHat'].display_progress(app.timeSinceUpdate / app.uploadDelay)

            # Do we need to wait for next sensor read? Or can 
            # we collect more 'specimen'? :-P
            if waitForSensor <= 0:
                exitApp = collect_data(app, data, timeCurrent)
                waitForSensor = max(app.ioWait, APP_MIN_PROG_WAIT)

        except KeyboardInterrupt:
            exitApp = True

        # Are we done?
        if not exitApp:
            time.sleep(app.loopWait)
            waitForSensor -= app.loopWait


# =========================================================
#      M A I N   F U N C T I O N    /   A C T I O N S
# =========================================================
def main(cliArgs=None):  # sourcery skip: extract-method
    """Main function.

    This function will goes through the setup and then runs the
    main application loop.

    NOTE:
     -  Application will exit with error level 1 if invalid Adafruit IO
        or Arduino Cloud feeds are provided

     -  Application will exit with error level 0 if either no arguments
        are entered via CLI, or if arguments '-V' or '--version' are used.
        No data will be uploaded will be sent in that case.

    Args:
        cliArgs:
            CLI arguments used to start application
    """
    global appRT

    # Parse CLI args and show 'help' and exit if no args
    cli = init_cli_parser(APP_NAME, APP_VERSION, True)
    cliArgs, _ = cli.parse_known_args(cliArgs)
    if not cliArgs and len(sys.argv) == 1:
        cli.print_help(sys.stdout)
        sys.exit(0)

    if cliArgs.version:
        print(f'{APP_NAME} (v{APP_VERSION})')
        sys.exit(0)

    # Get core settings and initialize core data queue
    appData = f451DemoData.DemoData(None, APP_MAX_DATA)
    appRT.init_runtime(cliArgs, appData)

    try:
        # Initialize device instance which includes all sensors
        # and LED display on Sense HAT. Also initialize joystick
        # events and set 'sleep' and 'display' modes.
        appRT.add_sensor('SenseHat', f451SenseHat.SenseHat)
        appRT.sensors['SenseHat'].joystick_init(**APP_JOYSTICK_ACTIONS)
        appRT.sensors['SenseHat'].display_init(**APP_DISPLAY_MODES)
        appRT.sensors['SenseHat'].update_sleep_mode(cliArgs.noLED)
        appRT.sensors['SenseHat'].displProgress = cliArgs.progress
        appRT.sensors['SenseHat'].display_message(APP_NAME)

        # Add fake sensor
        appRT.add_sensor('FakeSensor', f451Common.FakeSensor)

    except KeyboardInterrupt:
        print(f'{APP_NAME} (v{APP_VERSION}) - Session terminated by user')
        sys.exit(0)

    # --- Main application loop ---
    #
    appRT.logger.log_info('-- START Data Logging --')

    with contextlib.suppress(KeyboardInterrupt):
        main_loop(appRT, appData)

    appRT.logger.log_info('-- END Data Logging --')
    #
    # -----------------------------

    # A bit of clean-up before we exit
    appRT.sensors['SenseHat'].display_reset()
    appRT.sensors['SenseHat'].display_off()

    # Show session summary
    appRT.show_summary(cliArgs, appData)


# =========================================================
#            G L O B A L   C A T C H - A L L
# =========================================================
if __name__ == '__main__':
    main()  # pragma: no cover
