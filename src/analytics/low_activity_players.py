import logging
import os
import sqlite3
import sys

import pandas as pd

<<<<<<< HEAD
try:
    from cls_env_tools import EnvTools
except ImportError as e:
    logging.error(f"Error importing required modules: {e}")
    sys.exit(1)
=======
# Connect to the SQLite database
<<<<<<< HEAD
conn = sqlite3.connect('../player_metrics.db')
=======
conn = sqlite3.connect('../../player_metrics.db')
>>>>>>> bc82a28aaf306b45a51bca175410bffb23322f53
>>>>>>> origin/main


def _normalize_player_tags(tags):
    """Trim, de-duplicate, and preserve order for player tags."""
    normalized = []
    seen = set()

    for tag in tags:
        cleaned = str(tag).strip()
        if not cleaned:
            continue

        key = cleaned.lower()
        if key in seen:
            continue

        seen.add(key)
        normalized.append(cleaned)

    return normalized


def get_low_activity_report(
    conn,
    max_3mo_play_ratio=0.34,
    min_inactive_weeks=6,
    min_tenure_weeks=6,
    recent_weeks_for_score_check=6,
    max_recent_avg_score=300,
    excluded_players=None,
):
    """
    Identify players on the team who are not contributing and could be removed.

    Metrics per player:
      - Lifetime average score (weekends they actually played, score > 0)
      - Average score over the last 6 months (weekends they played)
      - Average score over the last 3 months (weekends they played)
      - Number of weekends played in each period
      - Weeks since they last played (last non-zero score)

    Included in report when either is true:
      - Weeks inactive >= min_inactive_weeks
      - Participation in last 3 months <= max_3mo_play_ratio
            - Average score in recent_weeks_for_score_check weeks <= max_recent_avg_score

        Eligibility gate:
            - Player tenure must be >= min_tenure_weeks

    Players in excluded_players are ignored.

    Sorted by:
      1. Weeks since played (DESC - longest inactive first)
      2. Avg last 3 months (ASC - lowest contributors first)
      3. Avg last 6 months (ASC)
      4. Lifetime average (ASC)
    """
    excluded_players = _normalize_player_tags(excluded_players or [])
    exclude_clause = ""

    # Keep parameter order aligned with SQL placeholder order.
    params = [int(recent_weeks_for_score_check)]

    if excluded_players:
        placeholders = ", ".join("?" for _ in excluded_players)
        exclude_clause = f" AND player_tag NOT IN ({placeholders})"
        params.extend(excluded_players)

    query = f"""
    WITH
    latest_tournament AS (
        SELECT MAX(weekend_date) AS max_date
        FROM tournament_results
    ),
    weekends_in_3_months AS (
        SELECT COUNT(DISTINCT weekend_date) AS total
        FROM tournament_results
        WHERE weekend_date >= date((SELECT max_date FROM latest_tournament), '-3 months')
    ),
    weekends_in_6_months AS (
        SELECT COUNT(DISTINCT weekend_date) AS total
        FROM tournament_results
        WHERE weekend_date >= date((SELECT max_date FROM latest_tournament), '-6 months')
    ),
    recent_n_weekends AS (
        SELECT weekend_date
        FROM (
            SELECT DISTINCT weekend_date
            FROM tournament_results
            ORDER BY weekend_date DESC
            LIMIT ?
        )
    ),
    team_players AS (
        SELECT id, player_tag
        FROM players
        WHERE on_team = 1
          {exclude_clause}
    ),
    lifetime_stats AS (
        SELECT
            player_id,
            ROUND(AVG(score), 0) AS avg_score,
            COUNT(*) AS weekends_played
        FROM tournament_results
        WHERE score > 0
        GROUP BY player_id
    ),
    six_month_stats AS (
        SELECT
            player_id,
            ROUND(AVG(score), 0) AS avg_score,
            COUNT(*) AS weekends_played
        FROM tournament_results
        WHERE score > 0
          AND weekend_date >= date((SELECT max_date FROM latest_tournament), '-6 months')
        GROUP BY player_id
    ),
    three_month_stats AS (
        SELECT
            player_id,
            ROUND(AVG(score), 0) AS avg_score,
            COUNT(*) AS weekends_played
        FROM tournament_results
        WHERE score > 0
          AND weekend_date >= date((SELECT max_date FROM latest_tournament), '-3 months')
        GROUP BY player_id
    ),
    last_played AS (
        SELECT
            player_id,
            MAX(weekend_date) AS last_played_date
        FROM tournament_results
        WHERE score > 0
        GROUP BY player_id
    ),
    first_seen AS (
        SELECT
            player_id,
            MIN(weekend_date) AS first_seen_date
        FROM tournament_results
        GROUP BY player_id
    ),
    recent_n_week_stats AS (
        SELECT
            tp.id AS player_id,
            ROUND(AVG(COALESCE(tr.score, 0)), 0) AS avg_score,
            COUNT(CASE WHEN COALESCE(tr.score, 0) > 0 THEN 1 END) AS weekends_played
        FROM team_players AS tp
        CROSS JOIN recent_n_weekends AS rw
        LEFT JOIN tournament_results AS tr
            ON tr.player_id = tp.id
           AND tr.weekend_date = rw.weekend_date
        GROUP BY tp.id
    ),
    final_stats AS (
        SELECT
            tp.player_tag AS "Player",
            COALESCE(ls.avg_score, 0) AS "Lifetime Avg",
            COALESCE(ls.weekends_played, 0) AS "Lifetime Played",
            COALESCE(sm.avg_score, 0) AS "6-Mo Avg",
            COALESCE(sm.weekends_played, 0) AS "6-Mo Played Count",
            (SELECT total FROM weekends_in_6_months) AS "6-Mo Total Weekends",
            COALESCE(tm.avg_score, 0) AS "3-Mo Avg",
            COALESCE(tm.weekends_played, 0) AS "3-Mo Played Count",
            (SELECT total FROM weekends_in_3_months) AS "3-Mo Total Weekends",
            COALESCE(rn.avg_score, 0) AS "Recent N-Week Avg",
            COALESCE(rn.weekends_played, 0) AS "Recent N-Week Played",
            (SELECT COUNT(*) FROM recent_n_weekends) AS "Recent N-Week Total",
            COALESCE(fs.first_seen_date, 'Unknown') AS "First Seen",
            COALESCE(lp.last_played_date, 'Never') AS "Last Played",
            CASE
                WHEN fs.first_seen_date IS NOT NULL
                THEN CAST(
                    ROUND((julianday((SELECT max_date FROM latest_tournament))
                           - julianday(fs.first_seen_date)) / 7.0)
                    AS INTEGER)
                ELSE 0
            END AS "Tenure Weeks",
            CASE
                WHEN lp.last_played_date IS NOT NULL
                THEN CAST(
                    ROUND((julianday((SELECT max_date FROM latest_tournament))
                           - julianday(lp.last_played_date)) / 7.0)
                    AS INTEGER)
                ELSE 999
            END AS "Weeks Inactive"
        FROM team_players AS tp
        LEFT JOIN lifetime_stats AS ls ON tp.id = ls.player_id
        LEFT JOIN six_month_stats AS sm ON tp.id = sm.player_id
        LEFT JOIN three_month_stats AS tm ON tp.id = tm.player_id
        LEFT JOIN recent_n_week_stats AS rn ON tp.id = rn.player_id
        LEFT JOIN first_seen AS fs ON tp.id = fs.player_id
        LEFT JOIN last_played AS lp ON tp.id = lp.player_id
    )
    SELECT
<<<<<<< HEAD
        "Player",
        "Lifetime Avg",
        "Lifetime Played",
        "6-Mo Avg",
        "6-Mo Played Count" || '/' || "6-Mo Total Weekends" AS "6-Mo Played",
        "3-Mo Avg",
        "3-Mo Played Count" || '/' || "3-Mo Total Weekends" AS "3-Mo Played",
        "Recent N-Week Avg",
        "Recent N-Week Played" || '/' || "Recent N-Week Total" AS "Recent N-Week Played",
        "First Seen",
        "Tenure Weeks",
        "Last Played",
        "Weeks Inactive",
        ROUND(
            CASE
                WHEN "3-Mo Total Weekends" > 0
                THEN (CAST("3-Mo Played Count" AS REAL) / "3-Mo Total Weekends") * 100.0
                ELSE 0
            END,
            1
        ) AS "3-Mo Participation %"
    FROM final_stats
    WHERE
        "Tenure Weeks" >= ?
        AND (
            "Weeks Inactive" >= ?
            OR (
                CASE
                    WHEN "3-Mo Total Weekends" > 0
                    THEN CAST("3-Mo Played Count" AS REAL) / "3-Mo Total Weekends"
                    ELSE 0
                END
            ) <= ?
            OR "Recent N-Week Avg" <= ?
        )
    ORDER BY
        "Weeks Inactive" DESC,
        "3-Mo Avg" ASC,
        "6-Mo Avg" ASC,
        "Lifetime Avg" ASC;
    """
