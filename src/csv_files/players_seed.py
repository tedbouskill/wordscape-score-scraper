import csv
import sqlite3

# Paths to the CSV file and SQLite database
csv_file = "./players_seed.csv"
db_file = "../player_metrics.db"

def seed_players_from_csv(csv_file, db_file):
    # Connect to the SQLite database
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()

    # Read the CSV file
    with open(csv_file, "r") as file:
        reader = csv.DictReader(file)

        for row in reader:
            player_tag = row["player_tag"]
            is_active = int(row["is_active"])
            join_date = row["join_date"]
            leave_date = row["leave_date"] if row["leave_date"] else None

            # Insert new player or ignore if already exists
            cursor.execute("""
            INSERT OR IGNORE INTO players (player_tag, is_active, join_date, leave_date)
            VALUES (?, ?, ?, ?)
            """, (player_tag, is_active, join_date, leave_date))

            # Update existing player's details (except player_tag)
            cursor.execute("""
            UPDATE players
            SET is_active = ?, join_date = ?, leave_date = ?
            WHERE player_tag = ?
            """, (is_active, join_date, leave_date, player_tag))

    # Commit and close the connection
    connection.commit()
    connection.close()
    print("Players successfully seeded from CSV.")

# Run the seeding process
seed_players_from_csv(csv_file, db_file)
