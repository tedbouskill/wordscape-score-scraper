--INSERT INTO players (player_tag, on_team, is_active, start_date) VALUES ('Kiwiz', 1, 1, '2025-11-21');

SELECT id, player_tag, on_team, is_active, start_date, leave_date
  FROM players
    WHERE on_team = 1
        ORDER BY player_tag;
