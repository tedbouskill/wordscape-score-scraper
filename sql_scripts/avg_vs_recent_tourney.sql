WITH recent_tournaments AS (
    -- Get the past 12 weeks based on weekend_date
    SELECT DISTINCT weekend_date
    FROM tournament_results
    WHERE weekend_date <= (SELECT MAX(weekend_date) FROM tournament_results)
    ORDER BY weekend_date DESC
    LIMIT 12
),
most_recent_tournament AS (
    -- Get the most recent tournament weekend
    SELECT MAX(weekend_date) AS most_recent_weekend
    FROM tournament_results
),
player_scores_and_ranks AS (
    -- Fetch scores and ranks for players in the past 12 weeks
    SELECT
        tr.player_id,
        p.player_tag,
        tr.weekend_date,
        tr.score,
        RANK() OVER (PARTITION BY tr.weekend_date ORDER BY tr.score DESC) AS rank
    FROM tournament_results AS tr
    INNER JOIN players AS p ON tr.player_id = p.player_id
    WHERE p.on_team = 1
      AND tr.weekend_date IN (SELECT weekend_date FROM recent_tournaments)
),
player_averages_12_weeks AS (
    -- Calculate the average score and average rank for the past 12 weeks
    SELECT
        psr.player_id,
        psr.player_tag,
        ROUND(AVG(psr.score)) AS average_score_12_weeks,
        ROUND(AVG(psr.rank)) AS average_rank_12_weeks
    FROM player_scores_and_ranks AS psr
    GROUP BY psr.player_id, psr.player_tag
),
most_recent_scores_and_ranks AS (
    -- Fetch the score and rank for the most recent tournament
    SELECT
        tr.player_id,
        p.player_tag,
        tr.score AS most_recent_score,
        RANK() OVER (ORDER BY tr.score DESC) AS most_recent_rank
    FROM tournament_results AS tr
    INNER JOIN players AS p ON tr.player_id = p.player_id
    WHERE p.on_team = 1
      AND tr.weekend_date = (SELECT most_recent_weekend FROM most_recent_tournament)
)
SELECT
    pa.player_tag,
    pa.average_score_12_weeks,
    COALESCE(mr.most_recent_score, 0) AS most_recent_score,
    pa.average_rank_12_weeks,
    COALESCE(mr.most_recent_rank, NULL) AS most_recent_rank
FROM player_averages_12_weeks AS pa
LEFT JOIN most_recent_scores_and_ranks AS mr ON pa.player_id = mr.player_id
ORDER BY most_recent_rank ASC;
