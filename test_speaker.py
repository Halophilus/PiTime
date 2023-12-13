import time, os, pygame, threading, random

class Speaker:
    def __init__(self, urgency='None'):
        """
        Initializes the Speaker object.
        Args
            urgency (str): The urgency level for which to select a random alarm, the default of which is None
        """
        pygame.mixer.init() # Initializes instance of pygame that runs in the background waiting for calls
        self.playing = False
        self.urgency = urgency
        self.thread = None
        self.lock = threading.Lock()
        self.sound = None

    def start(self):
        """
        Starts playing a random alarm from the specified urgency level.
            Initializes thread and sets self.playing flag to True
        """
        with self.lock: # Lock context for thread safety
            if self.urgency != 'None': # If there is a described urgency for the reminder
                if not self.playing: # If there isn't audio already playing
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
                self.sound = pygame.mixer.Sound(alarm_file)
                while self.playing:
                    self.sound.play()
                    print(f"\n\n\n NOW PLAYING {alarm_file} \n\n\n")
                    start_time = time.time() # Rounds up quantity into one-second counts 
                    while time.time() - start_time < self.sound.get_length(): # For every tenth of a second in the rounded duration
                        time.sleep(0.1)
                        if not self.playing: # If the alarm is called abruptly to stop playing, it will break the loop for a responsive Speaker.stop call
                            break 
        except Exception as ex:
            print(f"Error in Speaker.play_loop: {ex}")

    def stop(self):
        """
        Stops the currently playing sound.
        Closes thread and takes down self.playing flag
        """
        try:
            with self.lock:
                if self.playing:
                    print("\n\n\n HALTING PLAYBACK \n\n\n")
                    if self.sound:
                        self.sound.stop()
                    self.playing = False
                    if self.thread:
                        self.thread.join()
        except Exception as ex:
            print(f"Error in Speaker.stop: {ex}")

    def select_random_alarm(self):
        """
        Selects a random alarm file from the directory associated with the alarm's urgency

        Returns:
            str: The path to the selected alarm file, or None if no valid alarm is found.
        """
        try:  # Ask for forgiveness
            script_directory = os.path.dirname(os.path.abspath(__file__))  # Builds an absolute path for the directory associated with the alarm's urgency
            alarm_dir = os.path.join(script_directory, 'alarms', self.urgency)
            print(f"\n\n\nFolder for {self.urgency} playback selected: {alarm_dir}\n\n\n")
            if os.path.isdir(alarm_dir):  # Check if the directory exists
                alarm_files = os.listdir(alarm_dir)  # List all files in the directory associated with that alarm urgency
                if alarm_files:  # If there are files in the folder
                    print(f"\n\n\nRETURNING ALARM PATH: {os.path.join(alarm_dir, random.choice(alarm_files))}\n\n\n")
                    return os.path.join(alarm_dir, random.choice(alarm_files))  # Return the absolute path of a random file in that urgency's folder
            
            return None  # Return None if no valid alarm file is found
        except Exception as ex:
            print(f"Error in Speaker.select_random_alarm: {ex}")
    
    def update_urgency(self, new_urgency):
        '''
            Updates the urgency and starts playing the new audio
        '''
        self.stop()
        self.urgency = new_urgency
        self.start()



def test_speaker():
    print("Testing Speaker with different urgencies")

    # Create a Speaker with the lowest urgency
    speaker = Speaker('None')
    
    # Define the urgencies to test
    urgencies = ['Not at all', 'Somewhat', 'Urgent', 'Very', 'Extremely']

    # Test updating the urgency
    for urgency in urgencies:
        print(f"Updating Speaker urgency to: {urgency}")
        speaker.update_urgency(urgency)
        speaker.start()
        print("Playing sound. Waiting for 5 seconds...")
        time.sleep(5)  # Let the sound play for 5 seconds
        speaker.stop()
        print(f"Finished testing {urgency}.\n")

    # Reset the Speaker to None urgency at the end
    speaker.update_urgency('None')
    print("All tests completed.")

# Run the test
test_speaker()
