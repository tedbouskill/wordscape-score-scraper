import sqlite3
import pandas as pd

# Connect to the SQLite database
conn = sqlite3.connect('../player_metrics.db')

# SQL Query to fetch data for the last six weeks and add the last weekend a player scored > 200
query = """
WITH recent_tournaments AS (
    -- Get the last 6 weeks based on weekend_date excluding the most recent Sunday
    SELECT DISTINCT weekend_date
    FROM tournament_results
    WHERE weekend_date < (SELECT MAX(weekend_date) FROM tournament_results)
    ORDER BY weekend_date DESC
    LIMIT 6
),
player_scores AS (
    -- Fetch scores for players in the last 6 weeks where they are on the team
    SELECT
        tr.player_id,
        p.player_tag,
        tr.weekend_date,
        tr.score
    FROM tournament_results AS tr
    INNER JOIN players AS p ON tr.player_id = p.player_id
    WHERE p.on_team = 1
      AND tr.weekend_date IN (SELECT weekend_date FROM recent_tournaments)
),
player_averages_recent AS (
    -- Calculate the average score over the last 6 weeks (excluding the most recent week)
    SELECT
        ps.player_id,
        ps.player_tag,
        AVG(ps.score) AS average_score_recent
    FROM player_scores AS ps
    GROUP BY ps.player_id, ps.player_tag
),
player_averages_all_time AS (
    -- Calculate the all-time average score for each player
    SELECT
        tr.player_id,
        p.player_tag,
        AVG(tr.score) AS average_score_all_time
    FROM tournament_results AS tr
    INNER JOIN players AS p ON tr.player_id = p.player_id
    WHERE p.on_team = 1
    GROUP BY tr.player_id, p.player_tag
),
last_200_plus AS (
    -- Find the last weekend each player scored more than 200
    SELECT
        tr.player_id,
        MAX(tr.weekend_date) AS last_200_plus_weekend
    FROM tournament_results AS tr
    WHERE tr.score > 200
    GROUP BY tr.player_id
)
SELECT
    p_recent.player_tag,
    p_recent.average_score_recent,
    p_all_time.average_score_all_time,
    ps.weekend_date,
    ps.score,
    COALESCE(lp.last_200_plus_weekend, 'Never') AS last_200_plus_weekend
FROM player_averages_recent AS p_recent
INNER JOIN player_scores AS ps ON p_recent.player_id = ps.player_id
INNER JOIN player_averages_all_time AS p_all_time ON p_recent.player_id = p_all_time.player_id
LEFT JOIN last_200_plus AS lp ON p_recent.player_id = lp.player_id
WHERE p_recent.average_score_recent < 200
ORDER BY p_recent.player_tag, ps.weekend_date;
"""

# Execute the query and load data into a Pandas DataFrame
df = pd.read_sql_query(query, conn)

# Pivot the data to show players as rows, weekend dates as columns, and include the last_200_plus_weekend
pivoted_df = df.pivot(index=['player_tag', 'last_200_plus_weekend', 'average_score_recent', 'average_score_all_time'], columns='weekend_date', values='score')

# Close the connection
conn.close()

# Fill missing values with 0
pivoted_df = pivoted_df.fillna(0)

# Display the filtered data
print(pivoted_df)

# Optionally save to a CSV
pivoted_df.to_csv('filtered_player_scores_with_last_200_plus.csv')
