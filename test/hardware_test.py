from gpiozero import LED, Buzzer
from time import sleep

# Initialize the LED and buzzer
vibration = LED(25)
buzzer = LED(5)

try:
    while True:
        vibration.on()
        
        sleep(1)
        vibration.off()
        buzzer.on()
        
        sleep(1)
        buzzer.off()
        vibration.on()

        sleep(1)
        vibration.off()
        buzzer.on()
        sleep(1)
        buzzer.off()
        sleep(5)

except KeyboardInterrupt:
    # Clean up the GPIOs on Ctrl+C exit
    vibration.close()
    buzzer.close()
