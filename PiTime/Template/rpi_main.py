from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from models import db, Event, Reminder
from time import sleep
from datetime import datetime
from dateutil.relativedelta import relativedelta

engine = create_engine('sqlite:///alarm-reminder.db') # initialize database engine
db_session = scoped_session(sessionmaker(bind=engine)) # bind to current session

def reminder_looper(original_datetime, repeater):
      '''
        Function: reminder_looper, adds a set amount of time to the reminder time based on repeater value
        Parameters:
            original_datetime, datetime
            repeater, str, from 
      '''
while True:
    sleep(60)
    current_time = datetime.now()
    ## PULL LIST OF REMINDERS ##
        # DATETIME BEFORE CURRENT DATETIME
        # REMINDER_LOCK
    ## FOR ALL TRIGGERED REMINDERS ##
        # IF REPEATER == NEVER
            # REMINDER_LOCK = False
        # IF REPEATER == DAILY
            reminder_datetime =
    ## COMPILE LIST OF OPTIONS ##
