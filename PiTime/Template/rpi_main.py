import os
import random
import string
import rpi_models
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import db, Event, Reminder
from time import sleep
from datetime import datetime
from dateutil.relativedelta import relativedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alarm-reminder.db'
db.init_app(app)

global options_dict
global alarm_trigger
global current_events_dict
alarm_trigger = False
options_dict = {'buzzer':False,
                'vibration':False,
                'spoken':False,
                'web_unlock':False,
                'alarm':set('None')}
current_events_dict = {}

global buzzer_module
global speaker_module


def reminder_looper(original_datetime, repeater):
    '''
        Function: reminder_looper, adds a set amount of time to the reminder time based on repeater value
        Parameters:
            original_datetime, datetime
            repeater, str, from reminder object
    '''
    time_additions = {
            "Never": relativedelta(),  # No addition
            "Daily": relativedelta(days=1),
            "Weekly": relativedelta(weeks=1),
            "Monthly": relativedelta(months=1),
            "Yearly": relativedelta(years=1)
        }
    addition = time_additions.get(repeater, relativedelta())  # Default to no addition if the string is not found
    return original_datetime + addition

def process_event_reminders():
    '''
    Sets up context for Database queries based on current datetime
        modifies global options dictionary
        appends events to current events
    '''
    global options_dict
    global alarm_trigger
    global current_events_dict
    current_time = datetime.now()
    with app.app_context(): # Manually create app context in the absence of Flask routes
        active_reminders = Reminder.query.join(Event).filter(Reminder.reminder_lock == False)\
            .filter(Reminder.date_time <= current_time) # Pull all active + past reminder
        alarm_trigger = len(active_reminders) > 0 or alarm_trigger or options_dict['web_unlock']
        for reminders in active_reminders:
            options_dict['buzzer'] = options_dict['buzzer'] or reminders.buzzer
            options_dict['vibration'] = options_dict['vibration'] or reminders.vibration
            options_dict['spoken'] = options_dict['spoken'] or reminders.spoken
            options_dict['web_unlock'] = options_dict['web_unlock'] or reminders.web_unlock
            options_dict['alarm'].add(reminders.alarm)
            current_events_dict[reminders.event.id] = (reminders.event.title, reminders.event.description)
            reminders.date_time = reminder_looper(reminders.date_time, reminders.repeater)
            if reminders.repeater == "Never":
                reminders.reminder_lock = False
        db.session.commit()

def reset():
    '''
    Resets global bookkeeping variables to default states
    '''
    global options_dict
    global alarm_trigger
    global current_events_dict
    alarm_trigger = False
    options_dict = {'buzzer':False,
                    'vibration':False,
                    'spoken':False,
                    'web_unlock':False,
                    'alarm':set()} # Only original entries are retained to simplify parsing
    current_events_dict = {}

def write_to_file(file, val):
    '''
    Replaces the content of a given filename within .unlock with a new value
        File: str, filename within .unlock
        Val: str, new value 
    '''
    script_directory = os.path.dirname(os.path.abspath(__file__)) # fetches current working directory
    new_path = os.path.join(script_directory, '.unlock', file) # builds a relative path
    with open(new_path, 'w') as alarm_flag:
        alarm_flag.write(val)

def get_from_file(file):
    '''
    Takes filename from within .unlock and returns the value stored in that file
        file: str, filename
    Returns str file contents
    '''
    script_directory = os.path.dirname(os.path.abspath(__file__)) # fetches current working directory
    new_path = os.path.join(script_directory, '.unlock', file) # builds a relative path
    with open(new_path, 'r') as alarm_flag:
        return alarm_flag.read.strip()

def get_web_unlock():
    '''
    Returns web_unlock flag from file (bool)
    '''
    flag = get_from_file('alarm.txt')
    if bool(flag):
        return True
    return False
    
def set_web_unlock(flag):
    '''
    Sets the web unlock flag to be recognized by the Flask server, generates a random value for the web unlock key if flag = True
    if flag = False, then the alarm flag is cleared.
        flag: bool
    '''
    if flag:
        write_to_file("alarm.txt", '1')
        chars = string.ascii_letters + string.digits + string.punctuation
        random_string = ''.join(random.choice(chars) for i in range(32))
        write_to_file("unlock.txt", random_string)
    else:
        write_to_file("alarm.txt", '')

def speak(speech):
    '''
    Hitherto unresolved text-to-speech application
    '''
    pass

def play(alarm_set):
    '''
    Hitherto unresolved selection from a group of alarms under a certain category
    ''' 
    pass

def main():
    global alarm_trigger
    global options_dict
    global current_events_dict
    while True:
        web_flag = get_web_unlock() # Checks web unlock flag from file
        if not(alarm_trigger or web_flag): # Only true when both alarm_trigger and web_flag are fasle
            number_of_items = len(current_events_dict)
            speak(f"You have {number_of_items} events today") # Bespoke event message
            for keys in current_events_dict: # Walks through each unique event saved 
                speak(current_events_dict[keys][0]) # Event title
                # Some pause between the readings
                speak(current_events_dict[keys][1]) # Event description
            reset()
        sleep(60)
        process_event_reminders()
        if options_dict['web_unlock']:
            set_web_unlock(True)
        if options_dict['buzzer']:
            
            print("A BUZZER SOUNDS")
        if options_dict['vibration']:
            print("THE DEVICE VIBRATES")
        if options_dict['web_unlock']:

        
        sleep(60)


            
        '''
        Unique variables needed:
            Alarm_On, bool, turns on when an alarm is triggered, 
        '''
        ## PULL LIST OF REMINDERS ##
            # DATETIME BEFORE CURRENT DATETIME
            # REMINDER_LOCK
        ## FOR ALL TRIGGERED REMINDERS ##
            # reminder_looper CALLED
            # ORIGINAL DATETIME REPLACED
            # IF repeater == "Never"
                # SET reminder_lock TO False
            ## FOR EVERY OPTION ##

        ## COMPILE LIST OF OPTIONS ##
