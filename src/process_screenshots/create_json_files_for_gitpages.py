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

def create_json_files():
    env_tools = EnvTools()

    # Connect to SQLite
    db_path = os.path.join(env_tools.find_repo_root(), 'player_metrics.db')
    print(db_path)

    conn = sqlite3.connect(db_path)

    json_folder = os.path.join(env_tools.find_repo_root(),'docs')

    # First Query: All Player Metrics
    query1 = """SELECT * FROM player_all_metrics;"""
    cursor1 = conn.cursor()
    cursor1.execute(query1)
    columns1 = [desc[0] for desc in cursor1.description]
    data1 = [dict(zip(columns1, row)) for row in cursor1.fetchall()]
    json_path = os.path.join(json_folder, 'all_player_metrics.json')
    with open(json_path, 'w') as f:
        json.dump(data1, f, indent=4)

    # Second Query: Recent Tournament Metrics
    query2 = """SELECT * FROM team_players_last_three_months;"""
    cursor2 = conn.cursor()
    cursor2.execute(query2)
    columns2 = [desc[0] for desc in cursor2.description]
    data2 = [dict(zip(columns2, row)) for row in cursor2.fetchall()]
    json_path = os.path.join(json_folder, 'recent_tournament_metrics.json')
    with open(json_path, 'w') as f:
        json.dump(data2, f, indent=4)

    conn.close()

def main():
    global script_name, script_directory

    # Get the script name without the extension
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    script_dir = os.path.dirname(os.path.abspath(__file__))

    create_json_files()

if __name__ == '__main__':
    main()