=======
        tr.player_id,
        p.player_tag,
        tr.weekend_date,
        tr.score
    FROM tournament_results AS tr
<<<<<<< HEAD
    INNER JOIN players AS p ON tr.player_id = p.player_id
=======
    INNER JOIN players AS p ON tr.player_id = p.id
>>>>>>> bc82a28aaf306b45a51bca175410bffb23322f53
    WHERE p.on_team = 1
      AND tr.weekend_date IN (SELECT weekend_date FROM recent_tournaments)
),
player_averages_recent AS (
    -- Calculate the average score over the last 6 weeks (excluding the most recent week)
    SELECT
        ps.player_id,
        ps.player_tag,
        AVG(ps.score) AS average_score_recent
    FROM player_scores AS ps
    GROUP BY ps.player_id, ps.player_tag
),
player_averages_all_time AS (
    -- Calculate the all-time average score for each player
    SELECT
        tr.player_id,
        p.player_tag,
        AVG(tr.score) AS average_score_all_time
    FROM tournament_results AS tr
<<<<<<< HEAD
    INNER JOIN players AS p ON tr.player_id = p.player_id
=======
    INNER JOIN players AS p ON tr.player_id = p.id
>>>>>>> bc82a28aaf306b45a51bca175410bffb23322f53
    WHERE p.on_team = 1
    GROUP BY tr.player_id, p.player_tag
),
last_200_plus AS (
    -- Find the last weekend each player scored more than 200
    SELECT
        tr.player_id,
        MAX(tr.weekend_date) AS last_200_plus_weekend
    FROM tournament_results AS tr
    WHERE tr.score > 200
    GROUP BY tr.player_id
)
SELECT
    p_recent.player_tag,
    p_recent.average_score_recent,
    p_all_time.average_score_all_time,
    ps.weekend_date,
    ps.score,
    COALESCE(lp.last_200_plus_weekend, 'Never') AS last_200_plus_weekend
