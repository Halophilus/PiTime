import os, random, string, textwrap
from I2C_LCD_driver import lcd
from gpiozero import Button
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import db, Event, Reminder
from rpi_models import Speaker, Buzzer, Vibration
from time import sleep
from datetime import datetime, date
from dateutil.relativedelta import relativedelta # Adjusts time accurately based on timezones / variable month lengths to ensure consistency in repeater functionality


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alarm-reminder.db'
db.init_app(app)

# Hardware objects
lcd_screen = lcd()
snooze_button = Button(23)

def snooze_button_press(): # Function to be called when the snooze button is pressed (gpiozero)
    global alarm_trigger
    alarm_trigger = False

snooze_button.when_pressed = snooze_button_press

def initialize_globals():
    '''
        Function: Initializes global variables for use in the main script
            alarm_trigger (bool), True if there is an active alarm, False if not
            options_dict (dict), current aggregate options to operate control structures that create relevant alarm device objects
                buzzer (bool), intermittent beeping if True
                vibration (bool), intermittent vibration if True
                web_unlock (bool), if True, the alarm requires the user to visit a custom URL to deactivate
                alarm (set), a set of all alarm urgencies currently triggered
            current_events_dict (dict)
                key: event.id (str) ID for each unique event triggered
                val: tuple
                    event.title (str), the title of the event
                    event.description (str), the description of the event
            current_urgency (str), the current maximum urgency of the triggered alarms, used to keep track of changes in urgency to control whether or not a new Speaker object is declared
    '''
    print("\n\nRPI_MAIN.initialize_globals: Intializing globals")
    global alarm_trigger, options_dict, current_events_dict, current_urgency
    try:
        alarm_trigger = False
        options_dict = {'buzzer': False, # Global dictionary for keeping track of triggered functions
                        'vibration': False,
                        'web_unlock': False,
                        'alarm': {'None'}}
        current_events_dict = {}
        current_urgency = 'None'
    except Exception as ex:
        print(f"Error initializing globals in rpi_main: {ex}\n")

def reminder_looper(original_datetime, repeater):
    '''
        Function: reminder_looper, adds a set amount of time to the reminder time based on repeater value
            Repeater values: "Never", "Daily", "Weekly", "Monthly", "Yearly"
                For each repeater value, the script takes a datetime and adds a corresponding amount of time to it, then returns that datetime object
        Args:
            original_datetime (datetime)
            repeater (str), from reminder object
        Returns:
            New datetime postponed by value corresponding to repeater (datetime)
    '''
    print(f"\n\nRPI_MAIN.reminder_looper: Trying to loop {original_datetime} by {repeater}")
    time_additions = {
            "Never": relativedelta(),  # No addition
            "Hourly": relativedelta(hours=1),
            "Daily": relativedelta(days=1),
            "Weekly": relativedelta(weeks=1),
            "Monthly": relativedelta(months=1),
            "Yearly": relativedelta(years=1)
        }
    if not(repeater in list(time_additions.keys())): # If the repeater value is illegal
        raise ValueError("Repeater value must be in the legal Repeater set") # Raise an error
    if type(repeater) != str: # If the repeater value is not a string
        raise TypeError("Repeater must be a string") # Raise an error
    addition = time_additions.get(repeater, relativedelta())  # Default to no addition if the string is not found
    print(f"Revised date_time: {original_datetime+addition}")
    return original_datetime + addition # Return the new datetime

def fetch_active_reminders():
    '''
        Function: Fetches active reminders from the database, which are described by reminders that have both:
            Reminder.date_time (datetime) that occurred in the past (Reminder.date_time <= current_time)
            Reminder.reminder_lock (bool) that indicates the reminder hasn't already been "spent"
                Until I come up with a means to alter existing reminders, these consist of reminders in Reminder.repeater == 'Never' that have already been triggered
                Currently, all reminders with non-zero repeaters just have their date_times updated to a future datetime
        Returns:
            Query object containing all relevant Reminder objects
    '''
    print(f"\n\nRPI_MAIN.fetch_active_reminders: Fetching active reminders")
    try:
        current_time = datetime.now()
        query_object = Reminder.query.join(Event).filter(Reminder.reminder_lock == False)\
            .filter(Reminder.date_time <= current_time).all()
        print(f"{query_object.count()} active reminders found")
        for reminders in query_object:
            print(f"{reminders}")
        return query_object
    except Exception as ex:
        print(f"An error occurred with rpi_main.fetch_active_reminders, {ex}")

