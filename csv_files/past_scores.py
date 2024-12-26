import csv
import sqlite3
from datetime import datetime, timedelta
import os

# Paths to the CSV file and SQLite database
csv_file = "past_scores.csv"
db_file = os.path.join("..", "player_metrics.db")  # Database in the parent folder

def convert_monday_to_sunday(date_str):
    """
    Convert a Monday date to the previous Sunday.
    Assumes the input date is in YYYY-MM-DD format.
    """
    date = datetime.strptime(date_str, "%Y-%m-%d")
    if date.weekday() == 0:  # 0 = Monday
        date -= timedelta(days=1)  # Go back one day to Sunday
    return date.strftime("%Y-%m-%d")

def calculate_friday_before(date_str):
    """
    Calculate the Friday before a given date.
    Assumes the input date is in YYYY-MM-DD format.
    """
    date = datetime.strptime(date_str, "%Y-%m-%d")
    return (date - timedelta(days=(date.weekday() + 3) % 7)).strftime("%Y-%m-%d")

def import_scores_from_csv(csv_file, db_file):
    # Connect to the SQLite database
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()

    # Read the CSV file
    with open(csv_file, "r") as file:
        reader = csv.reader(file)
        headers = next(reader)  # First row contains column headers (dates)

        # Parse and adjust the dates (skip the first column for player tags)
        weekend_dates = [convert_monday_to_sunday(date) for date in headers[1:]]
        earliest_date = calculate_friday_before(min(weekend_dates))  # Friday before the earliest tournament date

        for row in reader:
            player_tag = row[0]
            scores = row[1:]

            # Insert the player into the players table if not already exists
            cursor.execute("""
            INSERT OR IGNORE INTO players (player_tag, is_active, join_date)
            VALUES (?, 1, ?)
            """, (player_tag, earliest_date))

            # Retrieve the player_id and join_date
            cursor.execute("SELECT player_id, join_date FROM players WHERE player_tag = ?", (player_tag,))
            player = cursor.fetchone()  # Fetch one row as a tuple

            if player:
                player_id, current_join_date = player

                # Treat empty string as None
                if not current_join_date:  # Handles both None and ''
                    print(f"Player {player_tag} has no join_date, setting to {earliest_date}")
                    update_join_date = True
                else:
                    # Convert current_join_date to datetime for comparison
                    current_join_date = datetime.strptime(current_join_date, "%Y-%m-%d")
                    earliest_date_dt = datetime.strptime(earliest_date, "%Y-%m-%d")
                    # Compare dates
                    update_join_date = current_join_date > earliest_date_dt

                # Update the join_date if necessary
                if update_join_date:
                    print(f"Updating join_date for player_id {player_id} ({player_tag}) to {earliest_date}")
                    cursor.execute("""
                    UPDATE players
                    SET join_date = ?
                    WHERE player_id = ?
                    """, (earliest_date, player_id))
            else:
                print(f"Player {player_tag} not found in players table.")
                continue

            # Insert scores for each weekend
            for i, score in enumerate(scores):
                if score:  # Skip empty scores
                    weekend_date = weekend_dates[i]
                    #cursor.execute("""
                    #INSERT INTO scores (player_id, score, weekend_date)
                    #VALUES (?, ?, ?)
                    #""", (player_id, int(score), weekend_date))

    # Commit and close the connection
    connection.commit()
    connection.close()
    print("Data successfully imported from CSV.")

# Run the import
import_scores_from_csv(csv_file, db_file)
