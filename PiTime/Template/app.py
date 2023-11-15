from flask import Flask, render_template, request, redirect, url_for
from jinja2 import Template
from datetime import datetime
import re
import requests
import os
from models import db, Event, Reminder


app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))
app.config['SECRET_KEY'] = ';lkjfdsa'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alarm-reminder.db'
db.init_app(app)

with app.app_context(): # creates a background environment to keep track of application-level data for the current app instance 
    db.create_all() #idempotent, creates tables if absent but leaves them if they already exist

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/submit', methods=['POST'])
def submit():
    '''
        Request.form attributes:
            'main_event_title' str
            'main_event_description' str
            'reminder_time[]' str, delivered in sequence with added reminders
            'reminder_date[]' str, ibid.
            'reminder_options[x][option]' str, option
            'reminder_alarm[x]' str, alarm ID
        Converts data into:
            1 Event object
                main_event_title
                main_event_description
            Four lists
                reminder_time
                reminder_date
                reminder_options (list)
                reminder_alarm (if 'Alarm' in reminder_options)
            Converts lists into reminder objects per index with foreign key connected to Event object
    '''
    # print(request.form)
    # Only one declaration of these per event submission
    event_title = request.form.get('main_event_title')
    event_description = request.form.get('main_event_description')
    
    # Fetches a list of all reminder times and dates from form ImmutableMultiDict 
    reminder_times = request.form.getlist('reminder_time[]')
    reminder_dates = request.form.getlist('reminder_date[]')

    reminder_options = [[] for _ in reminder_times] # List of list of options for each reminder in order
    reminder_alarms = [None for _ in reminder_times] # List of alarm choices in order (default = None)
    '''
    # Error Handling
    valid = True # Stays true as long as all input is valid
    error_messages = [] # Collects messages for all errors encountered

    for index, (date, time) in enumerate(zip(reminder_dates, reminder_times)):
        # Check for empty fields
        if not date or not time:
            valid = False
            error_messages.append(f"Reminder {index + 1} has empty date/time fields.")
            continue

        # Validate date-time format
        try:
            reminder_datetime = datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')
            # Further check if the datetime is in the future
            if reminder_datetime <= datetime.now():
                valid = False
                error_messages.append(f"Reminder {index + 1} is set in the past.")
        # Improper input to datetime.strptime results in raising a ValueError
        except ValueError:
            valid = False
            error_messages.append(f"Reminder {index + 1} has an incorrect date/time format.")

    if not valid:
        for message in error_messages:
            flash(message)
        return render_template("index.html", 
                               event_title=event_title, 
                               event_description=event_description, 
                               reminder_times=reminder_times, 
                               reminder_dates=reminder_dates,
                               reminder_options=reminder_options,
                               reminder_alarms=reminder_alarms)

    '''
    current_event = Event(title = event_title, description = event_description) # Creates singular event
    db.session.add(current_event) # Commits event to db
    db.session.flush() # Assigns an ID to current_event so it can be associated w/ reminder objects
    
    # This is necessary to isolate the reminder identifiers that were actually submitted, as they user reminder addition/deletions can't be anticipated procedurally
    options_keys = [] # The serial number associated with each JS instance of a reminder. JS function addReminder increments a serial as a unique identifier, decrementing would introduce repetitive values to the domain 
    for key in request.form: # For every key in MultiImmutableDict.request.form, representing the names of the attributes in the alarm clock form...
        if key.startswith('reminder_options['): # one of two attributes that contains the reminder ID
            parse_key = re.split(r'\[|\]', key) # Treat the key as a regular expression and split at '[' and ']' delimiters
            options_keys.append(int(parse_key[1])) # Adds reminder serial number to list
    options_keys = sorted(set(options_keys)) # This ensures that reminded IDs are sorted in increasing order AND eliminates all redundant entries
    # print(options_keys)
    for index, reminder_id in enumerate(options_keys): # this maps the reminder ID to an index in the lists describing each reminder's attributes
        for key in request.form: # List of options per reminder index
            if key.startswith(f'reminder_options[{reminder_id}]'): # if one of the attributes submitted to the form is of the form of an optional attribute...
                reminder_options[index].append(request.form[key]) # Add the string value of that key to the list of options corresponding to a certain reminder
            if key.startswith(f'reminder_alarm[{reminder_id}]') and 'Alarm' in reminder_options[index]: # If the attribute describes a reminder's choice of alarm and the alarm is enabled by the optional attributes for that reminder...
                reminder_alarms[index] = request.form[key] # Even if a user does not enable Alarm as an optional parameter, a value for alarm choice is submitted. This eliminates adding an alarm to reminder objects that don't enable it.

    for reminder in zip(reminder_dates, reminder_times, reminder_options, reminder_alarms): # All of the indices of each of these lists have to correspond with the same reminder object
        # print(reminder)
        # it didn't like for w, x, y, z in zip(...) for some reason?
        date = reminder[0]
        time = reminder[1]
        options = reminder[2]
        alarm = reminder[3]
        # Convert text datetime to datetime object
        timepoint = datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')

        # Convert option choices into Boolean values
        buzzer_lock = 'Buzzer' in options
        alarm_lock = 'Alarm' in options
        web_unlock_lock = 'Web_Unlock' in options 
        spoken_lock = 'Spoken' in options
        vibration_lock = 'Vibration' in options
        reminder = Reminder(
            date_time = timepoint,
            buzzer = buzzer_lock,
            vibration = vibration_lock,
            spoken = spoken_lock,
            web_unlock = web_unlock_lock,
            alarm = alarm if alarm_lock else None,
            event = current_event
        )
        db.session.add(reminder) # Saves reminder object to current db session
    try:
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        print(f"An error occurred: {ex}")
    
    print(event_title)
    print(event_description)
    print(reminder_times)
    print(reminder_dates)
    print(reminder_options)
    print(reminder_alarms)
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
