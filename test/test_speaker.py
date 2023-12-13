import time
from rpi_models import Speaker

def test_speaker():
    print("Testing Speaker with different urgencies")

    # Create a Speaker with the lowest urgency
    speaker = Speaker('None')
    
    # Define the urgencies to test
    urgencies = ['Not at all', 'Somewhat', 'Urgent', 'Very', 'Extremely']

    # Test updating the urgency
    for urgency in urgencies:
        print(f"Updating Speaker urgency to: {urgency}")
        speaker.update_urgency(urgency)
        speaker.start()
        print("Playing sound. Waiting for 5 seconds...")
        time.sleep(5)  # Let the sound play for 5 seconds
        speaker.stop()
        print(f"Finished testing {urgency}.\n")

    # Reset the Speaker to None urgency at the end
    speaker.update_urgency('None')
    print("All tests completed.")

# Run the test
test_speaker()
