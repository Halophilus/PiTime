from flask import Flask, render_template, request, redirect, url_for
from jinja2 import Template
import datetime
import requests
import os
from models import db, Event, Reminder


app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))
app.config['SECRET_KEY'] = ';lkjfdsa'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yourdatabase.db'
db.init_app(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/submit', methods = ['POST'])
def submit():
    from datetime import datetime
from flask import flash

@app.route('/submit', methods=['POST'])
def submit():

    # Only one declaration of these per event submission
    event_title = request.form.get('main_event_title')
    event_description = request.form.get('main_event_description')
    
    # Fetches a list of all reminder times and dates from form ImmutableMultiDict 
    reminder_times = request.form.getlist('reminder_time[]')
    reminder_dates = request.form.getlist('reminder_date[]')

    reminder_options = [[] for _ in reminder_times] # List of list of options for each reminder in order
    reminder_alarms = [None for _ in reminder_times] # List of alarm choices in order (default = None)

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


    current_event = Event(title = event_title, description = event_description) # Creates singular event
    db.session.add(current_event) # Commits event to db
    db.session.flush() # Assigns an ID to current_event so it can be associated w/ reminder objects

    for index in range(0, len(reminder_options)):
        for key in request.form: # Allocates options into list per reminder
            if key.startswith(f'reminder_options[{index}]'):
                reminder_options[index].append(request.form[key])
            if key.startswith(f'reminder_alarm[{index}]') and 'Alarm' in reminder_options[index]: # Adds alarm selection if 'Alarm' has been added to options already
                reminder_alarms[index] = request.form[key]

    for date, time, options, alarm_file in zip(reminder_dates, reminder_times, reminder_options, reminder_alarms):
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
            alarm = alarm_file if alarm_lock else None,
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
