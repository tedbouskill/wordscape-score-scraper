SELECT weekend_date, team_score, team_rank, score_rank
FROM (
    SELECT *, RANK() OVER (ORDER BY team_score DESC) AS score_rank
    FROM team_tournament_results
) ranked
ORDER BY weekend_date DESC;