FROM player_averages_recent AS p_recent
INNER JOIN player_scores AS ps ON p_recent.player_id = ps.player_id
INNER JOIN player_averages_all_time AS p_all_time ON p_recent.player_id = p_all_time.player_id
LEFT JOIN last_200_plus AS lp ON p_recent.player_id = lp.player_id
<<<<<<< HEAD
WHERE p_recent.average_score_recent < 200
=======
WHERE p_recent.average_score_recent < 300
>>>>>>> bc82a28aaf306b45a51bca175410bffb23322f53
ORDER BY p_recent.player_tag, ps.weekend_date;
"""
>>>>>>> origin/main

    params.extend([
        int(min_tenure_weeks),
        int(min_inactive_weeks),
        float(max_3mo_play_ratio),
        float(max_recent_avg_score),
    ])
    return pd.read_sql_query(query, conn, params=params)


def main():
    # Configure these constants directly.
    EXCLUDED_PLAYERS = [
        'Hobbes',
        'Elen',
    ]
    MIN_INACTIVE_WEEKS = 4
    MIN_TENURE_WEEKS_FOR_REVIEW = 6
    MAX_3MO_PLAY_RATIO = 0.34
    RECENT_WEEKS_FOR_SCORE_CHECK = 9
    MAX_RECENT_AVG_SCORE = 300

    if MIN_INACTIVE_WEEKS < 0:
        raise ValueError('MIN_INACTIVE_WEEKS must be >= 0')
    if MIN_TENURE_WEEKS_FOR_REVIEW < 0:
        raise ValueError('MIN_TENURE_WEEKS_FOR_REVIEW must be >= 0')
    if RECENT_WEEKS_FOR_SCORE_CHECK <= 0:
        raise ValueError('RECENT_WEEKS_FOR_SCORE_CHECK must be > 0')
    if MAX_RECENT_AVG_SCORE < 0:
        raise ValueError('MAX_RECENT_AVG_SCORE must be >= 0')
    if not 0 <= MAX_3MO_PLAY_RATIO <= 1:
        raise ValueError('MAX_3MO_PLAY_RATIO must be between 0 and 1')

    excluded_players = _normalize_player_tags(EXCLUDED_PLAYERS)

    repo_root = EnvTools.find_repo_root()
    if repo_root is None:
        # Fallback: derive repo root from this script's location (src/analytics/)
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    db_path = os.path.join(str(repo_root), 'player_metrics.db')
    conn = sqlite3.connect(db_path)

    try:
        df = get_low_activity_report(
            conn,
            max_3mo_play_ratio=MAX_3MO_PLAY_RATIO,
            min_inactive_weeks=MIN_INACTIVE_WEEKS,
            min_tenure_weeks=MIN_TENURE_WEEKS_FOR_REVIEW,
            recent_weeks_for_score_check=RECENT_WEEKS_FOR_SCORE_CHECK,
            max_recent_avg_score=MAX_RECENT_AVG_SCORE,
            excluded_players=excluded_players,
        )

        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 160)
        pd.set_option('display.colheader_justify', 'right')

        print("\n" + "=" * 100)
        print("  LOW ACTIVITY PLAYERS - Candidates for Removal")
        print("  Included when: inactive OR low 3-month participation OR low recent n-week average")
        print(
            f"  Thresholds: min tenure={MIN_TENURE_WEEKS_FOR_REVIEW} weeks, "
            f"min inactive weeks={MIN_INACTIVE_WEEKS}, "
            f"max 3-mo participation={MAX_3MO_PLAY_RATIO:.0%}, "
            f"max recent {RECENT_WEEKS_FOR_SCORE_CHECK}-week avg score={MAX_RECENT_AVG_SCORE}"
        )
        if excluded_players:
            print(f"  Excluded players: {', '.join(excluded_players)}")
        else:
            print("  Excluded players: none")
        print("=" * 100)

        if df.empty:
            print("No low-activity players match the current filters.")
        else:
            print(df.to_string(index=False))

        print(f"\nTotal players in report: {len(df)}")
        print("=" * 100)

        output_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(output_dir, 'low_activity_players.csv')
        df.to_csv(csv_path, index=False)
        print(f"\nReport saved to: {csv_path}")
    finally:
        conn.close()


if __name__ == '__main__':
    main()