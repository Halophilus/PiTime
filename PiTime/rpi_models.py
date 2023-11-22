import threading
import time
import pygame
import os, random, math
# import gpiozero

class Buzzer: # active piezoelectric buzzer for droning alarm sound
    def __init__(self, pin):
        self.buzzer = pin #gpiozero.Buzzer(pin)
        self.buzzing = False
        self.thread = None

    def start(self):
        if not self.buzzing:
            self.buzzing = True
            self.thread = threading.Thread(target=self.buzz) # Opens buzz function in its own thread
            self.thread.start()
    
    def stop(self):
        if self.buzzing:
            self.flickering = False
            self.thread.join() # Terminates all current threads related to this object
            # self.buzzer.off()
    
    def buzz(self):
        while self.buzzing:
            print("BUZZING ON") #buzzer.on()
            time.sleep(1)
            print("BUZZING OFF") #buzzer.off()
            time.sleep(1)

class Vibration: # 5V vibration module driven by a transistor and 3.3V logic
    def __init__(self, pin):
        self.vibration = pin #gpiozero.LED(pin)
        self.vibrating = False
        self.thread = None

    def start(self):
        if not self.vibrating:
            self.vibrating = True
            self.thread = threading.Thread(target=self.vibrate)
            self.thread.start()
    
    def stop(self):
        if self.vibrating:
            self.vibrating = False
            self.thread.join()
            # self.buzzer.off()
    
    def vibrate(self):
        while self.vibrating:
            print("VIBRATING") #vibration.on()
            time.sleep(1)
            print("NOT VIBRATING") #vibration.off()
            time.sleep(1)

class Speaker:
    def __init__(self):
        pygame.mixer.init()
        self.playing = False
        self.alarm_file = None
        self.sound = pygame.mixer.Sound(self.alarm_file)
        self.current_urgency = 'None'
        self.thread = None
        self.urgency_rating = {'None':0, 
                               'Not at all':1,
                               'Somewhat':2,
                               'Urgent':3,
                               'Very':4,
                               'Extremely':5}

    
    def start(self, urgency_set):
        '''
        Takes the maximum urgency from a set of all urgencies and starts playing an alarm from that selection
        Is tolerant of multiple calls, will change sound playing behavior if a new urgency is being introduced while another sound is playing
        Is called once a minute, but will only have action when a new urgency is introduced or no alarm is playing
            alarms, set, contains all of the urgencies from the current instance of alarms
        '''
        initial_urgency = self.current_urgency # Record current urgency
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
                    self.alarm_file = os.path.join(alarm_selections_file_path, random.choice(os.listdir(alarm_selections_file_path))) # Summons random selection from urgency designation
                    self.playing = True # Flags object as currently playing 
                    self.thread = threading.Thread(target=self.play_loop)
                    self.thread.start()
    
    def play_loop(self):
        '''
        Plays looping video as long as playing flag is True
        Will interrupt in the middle of playback if the flag changes abruptly
        '''
        while self.playing:
            self.sound.play()
            duration = math.ceil(self.sound.get_length()) # Rounds up quantity into one-second counts
            for _ in range(duration): # For every second in the rounded duration
                time.sleep(1)
                if not self.playing:
                    break # Breaks loop for abrupt termination

    def stop(self):
        if self.playing:
            self.sound.stop()  # Stop the sound if it's playing
            self.playing = False
            self.thread.join()  # Wait for the thread to finish            
