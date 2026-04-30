SELECT tr.weekend_date,
       SUM(tr.score) AS team_score
FROM tournament_results tr
LEFT JOIN team_tournament_results ttr
       ON tr.weekend_date = ttr.weekend_date
WHERE ttr.weekend_date IS NULL
GROUP BY tr.weekend_date;
