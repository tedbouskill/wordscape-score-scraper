import json
import logging
import os
import sqlite3
import sys

try:
    from cls_env_tools import EnvTools

except ImportError as e:
    logging.error(f"Error importing required modules: {e}")
    sys.exit(1)


def generate_alltime_highlights(db_path, json_path):
    """
    Generate all-time highlights for the team dashboard.

    Includes:
      - Top 5 highest weekend team scores (with date and rank)
      - Top 5 highest individual player scores in a single weekend
      - Top 3 weekend score averages for active players (on_team=1, min 5 weekends played)
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # --- Top 5 highest team weekend scores ---
    c.execute("""
        SELECT weekend_date, team_score, team_rank
        FROM team_tournament_results
        ORDER BY team_score DESC
        LIMIT 5
    """)
    top_team_scores = [
        {"weekend_date": row[0], "team_score": row[1], "team_rank": row[2]}
        for row in c.fetchall()
    ]

    # --- Top 5 highest individual player scores in a single weekend ---
    c.execute("""
        SELECT p.player_tag, tr.score, tr.weekend_date, tr.rank
        FROM tournament_results tr
        JOIN players p ON tr.player_id = p.id
        ORDER BY tr.score DESC
        LIMIT 5
    """)
    top_player_scores = [
        {
            "player_tag": row[0],
            "score": row[1],
            "weekend_date": row[2],
            "weekend_rank": row[3]
        }
        for row in c.fetchall()
    ]

    # --- Top 3 weekend score averages for active players ---
    # Requires at least 5 weekends played to qualify
    c.execute("""
        SELECT p.player_tag, ROUND(AVG(tr.score)) AS avg_score, COUNT(tr.score) AS weekends_played
        FROM tournament_results tr
        JOIN players p ON tr.player_id = p.id
        WHERE p.on_team = 1
          AND tr.score > 0
        GROUP BY tr.player_id
        HAVING weekends_played >= 5
        ORDER BY avg_score DESC
        LIMIT 3
    """)
    top_player_averages = [
        {
            "player_tag": row[0],
            "avg_score": int(row[1]),
            "weekends_played": row[2]
        }
        for row in c.fetchall()
    ]

    report = {
        "top_team_scores": top_team_scores,
        "top_player_scores": top_player_scores,
        "top_player_averages": top_player_averages
    }

    with open(json_path, 'w') as f:
        json.dump(report, f, default=str, indent=2)

    conn.close()
    return json.dumps(report, default=str, indent=2)


def main():
    env_tools = EnvTools()

    db_path = os.path.join(env_tools.find_repo_root(), 'player_metrics.db')
    print(db_path)

    json_folder = os.path.join(env_tools.find_repo_root(), 'docs')
    json_path = os.path.join(json_folder, 'alltime_highlights.json')

    result = generate_alltime_highlights(db_path, json_path)
    print(result)


if __name__ == '__main__':
    main()
