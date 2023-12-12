import unittest
from unittest.mock import patch
from rpi_main import *

class TestRPIFunctions(unittest.TestCase):
    def setUp(self):
        # Setup before each test
        initialize_globals()

    def test_initialize_globals(self):
        # Test if the global variables are initialized correctly
        self.assertFalse(alarm_trigger)
        self.assertEqual(options_dict, {'buzzer': False, 'vibration': False, 'web_unlock': False, 'alarm': {'None'}})
        self.assertEqual(current_events_dict, {})
        self.assertEqual(current_urgency, 'None')

    @patch('RPI_main.Reminder.query')
    def test_fetch_active_reminders(self, mock_query):
        # Mock the database query and test fetch_active_reminders function
        mock_query.join.filter.filter.return_value.all.return_value = []
        reminders = fetch_active_reminders()
        self.assertEqual(reminders, [])

    def test_reminder_looper(self):
        # Test reminder_looper function with various repeater values
        original_datetime = datetime(2021, 1, 1, 12, 0)
        self.assertEqual(reminder_looper(original_datetime, "Never"), original_datetime)
        self.assertEqual(reminder_looper(original_datetime, "Daily"), original_datetime + relativedelta(days=1))
        self.assertEqual(reminder_looper(original_datetime, "Monthly"), original_datetime + relativedelta(months=1))
        # Add more assertions for other repeater values

    @patch('RPI_main.db.session.commit')
    def test_update_reminder(self, mock_commit):
        # Test update_reminder function with a mock reminder
        reminder = Reminder(date_time=datetime.now(), repeater='Never', reminder_lock=False)
        update_reminder(reminder)
        self.assertTrue(reminder.reminder_lock)
        mock_commit.assert_called_once()

    @patch('RPI_main.speak')
    def test_speak(self, mock_speak):
        # Test if speak function is calling with correct parameter
        speech = "Test speech"
        speak(speech)
        mock_speak.assert_called_with(speech)

    def test_reset(self):
        # Test if reset function correctly resets global variables
        reset()
        self.assertFalse(alarm_trigger)
        self.assertEqual(options_dict, {'buzzer': False, 'vibration': False, 'web_unlock': False, 'alarm': {'None'}})
        self.assertEqual(current_events_dict, {})
        self.assertEqual(current_urgency, 'None')

    @patch('RPI_main.write_to_file')
    def test_set_web_unlock(self, mock_write_to_file):
        # Test set_web_unlock function with different flags
        set_web_unlock(True)
        mock_write_to_file.assert_any_call('alarm.txt', '1')
        set_web_unlock(False)
        mock_write_to_file.assert_called_with('alarm.txt', '')




if __name__ == '__main__':
    unittest.main()
