from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import *

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory SQLite database for testing
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize the database
with app.app_context():
    db.create_all()

    # Create sample data
    event1 = Event(title='Birthday Party', description='My 26th birthday')
    reminder1 = Reminder(date_time=datetime(2023, 1, 19, 24, 0), buzzer=True, event=event1)

    # Add to database
    db.session.add(event1)
    db.session.add(reminder1)
    db.session.commit()

    # Query and print data
    events = Event.query.all()
    print('Events in database:')
    for event in events:
        print(event)
        for reminder in event.reminders:
            print(reminder)

    # Update an event
    event_to_update = Event.query.filter_by(title='Birthday Party').first()
    if event_to_update:
        event_to_update.description = 'My 26th birthday'
        db.session.commit()

    # Delete an event
    event_to_delete = Event.query.filter_by(title='Birthday Party').first()
    if event_to_delete:
        db.session.delete(event_to_delete)
        db.session.commit()

    # Print data after modifications
    print('Events after modification:')
    events = Event.query.all()
    for event in events:
        print(event)
