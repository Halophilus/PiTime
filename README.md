# PiTime - Software Documentation

![PiTime Title](/docs/title.png)


## Table of Contents
1. [Introduction](#introduction)
2. [Overview](#overview)
   - [Target Audience](#target-audience)
   - [Hardware Compatibility](#hardware-compatibility)
3. [Key Features](#key-features)
   - [Future Enhancements](#future-enhancements)
4. [Hardware and Software Requirements](#hardware-and-software-requirements)
   - [Hardware](#hardware)
   - [Software](#software)
   - [Script Details](#script-details)
5. [Installation and Setup](#installation-and-setup)
   - [Raspberry Pi Setup](#raspberry-pi-setup)
   - [Database Configuration](#database-configuration)
   - [Hardware Connections](#hardware-connections)
6. [Usage](#usage)
   - [Running the Flask Server](#running-the-flask-server)
   - [Web Interface](#web-interface)
   - [Raspberry Pi Interactions](#raspberry-pi-interactions)
7. [User Interface](#user-interface)
   - [Event Submission Page](#event-submission-page)
   - [Event Details Page](#event-details-page)
   - [Event Deletion](#event-deletion)
8. [Known Issues and Limitations](#known-issues-and-limitations)
9. [Future Enhancements](#future-enhancements-1)
10. [Contact Information](#contact-information)
11. [License](#license)

## Introduction
This project is a Flask-based web application designed to help disorganized individuals, particularly in areas of time management and task organization to overcome time blindness, habituation to existing alarm systems, the limitations of task switching with a simple, uncluttered UI, and the curse of easily-snoozed reminders. The web form and events page is extremely simple, allowing for event creation with an arbitrary number of reminders. Instead of having to set 100 individual alarms or separate reminders for an event, this allows for single, centralized events with an arbitrary number of reminders. Custom images can be associated with events, providing an added element of recall. Various alarm hardware allows for dynamic alarms without the need for a phone to be present, including a loud beeper (or buzzer), a vibration motor, and a speaker. The alarm system allows the user to pick an urgency associated with a reminder, and then an alarm audio file will be randomly selected from a pool of alarms associated with that urgency, reducing the predictability of the alarm system. This system allows many reminders to be triggered at the same time, aggregating all of the attributes from each reminder triggered and updating the urgency of the alarm if a more urgent reminder is triggered. The alarm will then not stop until the alarm loop is disengaged. Standard reminders can be disengaged with the snooze button: a physical button attached to the Raspberry Pi. Web-unlock reminders have an additional protocol. The main script will generate a 32 character string, which is then displayed on the LCD screen, after which the screen's backlight turns off. It is up to the user to enter that string as an extension of a URL to the webpage, which then disengages the web-unlock flag. Since this device does not require the presence of a phone to function, it forces the user to get up, turn the light on, and get their phone to turn off the app. The font on the LCD is not always supremely legible, so it creates a mental task of turning off the alarm that cannot be ignored or snoozed. When the alarm loop is disengaged, the device reads out the event information in text-to-speech. It does so very quietly, so the user must focus in order to hear it. This approach ensures that reminders are noticeable, persistent, customizable, and hard to ignore. 

## Overview
The system comprises several interconnected components:
- A Flask web server to manage user inputs for alarms and reminders that can be accessed locally.
- A SQLite database to store event and reminder data.
- A Raspberry Pi (developed on Raspberry Pi Zero for its compact size) that interacts with various hardware components to manifest physical alarm signals.
- Hardware interactions include buzzing, vibration, and audio output, controlled by custom Python classes tailored to the specific hardware used.

This application is particularly suited for individuals seeking a more engaging and hard-to-ignore method of receiving reminders.

### Target Audience
- Individuals with executive dysfunction.
- Anyone who requires a more effective and persistent reminder system than typical digital notifications.

### Hardware Compatibility
- The project is developed on a Raspberry Pi Zero but can be adapted for use with other microcontrollers compatible with the gpiozero library or similar GPIO manipulation libraries.
- See the [Hardware Summary](hardware_summary.md) for more information.

## Key Features
- User-friendly web interface for setting events and reminders, as well as viewing/deleting existing events.
- Physical alarm signals including sound (speaker and buzzer), vibration, and visual cues via Raspberry Pi.
- Customizable hardware interactions to suit individual needs and preferences.
-  Assignment of an arbitrary number of reminders to a given event, with the option to select different alarm types depending on the nature of the reminder.
- Prescribed repetition of reminders for recurring events.
- A persistent alarm system that aggregates alarm notification types when many are triggered simultaneously, but doesn't stop until the user successfully terminates the alarm.
- An audio alarm system that selects a random alarm audio file based on urgency, and updates the alarm if another reminder is triggered of a higher urgency.
- A two part alarm-unlock system:
    - A snooze button which disengages a global variable associated with active alarms
    - OPTIONAL: a web-unlock feature that requires the user to enter a random string into a URL to trigger a route that disables the alarm.
- Text-to-speech reading of all active event details from the currently triggered reminders when an alarm is successfully disabled

### Future Enhancements
- Integration of a higher volume audio amplifier for louder alarms.
- Development of a web page for testing hardware functions and adjusting general settings.
- Implementation of variable buzzer volumes controlled by a potentiometer.
- Feature to display IP address on the LCD screen using a snooze button.
- Diverse UI options for clearer distinction between AM and PM reminders.
- Email and text message reminders.
- A custom 3D-printed case to house the Raspberry Pi and other components.

---
## Hardware and Software Requirements

### Hardware
- **Raspberry Pi Zero**: Preferred for its compact size. The system is adaptable for other Raspberry Pi models or similar microcontrollers. This is the device on which the web app will be hosted as well as the actuator of GPIO devices.
    - Must be connected to a local network.
    - Can be debugged using SSH and tmux for concurrent script evaluation.
    - LCD displays device IP on startup for easy user access.
- **Piezoelectric Buzzer**: For audible alarm signals.
    - Future versions will allow different volumes.
- **Vibration Motor**: To provide physical alert signals.
- **Speaker**: For text-to-speech announcements and customizable alarm sounds. 
    - For the RPi Zero, this requires an additional off-board filter and amp.
- **Additional Components**: Future enhancements may include an LM386 for higher volume control, potentiometers for adjustable buzzer volume, and a custom 3D-printed case.

### Software
- **Operating System**: Raspberry Pi OS Buster was used for this project, but it isn't a requirement for functioning.
- **Python 3**: The scripts are written in Python 3.
- **Flask**: For running the web server.
- **SQLAlchemy**: For database management.
- **gpiozero**: For controlling Raspberry Pi GPIO pins.
- **pyttsx3**: For text-to-speech functionalities.
- **pygame**: For handling audio playback in the `Speaker` class.

### Script Details

#### app.py
This script is the backbone of the web application, facilitating user interactions and data management.
- **Flask Setup**: Initializes the Flask app, configures the database, and sets up routes.
- **Web Routes**: Includes routes for creating, viewing, and managing alarms/reminders.
- **Database Interaction**: Uses SQLAlchemy for database operations related to events and reminders.
- **File Handling**: Manages image files for events.
- **Form Processing**: Takes HTML POST form submission data and uses it to generate Alarm and associated Reminder objects.
- **Security**: Basic security setup with Flask, suitable for a closed network environment.

#### models.py
Defines database models to structure event and reminder data.
- **Event Model**: Stores information about each event, including title, description, and related reminders.
- **Reminder Model**: Details for each reminder, such as date/time, types of alerts (buzzer, vibration, etc.), and repeat frequency.
- Both objects contain flags to determine if they are active or not.
    - Events will be flagged inactive when they are deleted
    - Reminders will be flagged inactive if they have already been triggered and there is no present repeater.

#### rpi_main.py
Runs on the Raspberry Pi, handling physical alarms based on web app data.
- **Global Variables**: Manages state information like alarm triggers, options, and events from currently triggered reminders.
- **Reminder Processing**: Fetches active reminders and updates global state.
- **Hardware Interactions**:
    - Controls buzzer, vibration, and speaker based on reminder settings.
    - I2C LCD web unlock keys are displayed for relevant alarms.
- **Snooze Functionality**: 
    - Physical button provides a method to disable simple alarms.
    - Web unlock presents a more engaging, challenging task to disable active alarms.
    - The button must always be pressed to disable alarms, but for web-unlock alarms both procedures must be followed.

#### rpi_models.py
Contains classes for controlling individual hardware components without interrupting the flow of the code in rpi_main.py
- **Buzzer Class**: Manages the piezoelectric buzzer with threading for asynchronous operation.
- **Vibration Class**: Controls a vibration motor, similar to the buzzer class in terms of threading.
- **Speaker Class**: Handles audio output, playing alarms with varying urgency levels.

---

## Installation and Setup

### Raspberry Pi Setup
1. Install the latest version of Raspberry Pi OS.
    - Configure the OS to have the login details for your local network so that it automatically connects.
    - Set up the OS for SSH in the Raspbian install manager for remote access. This is the easiest way to access a RPi Zero. If done properly, the device's console can be accessed remotely through PowerShell after the device powers on:
    ```bash
    ssh user@device_name.local
    ```
    - Ensure that the distribution is up to date:
    ```bash
    sudo apt-get update
    sudo apt-get upgrade
    ```
    - If debugging is necessary, download the `tmux` application to view the console statements from multiple scripts concurrently from the same terminal window.
    ```bash
    sudo apt-get update
    sudo apt-get install tmux
    ```
    - Ensure that git is installed correctly
    ```bash
    git --version
    ```
2. Clone the `PiTime` git repository.
```bash
cd /path
git clone https://github.com/Halophilus/PiTime.git
cd /PiTime
```
3. Use `crontab` to schedule `app.py` and `rpi_main.py` to load simultaneously on boot.
    - Open the Crontab file for editing
    ```bash
    sudo crontab -e
    ```
    - Add delayed execution entries. This will allow the RPi to latch onto a local network before attempting to start the Flask server. Assume that `/path` represents the chosen directory for the git repository
    ```bash
    @reboot sleep 30 && /usr/bin/python3 /path/PiTime/app.py
    @reboot sleep 30 && /usr/bin/python3 /path/PiTime/rpi_main.py
    ```
    - Save and exit: press `ctrl + x` then `y` then `enter`.
    - Check to see if the new cronjobs have been added:
    ```bash
    crontab -l
    ```
4. Ensure that each file has execute permissions with the following command:
    ```bash
    sudo chmod +x /path/PiTime/app.py
    sudo chmod +x /path/PiTime/rpi_main.py
    ```
5. Configure audio for GPIO PWM:
    ```bash
    sudo nano /boot/config.txt
    ```
    - Add the following line to enable PWM audio at GPIO13
    ```bash
    dtoverlay=pwm,pin=13,func=4
    ```
    - Save and close config.txt
5. Enable I2C LCD Displays in `raspi-config`
    - Run `sudo raspi-config` in the terminal
    - Navigate to `Interfacing Options`
    - Select `I2C` and choose `<Yes>`
    - Exit `raspi-config`
    - Verify that I2C is enabled by running the following:
    ```bash
    lsmod | grep i2c
    ```
6. Ensure Python 3.X and pip are installed.
7. Install all software dependencies.
```bash
pip install Flask SQLAlchemy gpiozero pyttsx3 pygame
```
7. Rebooting the device will run those two scripts on startup.
```bash
sudo reboot
```
- To debug, kill the tasks in SSH and run them independently in `tmux` windows to view the console output.

### Database Configuration
-  The application uses SQLAlchemy to interact with a SQLite database.
- On first run, the application should initialize the database with tables specified by `models.py`

### Hardware Connections
- Make sure that all of the device objects in code are assigned to GPIO pins that match their point of connection to the RPi.
- Refer to the [Hardware Summary](hardware_summary.md) for more information.

## Usage

### Running the Flask Server
1. Given the above configuration, `app.py` and `rpi_main.py` should be loaded automatically upon boot.
2. Given a valid local network, the web interface will become accessible from any device on that network.
3. The IP for the device is presented on the LCD screen upon boot.

### Web Interface

- **Flask App Initialization**: The script initializes a Flask application, configures its parameters, and sets up an SQLite database for storing event and reminder data.

- **Routes and Functionality**:
    - `@app.route("/")`: Displays the alarm submission form.
    - `@app.route('/submit', methods=['POST'])`: Handles form submission, processes user input, and stores event and reminder data in the database. Also handles image uploads for events.
    - `@app.route('/unlock/<path:key>')`: A route for web-unlock functionality through the web interface.
    - `@app.route('/events')`: Displays active alarms and associated information.
    - `@app.route('/delete-event/<int:event_id>', methods=['POST'])`: Allows for the deletion of events.

- **Helper Functions**:
    - `validate_reminders`: Validates reminder dates and times.
    - `parse_form_data`: Parses form data to structure event and reminder information.
    - `add_event_and_reminders` `: Creates event and reminder objects and commits them to the database.
    - `clear_web_unlock`: Clears the web unlock status.
    - `read_unlock_val`: Reads the unlock key from a file.
    Plus various functions for sorting and processing event data.

- **Database Models**: Uses SQLAlchemy for database interactions. The models include `Event` and `Reminder`.
    - **`Event`**
        - `id`, primary key for distinguishing `Event` objects
        - `title`, string of 120 chars or less
        - `description`, string of 500 chars or less
        - `event_lock`, boolean determining if an `Event` object is active or not
        - `reminders`, `Reminder` objects back reference a parent `Event` object in a one to many Events to Reminders dynamic relationship. This allows an Event's connected reminders to be queryable from the original `Event` object.
    -**`Reminder`**
        - `id`
        - `date_time`, datetime object indicating timepoint associated with alarm trigger
        - `reminder_lock`, boolean indicating if an alarm is inactive or not.
        - `buzzer`, boolean controlling buzzer functionality
        - `vibration`, bool.
        - `alarm`, string associated with the relative urgency of an audio alarm. If alarm is not enabled, then it is set to `None`.
        - `repeater`, string associated with the frequency with which a given reminder repeats. If a reminder is triggered and it has a repeater, its `date_time` will be adjusted accordingly. If the repeater is set to 'Never', then `reminder_lock` will be set to True.
        - `event_id`, integer foreign key connecting a `Reminder` instance to an `Event.id`.

- **File Handling**: Manages image files related to events, storing them in a specified folder.
    - Event images are not stored in the Event library, and are instead saved as files in `/static` with names corresponding to an `Event.id`. When the events page is rendered, it searches the folder for images that match active events and displays them next to the listed event.


- **Raspberry Pi Interactions**:
    - **Physical Alarm Indicators**: when an event's reminder's time is reached, the `rpi_main.py` script triggers connected hardware based on the reminder's attributes. `rpi_main.py` imports the dame database engine used in `models.py` and uses Flask and FlaskSQLAlchemy to query it without running an additional server in the context of that session.
    - **Snooze Button**: a physical button is present to snooze alarms without the `web_unlock` flag.
    - **Web Unlock**: The most direct interactions between the two scripts.
        - When a web-unlock reminder is triggered, it overwrites a txt flag and writes a randomly-generated 32 character string to a txt file in the same folder.
        - The string is displayed on the I2C LCD display, whose backlight promptly turns off. This makes it impossible to read in the dark.
        - The user must then visit the URL of form `0.0.0.0:5000/unlock/<unlock key>`, which then resets the flag.
        -`rpi_main.py` detects this change and releases the web unlock.
    - **LCD Display**: other than the web-unlock key, it also displays the date and time, the device's IP (presently only on startup), and triggered event information.
    - **Speaker Audio**: Other than playing alarm sounds, when the alarm loop has been disengaged it will read out the titles and descriptions for all of the triggered events. 

---
## User Interface


### Event Submission Page
- **Structure / Design**:
    - Homepage.
    - Text entry boxes for the event title and description.
        - HTML enforces character limits within the text forms.
        - 120char for Event Title
        - 500char for Event Description
        - These are required fields and are used to declare an `Event` object.
    - An upload field for the reminder image
        - After POST, the Flask server will filter out any non-image uploads.
        - Those with successful image uploads will have the file renamed after the event's `id` ane saved in static as `/static/{id}.{img_ext}`.
- **Navigation bar**:
    - Contains a link to the Events page.
- **Reminder**:
    - Dynamic field for entering `Reminder` attributes.
    - There will always be at least one available Reminder field on the screen as events require at least one reminder to be valid.
    - Additional reminders can be added and removed as necessary.
    - Time and date are required fields but the remaining fields are optional

![PiTime Alarm Form](/docs/readme/form.png)

- **Behavior of Provided Input**:
    - **Object Declaration**:
        - An `Event` object is created and committed to the database.
            - Title: `Write the README for PiTime`
            - Description: `Compile relevant information about the[...]useful`
        - An image is uploaded associated with this event, but is tangentially connected to the actual object.
        - Two reminders are created:
            - **Reminder 1**
                - date_time: 0030, 12/21/2023
                - Repeats `Never`
                - Optional flags: Vibration, Alarm (`Somewhat`)
            - **Reminder 2**
                - date_time: 0035, 12/21/2023
                - Repeats `Hourly`
                - Optional flags: Buzzer, Web_unlock, Alarm (`Extremely`)
            - Both of these reminders reference their parent Event.

- **Reminder Behavior**
    - If Reminder 1 isn't snoozed before Reminder 2 is triggered:
        - All of the alarm options from Reminder 2 will union with those from Reminder 1,  adding to the existing set of alarm triggers for the ongoing alarm.
        - Despite the fact that Reminder 1 did not have Web_Unlock, the procedure to read the random string back to the server will be necessary to disable the options inherited from Reminder 1.
        - The alarm urgency will be upgraded to `Extremely`.
    - If Reminder 2 is snoozed initially:
        - Reminder 1's `reminder_lock` will be set to True, deactivating it indefinitely.
        - The `date_time` for Reminder 2 will be adjusted to 1 hour advanced from the time of snooze.
        - The alarm for Reminder 2 will then repeat every hour until deleted.

![Successful Submission](/docs/readme/submit.png)

Flash messages are used to make the user aware of the result of event submission. One of the ways that a submission can go wrong is if is set in the past, as the others have failsafes.

![Failed submission](/docs/readme/fail.png)

### Event Details Page
- **Structure / Design**:
    - Secondary page
    - Can be reached from a navbar link on the homepage.
    - Shows all active events
- **Events**:
    - Event title
    - Event description
    - Itemized connected reminders
        - Date time
        - Alarm urgency
        - Repeater
        - Previously triggered reminders are grayed out.
        - When all associated reminders are inactive, the event also grays out
    - Delete button for whole event
        - Switches `event_lock` to `True`
        - Event will no longer be visible on the events page.
        - All reminders will be deactivated as well.
    - Edit button for events/reminders
        - Currently non-functional
    - Optional image associated with event
- **Navbar**:
    - Link to **Event Submission Page**
    - Sorting options:

![Ascending Order](/docs/readme/asc.png)

Ascending order will sort events by earliest reminder event from earliest to latest datetimes.

![Descending Order](/docs/readme/desc.png)

Descending order will sort events by earliest reminder event from latest to earliest datetimes

- **Flash Messages**
    - Flash messages are returned when events are deleted for confirmation.
    - For every reminder in the event, a message indicating which event is being deleted is provided.

![Flash Message for Delete](/docs/readme/delete.png)

### Event Deletion
- **Structure / Design**
    - There is no formal webpage associated with this function, just a return message depending on the success of the web-unlock attempt.
    - If the user enters a key that matches the stored key generated by the `rpi_main.py` script, the Flask server will reset the web-unlock flag and wipe the key. This message will be displayed:

![Web-unlock Success](/docs/readme/unlock.png)

If the user enters an incorrect key, this message will be displayed:

![Web-unlock failure](/docs/readme/lock.png)

---
## Known Issues and Limitations

- **Volume Control**: The current system does not support dynamic volume control for the speaker and buzzer.
- **Hardware Testing Interface**: There is no dedicated interface for testing and adjusting the settings of the hardware components. This will eventually be added as an additional page that can be accessed from within the web app.
- **Security Aspects**: The application is designed for use in a closed or private network and has not been extensively tested for security vulnerabilities in a broader network environment.
- **IP Display**: The IP of the device is only displayed on startup, but realistically this information should be accessible at any time, possibly through a snooze button press.
- **Reading Upcoming Events**: The user should be able to access daily event information without accessing the web app. In the future I will add a button press event that reads off upcoming events.


## Future Enhancements

1. **Hardware Control Improvements**:
    - Implement an LM386 or similar component for enhanced audio amplifier functionality.
    - Introduce a potentiometer or similar control mechanism for adjustable buzzer volume.
    - Develop a 3D-printed case for housing the Raspberry Pi and hardware components neatly.

2. **Software Features**:
    - Develop a web interface for hardware function testing and general settings adjustments.
    - Add functionality to check the Raspberry Pi's IP address on the LCD screen via a button press.
    - Enhance the web UI to differentiate AM and PM reminders visually.
    - Integrate email and text message reminder capabilities.

3. **Security Enhancements**:
    - Conduct a thorough security review and implement necessary measures for safer use on broader networks.

4. **Editing Events**:
    - A feature for editing existing events.
    - Currently, the option is to delete old events and create a new one.

## Contact Information

If you encounter issues or have questions regarding the setup or operation of this system, please reach out to [Halophilus](email:benshaw@halophil.us).

---

## License
This project is licensed under the GNU General Public License v3.0 - see the [LICENSE file](LICENSE.txt) for details.