def update_reminder(reminder):
    '''
        Function: Modifies a given reminder object based on its repeater value, updates the global current_events_dict, and commits changes to the database.
            The function adjusts the reminder's date_time based on its repeater value using the reminder_looper function. If the repeater is set to "Never", it locks the reminder by setting reminder_lock to True. It also updates the global current_events_dict with the event's title and description linked to this reminder.
        Args:
            reminder (Reminder): representing a row in the Reminder table of the database
    '''
    print(f"\n\nRPI_MAIN.update_reminder: Trying to update reminder {reminder}")
    initial_reminder = reminder
    try:
        print(f"Reminder {reminder.id} set to repeat {reminder.repeater}")
        reminder.date_time = reminder_looper(reminder.date_time, reminder.repeater)
        print(f"New reminder datettime: {reminder.date_time}")
        if reminder.repeater == "Never":
            print("Reminder terminated")
            reminder.reminder_lock = True
        try: # Ask for forgiveness
            print(f"Revised reminder: {reminder}")
            print("Trying to commit to database...")
            db.session.commit() # Add floating entries to database
        except Exception as e: # Generic error message
            db.session.rollback() # Deletes current floating session instead of committing it
            print(f"An error occurred in committing update_reminder to database for {reminder.id} from event {reminder.event.id} ({reminder.event.title}): {e}")
    except Exception as e:
        print(f"An error occurred in update_reminder for {reminder.id} from event {reminder.event.id} ({reminder.event.title}): {e}")
    print(f"{initial_reminder} successfully updated to {reminder}")

def update_options_dict(reminder):
    '''
        Function: adds options from Reminder object to running conglomerate of options for all active alarms
            'buzzer', 'vibration', 'web_unlock' (bool): aforementioned flags for various alarm functionalities
            'alarm': a list of all urgencies from currently active alarms
        Args:
            reminder (Reminder): representing a row in the Reminder table of the database
    '''
    global options_dict
    print(f"\n\nRPI_MAIN.update_options_dict: updating options dict for reminder {reminder}")
    print(f"Initial options_dict: {options_dict}\n")
    try:
        options_dict['buzzer'] = options_dict['buzzer'] or reminder.buzzer # OR logic makes it so additional True or False calls will only yield True given at least one True assignment
        options_dict['vibration'] = options_dict['vibration'] or reminder.vibration
        options_dict['web_unlock'] = options_dict['web_unlock'] or reminder.web_unlock
        options_dict['alarm'].add(reminder.alarm) # Adds urgency to set so that only original entries are stored
        print(f"Final options_dict: {options_dict}")
    except Exception as e:
        print(f"An error occurred in update_options_dict for {reminder.id} from {reminder.event.id} ({reminder.event.title}): {e}")
    print(f"Final options_dict: {options_dict}")

def update_current_events_dict(reminder):
    '''
        Function: adds the Event object associated with the Reminder object to a running dictionary of events connected to the alarm
            Relies on event.id for keys so multiple events with repetitive event.title and event.description content get logged separately
            This dictionary is used to read the current events when the alarm is deactivated
        Args:
            reminder (Reminder): representing a row in the Reminder table of the database
    '''
    global current_events_dict
    print(f"\n\nRPI_MAIN.update_current_events_dict: Trying to update current_events_dict\n")
    print(f"Current current_events_dict: {current_events_dict}\n")
    try:
        current_events_dict[reminder.event.id] = (reminder.event.title, reminder.event.description)
        print(f"Updated current_events_dict: {current_events_dict}\n")    
    except Exception as e:
        print(f"An error occurred in update_current_events for {reminder.id} from event {reminder.event.id} ({reminder.event.title}): {e}")

