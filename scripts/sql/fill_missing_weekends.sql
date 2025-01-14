-- Step 1: Define the player_id as a variable
WITH vars AS (
    SELECT 59 AS player_id -- Change this value to set the desired player_id
),

-- Step 2: Create a list of all tournament dates
tournament_dates AS (
    SELECT DATE('2023-09-29') AS weekend_date
    UNION ALL
    SELECT DATE(weekend_date, '+7 days')
    FROM tournament_dates
    WHERE weekend_date < DATE('now') -- Generate up to the current date
),

-- Step 3: Find missing dates for the player_id
missing_dates AS (
    SELECT td.weekend_date, v.player_id
    FROM tournament_dates td, vars v
    LEFT JOIN tournament_results tr
        ON td.weekend_date = tr.weekend_date AND tr.player_id = v.player_id
    WHERE tr.weekend_date IS NULL -- Dates not present for the player
)

-- Step 4: Insert missing results
INSERT INTO tournament_results (weekend_date, player_id, score)
SELECT weekend_date, player_id, 0
FROM missing_dates;
