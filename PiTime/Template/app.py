from flask import Flask, render_template, request, redirect, url_for, flash, abort
from datetime import datetime
import re
import os
from models import db, Event, Reminder


app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))
app.config['SECRET_KEY'] = ';lkjfdsa' # nice try hacker man
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alarm-reminder.db'
db.init_app(app)

with app.app_context(): # creates a background environment to keep track of application-level data for the current app instance 
    db.create_all() #idempotent, creates tables if absent but leaves them if they already exist
    reminder = Reminder.query.all()
    for reminders in reminder:
        print(reminders.repeater)

@app.route("/") # When accessing the root website
def index():
    return render_template("index.html")

@app.route('/submit', methods=['POST']) # HTTP verb called for sending data to a server when host/submit URL is called
def submit():
    '''
        Takes form information, parses it, and converts it to event/reminder objects
        Request.form attributes:
            'main_event_title' str
            'main_event_description' str
            'reminder_time[]' str, delivered in sequence with added reminders
            'reminder_date[]' str, ibid.
            'reminder_options[x][option]' str, option
            'reminder_alarm[x]' str, alarm ID
            'reminder_repeats[]' str
        Converts data into:
            1 Event object
                main_event_title
                main_event_description
            Five lists
                reminder_time
                reminder_date
                reminder_options (list)
                reminder_alarm (if 'Alarm' in reminder_options)
                reminder_repeats
            Converts lists into reminder objects per index with foreign key connected to Event object
            ## PERSONAL ADDENDUM ##
            I wrote this function while still figuring out how to use Flask. I thought you could only
            write one function per route. It didn't occur to me to dissect the functionality of this
            script and invest it in individual, external functions. I may come back and fix this,
            I may not. Either way, this code is heavily commented for the sake of legibility
    '''
    print(request.form)
    # Only one declaration of these per event submission
    event_title = request.form.get('main_event_title')
    event_description = request.form.get('main_event_description')
    
    # Fetches a list of all reminder times and dates from form ImmutableMultiDict 
    reminder_times = request.form.getlist('reminder_time[]')
    reminder_dates = request.form.getlist('reminder_date[]')

    #reminder_repeats = request.form.getlist('reminder_repeats[]')# All reminders will have at least and at most 1 attribute for "Repeat", so an ordered list represents each reminder in order


    reminder_options = [[] for _ in reminder_times] # List of list of options for each reminder in order
    reminder_alarms = [None for _ in reminder_times] # List of alarm choices in order (default = None)
    reminder_repeats = [None for _ in reminder_times]

    # Error Handling
    valid = True # Stays true as long as all input is valid
    error_messages = [] # Collects messages for all errors encountered

    for index, (date, time) in enumerate(zip(reminder_dates, reminder_times)):
        if not date or not time: # Check for empty fields
            valid = False # Raise valid input flag
            error_messages.append(f"Reminder {index + 1} has empty date/time fields.")
            continue
    
        try: # ask for forgiveness
            reminder_datetime = datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M') # Validate date-time format
            if reminder_datetime <= datetime.now(): # Further check if the datetime is in the future
                valid = False
                error_messages.append(f"Reminder {index + 1} is set in the past.")
        # Improper input to datetime.strptime results in raising a ValueError
        except ValueError:
            valid = False
            error_messages.append(f"Reminder {index + 1} has an incorrect date/time format.")

    if not valid:
        for message in error_messages:
            flash(message) # Display the errors on the bottom of the screen
        return render_template("index.html", # Returns use to filled out form to revise
                               event_title=event_title, 
                               event_description=event_description, 
                               reminder_times=reminder_times, 
                               reminder_dates=reminder_dates,
                               reminder_options=reminder_options,
                               reminder_alarms=reminder_alarms)
    
    current_event = Event(title = event_title, description = event_description) # Creates singular event
    db.session.add(current_event) # Commits event to db
    db.session.flush() # Assigns an ID to current_event so it can be associated w/ reminder objects
    
    # This is necessary to isolate the reminder identifiers that were actually submitted, as they user reminder addition/deletions can't be anticipated procedurally
    options_keys = [] # The serial number associated with each JS instance of a reminder. JS function addReminder increments a serial as a unique identifier, decrementing would introduce repetitive values to the domain 
    for key in request.form: # For every key in MultiImmutableDict.request.form, representing the names of the attributes in the alarm clock form...
        if key.startswith('reminder_options[') or key.startswith('reminder_repeats[') or key.startswith('reminder_alarm['): # one of two attributes that contains the reminder ID
            print(key)
            parse_key = re.split(r'\[|\]', key) # Treat the key as a regular expression and split at '[' and ']' delimiters
            options_keys.append(int(parse_key[1])) # Adds reminder serial number to list
    options_keys = sorted(set(options_keys)) # This ensures that reminded IDs are sorted in increasing order AND eliminates all redundant entries
    print(options_keys)
    for index, reminder_id in enumerate(options_keys): # this maps the reminder ID to an index in the lists describing each reminder's attributes
        for key in request.form: # List of options per reminder index
            if key.startswith(f'reminder_options[{reminder_id}]'): # if one of the attributes submitted to the form is of the form of an optional attribute...
                reminder_options[index].append(request.form[key]) # Add the string value of that key to the list of options corresponding to a certain reminder
            if key.startswith(f'reminder_alarm[{reminder_id}]') and 'Alarm' in reminder_options[index]: # If the attribute describes a reminder's choice of alarm and the alarm is enabled by the optional attributes for that reminder...
                reminder_alarms[index] = request.form[key] # Even if a user does not enable Alarm as an optional parameter, a value for alarm choice is submitted. This eliminates adding an alarm to reminder objects that don't enable it.
            if key.startswith(f'reminder_repeats[{reminder_id}]'):
                reminder_repeats[index] = request.form[key]
    #for reminder_data in zip(reminder_dates, reminder_times, reminder_options, reminder_alarms, reminder_repeats):
    # Iterate through the indices of the reminder lists
    for i in range(len(reminder_dates)):
        # Access each attribute using the index
        date = reminder_dates[i]
        time = reminder_times[i]
        options = reminder_options[i]
        alarm = reminder_alarms[i] if 'Alarm' in reminder_options[i] else None
        repeats = reminder_repeats[i]

        # Convert text datetime to datetime object
        timepoint = datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')

        # Convert option choices into Boolean values
        buzzer_lock = 'Buzzer' in options
        vibration_lock = 'Vibration' in options
        web_unlock_lock = 'Web_Unlock' in options

        # Create a new Reminder instance
        new_reminder = Reminder(
            date_time=timepoint,
            buzzer=buzzer_lock,
            vibration=vibration_lock,
            web_unlock=web_unlock_lock,
            alarm=alarm,
            repeater=repeats,
            event=current_event
        )

        # Add the new reminder to the session
        db.session.add(new_reminder) # Saves reminder object to current db session

    try: # Ask for forgiveness
        db.session.commit() # Add floating entries to solid state database
    except Exception as ex: # Generic error message
        db.session.rollback() # Deletes current floating session instead of committing it
        print(f"An error occurred: {ex}") # Not overly familiar with the type of errors that could occur here
    # Test block
    print(event_title)
    print(event_description)
    print(reminder_times)
    print(reminder_dates)
    print(reminder_options)
    print(reminder_alarms)
    print(reminder_repeats)
    
    return render_template("index.html")