def update_urgency(urgency_comparator):
    '''
        Function: checks all current urgencies listed in options_dict['Alarm'] and replaces current_urgency with the new maximal urgency if new urgency is higher. Otherwise does nothing.
            This is called after every Reminder database query to check if a more urgent reminder has been triggered
            If a more urgent reminder is present upon starting a new cycle, the control structure in the main loop will instantiate a new Speaker object with the revised urgency
        Args:
            urgency_comparator (dict), associates urgency values with a finite score  
    '''
    global current_urgency, options_dict
    print(f"\n\nRPI_MAIN.update_urgency: Trying to update current alarm urgency")
    print(f"Current urgency: {current_urgency}")
    try:
        for urgencies in options_dict['alarm']:
            if urgency_comparator[urgencies] > urgency_comparator[current_urgency]:
                print(f"Higher urgency found: {urgencies}")
                current_urgency = urgencies
            print(f"Updated urgency: {current_urgency}")
    except Exception as ex:
        print(f"Error in rpi_main.update_urgency(): {ex}")

def process_event_reminders(urgency_comparator):
    '''
        Function: Parses reminder objects using fetch_active_reminders(), update_reminder(), update_options_dict(), update_current_event_dict(), and update_urgency()
            Pulls active alarms and uses the data from each Reminder to update bookkeeping global variables + update triggered reminder objects
            Updates alarm_trigger based on results
        Args:
            urgency_comparator (dict), associates urgency values with a finite score
    '''
    global alarm_trigger, options_dict, current_events_dict, current_urgency
    print(f"\n\nRPI_MAIN.process_event_reminders(): Trying to process event reminders")
    try:
        print(f"Current alarm trigger: {alarm_trigger}")
        active_reminders = fetch_active_reminders()
        for reminder in active_reminders:
            print("Updating global variables")
            print(f"Current reminder: {reminder}")
            update_options_dict(reminder)
            update_current_events_dict(reminder)
            update_urgency(urgency_comparator)
            update_reminder(reminder)
            print(f"Updated reminder: {reminder}\n")
        print("Revised globals:")
        print(f"Options dict: {options_dict}")
        print(f"Current events dict: {current_events_dict}")
        print(f"Urgency: {current_urgency}")
        alarm_trigger = len(list(active_reminders)) > 0 or alarm_trigger # So process_event_reminders doesn't deactivate the alarm when checking for new events
        print(f"Updated alarm trigger: {alarm_trigger}")
    except Exception as ex:
        print(f"Error in rpi_main.process_event_reminders: {ex}")

def reset():
    '''
    Resets global bookkeeping variables to default states
    '''
    global options_dict, alarm_trigger, current_events_dict, current_urgency
    alarm_trigger = False
    print("\n\nRPI_MAIN: Trying to reset default values")
    print(f"Current options dict: {options_dict}\n")
    print(f"Current events dictionary: {current_events_dict}\n")
    print(f"Current urgency: {current_urgency}")
    try:
        options_dict = {'buzzer':False,
                        'vibration':False,
                        'spoken':False,
                        'web_unlock':False,
                        'alarm':{'None'}} # Only original entries are retained to simplify parsing
        current_events_dict = {}
        current_urgency = 'None'
        print(f"Reset options dict: {options_dict}")
        print(f"Reset current events dict: {current_events_dict}")
        print(f"Reset urgency: {current_urgency}")
    except Exception as ex:
        print(f"An error occurred in rpi_main.reset(): {ex}")

def write_to_file(file, val):
    '''
    Replaces the content of a given filename within .unlock with a new value
        File: str, filename within .unlock
        Val: str, new value 
    '''
    print(f"\n\nRPI_MAIN.write_to_file: Trying to write {val} to {file}")
    try:
        script_directory = os.path.dirname(os.path.abspath(__file__)) # fetches current working directory
        new_path = os.path.join(script_directory, '.unlock', file) # builds a relative path
        print(f"File path: {new_path}")
        with open(new_path, 'w') as alarm_flag:
            alarm_flag.write(val)
            print(f"{val} successfully written to {file}")
    except Exception as ex:
        print(f"An error occurred in rpi_main.write_to_file(): {ex}")

