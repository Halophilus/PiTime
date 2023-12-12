import unittest
from app import app, db, Event, Reminder
from datetime import datetime

class FlaskAppTests(unittest.TestCase):
    def setUp(self):
        # Set up a test client and create a testing environment
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory database
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        # Clear up after each test
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_index_route(self):
        # Test the index route
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_submit_route(self):
        # Test the submit route
        test_event = {
            'main_event_title': 'Test Event',
            'main_event_description': 'Test Description',
            'reminder_time[]': ['12:00'],
            'reminder_date[]': [str(datetime.now().date())]
        }
        response = self.app.post('/submit', data=test_event)
        self.assertEqual(response.status_code, 302)  # Check for redirect after submission

    def test_event_creation(self):
        # Test if an event is created successfully
        with app.app_context():
            event = Event(title='Test Event', description='Test Description')
            db.session.add(event)
            db.session.commit()
            self.assertIsNotNone(Event.query.filter_by(title='Test Event').first())

if __name__ == '__main__':
    unittest.main()