@app.route('/unlock/<path:key>')
def key_check(key):
    '''
    Function: Determines if a user-entered URL matches the web_unlock key decided in rpi_main
    Parameters: key, string
    Returns: Switches web_unlock value to 0 from 1 and wipes unlock.txt
    '''
    unlock_key = read_unlock_val('unlock.txt')
    if key == unlock_key:
        return clear_web_unlock(unlock_key)  # Call the function that should be triggered
    else:
        abort(404)  # Not found if the key is not valid

def clear_web_unlock():
    '''
    Function performed when web_unlock procedure fulfilled successfully
        Sets alarm to 0
        Resets unlock key
    '''
    script_directory = os.path.dirname(os.path.abspath(__file__)) # fetches current working directory
    unlock = os.path.join(script_directory, '.unlock', 'unlock.txt') # builds a relative path
    alarm = os.path.join(script_directory, '.unlock', 'alarm.txt')
    open(unlock, 'w').close()
    with open(alarm, 'w') as alarm_unlock:
        alarm_unlock.write('0')
    return "Function triggered successfully!"

def read_unlock_val(file):
    '''
    Function: reads relevant unlock keys from file
    Parameters: file, str, filename of stored value
    Returns: string contents of file
    '''
    script_directory = os.path.dirname(os.path.abspath(__file__)) # fetches current working directory
    unlock_file_path = os.path.join(script_directory, '.unlock', file) # builds a relative path

    with open(unlock_file_path, 'r') as file: # reads key from file
        return file.read().strip() # returns key minus leading white space




if __name__ == "__main__":
    app.run(debug=True)