def get_from_file(file):
    '''
    Takes filename from within .unlock and returns the value stored in that file
        file: str, filename
    Returns str file contents
    '''
    print(f"\n\nRPI_MAIN.get_from_file: Trying to get contents {file}")
    try:
        script_directory = os.path.dirname(os.path.abspath(__file__)) # fetches current working directory
        new_path = os.path.join(script_directory, '.unlock', file) # builds a relative path
        with open(new_path, 'r') as alarm_flag:
            file_contents = str(alarm_flag.read()).strip()
            print(f"Contents found: {file_contents}")
            return file_contents
    except Exception as ex:
        print(f"Error at rpi_main.get_from_file(): {ex}")

def get_web_unlock():
    '''
    The web_unlock flag is partially determined by the state of a text file containing either '1' or ''
    This is because deactivating the web_unlock is performed on the other Flask server by manipulating 'alarm.txt'
    Returns web_unlock flag from file (bool)
        '1': web_unlock is active
        '': web_unlock is inactive
    '''
    print("\n\nRPI_MAIN.get_web_unlock: Trying to retrieve web_unlock flag from file")
    try:
        script_directory = os.path.dirname(os.path.abspath(__file__))
        alarm = os.path.join(script_directory, '.unlock', 'alarm.txt')
        flag = get_from_file(alarm)
        print(f"Flag pulled from file: {flag}")
        if bool(flag):
            print("Web unlock flag file: True")
            return True
        print("Web unlock flag file: False")
        return False
    except Exception as ex:
        print(f"Error at rpi_main.get_web_unlock(): {ex}")
    
def set_web_unlock(flag):
    '''
    Sets the web unlock flag to be recognized by the Flask server, generates a random value for the web unlock key if flag = True
    if flag = False, then the alarm flag is cleared.
        flag: bool
    Args:
        flag (bool), determined by options_dict['web_unlock'], indicates that web unlock has been enabled for this reminder
    Returns:
        random_string (str) 32 random characters to be used for the web unlock
    '''
    global options_dict
    print(f'\n\nRPI_MAIN.set_web_unlock: Setting web unlock file flag to {flag}')
    try:
        script_directory = os.path.dirname(os.path.abspath(__file__))
        alarm = os.path.join(script_directory, '.unlock', 'alarm.txt')
        if flag:
            print("Setting to True, writing '1' to file")
            write_to_file(alarm, '1')
            chars = string.ascii_letters + string.digits + string.punctuation
            random_string = ''.join(random.choice(chars) for i in range(32))
            write_to_file("unlock.txt", random_string)
            print(f"Unlock key set to {random_string}")
            return random_string
        else:
            print("Setting to False")
            write_to_file(alarm, '')
            options_dict['web_unlock'] = False
            return None
    except Exception as ex:
        print(f"Error at rpi_main.set_web_unlock(): {ex}")

def speak(speech):
    '''
    Hitherto unresolved text-to-speech application
    '''
    print(speech)

