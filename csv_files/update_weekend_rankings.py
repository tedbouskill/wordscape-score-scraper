import sqlite3

def update_weekend_rankings(db_file):
    # Connect to the SQLite database
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()

    # Get all unique weekend dates
    cursor.execute("SELECT DISTINCT weekend_date FROM scores")
    weekend_dates = cursor.fetchall()

    for (weekend_date,) in weekend_dates:
        # Retrieve scores for the weekend, ordered by score descending
        cursor.execute("""
        SELECT score_id, score, player_id
        FROM scores
        WHERE weekend_date = ?
        ORDER BY score DESC, player_id ASC
        """, (weekend_date,))
        scores = cursor.fetchall()

        # Assign ranks
        rank = 1
        for i, (score_id, score, player_id) in enumerate(scores):
            if i > 0 and scores[i - 1][1] == score:  # Check for ties
                # Keep the same rank for tied scores
                rank = rank
            else:
                # Otherwise, increment rank
                rank = i + 1

            # Update the rank in the database
            cursor.execute("""
            UPDATE scores
            SET rank = ?
            WHERE score_id = ?
            """, (rank, score_id))

    # Commit changes and close the connection
    connection.commit()
    connection.close()
    print("Weekend rankings updated successfully.")

# Path to the database
db_file = "../player_metrics.db"

# Update rankings
update_weekend_rankings(db_file)
