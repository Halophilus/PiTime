from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Event(db.Model): # Objects are not being stored in memory and thus do not inherit 'self'
    '''
    Event object based on database model (SQLite), given its own table
        Event.id (int), primary key keeping distinguishing distinct objects, handled by SQLite to avoid redundant Event objects
        Event.title (str), the event title
        Event.description (str), the event description
        Event.reminders (key), backreferences all connected Event objects which is linked by the Event.id value
    '''
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500))
    event_lock = db.Column(db.Boolean, default = False)
    reminders = db.relationship('Reminder', backref='event', lazy='dynamic') # Enabeles a 1 event to many reminders configuration

    def __repr__(self):
        return f"<Event(id='{self.id}', title='{self.title}')>"


class Reminder(db.Model):
    '''
    Reminder object based on database model (SQLite), given its own table
        Reminder.id (int), primary key distringuishing distinct Reminder objects
        Reminder.date_time (datetime), date and time of Reminder object trigger
        Reminder.buzzer (bool), flag for buzzer activity
        Reminder.vibration (bool), flag for vibration activity 
        Reminder.alarm (str), selected alarm urgency
        Reminder.repeater (str), the frequency with which an alarm is set to repeat, date_time adjusted at each trigger by interval repeater
        Reminder.event_id (int), the foreign key from the associated event object (event.id)
    '''
    # Uniquely identify record in the database, set internally
    id = db.Column(db.Integer, primary_key=True)

    # Enforces that this field cannot be empty
    date_time = db.Column(db.DateTime, nullable=False)
    
    # Boolean attributes
    buzzer = db.Column(db.Boolean, default = False)
    vibration = db.Column(db.Boolean, default = False)
    web_unlock = db.Column(db.Boolean, default = False)
    reminder_lock = db.Column(db.Boolean, default = False)
    alarm = db.Column(db.String(120))  # Indicates urgency of the alarm required for this reminder. Hereafter referred to as 'urgency'
    repeater = db.Column(db.String(50)) # String reminder repeat
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False) # Implicit connection to some event object

    def __repr__(self):
        optional_flags = f"buzzer={self.buzzer}, vibration={self.vibration}, web_unlock={self.web_unlock}, reminder_lock={self.reminder_lock}"
        return f"<Reminder(id='{self.id}', event_id='{self.event_id}', date_time='{self.date_time}', alarm='{self.alarm}', repeater='{self.repeater}')\n   Optional Flags: {optional_flags}>"


