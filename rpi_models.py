import os, random, time, pygame, threading
from gpiozero import LED, Buzzer as GPIOBuzzer

class Buzzer: # active piezoelectric buzzer for droning alarm sound
    def __init__(self):
        '''
        Initializes Buzzer object
            Utilizes gpiozero driver for an active piezoelectric buzzer to add a beeping sound to the alarm
            Utilizes threading to permit background control and a lock for thread safety
        Args:
            pin (int), GPIO pin number assigned to the vibration module        
        '''
        self.buzzer = GPIOBuzzer(17)
        self.buzzing = False
        self.thread = None
        self.lock = threading.Lock()

    def start(self):
        '''
        Starts buzzing sequence, self.buzz in its own thread
            Initializes thread then starts self.vibrate function
        '''
        with self.lock:
            try:
                if not self.buzzing:
                    self.buzzing = True
                    self.thread = threading.Thread(target=self.buzz) # Opens buzz function in its own thread
                    self.thread.start()
            except Exception as ex:
                print(f"Error in Buzzer start method: {ex}")

    def stop(self):
        '''
        Stops buzzing sequence
            Closes thread and takes down buzzing flag
        '''        
        with self.lock:
            try:
                if self.buzzing:
                    self.buzzing = False
                    self.buzzer.off()
                    self.thread.join() # Terminates all current threads related to this object
            except Exception as ex:
                print(f"Error in Buzzer stop method: {ex}")

    def buzz(self):
        while self.buzzing:
            self.buzzer.on()
            # print("BUZZING ON")
            time.sleep(1)
            self.buzzer.off()
            # print("BUZZING OFF")
            time.sleep(1.5)

class Vibration: # 5V vibration module driven by a transistor and 3.3V logic
    def __init__(self):
        '''
        Initializes the Vibration object
            Sets up a gpiozero LED instance that triggers a high power mosfet to activate a 5V ERM vibration motor
            Utilizes threading to permit background control and a lock for thread safety
        Args:
            pin (int), GPIO pin number assigned to the vibration module
        '''
        self.vibration = LED(25)
        self.vibrating = False
        self.thread = None
        self.lock = threading.Lock()

    def start(self):
        '''
        Starts vibration sequence, self.vibrate in its own thread
            Initializes thread then starts self.vibrate function
        '''
        with self.lock:
            try:
                if not self.vibrating:
                    self.vibrating = True
                    self.thread = threading.Thread(target=self.vibrate)
                    self.thread.start()
            except Exception as ex:
                print(f"Error in Vibration start method: {ex}")

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
                    self.vibration.off()
            except Exception as ex:
                print(f"Error in Vibration.stop method: {ex}")

    def vibrate(self):
        '''
        Controls gpiozero driver, turning vibration motor on and off as long as self.vibrating is True
        '''
        while self.vibrating:
            self.vibration.on()
            # print("VIBRATING ON")
            time.sleep(1)
            self.vibration.off()
            # print("VIBRATING OFF")
            time.sleep(1.5)

class Speaker:
    def __init__(self, urgency='None'):
        """
        Initializes the Speaker object. Originally used Sound object but switched to music for mp3 compatibility
        Args:
            urgency (str): The urgency level for which to select a random alarm, the default of which is None.
        """
        pygame.mixer.init()
        self.playing = False
        self.urgency = urgency
        self.thread = None
        self.lock = threading.Lock()

    def start(self):
        """
        Starts playing a random alarm from the specified urgency level.
        Initializes thread and sets self.playing flag to True.
        """
        with self.lock:
            if self.urgency != 'None':
                if not self.playing:
                    try:
                        self.playing = True
                        self.thread = threading.Thread(target=self.play_loop)
                        self.thread.start()
                    except Exception as ex:
                        print(f"Error in Speaker.start: {ex}")

    def play_loop(self):
        """
        Plays the selected alarm sound in a loop.
        Can be disengaged at any time within a 0.1 second interval if the call to close the thread is made.
        """
        try:
            alarm_file = self.select_random_alarm()
            print(f"\n\n\n ATTEMPTING TO PLAY: {alarm_file} \n\n\n")
            if alarm_file:
                pygame.mixer.music.load(alarm_file)
                pygame.mixer.music.play(-1)  # Set the number of repeats to -1 for indefinite looping
        except Exception as ex:
            print(f"Error in Speaker.play_loop: {ex}")

    def stop(self):
        """
        Stops the currently playing sound.
        Closes thread and takes down self.playing flag.
        """
        try:
            with self.lock:
                if self.playing:
                    print("\n\n\n HALTING PLAYBACK \n\n\n")
                    pygame.mixer.music.stop()
                    self.playing = False
                    if self.thread:
                        self.thread.join()
        except Exception as ex:
            print(f"Error in Speaker.stop: {ex}")

    def select_random_alarm(self):
        """
        Selects a random alarm file from the directory associated with the alarm's urgency.

        Returns:
            str: The path to the selected alarm file, or None if no valid alarm is found.
        """
        try:
            script_directory = os.path.dirname(os.path.abspath(__file__))
            alarm_dir = os.path.join(script_directory, 'alarms', self.urgency)
            print(f"\n\n\nFolder for {self.urgency} playback selected: {alarm_dir}\n\n\n")
            if os.path.isdir(alarm_dir):
                alarm_files = os.listdir(alarm_dir)
                if alarm_files:
                    print(f"\n\n\nRETURNING ALARM PATH: {os.path.join(alarm_dir, random.choice(alarm_files))}\n\n\n")
                    return os.path.join(alarm_dir, random.choice(alarm_files))
            
            return None
        except Exception as ex:
            print(f"Error in Speaker.select_random_alarm: {ex}")
    
    def update_urgency(self, new_urgency):
        """
        Updates the urgency and starts playing the new audio.
        """
        self.stop()
        self.urgency = new_urgency
        self.start()


