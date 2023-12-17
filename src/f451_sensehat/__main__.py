"""Demo for using f451 Labs SenseHat Module."""

import time
import f451_sensehat.sensehat as f451SenseHat


# =========================================================
#          G L O B A L S   A N D   H E L P E R S
# =========================================================
# Initialize device instance which includes all sensors
# and LED display on Sense HAT
SENSE_HAT = f451SenseHat.SenseHat({'ROTATION': 0, 'DISPLAY': 0, 'PROGRESS': 0, 'SLEEP': 600})
EXIT_NOW = False

def btn_up(event):
    """SenseHat Joystick UP event"""
    if event.action != f451SenseHat.BTN_RELEASE:
        SENSE_HAT.display_rotate(-1)


def btn_down(event):
    """SenseHat Joystick DOWN event"""
    if event.action != f451SenseHat.BTN_RELEASE:
        SENSE_HAT.display_rotate(1)


def btn_left(event):
    """SenseHat Joystick LEFT event"""
    if event.action != f451SenseHat.BTN_RELEASE:
        SENSE_HAT.display_rotate(-1)


def btn_right(event):
    """SenseHat Joystick RIGHT event"""
    if event.action != f451SenseHat.BTN_RELEASE:
        SENSE_HAT.display_rotate(1)


def btn_middle(event):
    """SenseHat Joystick MIDDLE (down) event"""
    global EXIT_NOW

    if event.action != f451SenseHat.BTN_RELEASE:
        SENSE_HAT.display_blank()
        SENSE_HAT.display_off()
        EXIT_NOW = True


# Assign Sense Hat joystick event callbacks
APP_JOYSTICK_ACTIONS = {
    f451SenseHat.KWD_BTN_UP: btn_up,
    f451SenseHat.KWD_BTN_DWN: btn_down,
    f451SenseHat.KWD_BTN_LFT: btn_left,
    f451SenseHat.KWD_BTN_RHT: btn_right,
    f451SenseHat.KWD_BTN_MDL: btn_middle,
}
SENSE_HAT.joystick_init(**APP_JOYSTICK_ACTIONS)


def create_image():
    x = (255, 0, 0)         # Color: red
    o = (255, 255, 255)     # Color: white

    image = [
        o, o, o, x, x, o, o, o,
        o, o, x, o, o, x, o, o,
        o, o, o, o, o, x, o, o,
        o, o, o, o, x, o, o, o,
        o, o, o, x, o, o, o, o,
        o, o, o, x, o, o, o, o,
        o, o, o, o, o, o, o, o,
        o, o, o, x, o, o, o, o
    ]

    return image
    # sense = SenseHat()

    # sense.set_pixels(question_mark)

    # sense.set_pixel(0, 0, 255, 0, 0)
    # sense.set_pixel(0, 7, 0, 255, 0)
    # sense.set_pixel(7, 0, 0, 0, 255)
    # sense.set_pixel(7, 7, 255, 0, 255)

    # while True:
    #     for r in [0, 90, 180, 270]:
    #         sense.set_rotation(r)
    #         time.sleep(0.3)

# =========================================================
#                    D E M O   A P P
# =========================================================
def main():
    # Skip display demos if we're using fake HAT
    if not SENSE_HAT.is_fake():
        SENSE_HAT.display_init()

        # Display text on 8x8 LED
        SENSE_HAT.display_message("Hello world!")

        for _ in range(100):
            SENSE_HAT.display_sparkle()
            time.sleep(0.2)

        SENSE_HAT.display_blank()
        SENSE_HAT.display_off()

        SENSE_HAT.display_8x8_image(create_image())

        while not EXIT_NOW:
            pass

    else:
        print("\nSkipping LED demo since we don't have a real Sense HAT")

    # Get enviro data, even if it's fake
    tempRaw = round(SENSE_HAT.get_temperature(), 1)
    pressRaw = round(SENSE_HAT.get_pressure(), 1)
    humidRaw = round(SENSE_HAT.get_humidity(), 1)

    print("\n===== [Demo of f451 Labs Enviro+ Module] ======")
    print(f"TEMP:     {tempRaw} C")
    print(f"PRESSURE: {pressRaw} hPa")
    print(f"HUMIDITY: {humidRaw} %")
    # print("Beep boop!")
    print("=============== [End of Demo] =================\n")


if __name__ == '__main__':
    main()