def main():
    '''
    Tentative looping event/reminder checker that queries active events at regular intervals and triggers alarms if the events are active and at least one of the reminders is in the past.
        It accumulates the flags of all of the triggered reminders as new ones are discovered and only pulls down the flags when the alarm unlock conditions are met
    '''
    with app.app_context(): # Manually create app context in the absence of Flask routes so that the app doesn't have to be destroyed and recreated for every check
        print("\n\n\nINITIALIZING MAIN SCRIPT")
        initialize_globals()
        urgency_comparator = {'None' : 0, #  Means of quantifying/comparing urgency
                            'Not at all' : 1,
                            'Somewhat' : 2,
                            'Urgent' : 3,
                            'Very' : 4,
                            'Extremely' : 5}
        buzzer = speaker = vibration = None # Preemptively create objects associated with each alarm function so that they can be used in the control structures of the loop before being declared as rpi_models objects
        while True:
            print("MAIN LOOP BEGIN")
            print("PROCESSING REMINDERS")
            process_event_reminders(urgency_comparator)
            while alarm_trigger or options_dict['web_unlock']:               
                print("CHECKING WEB UNLOCK")
                if not get_web_unlock():
                    print("NO LOCK FOUND")
                    print("WEB UNLOCK FLAG SET TO FALSE")
                    print("SETTING LOCAL WEB UNLOCK FLAG TO FALSE")
                    set_web_unlock(False)
                elif options_dict["web_unlock"]:
                    print("WEB LOCK ENABLED")
                    print("GENERATING NEW WEB UNLOCK KEY")
                    web_unlock_key = set_web_unlock(True) # Generates a new web_unlock key every 30 seconds
                    print(f"WEB UNLOCK KEY: {web_unlock_key}")
                    print("PROCESSING EVENT REMINDERS")
                    process_event_reminders(urgency_comparator)
                    random_string = set_web_unlock(options_dict['web_unlock'])
                    split_strings = textwrap.wrap(random_string, 16)
                    lcd_screen.lcd_display_string(split_strings[0], 1)
                    lcd_screen.lcd_display_string(split_strings[1], 2)
                    lcd_screen.backlight(0)
                print("CHECKING FOR CURRENT URGENCY")
                if current_urgency != 'None':
                    print(f"CURRENT URGENCY: {current_urgency}")
                    if not speaker:
                        print("STARTING A NEW SPEAKER OBJECT")
                        speaker = Speaker(current_urgency)
                        speaker.start()
                    if urgency_comparator[current_urgency] > urgency_comparator[speaker.urgency]:
                        print(f"CURRENT URGENCY {current_urgency} GREATER THAN SPEAKER URGENCY {speaker.urgency}")
                        speaker.stop()
                        speaker = Speaker(current_urgency)
                        speaker.start()
                        print(f"PROCESSING REMINDERS")
                        process_event_reminders()
                print("CHECKING FOR BUZZER")
                if options_dict['buzzer']:
                    print("BUZZER OPTION ENABLED")
                    if not buzzer:
                        print("CREATING NEW BUZZER OBJECT")
                        buzzer = Buzzer(1)
                    buzzer.start()
                else:
                    print("BUZZER OPTION DISABLED")
                    if buzzer:
                        print("STOPPING BUZZER")
                        buzzer.stop()
                        buzzer.buzzer.close()
                print("CHECKING FOR VIBRATION")
                if options_dict['vibration']:
                    print("VIBRATION ENABLED")
                    if not vibration:
                        print("CREATING VIBRATION OBJECT")
                        vibration = Vibration(1)
                    vibration.start()
                else:
                    print("VIBRATION DISABLED")
                    if vibration:
                        print("STOPPING VIBRATION")
                        vibration.stop()
                        vibration.vibration.close()
                print("CHECKING FOR WEB LOCK")
                if options_dict['web_unlock']:
                    print("WEB LOCK ENABLED")
                    print("GENERATING NEW WEB UNLOCK KEY")
                    web_unlock_key = set_web_unlock(True) # Generates a new web_unlock key every 30 seconds
                    print(f"WEB UNLOCK KEY: {web_unlock_key}")
                print("PROCESSING EVENT REMINDERS")
                process_event_reminders(urgency_comparator)
                sleep(30)
                print("END OF ALARM LOOP")
            else:
                number_of_events = len(current_events_dict)
                if number_of_events > 0:
                    speak(f'You have {number_of_events} events currently')
                    for keys in current_events_dict:
                        speak(f"Event number {keys}")
                        speak(current_events_dict[keys][0])
                        speak(current_events_dict[keys][1])
                        sleep(3)
                reset()
            lcd_screen.clear()
            lcd_screen.backlight(1)
            today = date.today()
            time = datetime.now()
            current_time = time.strftime("%I:%M %p")
            current_date = today.strftime("%B %d, '%y")
            sleep(60)

if __name__ == '__main__':
    main()
