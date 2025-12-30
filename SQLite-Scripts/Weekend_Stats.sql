WITH weekend_totals AS (
    -- Calculate total scores and participant metrics for each weekend
    SELECT 
        tr.weekend_date,
        SUM(tr.score) AS 'Stars',
        COUNT(DISTINCT CASE WHEN tr.score = 0 THEN tr.player_id END) AS 'No Score',
        COUNT(DISTINCT CASE WHEN tr.score > 0 THEN tr.player_id END) AS 'Played',
        COUNT(DISTINCT CASE WHEN tr.score > 500 THEN tr.player_id END) AS '>500',
        COUNT(DISTINCT CASE WHEN tr.score < 200 AND tr.score > 0 THEN tr.player_id END) AS '<200'
    FROM players p
    JOIN tournament_results tr ON p.id = tr.player_id
    GROUP BY tr.weekend_date
),
participant_stats AS (
    -- Rank weekends by participants_with_score_above_zero to calculate the median number of participants
    SELECT 
        weekend_date,
        participants_with_score_above_zero,
        ROW_NUMBER() OVER (ORDER BY participants_with_score_above_zero ASC) AS rank,
        COUNT(*) OVER () AS total_weekends
    FROM weekend_totals
)
SELECT wt.*--, tr.rank
  FROM weekend_totals AS wt
    LEFT JOIN team_tournament_results AS tr ON tr.weekend_date = wt.weekend_date

