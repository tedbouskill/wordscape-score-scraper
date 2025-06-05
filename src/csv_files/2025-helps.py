import csv
import sqlite3
from datetime import datetime

# File paths
csv_file_path = '/Users/tedbouskill/Repos/MyGitHub/wordscape-score-scraper/src/csv_files/2025-helps.csv'
db_path = '/Users/tedbouskill/Repos/MyGitHub/wordscape-score-scraper/player_metrics.db'

# Connect to the SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Read the CSV file
with open(csv_file_path, 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        player_tag = row['Player Tag']

        # Get the player ID from the players table
        cursor.execute("SELECT player_id FROM players WHERE LOWER(player_tag) = LOWER(?)", (player_tag,))
        player_id = cursor.fetchone()

        if player_id:
            player_id = player_id[0]
            for weekend_date, helps in row.items():
                if weekend_date != 'Player Tag':
                    # Convert the weekend_date to a proper date format
                    weekend_date = datetime.strptime(weekend_date, '%Y-%m-%d').date()

                    # Insert the data into the weekly_player_stats table
                    cursor.execute("""
                        INSERT INTO weekly_player_stats (weekend_date, player_id, helps)
                        VALUES (?, ?, ?)
                    """, (weekend_date, player_id, helps))

# Commit the transaction and close the connection
conn.commit()
conn.close()