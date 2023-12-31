import os
import random
import pygame
import threading
import time

class Speaker:
    def __init__(self, urgency='None'):
        """
        Initializes the Speaker object.
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
                pygame.mixer.music.play()
                while self.playing:
                    pygame.time.delay(100)  # Delay for 100 milliseconds
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

def test_speaker():
    print("Testing Speaker with different urgencies")

    speaker = Speaker('None')
    
    urgencies = ['Not at all', 'Somewhat', 'Urgent', 'Very', 'Extremely']

    for urgency in urgencies:
        print(f"Updating Speaker urgency to: {urgency}")
        speaker.update_urgency(urgency)
        speaker.start()
        print("Playing sound. Waiting for 5 seconds...")
        time.sleep(5)
        speaker.stop()
        print(f"Finished testing {urgency}.\n")

    speaker.update_urgency('None')
    print("All tests completed.")

if __name__ == "__main__":
    test_speaker()
