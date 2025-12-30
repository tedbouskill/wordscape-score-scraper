WITH scores AS (
    SELECT SUM(score) team_score
    FROM tournament_results 
    WHERE weekend_date NOT IN (SELECT MAX(weekend_date) max_date FROM tournament_results) GROUP BY weekend_date
)
SELECT MAX(team_score) FROM scores;