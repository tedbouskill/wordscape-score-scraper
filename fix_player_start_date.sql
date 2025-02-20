WITH first_weekend AS (
SELECT tr.player_id, MIN(weekend_date) first_weekend
FROM tournament_results tr
  INNER JOIN players p ON tr.player_id = p.player_id
GROUP BY tr.player_id
)
SELECT p.player_id, p.player_tag, p.start_date, first_weekend
  FROM players p
    INNER JOIN first_weekend ON p.player_id = first_weekend.player_id
WHERE first_weekend < p.start_date;
    
UPDATE players
SET start_date = DATE(
  (SELECT MIN(tr.weekend_date)
   FROM tournament_results tr
   WHERE tr.player_id = players.player_id),
  '-2 days'
)
WHERE start_date > (
  SELECT MIN(tr.weekend_date)
  FROM tournament_results tr
  WHERE tr.player_id = players.player_id
);
