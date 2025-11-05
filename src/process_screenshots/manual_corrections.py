import fnmatch
import json
import logging
import pytesseract
import os
import re
import sqlite3
import sys
import time

from calendar import week
from numpy import insert
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image, ImageOps
from requests import get
from sympy import im

try:
    from cls_env_config import EnvConfigSingleton as EnvConfig
    from cls_env_tools import EnvTools
    from cls_img_tools import ImageTools
    from cls_logging_manager import LoggingManagerSingleton as LoggingManager
    from cls_string_helpers import StringHelpers

    from cls_db_tools import DbRepositorySingleton
except ImportError as e:
    logging.error(f"Error importing required modules: {e}")
    sys.exit(1)

# Initialize the dictionary
weekend_data = {}

# Adding a weekend date
weekend_date = "2025-07-27"
if weekend_date not in weekend_data:
    weekend_data[weekend_date] = set()  # Create an empty set for the weekend date

weekend_data[weekend_date].add(("loulou", 1901))

#weekend_data[weekend_date].add(("Nirazz", 94))
#weekend_data[weekend_date].add(("trrr", 22))
#weekend_data[weekend_date].add(("Punches616", 0))
#weekend_data[weekend_date].add(("vfo", 78))
#weekend_data[weekend_date].add(("justme", 43))
#weekend_data[weekend_date].add(("cariann", 1045))
#weekend_data[weekend_date].add(("jon", 0))
#weekend_data[weekend_date].add(("Da'man", 57))
#weekend_data[weekend_date].add(("val", 0))
#weekend_data[weekend_date].add(("Hobbes", 0))
#weekend_data[weekend_date].add(("Stormy", 0))
#weekend_data[weekend_date].add(("fin", 3145))
#weekend_data[weekend_date].add(("Weeminx", 15005))
#weekend_data[weekend_date].add(("Dewey", 5054))
#weekend_data[weekend_date].add(("JoCo", 4998))
#weekend_data[weekend_date].add(("Sienna", 4819))
#weekend_data[weekend_date].add(("Siley", 3796))
#weekend_data[weekend_date].add(("Mar", 3732))
#weekend_data[weekend_date].add(("Jay", 3661))
#weekend_data[weekend_date].add(("Gardener", 3269))
#weekend_data[weekend_date].add(("Suriel", 3029))
#weekend_data[weekend_date].add(("Burpalot", 2894))
#weekend_data[weekend_date].add(("Laura", 2874))
#weekend_data[weekend_date].add(("Pop", 2693))
#weekend_data[weekend_date].add(("Grandmaphyll", 2392))
#weekend_data[weekend_date].add(("Springerpup", 2193))
#weekend_data[weekend_date].add(("ZMewis", 1819))
#weekend_data[weekend_date].add(("FleurDeLys", 1711))
#weekend_data[weekend_date].add(("Mary", 1653))
#weekend_data[weekend_date].add(("Marbl", 1566))
#weekend_data[weekend_date].add(("Tedbilly", 1470))
#weekend_data[weekend_date].add(("Stranger", 1398))
#weekend_data[weekend_date].add(("Kay", 1374))
#weekend_data[weekend_date].add(("Spudly", 1343))
#weekend_data[weekend_date].add(("Mike", 1302))
#weekend_data[weekend_date].add(("Fin", 1184))
#weekend_data[weekend_date].add(("Wilbur", 1106))
#weekend_data[weekend_date].add(("Quinn", 1006))
#weekend_data[weekend_date].add(("Cheech", 920))
#weekend_data[weekend_date].add(("Maggie", 900))
#weekend_data[weekend_date].add(("justme", 883))
#weekend_data[weekend_date].add(("Ami", 665))
#weekend_data[weekend_date].add(("Trick", 664))
#weekend_data[weekend_date].add(("Soggy", 619))
#weekend_data[weekend_date].add(("Hunny", 423))
#weekend_data[weekend_date].add(("Murphy", 359))
#weekend_data[weekend_date].add(("Nvk", 334))
#weekend_data[weekend_date].add(("Akp", 271))
#weekend_data[weekend_date].add(("Giddyupjenny", 219))

def get_weekend_dates(file_date_str: str) -> tuple:
    """
    Calculate the weekend date (Sunday) and the Friday date for a given tournament date.
    """
    tournament_date = datetime.strptime(file_date_str, "%Y-%m-%d")
    sunday_date = tournament_date + timedelta(days=(6 - tournament_date.weekday()))
    friday_date = sunday_date - timedelta(days=2)

    return sunday_date.strftime("%Y-%m-%d"), friday_date.strftime("%Y-%m-%d")

def process_manual_corrections():

    for weekend_date, tuples in weekend_data.items():
        sunday_date, friday_date = get_weekend_dates(weekend_date)

        print(f"Weekend Date: {sunday_date}, Scores: {tuples}")

        for player_tag, score in tuples:
            player_id = db_repository.get_player_id_create_if_new(player_tag, friday_date)
            if player_id is None:
                print(f"Player ID not found for tag: {player_tag}, adding for weekend date: {weekend_date} with start date: {friday_date}")
                continue

            db_repository.update_player_start_date(player_tag.lower(), friday_date)
            print(f"Insert Player {player_tag} ID: {player_id}, Score: {score} for weekend date: {weekend_date}")
            db_repository.upsert_weekend_player_score(sunday_date, player_id, score)

        print(f"Updating scores for weekend date: {sunday_date}")
        db_repository.update_ranks_for_weekend_date(sunday_date)

    return


def main():
    global db_repository

    env_config = EnvConfig()

    repo_root = EnvTools.find_repo_root()

    db_path_config = env_config.merged_config['constants']['db_path']
    db_path = db_path_config.replace("{repo_root}", str(repo_root))

    db_repository = DbRepositorySingleton(db_path)

    process_manual_corrections()

    db_repository.cleanup()

    return

if __name__ == "__main__":
    global script_name, script_directory

    # Get the script name without the extension
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    #script_folder = os.getcwd()

    main()