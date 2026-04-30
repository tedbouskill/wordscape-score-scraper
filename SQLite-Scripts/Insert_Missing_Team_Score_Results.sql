INSERT INTO team_tournament_results (weekend_date, team_score)
SELECT weekend_date, SUM(score) AS team_score
    FROM tournament_results
GROUP BY weekend_date
ON CONFLICT(weekend_date) DO UPDATE SET
    team_score = excluded.team_score;
