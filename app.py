from flask import Flask, render_template, request, redirect, url_for, flash, abort, request
from datetime import datetime
import re, os
from glob import glob
from models import db, Event, Reminder

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))

image_folder = os.path.join(app.root_path, 'static') # Create a default folder to store images, in this case shared with the static folder
if not os.path.exists(image_folder):
    os.makedirs(image_folder)
app.config['UPLOAD_FOLDER'] = image_folder

app.config['SECRET_KEY'] = ';lkjfdsa' # nice try hacker man
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alarm-reminder.db'
db.init_app(app) # Initializes context for database reads/writes

with app.app_context(): # creates a background environment to keep track of application-level data for the current app instance 
    db.create_all() #idempotent, creates tables if absent but leaves them if they already exist
    reminder = Reminder.query.all()
    for reminders in reminder:
        print(reminders.repeater)

@app.route("/") # When accessing the root website, which shows the alarm submission form
def index():
    return render_template("index.html")

@app.route('/submit', methods=['POST']) # HTTP verb called for sending data to a server when host/submit URL is called
def submit():
    '''
    Uses functions parse_form_data and add_event_reminders to convert user input into Event and Reminder objects, which are then stored in an SQLite database
    '''
    event_title, event_description, reminders = parse_form_data(request.form)
    
    reminder_dates = [reminder['date'] for reminder in reminders]
    reminder_times = [reminder['time'] for reminder in reminders]

    valid, error_messages = validate_reminders(reminder_dates, reminder_times) # Error handling for user input problems

    if not valid:
        for message in error_messages:
            flash(message)
            return redirect(url_for('index'))

    try:
        event_id = add_event_and_reminders(event_title, event_description, reminders)
        flash(f"{event_title} added successfully!")

        if 'event_image' in request.files:
            file = request.files['event_image']
            if file.filename != '':
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                if not('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                    flash("File must be an image of the extension png, jpg, jpeg, or gif.")
                else:
                    _, file_extension = os.path.splitext(file.filename)
                    new_filename = f"{event_id}{file_extension}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                    file.save(file_path)

        return redirect(url_for('index'))
    except Exception as ex:
        flash("An error occurred: " + str(ex))
        return redirect(url_for('index'))

def validate_reminders(reminder_dates, reminder_times):
    '''
        Determines if all time and date input is legal
            Must occur in the future
            Must be non-zero
            Must be in %Y-%m-%d %H:%M format
        Args:
            reminder_dates (list), a list of strings representing the dates of each reminder
            reminder_times (list), a list of strings representing the times of each reminder
        Returns:
            valid (bool), T/F flag if the all the form data is legal
            error_messages (list), list of relevant error messages to be included as a flesh message after POST
    '''
    valid = True # Default is a legal position, only specific rules can violate it
    error_messages = []

    for index, (date, time) in enumerate(zip(reminder_dates, reminder_times)): # Zips dates and times into single reminders and sorts them by index
        if not date or not time: # If these fields are empty
            valid = False # A violation has been raised
            error_messages.append(f"Reminder {index + 1} has empty date/time fields.") # Bespoke message describing which reminders posed problems
            continue # Since this reminder lacks the relevant data to be tested as a valid datetime object, the remaining steps in this loop are skipped

        try: # An attempt will be made to force the current date/time data into a datetime object
            reminder_datetime = datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')
            if reminder_datetime <= datetime.now(): # If a reminder is set in the past
                valid = False
                error_messages.append(f"Reminder {index + 1} is set in the past.")
        except ValueError: # If the form data is not parsable as a datetime object
            valid = False
            error_messages.append(f"Reminder {index + 1} has an incorrect date/time format.")

    return valid, error_messages # Fed to the function associated with the /submit route


def parse_form_data(form):
    '''
        Function: Takes form information and parses it into a more readily usable data structure for the creation of Event and Reminder objects
        Request.form attributes:
            'main_event_title' str
            'main_event_description' str
            'reminder_time[]' str, delivered in sequence with added reminders
            'reminder_date[]' str, ibid.
            'reminder_options[x][option]' str, option
            'reminder_alarm[x]' str, alarm ID
            'reminder_repeats[]' str
        Returns:
            event_title (str), readabale title of the event object
            event_description (str), readable description of the event object
            reminders (list), list of dictionaries containing Reminder attributes per each
                date (str), date of reminder, sorted by index of 'reminder_date[]'
                time (str), time of reminder, sorted by index of 'reminder_time[]'
                options (list), a list of strings representing each optional attribute of the reminder
                    i.e., 'Buzzer', 'Vibration', 'Web_unlock', 'Alarm'
                alarm (str), the level of urgency associated with a randomly selected alarm, only populated if 'Alarm' in options
                    i.e., None, 'Not at all', 'Somewhat', 'Urgent', 'Very', 'Extremely'
                repeats (str), the frequency with which that reminder repeats
                    i.e., 'Never', 'Hourly', 'Daily', 'Weekly', 'Monthly', 'Yearly'
    '''
    event_title = form.get('main_event_title') # One string
    event_description = form.get('main_event_description') # One string
    
    reminder_times = form.getlist('reminder_time[]') # Times for each reminder in order
    reminder_dates = form.getlist('reminder_date[]') # Dates for each reminder in order
    # reminder_repeats = form.getlist('reminder_repeats[]') # Deprecated in favor of new reminders data structure

    # reminder_options = [[] for _ in reminder_times]
    # reminder_alarms = [None for _ in reminder_times]

    options_keys = [] # List of all unique reminder IDs submitted in form
    for key in form: # IDs are assigned an integer whenever a reminder form is instantiated, but the number does not decrement when forms are closed
        if key.startswith('reminder_options[') or key.startswith('reminder_repeats[') or key.startswith('reminder_alarm['): # Each of these form keys contain a submitted reminder ID
            parse_key = re.split(r'\[|\]', key) # Treats header as a regular expression and splits them at square brackets
            options_keys.append(int(parse_key[1])) # Cracks the ID out of the key
    options_keys = sorted(list(set(options_keys))) # Set eliminates redundant terms, converts it to a list so it can be ordered, then is ordered alphanumerically from low to high ID

    reminders = [] # A list of dictionaries each representing reminder objects 
    for index, reminder_id in enumerate(options_keys): # Pairing submitted reminder IDs to the order in which the reminders are declared
        options, alarm, repeats = [], None, None # Options are a collection of qualities, alarm and repeats are single items that either exist or don't
        for key in form: # For every submitted value in the form
            if key.startswith(f'reminder_options[{reminder_id}]'): # These keys occur first in the form, and are therefore processed first
                options.append(form[key]) # Adds option (str) to the options list
            if key.startswith(f'reminder_alarm[{reminder_id}]'): # These keys sometimes are sent out of order and thus need to be sorted by reminder ID
                alarm = form[key] if 'Alarm' in options else None # Because options have already been parsed, this control structure allows an urgency to be set if and only if the alarm function has been enabled
            if key.startswith(f'reminder_repeats[{reminder_id}]'): # ibid.
                repeats = form[key]

        reminder_data = { # Each reminder objects gets mocked as a dictionary
            'date': reminder_dates[index], # Corresponds submitted date time data to mocked reminder object using the index of the reminder ID in the sorted reminder ID data
            'time': reminder_times[index],
            'options': options,
            'alarm': alarm,
            'repeats': repeats
        }
        reminders.append(reminder_data) # Adds finished reminder object to running list of reminders

    return event_title, event_description, reminders # All of the information necessary to create an event-reminder relationship

def add_event_and_reminders(event_title, event_description, reminders_data):
    '''
        Function: Takes parsed event-reminder data and uses it to create Event and Reminder objects
        Args:
            event_title (str), readabale title of the event object
            event_description (str), readable description of the event object
            reminders (list), list of dictionaries containing Reminder attributes per each
        Commits new Event and Reminder objects to database within the context established for this Flask server
        Returns:
            current_event.id (int), primary key for the event being created, returned for image naming purposes
    '''
    current_event = Event(title=event_title, description=event_description) # Defines a new Event object
    db.session.add(current_event) # Commits Event to db within the context of the current session
    db.session.flush() # Assigns a primary key ID to current_event so it can be associated w/ reminder objects

    for reminder_data in reminders_data: # for every mock Reminder dictionary in the reminder_data
        timepoint = datetime.strptime(f"{reminder_data['date']} {reminder_data['time']}", '%Y-%m-%d %H:%M') # Parses text data into usable datetime objects
        new_reminder = Reminder( # Definition of reminder_lock defaults to False but the remaining attributes are defined here
            date_time=timepoint,
            buzzer='Buzzer' in reminder_data['options'], # Creates a boolean flag depending on whether or not a certain target option is included for the reminder object
            vibration='Vibration' in reminder_data['options'],
            web_unlock='Web_Unlock' in reminder_data['options'],
            alarm=reminder_data['alarm'],
            repeater=reminder_data['repeats'],
            event=current_event
        )
        db.session.add(new_reminder)

    try:
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        print(f"An unexpected error occurred, {ex}")
    
    return current_event.id

@app.route('/unlock/<path:key>')
def key_check(key):
    '''
    Function: Determines if a user-entered URL matches the web_unlock key decided in rpi_main
    Parameters: 
        key (string), optional parameter passed in from the URL
    Returns: 
        Switches alarm.txt content to '' from '1' and wipes unlock.txt
    '''
    unlock_key = read_unlock_val('unlock.txt') # Reads in web_unlock key
    if key == unlock_key: # If the value entered in the URL matches the key stored in .unlock
        return clear_web_unlock(unlock_key)  # Call the function to unlock the web_unlock functionality
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
    open(unlock, 'w').close() # Wipes each alarm (flag? not sure what word to use here)
    open(alarm, 'w').close()
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

@app.route('/events')
def events():
    '''
        Function: events(), route for displaying all active alarms
            Alarms are active when Events.event_lock is False
            Queries all active events and parses them with relevant_events_filter
            Pulls all images connected to an active event and adds them to the appropriate event in the query dictionary
        Optional args (passed from URL):
            'desc' --> sorts events by date in descending order
            '*' --> sorts events by ascending order
        Returns:
            Renders template based on current parameters
    '''
    sort_order = request.args.get('sort', 'desc')  # Looks for a value in the arguments passed in the /events call, default sort order is descending

    events = Event.query.filter_by(event_lock = False).all() # Pull all events from the database that haven't been deactivated
    # print(events)
    events_with_images = []
    events_with_reminders = []
    try:
        events_with_reminders = relevant_events_filter(events) 
        events_with_images = add_image_filepath_to_event_dictionary(events_with_reminders)
        # print(events_with_images)
    except TypeError as ex:
        print("No events have been created yet")
    # Sort events by their most recent reminder. My friend Ethan helped me with this part I'll be honest I have no idea how it works
    if sort_order == 'desc':
        events_with_images.sort(key=latest_reminder_date, reverse=True) # applies latest_reminder_date to each event entry as a point of comparison between each event so the event with the most recent reminder comes first, then reverses it to be in descending order
    else:
        events_with_images.sort(key=earliest_reminder_date) # sorts so the events with the earliest reminder in ascending order

    return render_template('events.html', events=events_with_images, sort_order=sort_order)

def latest_reminder_date(event):
    '''
        Function: returns the latest reminder date for an event element in a list of parsed event object dictionaries
        Args:
            event (dict), dictionary of the attributes of queried Event objects
    '''
    return max(reminder.date_time for reminder in event['reminders'])

def earliest_reminder_date(event):
    '''
        Function: returns the earliest reminder date for an event element in a list of parsed event object dictionaries
        Args:
            event (dict), dictionary of the attributes of queried Event objects
    '''    
    return min(reminder.date_time for reminder in event['reminders'])

def add_image_filepath_to_event_dictionary(events_with_reminders):
    '''
        Function: The Event object lacks an attribute that associates the object with an image filepath
        Args:
            events_with_reminders (list): contains a series of dictionaries containing the event data for all relevant objects to be displayed
        Returns:
            events_with_reminders (list): A modified list containing file paths when relevant, default image is None
    '''
    for event in events_with_reminders:
        event['image_path'] = None # Initialize default image_path 
        for ext in ['png', 'jpg', 'jpeg', 'gif']:
            possible_path = os.path.join('static', f"{event['id']}.{ext}") # Tests if the image associated with an alarm ID is valid
            full_path = os.path.join(app.root_path, possible_path) # Joins that path with the absolute path of the current working directory
            if os.path.isfile(full_path): # If this path is valid
                event['image_path'] = f"{event['id']}.{ext}" # Store the image path in the parsed event object dictionary
                break # No need to look any further
    return events_with_reminders # Return list of parsed event dictionary objects with the added image filepath (if present)

def relevant_events_filter(events_query):
    '''
        Function: Takes an Event Query object and parses the data into a list of dictionaries for interpretation at the scripting level
        Args:
            events_query (Query), a query containing Event instances
        Returns:
            events_with_reminders (list), a list of dictionaries containing all the data to be handled by the HTML form
    '''
    events_with_reminders = []
    for event in events_query:
        try:
            reminders = Reminder.query.filter_by(event_id=event.id).all()
            all_locked = all(reminder.reminder_lock for reminder in reminders) # If all the reminders are spent, tested using a tuple comprehension and the all function
            event_data = {
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'reminders': reminders, # These objects can now be readily queries 
                'all_locked': all_locked # This is used to determine whether or not an entry will be grayed out
            }
            events_with_reminders.append(event_data)
        except ValueError as e:
            print(f"No reminders associated with this event, {e}")
    return events_with_reminders

if __name__ == "__main__":
    app.run(debug=True)