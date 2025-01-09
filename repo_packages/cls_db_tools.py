import sqlite3
import threading

class DbRepositorySingleton:
    _instance = None
    _lock = threading.Lock()  # Lock object to ensure thread safety

    def __new__(cls, *args, **kwargs):
        """
        Ensures only one instance of the class is created, even in a multithreaded environment.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-checked locking
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_path):
        """
        Initialize the singleton instance.
        """
        if not hasattr(self, '_initialized'):
            self.connection = sqlite3.connect(db_path)
            self._initialized = True

    @classmethod
    def cleanup(cls):
        """
        Cleanup method to reset or release resources.
        """
        with cls._lock:
            if cls._instance is not None:
                cls._instance = None

    def __del__(self):
        """
        Destructor to handle cleanup automatically if the singleton is deleted.
        """
        self.connection.close()

    def insert_weekend_player_score(self, weekend_date, player_id, score):
        """
        Insert extracted data into SQLite database.
        """
        cursor = self.connection.cursor()
        insert_query = """
            INSERT OR IGNORE INTO tournament_results (weekend_date, player_id, score)
            VALUES (?, ?, ?)
            """
        cursor.execute(insert_query, (weekend_date, player_id, score))
        self.connection.commit()

        return

    def insert_weekend_team_rank(self, weekend_date, rank):
        """
        Insert extracted data into SQLite database.
        """
        cursor = self.connection.cursor()
        insert_query = """
            INSERT OR IGNORE INTO team_tournament_results (weekend_date, rank)
            VALUES (?, ?)
            """
        cursor.execute(insert_query, (weekend_date, rank))
        self.connection.commit()

        return

    def get_player_id(self, player_tag):
        cursor = self.connection.cursor()
        cursor.execute("SELECT player_id FROM players WHERE player_tag = ?", (player_tag,))
        row = cursor.fetchone()
        if row:
            player_id = row[0]
        else:
            player_id = None

        return player_id

    def get_player_id_create_if_new(self, player_tag, friday_date):

        player_id = self.get_player_id(player_tag)
        if player_id:
            return player_id

        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO players (player_tag, start_date) VALUES (?, ?)", (player_tag, friday_date,))
        player_id = cursor.lastrowid
        self.connection.commit()

        return player_id

    def reset_scores_for_tournament(self, weekend_date):
        """
        Reset all player scores for a given weekend date to 0.
        """
        cursor = self.connection.cursor()
        cursor.execute("UPDATE tournament_results SET score = 0 WHERE weekend_date = ? AND score IS NULL", (weekend_date,))
        self.connection.commit()

        return

    def update_player_start_date(self, player_id, friday_date):
        """
        Update the player's start_date in the players table if it's earlier than the existing start_date.
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT start_date FROM players WHERE player_id = ?", (player_id,))
        row = cursor.fetchone()
        if row:
            current_start_date = row[0]
            if current_start_date is None or friday_date < current_start_date:
                cursor.execute("UPDATE players SET start_date = ? WHERE player_id = ?", (friday_date, player_id))
        self.connection.commit()

        return

    def update_ranks_for_weekend_date(self, weekend_date):
        cursor = self.connection.cursor()

        # SQL query to update ranks for the specific weekend_date
        sql = """
        WITH ranked_results AS (
            SELECT
                player_id,
                RANK() OVER (PARTITION BY weekend_date ORDER BY score DESC) AS calculated_rank
            FROM
                tournament_results
            WHERE
                weekend_date = ?
        )
        UPDATE tournament_results
        SET rank = (
            SELECT calculated_rank
            FROM ranked_results
            WHERE ranked_results.player_id = tournament_results.player_id
        )
        WHERE weekend_date = ?;
        """

        # Execute the query with the specified date
        cursor.execute(sql, (weekend_date, weekend_date))
        self.connection.commit()

        return

# Example usage
#if __name__ == "__main__":
#    def create_instance(value):
#        instance = DbRepositoryeSingleton(value)
#        instance.some_method()

#    threads = [threading.Thread(target=create_instance, args=(f"Value{i}",)) for i in range(5)]

#    for thread in threads:
#        thread.start()

#    for thread in threads:
#        thread.join()

#    print("[INFO] Cleaning up the thread-safe singleton...")
#    DbRepositoryeSingleton.cleanup()

#    print("[DONE] All threads completed.")