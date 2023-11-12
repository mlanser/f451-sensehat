"""Demo for using f451 Labs SenseHat Module."""

import time
from f451_sensehat.sensehat import SenseHat


# =========================================================
#                    D E M O   A P P
# =========================================================
def main():
    # Initialize device instance which includes all sensors
    # and LED display on Sense HAT
    sense = SenseHat({
        "ROTATION": 90,
        "DISPLAY": 0,
        "PROGRESS": 0,
        "SLEEP": 600    
    })

    # Skip display demos if we're using fake HAT
    if not sense.is_fake():
        sense.display_init()

        # Display text on LCD
        sense.display_message("Hello world!")

        for _ in range(100):
            sense.display_sparkle()
            time.sleep(0.2)

        sense.display_blank()
        sense.display_off()

    else:
        print("\nSkipping LED demo since we don't have a real Sense HAT")

    # Get enviro data, even if it's fake
    tempRaw = round(sense.get_temperature(), 1)
    pressRaw = round(sense.get_pressure(), 1)
    humidRaw = round(sense.get_humidity(), 1)

    print("\n===== [Demo of f451 Labs Enviro+ Module] ======")
    print(f"TEMP:     {tempRaw} C")
    print(f"PRESSURE: {pressRaw} hPa")
    print(f"HUMIDITY: {humidRaw} %")
    # print("Beep boop!")
    print("=============== [End of Demo] =================\n")


if __name__ == "__main__":
    main()