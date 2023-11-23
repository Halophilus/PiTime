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
                    # self.buzzer.off()
            except Exception as e:
                print(f"Error in Vibration stop method: {e}")

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
    def __init__(self):
        """
        Initializes the Speaker object.

        Sets up the pygame mixer for sound playback, initializes instance variables for tracking
        the state of sound playback, and prepares a lock for thread safety.
        """
        pygame.mixer.init()
        self.playing = False
        self.alarm_file = None
        self.sound = None
        self.current_urgency = 'None'
        self.thread = None
        self.lock = threading.Lock() #
        self.urgency_rating = {'None':0, 
                               'Not at all':1,
                               'Somewhat':2,
                               'Urgent':3,
                               'Very':4,
                               'Extremely':5}

    
    def start(self, urgency_set):
        """
        Starts playing an alarm based on the maximum urgency level in the given set.
        
        If a higher urgency alarm needs to be played, it stops the current alarm and starts the new one.
        If no alarm is currently playing, selects and starts an alarm based on the current urgency.
        
        Args:
        urgency_set (set): A set of urgency levels (str) from the current alarms.
        """
        with self.lock:
            try: 
                initial_urgency = revised_urgency = self.current_urgency # Record current urgency and set initial revised urgency in case urgency doesn't change
                for level in urgency_set: # For every original urgency in the passed set
                    if self.urgency_rating[level] > self.urgency_rating[self.current_urgency]: # If one of the values is more urgent than the object's current urgency
                        self.current_urgency = revised_urgency = level # Reset the current urgency and record this new level
                    if self.playing and revised_urgency != initial_urgency: # If there is a sound already playing but there is a new urgency being introduced
                        self.stop() # Stop playing
                        self.current_urgency = revised_urgency # Re-introduce revised urgency for new instance of play_loop  
                    if not self.playing: # If there is currently no sound playing
                        if self.current_urgency != 'None': # As long as some alarm is being requested
                            script_directory = os.path.dirname(os.path.abspath(__file__)) # fetches current working directory
                            alarm_selections_file_path = os.path.join(script_directory, 'alarms', self.current_urgency) # builds a relative path
                            try:
                                # Test if the directory exists and there are files within the directory
                                if os.path.isdir(alarm_selections_file_path) and os.listdir(alarm_selections_file_path):
                                    self.alarm_file = os.path.join(alarm_selections_file_path, random.choice(os.listdir(alarm_selections_file_path))) # Summons random selection from urgency designation
                                    self.sound = pygame.mixer.Sound(self.alarm_file)
                                    self.playing = True # Flags object as currently playing 
                                    self.thread = threading.Thread(target=self.play_loop)
                                    self.thread.start()
                                else:
                                    print(f"No alarm files found in {alarm_selections_file_path}")
                            except Exception as e:
                                print(f"An error occurred while accessing this alarm file, {e}")
            except pygame.error as e:
                print(f"Error occurred with Pygame instance: {e}")
            except RuntimeError as e:
                print(f"Runtime error in threading: {e}")
            except IOError as e:
                print(f"I/O error: {e}")
            except Exception as e:
                print(f"An unexpected error occurred in stop method: {e}")

    def play_loop(self):
        """
        Plays the selected alarm sound in a loop.

        Continuously plays the sound until the 'playing' flag is set to False. This method is 
        intended to be run in a separate thread.
        """
        while self.playing:
            try:
                self.sound.play()
                start_time = time.time() # Rounds up quantity into one-second counts 
                while time.time() - start_time < self.sound.get_length(): # For every tenth of a second in the rounded duration
                    time.sleep(0.1)
                    if not self.playing:
                        break # Breaks loop for abrupt termination
            except Exception as e:

        
    def stop(self):
        """
        Stops the currently playing sound and resets the state.

        If a sound is playing, it stops the sound and joins the thread running the play loop.
        Resets the alarm file, sound object, and current urgency to their initial states.
        """
        with self.lock:
            try:
                if self.playing:
                    self.sound.stop()  # Stop the sound if it's playing
                    self.playing = False
                    self.alarm_file = None
                    self.sound = None
                    self.current_urgency = 'None'
                    if self.thread is not None: # If there is a current thread
                        self.thread.join()  # Wait for the thread to finish            
            except pygame.error as e:
                print(f"Pygame error occurred: {e}")
            except RuntimeError as e:
                print(f"Runtime error in threading: {e}")
            except IOError as e:
                print(f"I/O error: {e}")
            except Exception as e:
                print(f"An unexpected error occurred in stop method: {e}")
