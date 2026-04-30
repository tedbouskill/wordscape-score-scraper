-- Use a CTE to calculate ranks for the specific weekend_date
WITH ranked_results AS (
    SELECT
        player_id,
        RANK() OVER (PARTITION BY weekend_date ORDER BY score DESC) AS calculated_rank
    FROM
        tournament_results
    WHERE
        weekend_date = '2024-09-01' -- Placeholder for the specific date
)
-- Update the rank column for the specific weekend_date
UPDATE tournament_results
SET rank = (
    SELECT calculated_rank
    FROM ranked_results
    WHERE ranked_results.player_id = tournament_results.player_id
)
WHERE weekend_date = '2024-09-01'; -- Restrict update to the specific date
