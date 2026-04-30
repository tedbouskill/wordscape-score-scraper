SELECT weekend_date,
       player_id,
       p.player_tag,
       helps,
       stars
FROM weekly_player_stats wps
    INNER JOIN players p ON wps.player_id = p.id
WHERE
    p.is_active = 1
ORDER BY wps.weekend_date DESC;
--WHERE player_id = 63;
