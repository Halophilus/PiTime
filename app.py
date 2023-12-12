from flask import Flask, render_template, request, redirect, url_for, flash, abort
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
    print("INDEX.APP.PY: '/' Root route triggered. Rendering alarm template.")
    return render_template("index.html")

@app.route('/submit', methods=['POST']) # HTTP verb called for sending data to a server when host/submit URL is called
def submit():
    '''
    Uses functions parse_form_data and add_event_reminders to convert user input into Event and Reminder objects, which are then stored in an SQLite database
    '''
    print(f"\n\nSUBMIT.APP.PY: Event and reminder form submitted.\n Request form: {request.form}\n\n Request files: {request.files}\n\n")
    print("Passing form to parse_form_data...")
    event_title, event_description, reminders = parse_form_data(request.form)
    print("\n\n Returning to submit()\n")
    print(f"Event title: {event_title}\n Event description: {event_description}\nReminders:")
    for current_reminders in reminders:
        print(f"{current_reminders}")
    
    reminder_dates = [reminder['date'] for reminder in reminders]
    reminder_times = [reminder['time'] for reminder in reminders]

    valid, error_messages = validate_reminders(reminder_dates, reminder_times) # Error handling for user input problems

    if not valid:
        print("Errors found in event form submission data.")
        for message in error_messages:
            flash(message)
            print(f"Error in event submission: {message}")
            return redirect(url_for('index'))
    print("\n")
    try:
        print("Passing to add_event_and_reminders...")
        event_id = add_event_and_reminders(event_title, event_description, reminders)
        print("\n\n Returning to submit()...")
        print(f"\nEvent {event_title} added successfully")
        flash(f"{event_title} added successfully!")

        if 'event_image' in request.files:
            file = request.files['event_image']
            if file.filename != '':
                print(f"Initial file name: {file.filename}")
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                if not('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                    print(f"File submitted is not an image of ext. {allowed_extensions}")
                    flash("File must be an image of the extension png, jpg, jpeg, or gif.")
                else:
                    _, file_extension = os.path.splitext(file.filename)
                    new_filename = f"{event_id}{file_extension}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                    file.save(file_path)
                    print(f"File uploaded for event {event_id} at {file_path}")

        return redirect(url_for('index'))
    except Exception as ex:
        flash(f"An error occurred in submit.app.py: {ex} \n")
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
    print(f"\n\nVALIDATE_REMINDERS.APP.PY: Validating all reminders for legal content from raw data.\n Reminder dates: {reminder_dates}\n Reminder times {reminder_times}")
    valid = True # Default is a legal position, only specific rules can violate it
    error_messages = []
    try:
        for index, (date, time) in enumerate(zip(reminder_dates, reminder_times)): # Zips dates and times into single reminders and sorts them by index
            if not date or not time: # If these fields are empty
                valid = False # A violation has been raised
                error_messages.append(f"Reminder {index + 1} has empty date/time fields.") # Bespoke message describing which reminders posed problems
                print(f"Empty date/time fields for reminder {index + 1} at {(date, time)}\n")
                continue # Since this reminder lacks the relevant data to be tested as a valid datetime object, the remaining steps in this loop are skipped

            try: # An attempt will be made to force the current date/time data into a datetime object
                reminder_datetime = datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')
                if reminder_datetime <= datetime.now(): # If a reminder is set in the past
                    valid = False
                    print(f"Reminder {index + 1} has a datetime set in the past: {(date, time)}")
                    error_messages.append(f"Reminder {index + 1} is set in the past.\n")
            except ValueError: # If the form data is not parsable as a datetime object
                valid = False
                print(f"Reminder {index + 1} has an invalid date/time: {(date, time)}")
                error_messages.append(f"Reminder {index + 1} has an incorrect date/time format.\n")
    except Exception as ex:
        print(f"Error at validate_numbers.app.py: {ex}")
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
    print(f"\n\nPARSE_FORM_DATA.APP.PY: Attempting to parse form data from form:\n {form}")
    try:
        event_title = form.get('main_event_title') # One string
        event_description = form.get('main_event_description') # One string
        print(f"Event title: {event_title}")
        print(f"Event description: {event_description}")

        reminder_times = form.getlist('reminder_time[]') # Times for each reminder in order
        reminder_dates = form.getlist('reminder_date[]') # Dates for each reminder in order
        print(f"Reminder times:\n {reminder_times}\n")
        print(f"Reminder dates:\n {reminder_dates}\n")
        # reminder_repeats = form.getlist('reminder_repeats[]') # Deprecated in favor of new reminders data structure
        # reminder_options = [[] for _ in reminder_times]
        # reminder_alarms = [None for _ in reminder_times]

        options_keys = [] # List of all unique reminder IDs submitted in form
        for key in form: # IDs are assigned an integer whenever a reminder form is instantiated, but the number does not decrement when forms are closed
            if key.startswith('reminder_options[') or key.startswith('reminder_repeats[') or key.startswith('reminder_alarm['): # Each of these form keys contain a submitted reminder ID
                parse_key = re.split(r'\[|\]', key) # Treats header as a regular expression and splits them at square brackets
                options_keys.append(int(parse_key[1])) # Cracks the ID out of the key
        options_keys = sorted(list(set(options_keys))) # Set eliminates redundant terms, converts it to a list so it can be ordered, then is ordered alphanumerically from low to high ID
        print(f"Registered reminder IDs: {options_keys}\n")

        reminders = [] # A list of dictionaries each representing reminder objects 
        for index, reminder_id in enumerate(options_keys): # Pairing submitted reminder IDs to the order in which the reminders are declared
            options, alarm, repeats = [], None, None # Options are a collection of qualities, alarm and repeats are single items that either exist or don't
            for key in form: # For every submitted value in the form
                if key.startswith(f'reminder_options[{reminder_id}]'): # These keys occur first in the form, and are therefore processed first
                    options.append(form[key]) # Adds option (str) to the options list
                    print(f"{form[key]} option added to Reminder {index}")
                if key.startswith(f'reminder_alarm[{reminder_id}]'): # These keys sometimes are sent out of order and thus need to be sorted by reminder ID
                    alarm = form[key] if 'Alarm' in options else None # Because options have already been parsed, this control structure allows an urgency to be set if and only if the alarm function has been enabled
                    print(f"Alarm urgency {form[key]} added to Reminder {index}")
                if key.startswith(f'reminder_repeats[{reminder_id}]'): # ibid.
                    repeats = form[key]
                    print(f"Repeater {form[key]} added to Reminder {index}")

            reminder_data = { # Each reminder objects gets mocked as a dictionary
                'date': reminder_dates[index], # Corresponds submitted date time data to mocked reminder object using the index of the reminder ID in the sorted reminder ID data
                'time': reminder_times[index],
                'options': options,
                'alarm': alarm,
                'repeats': repeats
            }

            print(f"Current reminder being processed:\n {reminder_data}")
            reminders.append(reminder_data) # Adds finished reminder object to running list of reminders
        print(f"Reminders processed:\n {reminders}\n")
    except Exception as ex:
        print(f"Error in parse_form_data.app.py: {ex}\n")
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
    print(f"\n\nADD_EVENT_AND_REMINDERS.APP.PY: Attempting to add event and reminders for\n Event: {event_title}\n Desc: {event_description}\n Reminders: {reminders_data}")

    current_event = Event(title=event_title, description=event_description) # Defines a new Event object
    db.session.add(current_event) # Commits Event to db within the context of the current session
    db.session.flush() # Assigns a primary key ID to current_event so it can be associated w/ reminder objects
    try:
        for reminder_data in reminders_data: # for every mock Reminder dictionary in the reminder_data
            print(f"Current reminder data: {reminder_data}\n")
            timepoint = datetime.strptime(f"{reminder_data['date']} {reminder_data['time']}", '%Y-%m-%d %H:%M') # Parses text data into usable datetime objects
            print(f"Current timepoint: {timepoint}")
            new_reminder = Reminder( # Definition of reminder_lock defaults to False but the remaining attributes are defined here
                date_time=timepoint,
                buzzer='Buzzer' in reminder_data['options'], # Creates a boolean flag depending on whether or not a certain target option is included for the reminder object
                vibration='Vibration' in reminder_data['options'],
                web_unlock='Web_Unlock' in reminder_data['options'],
                alarm=reminder_data['alarm'],
                repeater=reminder_data['repeats'],
                event=current_event
            )
            print(f"\nNew reminder: {new_reminder}\n")
            db.session.add(new_reminder)
        db.session.commit()
        print("Reminders added successfully.")
    except Exception as ex:
        db.session.rollback()
        print(f"An unexpected error occurred in add_event_and_reminder.app.py, {ex}\n")
    print(f"Returning ID for current event: {current_event.id}\n")
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
    print(f"\n\nKEY_CHECK.APP.PY: Web unlock route attempt with key {key}")
    try:
        script_directory = os.path.dirname(os.path.abspath(__file__)) # fetches current working directory
        unlock = os.path.join(script_directory, '.unlock', 'unlock.txt') # builds a relative path
        unlock_key = read_unlock_val(unlock) # Reads in web_unlock key
        print(f"Actual unlock key: {unlock_key}")
        if key == unlock_key: # If the value entered in the URL matches the key stored in .unlock
            print("Web unlock engaged\n")
            return clear_web_unlock()  # Call the function to unlock the web_unlock functionality
        else:
            print("Web unlock failed\n")
            abort(404)  # Not found if the key is not valid
    except Exception as ex:
        return_string = f"Error in key_check.app.py: {ex}\n"
        print(return_string)
        return return_string

def clear_web_unlock():
    '''
    Function performed when web_unlock procedure fulfilled successfully
        Sets alarm to ''
        Resets unlock key
    '''
    print("\n\nCLEAR_WEB_UNLOCK.APP.PY: Attempting to clear web lock")
    try:
        script_directory = os.path.dirname(os.path.abspath(__file__)) # fetches current working directory
        unlock = os.path.join(script_directory, '.unlock', 'unlock.txt') # builds a relative path
        alarm = os.path.join(script_directory, '.unlock', 'alarm.txt')
        open(unlock, 'w').close() # Wipes each alarm flag
        open(alarm, 'w').close()
        print("Web unlock completed successfully\n")
        return "Web unlock completed successfully"
    except Exception as ex:
        print(f"Error in clear_web_unlock.app.py, {ex}\n")
        return f"Error with web unlock: {ex}"

def read_unlock_val(file):
    '''
    Function: reads relevant unlock keys from file
    Parameters: file, str, filename of stored value
    Returns: string contents of file
    '''
    print(f"\n\nREAD_UNLOCK_VAL.APP.PY: Attempting to read web unlock key from file for file {file}")
    try:
        script_directory = os.path.dirname(os.path.abspath(__file__)) # fetches current working directory
        unlock_file_path = os.path.join(script_directory, '.unlock', file) # builds a relative path
        print(f"Key file directory: {unlock_file_path}")
        print("Attempting to read key file")
        with open(unlock_file_path, 'r') as file: # reads key from file
            key_content = file.read().strip()
            print(f"Unlock key: {key_content}\n")
            return key_content # returns key minus leading white space
    except Exception as ex:
        print(f"An error occurred in read_unlock_val.app.py: {ex}\n")
        return ''
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
    print("\n\nEVENTS.APP.PY: /events route triggered by web access, attempting to display events\n")
    sort_order = request.args.get('sort', 'desc')  # Looks for a value in the arguments passed in the /events call, default sort order is descending
    print(f"Events sorting order: {sort_order}")
    events = Event.query.filter_by(event_lock = False).all() # Pull all events from the database that haven't been deactivated
    print("Printing query info for active events")
    for event in events:
        print(f"\nEvent ID: {event.id}")
        print(f"Title: {event.title}")
        print(f"Description: {event.description}")
        
        # Print details of each reminder associated with the event
        for reminder in event.reminders:
            print(f"  Reminder ID: {reminder.id}")
            print(f"  Date and Time: {reminder.date_time}")
            print(f"  Buzzer: {reminder.buzzer}")
            print(f"  Vibration: {reminder.vibration}")
            print(f"  Alarm: {reminder.alarm}")
            print(f"  Repeater: {reminder.repeater}")
        # Separate each event for clarity
        print("-" * 30)

    events_with_images = []
    events_with_reminders = []
    try:
        events_with_reminders = relevant_events_filter(events) 
        print(f"Events with reminders: {events_with_reminders}")
        for event in events_with_reminders:
            print(event)
        events_with_images = add_image_filepath_to_event_dictionary(events_with_reminders)
        print(f"Events with file data: {events_with_images}")
        for event in events_with_images:
            print(event)
        # print(events_with_images)
    except TypeError as ex:
        print(f"No events have been created yet (events.app.py): {ex}")
    except Exception as ex:
        print(f"Error in events.app.py, {ex}")
    if sort_order == 'desc':
        print("Sorting events in descending order")
        events_with_images.sort(key=latest_reminder_date, reverse=True) # applies latest_reminder_date to each event entry as a point of comparison between each event so the event with the most recent reminder comes first, then reverses it to be in descending order
    else:
        print("Sorting events in ascending order")
        events_with_images.sort(key=earliest_reminder_date) # sorts so the events with the earliest reminder in ascending order
    print("Rendering template with pulled events")
    return render_template('events.html', events=events_with_images, sort_order=sort_order)

def latest_reminder_date(event):
    '''
        Function: returns the latest reminder date for an event element in a list of parsed event object dictionaries
        Args:
            event (dict), dictionary of the attributes of queried Event objects
    '''
    print(f"\n\nLATEST_REMINDER_DATE.APP.PY: Fetching latest reminder from Event {event}, ")
    print(f"{max(reminder.date_time for reminder in event['reminders'])}\n")
    return max(reminder.date_time for reminder in event['reminders'])

def earliest_reminder_date(event):
    '''
        Function: returns the earliest reminder date for an event element in a list of parsed event object dictionaries
        Args:
            event (dict), dictionary of the attributes of queried Event objects
    '''    
    print(f"\n\nEARLIEST_REMINDER_DATE.APP.PY: Fetching earilest reminder from Event {event}")
    print(f"{min(reminder.date_time for reminder in event['reminders'])}")
    return min(reminder.date_time for reminder in event['reminders'])

def add_image_filepath_to_event_dictionary(events_with_reminders):
    '''
        Function: The Event object lacks an attribute that associates the object with an image filepath
        Args:
            events_with_reminders (list): contains a series of dictionaries containing the event data for all relevant objects to be displayed
        Returns:
            events_with_reminders (list): A modified list containing file paths when relevant, default image is None
    '''
    print(f"\n\nADD_IMAGE_FILEPATH_TO_EVENT_DICTIONARY.APP.PY: Attaching available image filepaths to event dictionaries")
    print("Current events: ")
    for event_print in events_with_reminders:
        print(f"{event_print}")
    try:
        for event in events_with_reminders:
            print(f"\nProcessing {event}")
            event['image_path'] = None # Initialize default image_path 
            for ext in ['png', 'jpg', 'jpeg', 'gif']:
                possible_path = os.path.join('static', f"{event['id']}.{ext}") # Tests if the image associated with an alarm ID is valid
                full_path = os.path.join(app.root_path, possible_path) # Joins that path with the absolute path of the current working directory
                if os.path.isfile(full_path): # If this path is valid
                    event['image_path'] = f"{event['id']}.{ext}" # Store the image path in the parsed event object dictionary
                    print(f"Path found for Event {event} at {full_path}")
                    break # No need to look any further
    except Exception as ex:
        print(f"Error in add_image_filepath_to_event_dictionary.app.py, {ex}\n")
    print(f"Revised event dictionary with file paths: {events_with_reminders}\n")
    return events_with_reminders # Return list of parsed event dictionary objects with the added image filepath (if present)

def relevant_events_filter(events_query):
    '''
        Function: Takes an Event Query object and parses the data into a list of dictionaries for interpretation at the scripting level
        Args:
            events_query (Query), a query containing Event instances
        Returns:
            events_with_reminders (list), a list of dictionaries containing all the data to be handled by the HTML form
    '''
    print("\n\nRELEVANT_EVENTS_FILTER.APP.PY: Converting pulled events to a dictionary")
    events_with_reminders = []
    for event in events_query:
        print(f"\nProcessing event: {event}")
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
            print(f"Parsed event: {event_data}")
            events_with_reminders.append(event_data)
        except ValueError as e:
            print(f"No reminders associated with this event, {e}")
    print(f"Full dictionary of pulled events: {events_with_reminders}\n\n")
    return events_with_reminders

@app.route('/delete-event/<int:event_id>', methods = ['POST'])
def delete_event(event_id):
    '''
        Function: delete_event, switches event_lock to True to inactivate events and associated reminders
        Args:
            event_id: submitted as part of the URL, corresponds to the SQL row representing the event
        Returns:
            Redirects to events page with deleted events removed
    '''
    event_to_delete = db.session.query(Event).filter(Event.id == event_id).one_or_none()
    print(f"\n\nDELETE_EVENT.APP.PY: Route triggered to delete event for {event_to_delete}")
    reminders_to_delete = event_to_delete.reminders.all()
    if event_to_delete:
        print(f"Setting {event_to_delete} event_lock flag to True")
        event_to_delete.event_lock = True
        for reminder in reminders_to_delete:
            print(f"Disabling reminder {reminder}")
            reminder.reminder_lock = True
            try:
                print("Attempting to commit change to database\n")
                db.session.commit()
                flash(f"{event_to_delete} deleted successfully")
            except Exception as ex:
                db.session.rollback()
                flash(f"Error occurred when deleting {event_to_delete}: {ex}")
    else:
        flash(f"Event {event_id} does not exist\n")
    return redirect(url_for('events'))


if __name__ == "__main__":
    app.run(debug=True)
