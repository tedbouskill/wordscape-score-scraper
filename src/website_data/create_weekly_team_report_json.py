import json
import logging
import os
import sys
import sqlite3

from datetime import datetime, timedelta

try:
    from cls_env_tools import EnvTools

except ImportError as e:
    logging.error(f"Error importing required modules: {e}")
    sys.exit(1)

def generate_weekend_report(db_path, json_path, weekend_date=None):
    """
    Generate a weekend report based on tournament and team results.

    The "recent" tournament is determined as follows:
      - If a weekend_date is provided, it is used.
      - Otherwise, the function first checks for the maximum weekend_date in
        the tournament_results table.
      - If no date is found in the table, the last Sunday from today is used.

    The report includes:
      - Total player score for the recent tournament and percentage change compared
        to the previous tournament.
      - Team score and team rank (as team_weekend_rank) for the recent and previous tournaments.
      - Top three players for the recent tournament (only players with on_team = 1 and a nonzero score),
        including their weekend_rank.
      - For each player in the recent tournament:
          * If they exceeded their past top score (from before the recent tournament), plus the percentage above.
          * If they exceeded their lifetime average (historical average before the recent tournament),
            plus the percentage above.
          * If their average over the past 4 tournaments (including the recent one) is below 300, include both their recent
            average and their lifetime average.

    Score averages are rounded to 0 decimals.
    Percentages are rounded to 1 decimal.

    After processing, the function filters and sorts:
      - players_exceeded_past_top: only those with a percentage (or 0 if null) > 10, sorted descending.
      - players_exceeded_lifetime_avg: only those with a percentage (or 0 if null) > 10, sorted descending.

    Finally, the JSON report is saved to a file.

    Parameters:
      - db_path: Path to the SQLite database file.
      - weekend_date: (Optional) A string representing the weekend date (e.g. '2025-02-15').
      - output_file: (Optional) File name to save the JSON report.

    Returns:
      - A JSON string containing the report.
    """

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Determine recent weekend_date if not provided.
    if not weekend_date:
        # Try to use the max weekend_date in the tournament_results table.
        c.execute("SELECT MAX(weekend_date) FROM tournament_results")
        weekend_date = c.fetchone()[0]


    # --- Find the previous weekend date ---
    c.execute(
        """ SELECT weekend_date, team_score, team_rank, score_rank
            FROM (
                SELECT *, RANK() OVER (ORDER BY team_score DESC) AS score_rank
                FROM team_tournament_results WHERE weekend_date <= ?
            ) ranked
            WHERE score_rank <= 2;
        """,
        (weekend_date,)
    )
    recent_weekend = c.fetchone()
    max_weekend = c.fetchone()

    recent_team_score = recent_weekend[1]
    recent_team_rank = recent_weekend[2]

    max_team_score = max_weekend[1]
    max_team_score_rank = max_weekend[2] or 0

    # --- Compute total player score for the recent tournament ---
    c.execute(
        "SELECT team_score, team_rank FROM team_tournament_results WHERE weekend_date < ? ORDER BY weekend_date DESC LIMIT 1",
        (weekend_date,)
    )
    previous_weekend = c.fetchone()
    previous_team_score = previous_weekend[0]
    previous_team_rank = previous_weekend[1]

    # --- Compute percentage difference relative to the previous tournament ---
    percent_diff_total = round(((recent_team_score - previous_team_score) / previous_team_score * 100), 1)

    # --- Get top three players for the recent tournament ---
    # Only include players that are on the team (on_team = 1) and have a nonzero score.
    c.execute("""
        SELECT tr.player_id, tr.score, tr.rank, p.player_tag
        FROM tournament_results tr
        JOIN players p ON tr.player_id = p.id
        WHERE tr.weekend_date = ?
          AND p.on_team = 1
          AND tr.score > 0
        ORDER BY tr.score DESC
        LIMIT 3
    """, (weekend_date,))
    top_three = []
    for row in c.fetchall():
        top_three.append({
            "player_id": row[0],
            "recent_score": row[1],
            "weekend_rank": row[2],
            "player_tag": row[3]
        })

    # --- Analyze each player who played in the recent tournament ---
    c.execute("""
        SELECT tr.player_id, tr.score, tr.rank, p.player_tag
        FROM tournament_results tr
        JOIN players p ON tr.player_id = p.id
        WHERE tr.weekend_date = ?
          AND p.on_team = 1
          AND tr.score > 0
    """, (weekend_date,))
    recent_players = c.fetchall()

    players_exceeded_past_top = []
    players_exceeded_lifetime_avg = []
    players_low_recent_avg = []

    for player_id, recent_score, weekend_rank, player_tag in recent_players:
        # -- Past top score (from tournaments before the recent one) --
        c.execute("""
            SELECT MAX(score) FROM tournament_results
            WHERE player_id = ? AND weekend_date < ?
        """, (player_id, weekend_date))
        past_top = c.fetchone()[0]
        if past_top is not None and recent_score > past_top:
            percent_above = round(((recent_score - past_top) / past_top * 100), 1) if past_top != 0 else None
            players_exceeded_past_top.append({
                "player_id": player_id,
                "player_tag": player_tag,
                "weekend_rank": weekend_rank,
                "recent_score": recent_score,
                "past_top_score": past_top,
                "percent_above": percent_above
            })

        # -- Lifetime average (historical average before the recent tournament) --
        c.execute("""
            SELECT AVG(score) FROM tournament_results
            WHERE player_id = ? AND weekend_date < ?
        """, (player_id, weekend_date))
        lifetime_avg = c.fetchone()[0]
        if lifetime_avg is not None:
            lifetime_avg = round(lifetime_avg)  # round to 0 decimals
            if recent_score > lifetime_avg:
                percent_above_avg = round(((recent_score - lifetime_avg) / lifetime_avg * 100), 1) if lifetime_avg != 0 else None
                players_exceeded_lifetime_avg.append({
                    "player_id": player_id,
                    "player_tag": player_tag,
                    "weekend_rank": weekend_rank,
                    "recent_score": recent_score,
                    "lifetime_avg": lifetime_avg,
                    "percent_above_avg": percent_above_avg
                })

        # -- Average for the past 4 tournaments (including the recent one) --
        c.execute("""
            SELECT score FROM tournament_results
            WHERE player_id = ? AND weekend_date <= ?
            ORDER BY weekend_date DESC
            LIMIT 4
        """, (player_id, weekend_date))
        last_four_scores = [row[0] for row in c.fetchall()]
        if len(last_four_scores) == 4:
            recent_avg = round(sum(last_four_scores) / 4.0)  # round to 0 decimals
            if recent_avg < 300:
                # Lifetime average up to and including the recent tournament.
                c.execute("""
                    SELECT AVG(score) FROM tournament_results
                    WHERE player_id = ? AND weekend_date <= ?
                """, (player_id, weekend_date))
                lifetime_avg_incl = c.fetchone()[0]
                if lifetime_avg_incl is not None:
                    lifetime_avg_incl = round(lifetime_avg_incl)
                players_low_recent_avg.append({
                    "player_id": player_id,
                    "player_tag": player_tag,
                    "weekend_rank": weekend_rank,
                    "recent_avg": recent_avg,
                    "lifetime_avg": lifetime_avg_incl
                })

    # --- Filter and sort the exceeded lists ---
    def filter_and_sort_exceeded(items, key, percent=10.0):
        # Replace None with 0 and filter out items with percentage <= 10%
        for item in items:
            if item[key] is None:
                item[key] = 0.0
        filtered = [item for item in items if item[key] > percent]
        return sorted(filtered, key=lambda x: x[key], reverse=True)

    players_exceeded_past_top = filter_and_sort_exceeded(players_exceeded_past_top, "percent_above")
    players_exceeded_lifetime_avg = filter_and_sort_exceeded(players_exceeded_lifetime_avg, "percent_above_avg", 50.0)

    # --- Assemble the final report ---
    report = {
        "weekend_date": weekend_date,
        "team_score_recent": recent_team_score,
        "team_score_recent_rank": recent_team_rank,
        "team_score_previous": previous_team_score,
        "team_score_previous_rank": previous_team_rank,
        "team_score_max": max_team_score,
        "team_score_max_rank": max_team_score_rank,
        "percent_change_previous": percent_diff_total,
        "top_three_players": top_three,
        "players_exceeded_past_top": players_exceeded_past_top,
        "players_exceeded_lifetime_avg": players_exceeded_lifetime_avg,
        "players_low_recent_avg": players_low_recent_avg
    }

    with open(json_path, 'w') as f:
        json.dump(report, f, default=str, indent=2)

    conn.close()
    return json.dumps(report, default=str, indent=2)


def main():
    global script_name, script_directory

    # Get the script name without the extension
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    script_dir = os.path.dirname(os.path.abspath(__file__))

    env_tools = EnvTools()

    # Connect to SQLite
    db_path = os.path.join(env_tools.find_repo_root(), 'player_metrics.db')
    print(db_path)

    json_folder = os.path.join(env_tools.find_repo_root(),'docs')
    json_path = os.path.join(json_folder, 'last_weekend_report.json')

    report_json = generate_weekend_report(db_path, json_path)


if __name__ == '__main__':
    main()
