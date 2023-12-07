from gpiozero import LED, Buzzer
from I2C_LCD_driver import lcd
from time import sleep

# Initial hardware test passed
screen = lcd()
vibration = LED(25)
buzzer = Buzzer(17)

# Function to test displaying strings
def test_display_string():
    print("Testing: Display String")
    screen.lcd_display_string("Testing Line 1", 1)  # Display on line 1
    sleep(3)
    screen.lcd_display_string("Testing Line 2", 2)  # Display on line 2
    sleep(5)  # Wait 5 seconds to visually check the display

# Function to test clearing the display
def test_clear_display():
    print("Testing: Clear Display")
    screen.lcd_clear()
    sleep(3)  # Wait 3 seconds to visually check the display

# Function to test backlight on and off
def test_backlight():
    print("Testing: Backlight On and Off")
    
    # Turn on the backlight
    print("Backlight On")
    screen.backlight(1)
    sleep(5)  # Wait 5 seconds to visually check the backlight

    # Turn off the backlight
    print("Backlight Off")
    screen.backlight(0)
    sleep(5)  # Wait 5 seconds to visually check the backlight


try:
    while True:
        test_display_string()
        test_clear_display()
        test_backlight()
        '''
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
        '''
except KeyboardInterrupt:
    # Clean up the GPIOs on Ctrl+C exit
    vibration.close()
    buzzer.close()
