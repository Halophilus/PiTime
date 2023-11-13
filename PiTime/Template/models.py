import hashlib
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500))
    reminders = db.relationship('Reminder', backref='event', lazy='dynamic')

class Reminder(db.Model):
    # Uniquely identify record in the database, set internally
    id = db.Column(db.Integer, primary_key=True)

    # Enforces that this field cannot be empty
    date_time = db.Column(db.DateTime, nullable=False)
    
    # Boolean attributes
    buzzer = db.Column(db.Boolean, default=False)
    vibration = db.Column(db.Boolean, default=False)
    spoken = db.Column(db.Boolean, default=False)
    web_unlock = db.Column(db.Boolean, default=False)
    
    alarm = db.Column(db.String(120))  # String alarm selection
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False) # Implicit connection to some event object
