class Event:
    def __init__(self, title, description, date_time, buzzer, vibration, spoken, alarm_on, alarm_ID, web_unlock):
        self._title = title
        self._description = description
        self._date_time = date_time
        self._buzzer = buzzer
        self._vibration = vibration
        self._spoken = spoken
        self._alarm_on = alarm_on
        self._alarm_ID = alarm_ID
        self._web_unlock = web_unlock
        self._reminders = []

    # Accessor methods
    def get_title(self):
        return self._title

    def get_description(self):
        return self._description

    def get_date_time(self):
        return self._date_time

    def get_buzzer(self):
        return self._buzzer

    def get_vibration(self):
        return self._vibration

    def get_spoken(self):
        return self._spoken

    def get_alarm_on(self):
        return self._alarm_on

    def get_alarm_ID(self):
        return self._alarm_ID

    def get_web_unlock(self):
        return self._web_unlock

    def get_reminders(self):
        return self._reminders

    # Mutator methods
    def set_title(self, title):
        self._title = title

    def set_description(self, description):
        self._description = description

    def set_date_time(self, date_time):
        self._date_time = date_time

    def set_buzzer(self, buzzer):
        self._buzzer = buzzer

    def set_vibration(self, vibration):
        self._vibration = vibration

    def set_spoken(self, spoken):
        self._spoken = spoken

    def set_alarm_on(self, alarm_on):
        self._alarm_on = alarm_on

    def set_alarm_ID(self, alarm_ID):
        self._alarm_ID = alarm_ID

    def set_web_unlock(self, web_unlock):
        self._web_unlock = web_unlock

    def add_reminder(self, date_time, buzzer, vibration, spoken, alarm_on, alarm_ID, web_unlock):
        reminder = Event(None, None, date_time, buzzer, vibration, spoken, alarm_on, alarm_ID, web_unlock)
        self._reminders.append(reminder)

    def __str__(self):
        return f"Title: {self._title}\nDescription: {self._description}\nDateTime: {self._date_time}\nBuzzer: {self._buzzer}\nVibration: {self._vibration}\nSpoken: {self._spoken}\nAlarm: {'On' if self._alarm_on else 'Off'}\nAlarm ID: {self._alarm_ID}\nWeb Unlock: {self._web_unlock}\nReminders: {len(self._reminders)}"

    def list_reminders(self):
        for index, reminder in enumerate(self._reminders, 1):
            print(f"Reminder {index} - DateTime: {reminder.get_date_time()}, Buzzer: {reminder.get_buzzer()}, Vibration: {reminder.get_vibration()}, Spoken: {reminder.get_spoken()}")
