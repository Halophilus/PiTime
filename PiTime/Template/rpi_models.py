import os
import random
import time
import pygame
import threading
# import gpiozero

class Buzzer: # active piezoelectric buzzer for droning alarm sound
    def __init__(self, pin):
        '''
        Initializes Buzzer object
        Utilizes gpiozero driver for an active piezoelectric buzzer to add a beeping sound to the alarm
        Utilizes threading to permit background control and a lock for thread safety
        '''
        self.buzzer = pin
        print(f"BUZZER DECLARED AT PIN {pin}")
        self.buzzing = False
        self.thread = None
        self.lock = threading.Lock()

    def start(self):
        with self.lock:
            try:
                if not self.buzzing:
                    self.buzzing = True
                    self.thread = threading.Thread(target=self.buzz) # Opens buzz function in its own thread
                    self.thread.start()
            except Exception as e:
                print(f"Error in Buzzer start method: {e}")

    def stop(self):
        with self.lock:
            try:
                if self.buzzing:
                    self.buzzing = False
                    self.thread.join() # Terminates all current threads related to this object
                    # self.buzzer.off()
            except Exception as e:
                print(f"Error in Buzzer stop method: {e}")

    def buzz(self):
        while self.buzzing:
            print("BUZZING ON") #buzzer.on()
            time.sleep(1)
            print("BUZZING OFF") #buzzer.off()
            time.sleep(1.5)

class Vibration: # 5V vibration module driven by a transistor and 3.3V logic
    def __init__(self, pin):
        '''
        Initializes the Vibration object
        Sets up a gpiozero LED instance that triggers a high power mosfet to activate a 5V ERM vibration motor
        Utilizes threading to permit background control and a lock for thread safety
        '''
        self.vibration = pin #gpiozero.LED(pin)
        print(f"VIBRATION DECLARED AT PIN {pin}")
        self.vibrating = False
        self.thread = None
        self.lock = threading.Lock()

    def start(self):
        '''
        Starts vibration sequence, self.vibrate in its own thread
        Initializes thread then starts function
        '''
        with self.lock:
            try:
                if not self.vibrating:
                    self.vibrating = True
                    self.thread = threading.Thread(target=self.vibrate)
                    self.thread.start()
            except Exception as e:
                print(f"Error in Vibration start method: {e}")
    def stop(self):
        '''
        Stops vibration sequence
        Closes thread and takes down vibrating flag
        '''
        with self.lock:
            try:
                if self.vibrating:
                    self.vibrating = False
                    self.thread.join()
                    # self.vibration.off()
            except Exception as e:
                print(f"Error in Vibration.stop method: {e}")

    def vibrate(self):
        '''
        Controls gpiozero driver, turning vibration motor on and off as long as self.vibrating is True
        '''
        while self.vibrating:
            print("VIBRATING") #vibration.on()
            time.sleep(1)
            print("NOT VIBRATING") #vibration.off()
            time.sleep(1.5)

class Speaker:
    def __init__(self, urgency='None'):
        """
        Initializes the Speaker object.

        Args:
        urgency (str): The urgency level for which to select a random alarm.
        """
        pygame.mixer.init()
        self.playing = False
        self.urgency = urgency
        self.thread = None
        self.lock = threading.Lock()

    def start(self):
        """
        Starts playing a random alarm from the specified urgency level.
        """
        with self.lock:
            if self.urgency != 'None':
                if not self.playing:
                    try:
                        self.playing = True
                        self.thread = threading.Thread(target=self.play_loop)
                        self.thread.start()
                    except Exception as e:
                        print(f"Error in Speaker.start: {e}")

    def play_loop(self):
        """
        Plays the selected alarm sound in a loop.
        """
        try:
            alarm_file = self.select_random_alarm()
            print(alarm_file)
            if alarm_file:
                self.sound = pygame.mixer.Sound(alarm_file)
                while self.playing:
                    self.sound.play()
                    start_time = time.time() # Rounds up quantity into one-second counts 
                    while time.time() - start_time < self.sound.get_length(): # For every tenth of a second in the rounded duration
                        time.sleep(0.1)
                        if not self.playing:
                            break 
        except Exception as e:
            print(f"Error in Speaker.play_loop: {e}")

    def stop(self):
        """
        Stops the currently playing sound.
        """
        try:
            with self.lock:
                self.sound.stop()
                self.playing = False
                if self.thread:
                    self.thread.join()
        except Exception as e:
            print(f"Error in Speaker.stop: {e}")

    def select_random_alarm(self):
        """
        Selects a random alarm file from the urgency directory.

        Returns:
        str: The path to the selected alarm file.
        """
        try:
            script_directory = os.path.dirname(os.path.abspath(__file__))
            alarm_dir = os.path.join(script_directory, 'alarms', self.urgency)
            if os.path.isdir(alarm_dir):
                alarm_files = os.listdir(alarm_dir)
                if alarm_files:
                    return os.path.join(alarm_dir, random.choice(alarm_files))
            return None
        except Exception as e:
            print(f"Error in Speaker.select_random_alarm: {e}")
