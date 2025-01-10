import pytz
from datetime import datetime, time
import time as time_module

def is_within_time_range(start_time, end_time, current_time):
    return start_time <= current_time <= end_time

def main():
    # Define the time range and days of the week
    start_time = time(9, 0)  # 9:00 AM
    end_time = time(17, 0)   # 5:00 PM
    days_of_week = {0, 1, 2, 3, 4}  # Monday to Friday

    # Define the time zone
    tz = pytz.timezone('Canada/Regina')

    while True:
        # Get the current time in the specified time zone
        current_time = datetime.now(tz)
        current_time_only = current_time.time()
        current_day_of_week = current_time.weekday()

        # Check if the current time is within the specified range and day of the week
        if current_day_of_week in days_of_week and is_within_time_range(start_time, end_time, current_time_only):
            # Run your code here
            print("Running code...")
            # Add your code here

        # Sleep for a while before checking again
        time_module.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()