import os
import sys
import time
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to working directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from rpi_models import Buzzer, Vibration, Speaker

# Testing with gpiozero implementation
class TestAlarmSystem(unittest.TestCase):

    @patch('rpi_models.gpiozero.Buzzer')
    def test_buzzer(self, MockBuzzer):
        mock_buzzer = MockBuzzer.return_value
        buzzer = Buzzer(pin=17)
        buzzer.start()
        self.assertTrue(buzzer.buzzing)
        self.assertIsNotNone(buzzer.thread)
        buzzer.stop()
        self.assertFalse(buzzer.buzzing)
        self.assertTrue(mock_buzzer.on.called)
        self.assertTrue(mock_buzzer.off.called)

    @patch('rpi_models.gpiozero.LED')
    def test_vibration(self, MockLED):
        mock_vibration = MockLED.return_value
        vibration = Vibration(pin=18)
        vibration.start()
        self.assertTrue(vibration.vibrating)
        self.assertIsNotNone(vibration.thread)
        vibration.stop()
        self.assertFalse(vibration.vibrating)
        self.assertTrue(mock_vibration.on.called)
        self.assertTrue(mock_vibration.off.called)

    @patch('rpi_models.pygame.mixer.Sound')
    def test_speaker(self, MockSound):
        mock_sound = MockSound.return_value
        mock_sound.get_length.return_value = 5
        speaker = Speaker()
        speaker.start({'Urgent'})
        self.assertTrue(speaker.playing)
        self.assertIsNotNone(speaker.thread)
        speaker.stop()
        self.assertFalse(speaker.playing)
        self.assertTrue(mock_sound.play.called)
        self.assertTrue(mock_sound.stop.called)


# The following are in-house tests of the general logic behavior of each 
def buzzer_test():
    test_buzzer = Buzzer(23)
    test_buzzer.start()
    print("Intermittent function #1")
    time.sleep(2)
    print("Intermittent function #2")
    time.sleep(2)
    print("Turning off")
    test_buzzer.stop()

def vibration_test():
    test_vibration = Vibration(24)
    test_vibration.start()
    print("Intermittent function #1")
    time.sleep(2)
    print("Intermittent function #2")
    time.sleep(2)
    print("Turning off")
    test_vibration.stop()

def test_simple_speaker():
    '''
        Testing generation 5 of the Speaker class
        I originally went through several other iterations of this class of varying complexity
        I encountered a series of threading issues, as well as weird behavior from Pygame
        This version radically simplified the functions for this class, while retaining the random alarm choice functionality I originally wanted to implement
        Logic for when this is called is offloaded onto the rpi_main script
    '''
    x = input("Enter the amount of time to let the audio play: ")
    speaker = Speaker('Urgent')
    speaker.start()
    time.sleep(1)
    print("intermittent function start")
    time.sleep(x)  # Let the v alarm play for x seconds
    print("intermittent function end")
    time.sleep(1)
    speaker.stop()



if __name__ == '__main__':
    test
    # unittest.main()
