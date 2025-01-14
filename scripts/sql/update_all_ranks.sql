WITH ranked_results AS (
    SELECT
        player_id,
        RANK() OVER (PARTITION BY weekend_date ORDER BY score DESC) AS calculated_rank
    FROM
        tournament_results
)
-- Update the rank column for the specific weekend_date
UPDATE tournament_results
SET rank = (
    SELECT calculated_rank
    FROM ranked_results
    WHERE ranked_results.player_id = tournament_results.player_id
)
