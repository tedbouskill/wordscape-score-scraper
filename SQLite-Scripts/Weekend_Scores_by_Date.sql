SELECT weekend_date,
       player_tag,
       score,
       rank
FROM tournament_results tr
    INNER JOIN players p ON tr.player_id = p.id
WHERE weekend_date = :weekend_date
ORDER BY weekend_date DESC, rank ASC;
