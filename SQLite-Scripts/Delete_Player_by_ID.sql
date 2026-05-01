DELETE FROM tournament_results
WHERE player_id IN (60, 61)
AND weekend_date < (SELECT start_date FROM players WHERE players.id = tournament_results.player_id);